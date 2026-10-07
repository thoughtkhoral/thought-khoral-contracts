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
The proposed `thought-khoral-agent-conversation-v1.0.0` tag is not published by this
work. Consumers adopt an actual reviewed immutable release commit/archive digest,
not a proposed tag or default branch. Release publication remains a separate gate.

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
