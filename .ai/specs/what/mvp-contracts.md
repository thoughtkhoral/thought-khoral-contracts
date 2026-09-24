# MVP contracts

## Sole MVP responsibility

`thought-khoral-contracts` is the compatibility authority for the versioned, language-neutral `n2n.room.v1` JSON Schema artifacts, normative protocol documentation, and compatibility fixtures. `n2n.room.v1` is a retained wire-compatibility value, not this project's public identity.

## Acceptance criteria

- Schemas define the `n2n.room.v1` envelopes, JSON-RPC requests, and room events.
- Live schema `title` metadata uses the ThoughtKhoral display identity while
  v1 `$id`, `$ref`, `contractVersion`, and fixture values remain unchanged.
- Valid and invalid fixtures prove the contract validator accepts and rejects the specified payloads.
- Protocol documentation records method semantics, structured errors, decision transitions, and compatibility rules.
- The additive chat mention fields define room-wide and mentioned-only
  delivery, typed participant and fixed alias targets, and a persisted
  `message.created` audience for delivery and replay filtering. Fixtures reject
  unsupported delivery, empty mentioned-only targets, excessive or duplicate
  mention identities, and malformed tokens.
- The additive slash-decisions extension defines human-only `decision.delete`,
  the server-produced `decision.deleted` audit event, and empty source-evidence
  lists on `decision.propose`; it does not delete room-event history.
- Additive A2A reference-task fixtures cover human task start, meaningful
  progress, optional external-input handoff, cited terminal results, and
  invalid skill, citation, and handoff values without changing retained v1
  identifiers.

## Interfaces

`chat.send` accepts optional `mentions` and `delivery`; `message.created`
retains those fields and gateway-resolved `audienceIds`. The schema defines at
most 50 typed targets, the `allhumans` and `allagents` aliases, and `room` or
`mentioned` delivery. Semantic uniqueness by participant ID or alias is
checked by the fixture validator and runtime because JSON Schema
`uniqueItems` alone cannot enforce it. The gateway owns current-roster and
canonical-token checks.

The project publishes `n2n.room.v1` for browser connection authentication (`session.authenticate`) and authenticated room operations (`room.join`, `chat.send`, `decision.propose`, `decision.transition`, and `decision.delete`), including their JSON-RPC 2.0 envelopes, `contractVersion`, RFC 4122 `requestId`, and structured error codes. The `decision.deleted` event retains the deleted row's prior status, title, summary, and source-event IDs as audit evidence under root [decision 008](https://github.com/thoughtkhoral/thought-khoral/blob/main/.ai/specs/decisions/008-slash-decisions-and-facilitator-boundary.md). The original in-process Action Items Agent retains its server-produced `agent.task.queued`, `agent.task.running`, `agent.task.succeeded`, and `agent.task.failed` events. The separate local A2A foundation adds human `agent.task.start` with one pinned agent and the `summarize-context` or `extract-action-items` skill. Its server-produced lifecycle is `agent.task.requested`, zero or more `agent.task.progressed`, optional `agent.task.awaiting_external_input`, and one terminal `agent.task.succeeded` or `agent.task.failed`, with task provenance, context revision, and bounded cited results. Per the accepted root [browser WebSocket authentication decision](https://github.com/thoughtkhoral/thought-khoral/blob/main/.ai/specs/decisions/002-browser-websocket-authentication.md), `session.authenticate` carries a non-empty OIDC `accessToken` and is the sole request permitted while a browser WebSocket is unauthenticated.

`session.authenticate` is an additive `n2n.room.v1` patch for browser connection establishment. It preserves the prior authenticated room-operation contract and release history.

A future `thought-khoral.room.v2` protocol is a separate compatibility migration. It must not change v1 schema identifiers, constants, fixture payloads, or immutable release tags. Human-facing `title` metadata is not a v1 wire identifier.

## Explicit exclusions

This project does not provide a shared runtime library, gateway implementation, user interface, persistence service, authentication provider, or platform deployment.
