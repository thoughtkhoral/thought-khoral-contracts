#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Exercise the local release preparer using actual Git archives and file mutation."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
SCRIPT = SOURCE / 'scripts/prepare-conversation-release.py'
TAG = 'thought-khoral-agent-conversation-v1.1.0'


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='conversation-release-')
        cls.root = Path(cls.temporary.name)
        cls.repo = cls.root / 'source'
        shutil.copytree(SOURCE, cls.repo, ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__'))
        subprocess.run(['git', 'init', '--quiet', str(cls.repo)], check=True)
        cls.git('add', '.')
        cls.git('-c', 'user.name=Release Test', '-c', 'user.email=release@example.invalid',
                'commit', '--quiet', '-m', 'synthetic packaged release source')
        cls.commit = cls.git('rev-parse', 'HEAD').stdout.strip()

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    @classmethod
    def git(cls, *args):
        return subprocess.run(['git', '-C', str(cls.repo), *args], capture_output=True, text=True, check=True)

    def run_script(self, *args):
        return subprocess.run(['python3', str(SCRIPT), *map(str, args)], cwd=self.repo,
                              capture_output=True, text=True)

    def build(self):
        output = Path(tempfile.mkdtemp(dir=self.root))
        result = self.run_script('--commit', self.commit, '--output', output)
        self.assertEqual(result.returncode, 0, result.stderr)
        info = json.loads(result.stdout)
        self.assertEqual(info['publication'], 'not-performed')
        return Path(info['releaseDirectory']), info

    def verify(self, path, anchor):
        return self.run_script('--verify', path, '--lock-sha256', anchor)

    def test_deterministic_archive_and_independent_vendor_comparison(self):
        first, info = self.build()
        second, other = self.build()
        self.assertEqual(info['archiveSha256'], other['archiveSha256'])
        self.assertEqual(info['lockSha256'], other['lockSha256'])
        lock = json.loads((first / 'lock.json').read_bytes())
        self.assertEqual(lock['tag'], TAG)
        self.assertNotIn('status', lock)
        self.assertNotIn('proposedTag', lock)
        self.assertEqual(lock['archiveFile'], TAG + '.tar')
        archive = (first / lock['archiveFile']).read_bytes()
        self.assertEqual(hashlib.sha256(archive).hexdigest(), lock['archiveSha256'])
        self.assertEqual(archive, (second / lock['archiveFile']).read_bytes())
        extracted = Path(tempfile.mkdtemp(dir=self.root))
        subprocess.run(['tar', '-xf', str(first / lock['archiveFile']), '-C', str(extracted)], check=True)
        for name, digest in lock['files'].items():
            original = (extracted / 'thought-khoral-contracts' / name).read_bytes()
            self.assertEqual(hashlib.sha256(original).hexdigest(), digest, name)
            self.assertEqual((first / 'vendor' / name).read_bytes(), original)
        self.assertIn('schemas/agent-conversation-v1/resolved-settings.schema.json', lock['files'])
        self.assertEqual(self.verify(first, info['lockSha256']).returncode, 0)
        self.assertNotEqual(self.run_script('--commit', self.commit, '--output', first.parent).returncode, 0)

    def test_dirty_and_non_head_source_refused_without_output(self):
        dirty = self.repo / 'unexpected.txt'
        dirty.write_text('untracked\n')
        output = self.root / 'dirty-output'
        try:
            result = self.run_script('--commit', self.commit, '--output', output)
            self.assertIn('dirty source', result.stderr)
            self.assertFalse(output.exists())
        finally:
            dirty.unlink()
        result = self.run_script('--commit', 'HEAD^', '--output', output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('HEAD', result.stderr)

    def test_committed_schema_and_oracle_drift_refused(self):
        for name in ['schemas/agent-conversation-v1/resolved-settings.schema.json',
                     'test/conversation-validation.mjs']:
            path = self.repo / name
            path.write_bytes(path.read_bytes() + b'\n')
            self.git('add', name)
            self.git('-c', 'user.name=Release Test', '-c', 'user.email=release@example.invalid',
                     'commit', '--quiet', '-m', 'synthetic drift')
            try:
                head = self.git('rev-parse', 'HEAD').stdout.strip()
                result = self.run_script('--commit', head, '--output', self.root / 'drift')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('approved candidate', result.stderr)
            finally:
                self.git('reset', '--hard', self.commit)

    def test_archive_vendor_metadata_symlink_and_extra_file_tampering_refused(self):
        for mutation in ['archive', 'vendor', 'metadata', 'symlink', 'extra', 'missing']:
            with self.subTest(mutation=mutation):
                path, info = self.build()
                if mutation == 'archive':
                    with (path / (TAG + '.tar')).open('ab') as out:
                        out.write(b'tamper')
                elif mutation == 'vendor':
                    (path / 'vendor/schemas/agent-conversation-v1/resolved-settings.schema.json').write_text('{}')
                elif mutation == 'metadata':
                    lock = json.loads((path / 'lock.json').read_text())
                    lock['status'] = 'published'
                    data = (json.dumps(lock, indent=2) + '\n').encode()
                    (path / 'lock.json').write_bytes(data)
                    info['lockSha256'] = hashlib.sha256(data).hexdigest()
                    (path / 'lock.sha256').write_text(info['lockSha256'] + '\n')
                elif mutation == 'symlink':
                    entry = path / 'vendor/test/conversation-validation.mjs'
                    entry.unlink()
                    entry.symlink_to(self.repo / 'test/conversation-validation.mjs')
                elif mutation == 'extra':
                    (path / 'unexpected').write_text('unexpected')
                else:
                    (path / 'vendor/test/conversation-validation.mjs').unlink()
                self.assertNotEqual(self.verify(path, info['lockSha256']).returncode, 0)

    def test_external_anchor_required_and_wrong_anchor_refused(self):
        path, info = self.build()
        self.assertNotEqual(self.run_script('--verify', path).returncode, 0)
        self.assertNotEqual(self.verify(path, '0' * 64).returncode, 0)
        self.assertNotEqual(self.verify(path, '../invalid').returncode, 0)


if __name__ == '__main__':
    unittest.main()
