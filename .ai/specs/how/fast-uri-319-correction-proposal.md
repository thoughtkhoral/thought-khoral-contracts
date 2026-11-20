# Approved release audit correction: fast-uri 3.1.9

Status: approved by the maintainer's “approve” on 2026-11-20 after review of
this exact correction and its isolated passing candidate. This is the bounded
dependency exception to the [release preparation scope](conversation-v1.1-release-preparation.md).
Record this approval before changing the lock. Publication remains a separate
later action; the earlier Task 9 approval alone did not grant this exception.

## Finding and exact correction

The locked development-only `fast-uri 3.1.8`, used by Ajv's fixture validator,
is affected by four advisories returned by `npm audit`: GHSA-w74x-v6f9-j3xg,
GHSA-xhq7-xmqj-769h, GHSA-wjr9-j795-jxcr and GHSA-333x-w4r6-6crp. The audit
reports one moderate vulnerable package, with two moderate and two low
advisories. The affected 3.x ranges end before 3.1.9. This is a verifier
dependency; no contract runtime library or provider integration is added.

Proposed change: in `package-lock.json`, change only
`packages["node_modules/fast-uri"]` fields `version`, `resolved`, `integrity`
to the following exact values:

```json
{
  "version": "3.1.9",
  "resolved": "https://registry.npmjs.org/fast-uri/-/fast-uri-3.1.9.tgz",
  "integrity": "sha512-hS/0Wt3Ya043oKXs0sIxrMpKQITXhMLIrVAKKXi4gozGC9v7YRWVnXIZzjNPTO02M9BdxLCWqK1yRXgNziVyJQ=="
}
```

The complete candidate lock SHA-256 is
`26b7382546939bc1a5e371ecb99f1655b617f381eea27b72d9400fc3c49ff585`.
Ajv 8.20.0, ajv-formats 3.0.1, dependency declarations, every other locked
package and all schema/fixture/oracle bytes stay unchanged. Ajv's existing
`^3.0.1` range admits this 3.1.9 patch. The BSD-3-Clause license bytes match
3.1.8 exactly. Update the implementation How's development-dependency evidence
row and derived status after applying the approved correction; do not rewrite
historical audit results or the immutable candidate archive/lock.

## Isolated evidence

Candidate path:
`/private/tmp/thoughtkhoral-task9-fast-uri-319-ji73184x/contracts`.
It is a disposable copy, not the release branch or canonical checkout.
Registry metadata and npm's integrity-checked install agree on the exact
version, archive URL and integrity above. An independent JSON comparison found
only those three lock fields changed, with identical package.json and license
bytes. `npm ci --ignore-scripts` and online `npm audit --audit-level=low`
passed with zero vulnerabilities.

The full candidate `npm test` passed retained room validation, 125 conversation
fixtures, 16 defaults fixtures, six candidate integrity tests and five new
release-preparation tests. The latter also build from a self-contained source
snapshot. This candidate evidence does not approve the correction, publish an
artifact or establish packaged-stack/live acceptance.

## Apply and acceptance

After approval, record acceptance in this How and commit it before replacing
the lock with these exact tested bytes. Install the lock, rerun all tests and
the online audit in the actual release worktree, then regenerate both release
archives from the resulting clean committed source. Confirm identical repeated
TAR/lock bytes and all 156 candidate payload hashes, with all 135 v1.0 schema
and fixture hashes preserved. The source lock's correction changes full archive
provenance but does not change the schema/fixture consumer payload.

Run the extracted archive's complete tests and audit too. Retain any earlier
3.1.8 artifacts as blocked diagnostic evidence; never publish them as passing
release inputs. Only the newly verified concrete release package can be
presented for separate publication approval.
