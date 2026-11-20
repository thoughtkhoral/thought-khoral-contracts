# Conversation v1.1 release preparation

Status: local implementation authorized on 2026-11-20 through approval of the
[root Task 9 procedure](https://github.com/thoughtkhoral/thought-khoral/blob/main/.ai/specs/how/task9-packaged-acceptance-2026-11-20.md)
and its platform execution plan. This details Task A under existing accepted
[contracts issue 1](https://github.com/thoughtkhoral/thought-khoral-contracts/issues/1)
and the [conversation How](agent-conversation-profile.md). It does not authorize
source publication, tag/release publication, consumer activation or provider use.

## Inputs and immutable payload

Prepare `thought-khoral-agent-conversation-v1.1.0` from a clean committed
checkout. Require its schema/fixture/oracle payload to match the approved
candidate commit `1ea828f28725ddaaefa21d083473f9abbd777975` exactly; fail on any
added, removed or changed payload entry. Compare all schemas and fixtures from
published v1.0 source `85baf86e574276fcd036e53e23641af6aad602f9` byte for byte.
The v1.0 shared oracle's additive defaults validation is already reviewed in the
candidate; it is not an unchanged-v1.0 oracle claim. No schema, fixture,
dependency, retained room contract or candidate builder changes are authorized.

## Local preparer and release lock

Add `scripts/prepare-conversation-release.py` using only the Python standard
library and Git. Reuse the candidate builder's strict archive parsing, payload
selection and duplicate-key rejection without altering candidate behavior.
`--commit COMMIT --output DIRECTORY` builds a complete deterministic Git TAR
with `thought-khoral-contracts/` prefix and the release filename
`thought-khoral-agent-conversation-v1.1.0.tar`. Source must be clean and its
selected commit must equal HEAD. Refuse an existing output directory.

Output directory is named by the full source commit and contains the TAR,
`lock.json`, `lock.sha256` and `vendor/`. Lock JSON has exactly these fields:
`profile`, `repository`, `tag`, `commit`, `archiveFile`, `archivePrefix`,
`archiveUrl`, `archiveSha256`, `files`. `files` uses sorted repository-relative
payload paths, matching candidate payload paths, with SHA-256 values. This is
the v1.1 consumer layout; it does not rewrite a v1.0 consumer lock. The URL names
the intended immutable release TAR asset and is not evidence of publication.
No candidate `status` or `proposedTag` field is relabeled as a release claim.

`--verify DIRECTORY --lock-sha256 DIGEST` requires an external reviewed lock
anchor. Validate closed metadata, commit/filename binding, TAR digest and Git
commit metadata, exact payload hashes and extracted vendor bytes. Reject
symlinks, unsupported entries, missing/extra payload and output files, duplicate
JSON keys and tampering. Verification does not contact GitHub or establish that
the intended release URL exists. Build/verify output explicitly states
`publication: not-performed`.

## Verification and review package

Add meaningful Python unittest coverage for deterministic repeated builds,
independent archive extraction and hashes, dirty/non-HEAD source, schema or
oracle drift from the accepted candidate, altered archive/vendor/lock,
symlinks, extra/missing files and missing external anchor. Observe failures
before implementing the preparer. Run these tests through `npm test` alongside
all existing suites without adding dependencies.

After committing the source, prepare twice outside Git and require identical
TAR and lock bytes. Extract the TAR to a clean external directory, install the
existing locked dependencies, run all packaged tests and `npm audit`. Record
fixture counts, immutable source/archive/lock hashes, the exact candidate
payload comparison, v1.0 schema/fixture preservation, legal/license review and
source-publication status. The full TAR includes verifier tooling and public
documentation; only the fixed payload subset belongs in consumer vendors.

Write review notes beside the assets with explicit unpublished status. Public
notes contain no credentials or private state. Publication approval must name
the actual source commit, intended tag and asset hashes. Only after publication
and download verification may consumers adopt the release and the Task 9 live
profile freeze those release identities. Stop at this concrete publication
checkpoint rather than manufacturing released provenance.

## Baseline test harness correction

The unchanged baseline on Node 25.5.0 fails its candidate test when `git show`
returns the intentional 1,050,802-byte context-overflow fixture: spawnSync's
default 1 MiB buffer produces ENOBUFS and no exit status. A controlled 2 MiB
probe returns all bytes with exit zero. Increase only that test's bounded Git
blob buffer to 2 MiB and expose subprocess errors in its assertion. Keep the
oversized negative fixture and all byte comparisons intact. This is necessary
to run the required full extracted-archive verification; no runtime bound or
contract byte changes.
