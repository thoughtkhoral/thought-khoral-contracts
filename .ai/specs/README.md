# ThoughtKhoral contracts specifications

Parent requirements in the ThoughtKhoral root `.ai/specs/` apply here. This project may diverge only through an accepted local decision record that identifies the overridden parent rule and its consequences.

See the [root specification index](https://github.com/thoughtkhoral/thought-khoral/blob/main/.ai/specs/README.md).

## Local areas

- [What: MVP contracts](what/mvp-contracts.md)
- [What: public documentation](what/public-documentation.md)
- [How: implementation](how/implementation.md)
- [Decisions](decisions/README.md)
- [Decision 002: ThoughtKhoral project identity](decisions/002-thoughtkhoral-identity.md)

## Approved Codex room-participation extension

- [What: conversation profile](what/conversation-profile.md)
- [How: conversation profile](how/agent-conversation-profile.md)
- [Coordinated implementation plan](https://github.com/thoughtkhoral/thought-khoral/blob/main/.ai/specs/how/codex-room-conversations-implementation-plan.md)

Approved by the maintainer on 2026-10-05 under [issue 1](https://github.com/thoughtkhoral/thought-khoral-contracts/issues/1).
Implementation follows the coordinated plan and its artifact/dependency gates.
Existing runtime behavior is unchanged until the relevant tasks pass verification.
- [Decision 003: separate conversation profile](decisions/003-conversation-profile-versioning.md)

## Published conversation artifact

[thought-khoral-agent-conversation-v1.0.0](https://github.com/thoughtkhoral/thought-khoral-contracts/releases/tag/thought-khoral-agent-conversation-v1.0.0) was published with maintainer authorization on 2026-10-05
at `85baf86e574276fcd036e53e23641af6aad602f9`. The attached TAR SHA-256 is
`0038fdbf858db013c4a269aeedbca51a5db9128a2f1d6e39754f92ba60fd8f36`.
Both fixture suites pass from the verified download. The release is on the
`codex-conversation-v1` branch/tag; this default checkout has not been merged
and does not yet contain the new schema/fixture implementation.

## Approved defaults-discovery amendment — 2026-10-07

The [approved design](https://github.com/thoughtkhoral/thought-khoral-codex-agent/blob/main/.ai/specs/how/default-settings-discovery-proposal.md) authorizes local defaults discovery and
independent optional controls, with verified unreleased candidate contract pins.
Implementation and synthetic verification follow the amendment plan; publication,
provider use, activation, merge and push retain their separate gates.

## Defaults-discovery candidate checkpoint — 2026-10-07

The approved defaults amendment was implemented and independently reviewed on
the local `codex-defaults-contracts` branch at
`1ea828f28725ddaaefa21d083473f9abbd777975`. It contains an unreleased
candidate for `thought-khoral-agent-conversation-v1.1.0`; the repository's
default `main` remains at `2e12609`, and no v1.1 release is published. The
candidate archive SHA-256 is
`fab59a486f6498b843467202debcb0768403bd57ba7dda41be2a01e5f23fdda8`; the
externally anchored lock SHA-256 is
`7914d32eae2487879a68405b5095a6b9aa91355f87529c43f4055844821902a9`.
Candidate fixture and integrity tests passed as part of the reviewed synthetic
checkpoint recorded in the [coordinated plan](https://github.com/thoughtkhoral/thought-khoral/blob/main/.ai/specs/how/codex-room-conversations-implementation-plan.md).
Publication remains pending.
