# 003 — Separate room conversation integration profile

## Status

Accepted by the project maintainer on 2026-10-05 under [issue 1](https://github.com/thoughtkhoral/thought-khoral-contracts/issues/1).
Scope: milestone-one design and coordinated implementation plan, including
the room-wide history filter. Release publication and live activation retain
separate gates; acceptance does not claim implemented runtime behavior.

## Governing sources

- [Root participant requirements](https://github.com/thoughtkhoral/thought-khoral/blob/main/.ai/specs/what/codex-chat-agent.md)
- [Root Decision 009](https://github.com/thoughtkhoral/thought-khoral/blob/main/.ai/specs/decisions/009-codex-chat-agent.md)
- [Exact profile design](../how/agent-conversation-profile.md)

## Decision

Publish thought-khoral.agent-conversation.v1 as separate language-neutral JSON
Schema and fixtures, served through /api/agent-conversations/v1 and the matching
workload API. Keep retained room requests/events and deterministic-agent validation
unchanged. Codex public prompts and replies are existing message.created events;
conversation task state and model/usage fields stay on the new profile API.
This avoids either silently widening retained enums or migrating all room
operations to a new major room protocol for one agent capability.

The profile's breaking changes require a new major identifier/API path. Publish
an immutable artifact release tagged thought-khoral-agent-conversation-v1.0.0;
record its actual commit and archive digest only after fixtures pass. Consumers
vendor that release, not this proposal or an unpinned default branch. The
profile is a contract artifact, not a shared runtime library.

## Alternatives and consequences

A room-protocol major migration would force coordinated updates to decisions,
chat, and every existing client. An unnegotiated retained-protocol patch would
violate existing compatibility rules and client result validation. The selected
API requires explicit browser HTTP authentication/CORS, task polling, and atomic
coordination with ordinary room events. Old clients can read public Codex replies
without acquiring new inference triggers. Runtime opt-in remains deployment policy.

## Overrides

None to retained room compatibility. This introduces an independent protocol;
its public-message projection must pass the unchanged retained fixtures.
