// SPDX-License-Identifier: Apache-2.0
import assert from 'node:assert/strict';
import { after, before, test } from 'node:test';
import { mkdtemp, mkdir, cp, readFile, writeFile, readdir, rm, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const source = fileURLToPath(new URL('../', import.meta.url));
const builder = join(source, 'scripts/build-conversation-candidate.py');
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const run = (command, args, cwd) => spawnSync(command, args, { cwd, encoding: 'utf8' });
const mustRun = (command, args, cwd) => {
  const result = run(command, args, cwd);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  return result.stdout.trim();
};
let root, repository, commit, candidate, digest;
before(async () => {
  root = await mkdtemp(join(tmpdir(), 'conversation-candidate-'));
  repository = join(root, 'source');
  await mkdir(repository);
  for (const entry of await readdir(source)) {
    if (entry !== '.git' && entry !== 'node_modules') await cp(join(source, entry), join(repository, entry), { recursive: true });
  }
  mustRun('git', ['init', '--quiet'], repository);
  mustRun('git', ['add', '.'], repository);
  mustRun('git', ['-c', 'user.name=Candidate Test', '-c', 'user.email=candidate@example.invalid', 'commit', '--quiet', '-m', 'synthetic candidate source'], repository);
  commit = mustRun('git', ['rev-parse', 'HEAD'], repository);
});
after(async () => { if (root) await rm(root, { recursive: true, force: true }); });
const build = output => run('python3', [builder, '--commit', commit, '--output', output], repository);
const verify = (path, anchor = digest) => run('python3', [builder, '--verify', path, '--lock-sha256', anchor], repository);
const copyCandidate = async name => {
  const path = join(root, name, commit);
  await cp(candidate, path, { recursive: true });
  return path;
};

test('builds committed source twice with identical archive, closed lock and exact payload hashes', async () => {
  const first = build(join(root, 'first'));
  assert.equal(first.status, 0, first.stderr);
  const info = JSON.parse(first.stdout);
  candidate = info.candidateDirectory;
  assert.equal(candidate, join(root, 'first', commit));
  assert.equal(info.commit, commit);
  const lockBytes = await readFile(join(candidate, 'lock.json'));
  digest = sha256(lockBytes);
  assert.equal(info.lockSha256, digest);
  assert.equal((await readFile(join(candidate, 'lock.sha256'), 'utf8')).trim(), digest);
  const lock = JSON.parse(lockBytes);
  assert.deepEqual(Object.keys(lock).sort(), ['profile','status','proposedTag','repository','commit','archiveFile','archiveSha256','archivePrefix','baseTag','baseCommit','baseArchiveSha256','files'].sort());
  assert.equal(lock.status, 'unreleased-local-candidate');
  assert.equal(lock.commit, commit);
  assert.equal(lock.archiveFile, `thought-khoral-agent-conversation-v1.1.0-candidate-${commit}.tar`);
  const archive = await readFile(join(candidate, lock.archiveFile));
  assert.equal(info.archiveSha256, sha256(archive));
  assert.equal(lock.archiveSha256, sha256(archive));
  assert.deepEqual(Object.keys(lock.files), Object.keys(lock.files).sort());
  for (const [path, hash] of Object.entries(lock.files)) {
    const committed = spawnSync('git', ['show', `${commit}:${path}`], { cwd: repository });
    assert.equal(committed.status, 0);
    assert.equal(hash, sha256(committed.stdout), path);
    assert.deepEqual(await readFile(join(candidate, 'vendor', path)), committed.stdout, path);
  }
  assert.ok(lock.files['schemas/agent-conversation-v1/resolved-settings.schema.json']);
  assert.ok(lock.files['fixtures/agent-conversation-v1.1/manifest.json']);
  const second = build(join(root, 'second'));
  assert.equal(second.status, 0, second.stderr);
  const other = JSON.parse(second.stdout).candidateDirectory;
  assert.deepEqual(await readFile(join(other, 'lock.json')), lockBytes);
  assert.deepEqual(await readFile(join(other, lock.archiveFile)), archive);
  assert.equal(verify(candidate).status, 0);
  const extracted = join(root, 'extracted');
  await mkdir(extracted);
  mustRun('tar', ['-xf', join(candidate, lock.archiveFile), '-C', extracted], repository);
  assert.deepEqual(await readFile(join(extracted, 'thought-khoral-contracts/package-lock.json')), await readFile(join(repository, 'package-lock.json')));
  assert.deepEqual(await readFile(join(extracted, 'thought-khoral-contracts/test/validate-fixtures.mjs')), await readFile(join(repository, 'test/validate-fixtures.mjs')));
});

test('refuses tracked or untracked dirty source and refuses an existing candidate', async () => {
  assert.equal(build(join(root, 'first')).status, 1);
  await writeFile(join(repository, 'README.md'), 'dirty source\n', { flag: 'a' });
  const tracked = build(join(root, 'dirty-tracked'));
  assert.equal(tracked.status, 1);
  assert.match(tracked.stderr, /dirty source/);
  mustRun('git', ['restore', 'README.md'], repository);
  await writeFile(join(repository, 'unexpected-source.txt'), 'untracked\n');
  assert.match(build(join(root, 'dirty-untracked')).stderr, /dirty source/);
  await rm(join(repository, 'unexpected-source.txt'));
});

test('rejects an altered archive', async () => {
  const path = await copyCandidate('archive-changed');
  const lock = JSON.parse(await readFile(join(path, 'lock.json')));
  await writeFile(join(path, lock.archiveFile), 'changed', { flag: 'a' });
  const result = verify(path);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /archive digest/);
});

