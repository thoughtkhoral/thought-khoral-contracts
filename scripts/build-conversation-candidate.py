#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build or verify an unreleased, externally anchored conversation candidate."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile


PROFILE = 'thought-khoral.agent-conversation.v1'
PROPOSED_TAG = 'thought-khoral-agent-conversation-v1.1.0'
PREFIX = 'thought-khoral-contracts/'
METADATA = {
    'profile': PROFILE,
    'status': 'unreleased-local-candidate',
    'proposedTag': PROPOSED_TAG,
    'repository': 'https://github.com/thoughtkhoral/thought-khoral-contracts',
    'archivePrefix': PREFIX,
    'baseTag': 'thought-khoral-agent-conversation-v1.0.0',
    'baseCommit': '85baf86e574276fcd036e53e23641af6aad602f9',
    'baseArchiveSha256': '0038fdbf858db013c4a269aeedbca51a5db9128a2f1d6e39754f92ba60fd8f36',
}
DIRECTORIES = ('schemas/agent-conversation-v1/', 'fixtures/agent-conversation-v1/',
               'fixtures/agent-conversation-v1.1/')
TEST_FILES = ('test/conversation-validation.mjs', 'test/validate-conversation-fixtures.mjs',
              'test/validate-default-settings-fixtures.mjs')
LOCK_KEYS = set(METADATA) | {'commit', 'archiveFile', 'archiveSha256', 'files'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(*args, data=None):
    return subprocess.check_output(['git', *args], input=data, stderr=subprocess.PIPE)


def archive_name(commit):
    return f'{PROPOSED_TAG}-candidate-{commit}.tar'


def archive_payload(archive, commit):
    require(git('get-tar-commit-id', data=archive).decode().strip() == commit,
            'archive commit metadata mismatch')
    payload = {}
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:') as tar:
        for member in tar.getmembers():
            path = PurePosixPath(member.name)
            require((member.name.startswith(PREFIX) or
                     (member.isdir() and member.name == PREFIX.rstrip('/'))) and not path.is_absolute()
                    and '..' not in path.parts and str(path) == member.name.rstrip('/'),
                    'unsafe archive path')
            require(member.name not in seen, 'duplicate archive path')
            seen.add(member.name)
            require(member.isdir() or member.isfile(), 'archive symlink or unsupported entry')
            if member.isfile():
                relative = member.name[len(PREFIX):]
                if relative.startswith(DIRECTORIES) or relative in TEST_FILES:
                    payload[relative] = tar.extractfile(member).read()
    require(all(path in payload for path in TEST_FILES), 'missing candidate fixture verifier')
    require('schemas/agent-conversation-v1/resolved-settings.schema.json' in payload,
            'missing resolved settings schema')
    for directory in DIRECTORIES:
        require(any(path.startswith(directory) for path in payload), 'missing candidate payload directory')
    for directory in DIRECTORIES[1:]:
        require(directory + 'manifest.json' in payload, 'missing candidate fixture manifest')
    return dict(sorted(payload.items()))


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate lock metadata key')
        result[key] = value
    return result


def verify(candidate, anchor):
    require(re.fullmatch(r'[0-9a-f]{64}', anchor) is not None, 'invalid external lock digest')
    require(candidate.is_dir() and not candidate.is_symlink(), 'candidate symlink or missing directory')
    for path in candidate.rglob('*'):
        require(not path.is_symlink(), 'candidate symlink rejected')
        require(path.is_dir() or path.is_file(), 'unsupported candidate entry')
    lock_bytes = (candidate / 'lock.json').read_bytes()
    require(digest(lock_bytes) == anchor, 'lock digest mismatch with external anchor')
    lock = json.loads(lock_bytes, object_pairs_hook=reject_duplicate_keys)
    require(type(lock) is dict and set(lock) == LOCK_KEYS, 'closed lock metadata mismatch')
    require(all(lock[key] == value for key, value in METADATA.items()), 'candidate metadata mismatch')
    commit = lock['commit']
    require(type(commit) is str and re.fullmatch(r'[0-9a-f]{40}', commit) is not None,
            'invalid commit metadata')
    require(candidate.name == commit and lock['archiveFile'] == archive_name(commit),
            'candidate commit metadata mismatch')
    require(set(path.name for path in candidate.iterdir()) ==
            {'lock.json', 'lock.sha256', 'vendor', lock['archiveFile']}, 'unexpected candidate file')
    require((candidate / 'lock.sha256').read_text() == anchor + '\n', 'lock digest sidecar mismatch')
    archive = (candidate / lock['archiveFile']).read_bytes()
    require(digest(archive) == lock['archiveSha256'], 'archive digest mismatch')
    payload = archive_payload(archive, commit)
    expected_hashes = {path: digest(data) for path, data in payload.items()}
    require(type(lock['files']) is dict and lock['files'] == expected_hashes
            and list(lock['files']) == sorted(lock['files']), 'payload digest metadata mismatch')
    vendor = candidate / 'vendor'
    require(vendor.is_dir(), 'missing vendor directory')
    expected_dirs = set()
    for path in payload:
        expected_dirs.update(str(parent) for parent in PurePosixPath(path).parents if str(parent) != '.')
    for path in vendor.rglob('*'):
        relative = path.relative_to(vendor).as_posix()
        require(relative in (expected_dirs if path.is_dir() else payload), 'unexpected payload file')
    actual_files = {path.relative_to(vendor).as_posix() for path in vendor.rglob('*') if path.is_file()}
    require(actual_files == set(payload), 'missing payload file')
    for path, data in payload.items():
        require(digest((vendor / path).read_bytes()) == expected_hashes[path], f'payload digest mismatch: {path}')
    return {'candidateDirectory': str(candidate), 'commit': commit,
            'archiveSha256': lock['archiveSha256'], 'lockSha256': anchor}


def build(revision, output):
    require(not git('status', '--porcelain', '--untracked-files=all').strip(), 'dirty source rejected')
    commit = git('rev-parse', '--verify', revision + '^{commit}').decode().strip()
    candidate = output / commit
    require(not candidate.exists() and not candidate.is_symlink(), 'existing candidate directory rejected')
    archive = git('archive', '--format=tar', '--prefix=' + PREFIX, commit)
    payload = archive_payload(archive, commit)
    lock = {**METADATA, 'commit': commit, 'archiveFile': archive_name(commit),
            'archiveSha256': digest(archive), 'files': {path: digest(data) for path, data in payload.items()}}
    lock_bytes = (json.dumps(lock, indent=2) + '\n').encode('utf-8')
    anchor = digest(lock_bytes)
    candidate.mkdir(parents=True, exist_ok=False)
    (candidate / lock['archiveFile']).write_bytes(archive)
    (candidate / 'lock.json').write_bytes(lock_bytes)
    (candidate / 'lock.sha256').write_text(anchor + '\n')
    for path, data in payload.items():
        target = candidate / 'vendor' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return verify(candidate, anchor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--lock-sha256')
    args = parser.parse_args()
    if args.verify:
        if not args.lock_sha256 or args.commit or args.output:
            parser.error('--verify requires --lock-sha256 and forbids build arguments')
        result = verify(args.verify.absolute(), args.lock_sha256)
    else:
        if not args.commit or not args.output or args.lock_sha256:
            parser.error('building requires --commit and --output')
        result = build(args.commit, args.output.absolute())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError, tarfile.TarError) as error:
        print(f'candidate rejected: {error}', file=sys.stderr)
        sys.exit(1)
