#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare or verify immutable v1.1 release inputs without publishing anything."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tarfile

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('candidate', Path(__file__).with_name('build-conversation-candidate.py'))
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
require, digest, git = candidate.require, candidate.digest, candidate.git
TAG = 'thought-khoral-agent-conversation-v1.1.0'
ARCHIVE = TAG + '.tar'
APPROVED = '1ea828f28725ddaaefa21d083473f9abbd777975'
BASE = '85baf86e574276fcd036e53e23641af6aad602f9'
PINS_SHA256 = 'f013d5a4eb7ac69555b0aa75f7b7769e90fe2aa4f567fc6517e4c58216f5fda7'
METADATA = {
    'profile': candidate.PROFILE,
    'repository': 'https://github.com/thoughtkhoral/thought-khoral-contracts',
    'tag': TAG,
    'archiveFile': ARCHIVE,
    'archivePrefix': candidate.PREFIX,
    'archiveUrl': f'https://github.com/thoughtkhoral/thought-khoral-contracts/releases/download/{TAG}/{ARCHIVE}',
}


def archive_for(commit):
    return git('archive', '--format=tar', '--prefix=' + candidate.PREFIX, commit)


def approved_payload(payload):
    raw = Path(__file__).with_name('conversation-v1.1-payload-pins.json').read_bytes()
    require(digest(raw) == PINS_SHA256, 'approved candidate hash inventory altered')
    pins = json.loads(raw, object_pairs_hook=candidate.reject_duplicate_keys)
    require(pins['candidateCommit'] == APPROVED and pins['publishedV1Commit'] == BASE,
            'approved candidate provenance mismatch')
    hashes = {name: digest(data) for name, data in payload.items()}
    require(hashes == pins['files'], 'payload differs from approved candidate')
    for name, expected in pins['unchangedV1SchemaFixtureFiles'].items():
        require(hashes.get(name) == expected, 'published v1.0 payload changed: ' + name)
    return len(pins['unchangedV1SchemaFixtureFiles'])


def verify(directory, anchor):
    require(re.fullmatch(r'[0-9a-f]{64}', anchor) is not None, 'invalid external lock anchor')
    require(directory.is_dir() and not directory.is_symlink(), 'missing release directory or symlink')
    for path in directory.rglob('*'):
        require(not path.is_symlink(), 'release symlink rejected')
        require(path.is_file() or path.is_dir(), 'unsupported release entry')
    require({p.name for p in directory.iterdir()} == {ARCHIVE, 'lock.json', 'lock.sha256', 'vendor'},
            'unexpected or missing release file')
    lock_bytes = (directory / 'lock.json').read_bytes()
    require(digest(lock_bytes) == anchor, 'lock digest differs from external anchor')
    lock = json.loads(lock_bytes, object_pairs_hook=candidate.reject_duplicate_keys)
    require(type(lock) is dict and set(lock) == set(METADATA) | {'commit', 'archiveSha256', 'files'},
            'closed release metadata mismatch')
    require(all(lock[k] == v for k, v in METADATA.items()), 'release metadata mismatch')
    commit = lock['commit']
    require(type(commit) is str and re.fullmatch(r'[0-9a-f]{40}', commit) is not None,
            'invalid source commit')
    require(directory.name == commit, 'release directory/source commit mismatch')
    require((directory / 'lock.sha256').read_text() == anchor + '\n', 'lock sidecar mismatch')
    archive = (directory / ARCHIVE).read_bytes()
    require(digest(archive) == lock['archiveSha256'], 'archive digest mismatch')
    payload = candidate.archive_payload(archive, commit)
    approved_payload(payload)
    hashes = {name: digest(data) for name, data in payload.items()}
    require(type(lock['files']) is dict and lock['files'] == hashes
            and list(lock['files']) == sorted(lock['files']), 'payload metadata mismatch')
    vendor = directory / 'vendor'
    require(vendor.is_dir(), 'missing vendor directory')
    directories = {str(p) for name in payload for p in Path(name).parents if str(p) != '.'}
    for path in vendor.rglob('*'):
        relative = path.relative_to(vendor).as_posix()
        require(relative in (directories if path.is_dir() else payload), 'unexpected vendor entry')
    require({p.relative_to(vendor).as_posix() for p in vendor.rglob('*') if p.is_file()} == set(payload),
            'missing vendor file')
    for name, data in payload.items():
        require((vendor / name).read_bytes() == data, 'vendor bytes mismatch: ' + name)
    return {'releaseDirectory': str(directory), 'commit': commit,
            'archiveSha256': lock['archiveSha256'], 'lockSha256': anchor,
            'payloadFiles': len(payload), 'publication': 'not-performed'}


def build(revision, output):
    require(not git('status', '--porcelain', '--untracked-files=all').strip(), 'dirty source rejected')
    commit = git('rev-parse', '--verify', revision + '^{commit}').decode().strip()
    require(commit == git('rev-parse', 'HEAD').decode().strip(), 'release source must equal HEAD')
    directory = output / commit
    require(not directory.exists() and not directory.is_symlink(), 'existing release output rejected')
    archive = archive_for(commit)
    payload = candidate.archive_payload(archive, commit)
    preserved = approved_payload(payload)
    lock = {**METADATA, 'commit': commit, 'archiveSha256': digest(archive),
            'files': {name: digest(data) for name, data in payload.items()}}
    lock_bytes = (json.dumps(lock, indent=2) + '\n').encode()
    anchor = digest(lock_bytes)
    directory.mkdir(parents=True, exist_ok=False)
    (directory / ARCHIVE).write_bytes(archive)
    (directory / 'lock.json').write_bytes(lock_bytes)
    (directory / 'lock.sha256').write_text(anchor + '\n')
    for name, data in payload.items():
        target = directory / 'vendor' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return {**verify(directory, anchor), 'approvedCandidate': APPROVED,
            'unchangedV1SchemaFixtureFiles': preserved}


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
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError, tarfile.TarError) as error:
        print(f'release preparation rejected: {error}', file=sys.stderr)
        sys.exit(1)
