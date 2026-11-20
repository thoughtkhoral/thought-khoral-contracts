# ThoughtKhoral contracts

`thought-khoral-contracts` is the compatibility authority for the versioned,
language-neutral v1 room-contract JSON Schema artifacts, normative protocol
documentation, and compatibility fixtures.

## Status

MVP / active development. The v1 wire identifier is retained for compatibility;
it is not the public product identity.

For the cross-project Codex conversation status and remaining gates, see the [shared status guide](https://github.com/thoughtkhoral/thought-khoral/blob/main/docs/codex-conversation-status.md).

## Contents

- [`protocol.md`](protocol.md) — methods, events, errors, and compatibility rules;
- [`schemas/`](schemas/) — JSON Schema Draft 2020-12 artifacts;
- [`fixtures/`](fixtures/) — valid and invalid compatibility examples;
- [`test/validate-fixtures.mjs`](test/validate-fixtures.mjs) — retained room fixture verifier;
- [`test/validate-conversation-fixtures.mjs`](test/validate-conversation-fixtures.mjs) — separate conversation fixture verifier;
- [local specifications](.ai/specs/README.md).

## Validate

Requires Node.js with npm:

```sh
npm ci
npm test
```

The project publishes contract artifacts and does not provide a shared runtime
library. Consumers should pin a released contract tag and verify compatibility
before adopting changes.

The retained-v1 decision contract includes human-only `decision.delete` and a
persisted `decision.deleted` audit event. `decision.propose` may have no source
events when a human creates a decision through `/decisions`; deletion never
removes the room's immutable event history. See [the decision protocol](protocol.md).

The additive local A2A task contract includes `agent.task.start`, durable
progress, optional external-input handoff, and source-cited terminal results.
The pinned reference agent exposes only `summarize-context` and
`extract-action-items`; this contract does not admit arbitrary remote agents.
See [the governed task protocol](protocol.md#governed-external-agent-tasks).

## Message mentions and delivery

`chat.send` accepts optional `mentions` and `delivery` fields. The default
delivery is `room`; `mentioned` delivers only to the resolved audience and the
sender. Mentions support direct, known participant targets and the fixed
aliases `@allhumans` and `@allagents`.

Mention tokens are lowercase ASCII slugs, so both `@maya` and `@maya-chen` are
valid forms. A request may include at most 50 unique targets. Participant
targets are unique by ID and aliases by alias, including in persisted
`message.created` payloads. See [`protocol.md`](protocol.md) and the valid and
invalid fixtures for the normative details.

## Contributing

Start with an issue in this repository. Contract changes require an approved
specification update, compatibility evidence, and a release decision. See the
[organization contribution guide](https://github.com/thoughtkhoral/.github/blob/main/CONTRIBUTING.md).

## Agent conversation profile

The approved [conversation profile](.ai/specs/how/agent-conversation-profile.md)
defines a separate HTTP API with ten JSON Schema entry points in
[`schemas/agent-conversation-v1/`](schemas/agent-conversation-v1/). `task.schema.json`
accepts AcceptedTurn or TaskView; shared definitions live in `turn.schema.json`.
Vendor the complete directory so relative references resolve. Schema identifiers
name artifacts; they do not imply a hosted schema-discovery service.

`npm test` runs retained, conversation, additive defaults and candidate integrity suites. The conversation manifest
names each wire schema or canonicalization case and supplies synthetic trusted
binding facts for semantic checks. Invalid fixtures must fail for their named
reason. The verifier checks raw duplicate keys, scalar Unicode, integer tokens,
byte limits, canonical digests, disclosure/authority bindings and replay
comparisons beyond JSON Schema. It is a test oracle, not a shared runtime library,
provider adapter, broker authorization implementation or persistence test.

The [full bound packet vector](fixtures/agent-conversation-v1/valid/full-bound-canonical-vector.json)
and Unicode/control/order vectors provide literal canonical bytes and independent
SHA-256 expectations. Ordinary public human/Codex message examples also pass the
unchanged retained event schema. Existing retained fixtures are unchanged.

This implementation is prepared under [accepted issue 1](https://github.com/thoughtkhoral/thought-khoral-contracts/issues/1).
The [published `thought-khoral-agent-conversation-v1.0.0` release](https://github.com/thoughtkhoral/thought-khoral-contracts/releases/tag/thought-khoral-agent-conversation-v1.0.0)
was authorized on 2026-10-05 at `85baf86e574276fcd036e53e23641af6aad602f9`;
its TAR SHA-256 is `0038fdbf858db013c4a269aeedbca51a5db9128a2f1d6e39754f92ba60fd8f36`.
Consumers pin that immutable release and verify its archive. The additive
[v1.1.0 release](https://github.com/thoughtkhoral/thought-khoral-contracts/releases/tag/thought-khoral-agent-conversation-v1.1.0)
was published on 2026-11-20 at `f1c8621810c8c121c1aafc8e5a342d6626c4b843`.
Its TAR SHA-256 is `b0370e43627ce6044852df75bfbc4b749d904aa9cedcfc558c61bb4e07dc95ff`;
release-lock SHA-256 is `b7f3ad928c5c17be7e936da4959b7e7e8555bb4ed3602fa62f71a8721f042d8f`.
Fresh downloads and all 156 payload hashes verify. See the
[retained publication evidence](docs/evidence/conversation-v1.1-publication-2026-11-20.json).
Consumer transition remains separately verified; the original synthetic
candidate below keeps its immutable unreleased-candidate metadata.

### Unreleased defaults candidate

The [approved defaults amendment](.ai/specs/how/agent-conversation-profile.md#approved-defaults-discovery-amendment--2026-10-07)
adds the closed [`ResolvedSettingsView`](schemas/agent-conversation-v1/resolved-settings.schema.json)
and [16 additive fixtures](fixtures/agent-conversation-v1.1/manifest.json).
Every existing v1.0 schema and fixture remains unchanged. The query's authority,
error mapping and read-only behavior are specified in [the protocol](protocol.md#additive-resolved-defaults-query).

From a clean committed checkout, build the full repository archive and required
vendor payload into storage outside the checkout:

```sh
python3 scripts/build-conversation-candidate.py --commit HEAD --output /private/tmp/conversation-candidates
```

The command prints the candidate directory, exact commit, archive SHA-256 and
lock SHA-256. It refuses dirty source and existing candidate directories. The
candidate directory is named by its full commit and contains `lock.json`,
`lock.sha256`, the TAR and `vendor/`. A changed source requires a new commit and
candidate; this tool creates no release or tag. The lock retains the original
v1.0 tag/commit/archive provenance and marks v1.1.0 `unreleased-local-candidate`.
The full archive includes the npm lockfile and all tests for independent checks.

Pin the printed lock SHA-256 in consumer code, then verify using that external
anchor (replace the example values with the reviewed directory and digest):

```sh
python3 scripts/build-conversation-candidate.py --verify /private/tmp/conversation-candidates/COMMIT --lock-sha256 REVIEWED_LOCK_SHA256
```

Verification rejects archive/payload changes, unexpected files, symlinks and
altered or additional metadata. The sidecar is evidence, while the independently
pinned digest establishes the consumer's trust. This exception permits only
isolated pre-publication development and synthetic tests.

### Local v1.1 release preparation

The [approved release preparation How](.ai/specs/how/conversation-v1.1-release-preparation.md)
defines a separate local preparer. From a clean committed checkout:

```sh
python3 scripts/prepare-conversation-release.py --commit HEAD --output /private/tmp/conversation-release-inputs
```

It produces the intended release TAR, closed `lock.json`, external digest
sidecar and exact vendor payload, without creating a tag, release or network
request. The payload must match the approved defaults candidate; every existing
v1.0 schema/fixture remains unchanged. Output explicitly reports
`publication: not-performed`. The lock's intended release URL is not evidence
that an asset exists there. Consumers must wait for authorized publication and
download verification before adopting it.

Verify using the independent digest reported by the reviewed preparation:

```sh
python3 scripts/prepare-conversation-release.py --help
```

The verification invocation is `--verify DIRECTORY --lock-sha256 DIGEST`, with
the actual prepared directory and externally reviewed lock digest. Verification
rejects archive/vendor drift, extra or missing files, symlinks and metadata
tampering. `npm test` includes candidate and release-preparation integrity tests;
Python 3 and Git are required as well as Node/npm. Extracted-archive tests create
their own temporary Git histories and need no upstream history or provider.