test('rejects altered payload bytes', async () => {
  const path = await copyCandidate('payload-changed');
  await writeFile(join(path, 'vendor/schemas/agent-conversation-v1/resolved-settings.schema.json'), '{}\n');
  const result = verify(path);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /payload digest/);
});

test('rejects symlink payloads and unexpected payload or candidate files', async () => {
  const linked = await copyCandidate('symlink');
  const payload = join(linked, 'vendor/test/conversation-validation.mjs');
  await rm(payload);
  await symlink(join(repository, 'test/conversation-validation.mjs'), payload);
  assert.match(verify(linked).stderr, /symlink/);
  const extra = await copyCandidate('extra-payload');
  await writeFile(join(extra, 'vendor/unexpected.json'), '{}\n');
  assert.match(verify(extra).stderr, /unexpected payload/);
  const extraRoot = await copyCandidate('extra-root');
  await writeFile(join(extraRoot, 'unexpected.json'), '{}\n');
  assert.match(verify(extraRoot).stderr, /unexpected candidate/);
});

test('requires an external lock anchor and rejects self-consistent metadata tampering', async () => {
  const noAnchor = run('python3', [builder, '--verify', candidate], repository);
  assert.notEqual(noAnchor.status, 0);
  const path = await copyCandidate('metadata');
  const lock = JSON.parse(await readFile(join(path, 'lock.json')));
  lock.status = 'published';
  const bytes = Buffer.from(JSON.stringify(lock, null, 2) + '\n');
  await writeFile(join(path, 'lock.json'), bytes);
  await writeFile(join(path, 'lock.sha256'), sha256(bytes) + '\n');
  assert.match(verify(path).stderr, /lock digest/);
  assert.match(verify(path, sha256(bytes)).stderr, /metadata/);
  lock.status = 'unreleased-local-candidate';
  lock.releaseUrl = 'https://example.invalid/release';
  const widened = Buffer.from(JSON.stringify(lock, null, 2) + '\n');
  await writeFile(join(path, 'lock.json'), widened);
  await writeFile(join(path, 'lock.sha256'), sha256(widened) + '\n');
  assert.match(verify(path, sha256(widened)).stderr, /metadata/);
});
