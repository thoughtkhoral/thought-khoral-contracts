# Room conversation integration profile

## Status and ownership

Approved by the project maintainer in the Codex working session on 2026-10-05,
including this milestone-one specification and the coordinated implementation
plan. Accepted contribution: [issue 1](https://github.com/thoughtkhoral/thought-khoral-contracts/issues/1).
Implementation follows the [plan](https://github.com/thoughtkhoral/thought-khoral/blob/main/.ai/specs/how/codex-room-conversations-implementation-plan.md) and its dependency gates.
Release/tag publication, provider use and service activation require their
separate later authorization. No completed runtime or live verification is claimed.

Governing sources are
[room participation requirements](https://github.com/thoughtkhoral/thought-khoral/blob/main/.ai/specs/what/codex-chat-agent.md),
[solution design](https://github.com/thoughtkhoral/thought-khoral/blob/main/.ai/specs/how/codex-chat-agent.md), and
[root Decision 009](https://github.com/thoughtkhoral/thought-khoral/blob/main/.ai/specs/decisions/009-codex-chat-agent.md).
The proposed profile identifier is `thought-khoral.agent-conversation.v1`.
This repository owns the profile, schema publication, canonicalization, and
compatibility fixtures. This Markdown specification fixes the v1 field shapes;
its JSON Schema and fixture artifacts are created in implementation Task 1.
No released schema or runtime compatibility is claimed before Task 1 verification.

## Invocation and control interfaces

The selected compatibility strategy is a separately versioned HTTPS API at
`/api/agent-conversations/v1`. Browser requests use the existing OIDC access
token in the Authorization bearer header, current configured origin checks,
and the same issuer/audience/role validation as the room gateway. Local development may use loopback HTTP
under the existing local identity constraints; production TLS is not implemented
by this milestone. Tokens never
appear in URLs or persisted payloads. CORS admits only configured workspace
origins and permits Authorization/Content-Type; it does not grant room authority.
This API adds no method, agent enum, or task result to the retained room protocol.
Existing clients continue using their existing socket and contract.

| Endpoint | Body/query | Success |
| --- | --- | --- |
| POST /turns | TurnRequest | HTTP 202 AcceptedTurn, including idempotent replay |
| GET /rooms/{roomId}/agents/{agentId} | none | HTTP 200 ConversationView; conversation is null if absent |
| GET /rooms/{roomId}/agents/{agentId}/models | cursor optional; limit integer 1..100, default 100 | HTTP 200 CatalogPage |
| GET /rooms/{roomId}/tasks/{taskId} | none | HTTP 200 TaskView, including ordered normalized task updates |

TurnRequest is a closed object with required profileVersion, requestId, roomId,
agentId, occurredAt, text, and mentions. Optional conversation and settings have
exact shapes below. profileVersion is the exact profile identifier. UUIDs are
canonical lower-case strings, occurredAt is RFC 3339, text contains 1..8,000
Unicode scalar values, and mentions contains 1..50 retained typed mention records
with semantic uniqueness. Delivery is implicitly room-wide; a delivery field,
requester ID, native thread ID, endpoint URL, or directory path is rejected.

A direct canonical Codex participant mention must occur exactly once. Explicit
composer selection inserts that same typed mention. Alias expansion or plain
quoted mention text does not qualify. Other mentions retain ordinary room-wide
meaning and cannot initiate additional tasks through this API. The request's
agentId must equal the directly addressed admitted identity. UI sends this request
instead of also issuing chat.send. A Codex mention sent through the retained
chat.send method is ordinary chat and never starts inference. Other existing
agent trigger paths remain intact.

conversation, when present, is either {mode: new} or {mode: continue, id: UUID,
generation: positive safe integer}, with no additional fields. Omission atomically
resolves the current ready room conversation, or new when absent. An unusable
conversation requires explicit new. settings, when supported and present, is
{model: option ID, reasoningEffort: option ID, catalogRevision: opaque string};
both option IDs contain 1..128 characters and catalogRevision 1..128 characters.
Omission resolves current server defaults. The UI requires explicit selection or
acknowledgement if a model change makes the previous effort unsupported.

All operations require an authenticated human's current permission under the
existing room authorization model. Mutations additionally require human room-chat
and agent-invocation authority. Authorization checks apply before returning an
idempotent response. This profile does not introduce durable membership, kicks,
or room.leave; browser Leave is disconnection, not history revocation. A future
room ACL must implement the same authorization port and policy invalidation.
The requester is derived from validated identity. Access-token expiry bounds
the task's authorizationExpiresAt; do not accept a turn with less than its
configured deadline plus interruption grace remaining. Mid-turn agent admission
or disclosure-policy revocation cancels execution; token expiry rejects a result.
Do not claim immediate identity-provider revocation without an approved mechanism.

An accepted request atomically stores one existing room-wide message.created
human event, reserves the room/agent generation, resolves settings, freezes its
context, and stores one conversation task. Retain the room/request-ID ledger
key, bind authenticated requester and submitted intent in its fingerprint, and
compare before resolving mutable defaults. Replays return the original message,
task, and frozen settings. A changed intent with the same key is a conflicting
duplicate; another caller cannot recover the original task by guessing its key.

Browser task polling is once per second while active, then stops at terminal
status, room Leave, or authentication loss. TaskView includes durable update IDs
and monotonically increasing ordinals for reconnect replay. These profile task
updates are stored separately from retained room events. They never masquerade
as existing deterministic task events or permit browser synthesis of room events.

## Request example

```json
{
  "profileVersion": "thought-khoral.agent-conversation.v1",
  "requestId": "11111111-1111-4111-8111-111111111111",
  "roomId": "22222222-2222-4222-8222-222222222222",
  "agentId": "74686f75-6768-746b-686f-72616c000004",
  "occurredAt": "2026-10-02T16:00:00Z",
  "text": "@codex-agent What did Maya propose?",
  "mentions": [{"type": "participant", "id": "74686f75-6768-746b-686f-72616c000004", "token": "codex-agent"}],
  "conversation": {"mode": "new"}
}
```

The optional settings object is absent here; the server resolves allowed defaults.
The worker native model ID and provider secrets never appear in this request.

## Admitted capability manifest

Pin profile version, agent identity, `chat` skill, endpoint, transport version,
and supported controls in reviewed registration. Declare `conversationScope:
room`, `invocation: explicitly-addressed`, `delivery: room`, and `roomHistory:
baseline-and-delta`. Model selection, reasoning effort, and usage reporting are
optional independent capabilities; their option IDs are agent-specific.
Codex initially supports model and effort controls. Non-Codex fixtures may omit
them. Unknown required capabilities, versions, or admission drift fail closed.
Catalog responses are authenticated, size-bounded, and restricted by policy;
catalog membership does not prove provider entitlement.

## Task input and context

The room gateway creates the authoritative packet; the agent gateway mediates
it in one structured A2A DataPart with a pinned profile discriminator. A2A
task/context IDs are transport IDs mapped to the platform task and conversation;
they do not substitute for authorization or native Codex thread IDs.

| Field | Meaning |
| --- | --- |
| profileVersion | Exact admitted integration profile |
| taskId, roomId, requesterId, agentId, skillId | Authorized platform binding; skillId is chat |
| conversation.id, generation, mode | Shared platform conversation binding |
| model, reasoningEffort, catalogRevision | Resolved allowed settings for this turn when supported |
| triggerEventId | Exactly one human room-wide message in entries |
| context.kind | baseline for a new thread; delta for continuation |
| context.baseRevision | Zero for baseline; committed consumed revision for delta |
| context.revision | Room sequence of the triggering message |
| context.policyRevision | Opaque revision of the agent's disclosure policy |
| context.entries | Ordered eligible transcript records through revision |
| context.activeDecisions | Complete current authorized room-wide projection at revision |
| context.nativeReplyBindings | References replacing text already present as this native thread's assistant output |
| context.digest | SHA-256 of canonical context bytes, including trigger and policy binding |
| guidanceRevision | Worker-admitted fixed instruction revision; future bundle identity |
| issuedAt, expiresAt, authorizationExpiresAt, lease binding | Task-scoped validity and current execution authority |

Transcript entries have eventId, positive sequence, authorId, authorRole,
occurredAt, and text. The optional displayName is 1..128 characters and is not authority. All other
entry fields are required; authorRole is human or agent, text is nonempty and
bounded by the total context byte cap. ActiveDecision is {decisionId: UUID, title:
nonempty string, summary: string, sourceEventIds: unique UUID array}; all listed
sources must be disclosable. Native-reply textDigest is lower-case hex64.
Policy/guidance revisions are opaque strings of 1..128 characters.
Native-reply bindings have eventId, sequence, sourceTaskId, generation, and text
digest; the receipt proves that exact text already belongs to the same native
thread. A baseline never uses these substitutions. The active-decision projection
contains no targeted sources; exclude a decision whose sources cannot all be
disclosed under this profile. Current decisions replace the previous projection;
their snapshot is not another conversational turn.

Validate strictly increasing entry/binding sequences, unique IDs, revision
bounds, base agreement, exact trigger membership, room-wide delivery, and current
policy. Membership and delivery filtering occur before packet construction.
Sequence gaps are valid. A delta cannot import an arbitrary client revision.
The digest input is the closed object {roomId, agentId, conversationId,
generation, triggerEventId, guidanceRevision, context}, where context has kind,
baseRevision, revision, policyRevision, entries, activeDecisions, nativeReplyBindings
and excludes digest itself. All object keys are ASCII schema-defined names;
recursively sort them lexicographically, retain array order, encode UTF-8 without
whitespace or Unicode normalization, and serialize safe integers in decimal.
Escape quotes/backslashes, use JSON short escapes for backspace/form-feed/newline/
carriage-return/tab and lower-case u00xx for other control characters; preserve
other Unicode scalars verbatim. Reject floats, non-finite values, duplicate object
keys, and integers outside 0..9007199254740991 before canonicalization. Strings
cannot contain unpaired surrogates. SHA-256 uses lower-case hexadecimal. The wire
annex supplies an independently computed Unicode canonicalization vector.
Authenticated transport covers the entire task/requester/lease binding; the
context digest alone is not authority.

Worker-to-gateway receipt reconciliation is task-scoped and authenticated. The
room gateway confirms accepted result event ID, sequence, text digest, generation,
and consumed revision. This is the only source of a native-reply binding.
The mediator forwards that broker acknowledgement using authenticated POST
/control/v1/receipts/{taskId}/ack with the exact ResultAcknowledgement body. The
worker validates task/generation/digest and writes it durably before another turn.
Replays of the same acknowledgement are idempotent; conflicting IDs/digests fail. A completed result
can be resubmitted to obtain a lost acknowledgement without provider execution.

## Results, progress, and provenance

The proposed result discriminator is `conversation-reply.v1`. Its required
fields are conversationId, generation, assistantText, consumedRevision, and
contextDigest. Required metadata fields contain citations and nullable settings confirmation
and turn-bound usage; an empty citation array and null telemetry/settings
represent unavailable metadata. The agent gateway also validates task/agent/requester and
lease binding from the authenticated invocation. Runtime thread IDs never reach
the browser; runtime turn bindings remain internal metadata, not resume authority.

Normalize one A2A terminal success only after verified runtime completion and
final text. Progress and settings/usage reports cannot synthesize success.
Raw reasoning, stderr, shell output, and provider failures are never room events.
The room gateway atomically accepts the result, persists one existing room-wide
message.created event with trusted Codex attribution, writes a profile terminal
update with that replyEventId and sequence, advances consumedRevision to the
input boundary, and releases the reservation. The profile TaskView holds the
bounded result and points to this message; its assistant text is rendered only
through the room transcript, never as a second task bubble. The room message is
the assistant transcript source and is reconciled on the next delta. No new
conversation-reply discriminator appears on the retained room event stream.

Citations reference disclosed event/decision IDs from the generation's committed
disclosure manifest plus the active packet. The room gateway stores that manifest
with source IDs and policy/revision bindings, not a second native history store.
The gateway verifies their current authorization. Native-reply substitutions
retain those source IDs. A model cannot
cite arbitrary IDs or turn IDs as room evidence. Optional guidance citations
require the future bundle contract; ordinary URLs are not verified room citations.

## State transitions and crash ordering

| State | Meaning and permitted next step |
| --- | --- |
| absent | No active conversation; a new request reserves a fresh generation |
| reserved | One frozen task, no turn submission; pre-submission failure releases reservation |
| running | Durable worker receipt authorizes one possibly submitted native turn |
| ready | Completed result and room reply committed; continue or explicit new is permitted |
| unusable | Native history or disclosure safety is uncertain; explicit new is required |
| superseded | Replaced generation; never resumable through this profile |

Every new request atomically installs the replacement generation as reserved and
marks the previous generation superseded. Reset is rejected while a task is active.
Failure does not silently restore the previous thread. A fresh generation that
fails before submission becomes unusable and offers explicit new. A ready thread
that fails validation before submission returns to ready with its old cursor.
If unchanged native history cannot be proven, it becomes unusable.

The worker durably records reserved before thread creation, stores the exact
thread ID before its first turn, and durably records submission-intent/running
with packet binding before sending turn/start. Record returned turn ID next;
absence of that ID after a crash does not prove nothing ran. Persist final output
as completed before sending it to the gateway. Record gateway acknowledgement
last. Process shutdown or receipt loss after submission-intent never permits
blind re-execution; mark interrupted and require new. A reserved receipt with
no submission-intent can fail safely without inference. Orphan empty threads
cannot be selected as a fallback. A completed receipt only replays its stored
result, subject to current generation, policy, and lease validation.

Broker lease recovery must consult receipts or fail closed. A new lease cannot
launch the same uncertain turn. Late replies after timeout, policy invalidation,
or generation replacement are rejected. These rules prevent duplicate logical
turns while making no exactly-once provider execution claim across crashes.

## Initial validated bounds

Proposed deployment defaults: 8,000 prompt characters, 1 MiB canonical context,
2,000 transcript records, 1 MiB JSONL line, 4 MiB total parsed output per turn,
64 KiB final assistant text, 180-second turn deadline, five-second interrupt
grace, four concurrent subprocesses, and 100 catalog entries per page. Context
records count text entries and native-reply bindings together. Reject overflow
before submission where possible; runtime overflow interrupts and fails the turn.
Image configuration may lower these limits; increases require reviewed deployment
configuration. Test limits as UTF-8 bytes where specified, not character counts.
Idle app-server processes are closed after each accepted turn/acknowledgement;
native files persist and the next turn resumes. Thus idle rooms consume no live
process slot. Pending acknowledgements occupy a bounded slot or close safely
with a durable completed receipt. These choices supersede an indefinite idle
process; successful turns still require protocol completion, never process exit.

Safe failure codes distinguish invalid_task_input, forbidden, conversation_busy,
conversation_stale, context_mismatch, context_too_large, runtime_unavailable,
authentication_required, session_unavailable, timeout, conversation_interrupted,
and execution_failed, plus duplicate_conflict. Contracts must assign their wire/error mapping; UI messages
describe recovery without raw runtime diagnostics. Limits and deadlines remain
separate from the deterministic Reference Agent's budgets.

## Compatibility and approval gates

Use the independent profile API, not a new room protocol major version or an
unnegotiated retained-protocol patch. Existing requests, schemas, event enums,
and deterministic-agent discriminators remain byte-for-byte compatible. Public
Codex prompts and replies validate as ordinary existing room messages. Profile
metadata, task lifecycle, model choices, and usage stay on the new API. An old
client can read public replies without initiating new inference. Consumers pin
the contracts release containing separate profile artifacts. Future breaking
profile changes require a new profile major version and API path.

Before implementation: approve root Decision 009 and the local What/How/decision;
publish schemas, authentication and canonicalization fixtures from this design; mirror
room persistence/disclosure, admission/dispatch, UI participation, and platform
deployment scope into their owning child specifications; accept an owning issue;
then approve the dependency-ordered implementation plan. Planned order is
contracts, room gateway reservation/context, agent gateway mediation, independent
Codex adapter, UI, and opt-in deployment. A test harness may precede consumers
after that plan is approved. The coordinated child specifications and plan were approved on 2026-10-05 with accepted issue traceability. Consumer runtime work still requires published artifacts and the dependency gates in the
[implementation plan](https://github.com/thoughtkhoral/thought-khoral/blob/main/.ai/specs/how/codex-room-conversations-implementation-plan.md).


## Workload control API

The agent gateway uses the existing audience-bound workload authentication for
room-gateway calls. The separate /internal/agent-conversations/v1 API has POST
/claim with {agentId, leaseOwner}, GET /tasks/{taskId}/context, POST /tasks/{taskId}/updates,
GET /tasks/{taskId}/receipt, and GET /tasks/{taskId}/authority. Claims return 204
when no task is available or 200 with the immutable packet and a freshly minted
leaseToken. Context, updates, and authority require that task's live lease header.
Receipt reads require the admitted workload's current task/agent scope; they may
recover an already accepted acknowledgement after lease expiry, but cannot
submit a result or launch execution. Lease tokens stay out of browser responses.

UpdateRequest is closed: {profileVersion, updateId: UUID, ordinal: positive safe
integer, taskId: UUID, generation: positive safe integer, contextDigest: hex64,
kind: progress|settings|usage|completed|failed, data: kind-specific object}.
Duplicate updateId plus identical payload returns the original acknowledgement;
a different payload conflicts. Ordinals are strictly increasing for new updates,
and terminal state is immutable. Completed data is the internal result object;
failed data is {code: failure enum}. Progress data is {phase: accepted|working|
finalizing, text: 1..512 characters}; it is coalesced to one accepted update per
second, whereas terminal updates are never coalesced. settings and usage data
use the normalized objects in the wire annex. Check task, generation, current
policy, digest, requester authority expiry, and lease before accepting any update.

The agent gateway polls authority once per second during execution and submits
A2A cancellation on revocation/lost authority or lease. The worker enforces the
packet deadline independently and validates invocation credential expiry.
The reviewed local agent gateway credential for the worker is a distinct bearer
secret, scoped by pinned agent registration and accepted packet bindings. It is
never forwarded to Codex; provider credentials never reach either gateway.
The worker exposes authenticated A2A task transport and authenticated bounded
catalog/receipt queries at /control/v1/models and /control/v1/receipts/{taskId}.
The latter returns reserved/running/completed/interrupted without re-execution.
Control queries and A2A use the same admitted invocation authority. The agent
gateway reconciles both worker and broker receipts before reclaiming a task;
unknown or unreachable running status fails closed to interrupted.

## A2A binding

Pin the Agent Card identity, URL, profile, skill chat, and JSON-RPC transport at
http://thought-khoral-codex-agent:9091; card discovery at /.well-known/agent-card.json
is authenticated and never follows redirects. The reviewed SDK supplies its
protocol version. message/send or message/stream carries one DataPart containing
{profileVersion, packet: TaskInput} and a unique message ID derived from the
platform task ID. A2A task/context IDs are persisted in the mediator before
subsequent task controls. Artifacts contain one bound reply DataPart; arbitrary
URI artifacts, additional text outputs, callbacks, and external-input handoffs
are rejected for initial Codex chat. Initial artifacts contain {reply: InternalReply,
runtimeBinding: {threadId, turnId}}, keeping native binding in the mediator;
only the normalized reply reaches the broker/browser. The worker validates the packet before
provider submission. Transport retries reconcile receipts before another send;
A2A message ID reuse is not by itself a provider exactly-once guarantee.

## Exact response and normalized object shapes

All objects are closed; all UUIDs/date-time values use the request conventions.
Every integer is a JSON safe integer. Fields are required unless marked optional.
A failure object is {code: one safe failure enum, message: safe text at most 512
characters}. At most 100 citation IDs and 2000 combined transcript/binding records
are accepted. The context object and TaskInput are closed to their listed fields;
leaseToken is in the authenticated broker envelope, not the model input or A2A
DataPart. Provider invocation credential and lease token are never the same value.
Text byte caps are normative semantic checks alongside JSON Schema maxLength.

- AcceptedTurn: {profileVersion, roomId, taskId, conversationId, generation,
  triggerEventId, contextRevision, selectedSettings}. selectedSettings is
  {model, reasoningEffort, catalogRevision}, or null for an agent without settings.
- ConversationView: {profileVersion, roomId, agentId, conversation}; conversation
  is null or {id, generation, state, activeTaskId: UUID|null, consumedRevision,
  policyRevision, guidanceRevision, selectedSettings, effectiveSettings: object|null,
  usage: object|null}. state is reserved|running|ready|unusable; superseded
  generations are not returned as active. Views never expose thread/turn IDs.
- CatalogPage: {profileVersion, catalogRevision, data: ModelOption[], nextCursor:
  string|null}; opaque cursors are 1..256 characters and bound to this catalog
  revision and agent. ModelOption: {id, displayName: 1..128 characters,
  defaultReasoningEffort: string|null, supportedReasoningEfforts: EffortOption[]};
  EffortOption: {id: 1..128 characters, description: 1..512 characters}. IDs are
  unique, and defaults must be supported. Agents without settings return no models.
- EffectiveSettings: {model: string|null, reasoningEffort: string|null,
  confirmation: confirmed|unconfirmed, reroutedModel: string|null}; confirmation
  is confirmed only when both supported settings are runtime-confirmed. Opaque
  catalog IDs map to native model/list fields inside the worker; unknown runtime
  reroutes are displayed without granting selection authority.
- Usage: {lastTotalTokens: nonnegative integer, modelContextWindow: positive
  integer|null, reportedAt: date-time, model: string|null, freshness: fresh|stale|
  unavailable}. Internal usage also binds taskId, generation, threadId, turnId;
  browser projection drops native IDs. Invalid numerator/window or unmatched
  binding yields unavailable, never an invented zero percent. Percentage is
  computed from lastTotalTokens/window, not cumulative usage. A missing or invalid
  numerator yields usage null; it is never replaced with zero. An unavailable
  window can retain a validated numerator with freshness unavailable and no meter.
- InternalReply: {kind: conversation-reply.v1, conversationId, generation,
  assistantText: nonempty UTF-8 at most 65536 bytes, consumedRevision,
  contextDigest, citations: unique UUID array at most 100, effectiveSettings:
  object|null, usage: object|null}. Worker result metadata additionally contains runtimeBinding: {threadId: nonempty string,
  turnId: nonempty string}; the internal result is {reply: InternalReply,
  runtimeBinding}. The mediator checks it against its worker receipt and retains
  that private binding. The broker/browser receive only InternalReply.
- TaskView: {profileVersion, roomId, taskId, conversationId, generation,
  requesterId, state: reserved|running|completed|failed, selectedSettings,
  effectiveSettings: object|null, usage: object|null, updates: TaskUpdate[],
  result: InternalReply|null, replyEventId: UUID|null, failure: object|null}.
  result/replyEventId exist only on completed; failure only on failed.
  TaskUpdate: {updateId, ordinal, kind, occurredAt, data}; private native fields
  and authentication bindings are removed. Poll responses include at most 256
  retained updates; coalescing/settings/usage replace prior snapshots while
  preserving acceptance and terminal updates. Ordinal gaps are valid.
- ResultAcknowledgement: {profileVersion, taskId, conversationId, generation,
  replyEventId, replySequence, textDigest, consumedRevision, contextDigest}.
  This internal object is returned only after the atomic room/task commit.
- ProfileError: {profileVersion, code, message: safe display text at most 512
  characters, requestId: UUID|null}. HTTP 400 maps invalid_task_input;
  401 authentication_required; 403 forbidden; 404 session_unavailable;
  409 conversation_busy|conversation_stale|context_mismatch|duplicate_conflict;
  413 context_too_large; 503 runtime_unavailable. timeout,
  conversation_interrupted, and execution_failed are terminal TaskView failures,
  not successful results. Empty/unsupported model access produces execution_failed
  with safe text and no fallback model. Unknown keys/fields fail closed.

## Schema publication and compatibility fixtures

Task 1 publishes schemas/agent-conversation-v1/{turn,view,catalog,task,input,update,
result,error,ack}.schema.json and fixtures/agent-conversation-v1/{valid,invalid}/.
Use JSON Schema Draft 2020-12, exact property lists, additionalProperties false,
UUID/date-time formats, profile const, integer ranges, oneOf branches for new/
continue and result/failure, and limits above. The fixture verifier implements
semantic UUID/mention uniqueness, UTF-8 caps, canonical digest, and binding checks
where a schema alone cannot express them. It does not create a shared runtime
library. Retained fixtures remain unchanged and validate with their original
entry points. Consumer builds vendor the approved immutable profile release.

Minimum fixture pairs: first turn; explicit new; continue by another human;
conflicting duplicate; empty/oversized prompt; targeted/private fields; stale
catalog/unsupported effort; wrong-room/generation/base/digest; hidden sequence gap;
duplicate source; native-reply substitution; invalid decision provenance;
late/expired lease; terminal replay; changed terminal; wrong-thread usage; missing/
zero window; cumulative-vs-last counts; over-capacity meter; non-Codex missing
settings; and ordinary Codex-attributed room messages accepted by retained schemas.

The canonicalization byte vector is {"z":"é","a":[1,"x\n"]}. Its canonical
UTF-8 text is {"a":[1,"x\n"],"z":"é"}; object input key order must not change
its digest, but array order and Unicode normalization must. Commit the independent
SHA-256 literal 089204610aca5bd0285b6c1285dee671b94a7afe21bf9af07f0a9a1b8a704a94
with the fixture during publication, along with a full bound packet vector,
and verify it in Node and Rust before pinning consumers.

## Task 1 wire annex — execution bindings

Task 1 makes the table's lease binding concrete without widening the browser
API. TaskInput requires profileVersion, taskId, roomId, requesterId, agentId,
skillId, conversation, triggerEventId, context, guidanceRevision, issuedAt,
expiresAt, authorizationExpiresAt, leaseOwner, and leaseExpiresAt. conversation
is the closed object {id, generation, mode: new|continue}; model,
reasoningEffort and catalogRevision are optional as an all-or-none trio using
the selected-settings option bounds. leaseOwner is a nonempty opaque string
of at most 128 characters, and leaseExpiresAt is RFC 3339. The broker's
leaseToken remains outside TaskInput. All four dates are required; issuedAt
precedes expiresAt, which is at most 180 seconds later and cannot exceed either
authorizationExpiresAt or leaseExpiresAt. Execution checks current time before
submission/result acceptance. Configured lower limits remain enforceable.

A new packet has a baseline with baseRevision zero and no native bindings.
A continue packet has a delta whose baseRevision matches the committed cursor.
Revision is positive and greater than baseRevision. Each transcript entry and
native binding has a distinct ID and sequence in (baseRevision, revision];
each array is strictly increasing. The single human trigger has requesterId
as its author and sequence equal to revision. Native bindings have the current
generation and are verified against broker acknowledgements in authenticated
validation context. Decision IDs and source lists are unique; sources may come
from the generation's committed disclosure manifest, not only this delta.

The 1 MiB context limit applies to canonical bytes of the complete bound digest
preimage described above. The combined record cap is 2000. Result assistantText
uses a 65536-byte UTF-8 cap; schema character bounds alone are insufficient.
A validator must receive trusted room/agent/generation/cursor/policy/guidance,
source manifest, frozen digest/revision/trigger, acknowledged native replies
and current authority separately
when validating cross-packet semantics. Fixture validation context supplies
those facts as synthetic test evidence; it is not a client wire object or an
implementation of broker authorization/storage.

TaskUpdate data uses exactly the same kind-specific objects as UpdateRequest.
For terminal TaskView, completed requires a nonnull result/replyEventId and
null failure; failed requires nonnull failure and null result/replyEventId;
reserved/running require all three null. Updates have unique IDs and strictly
increasing positive ordinals, with the terminal update last and matching the
terminal projection. Completed result generation/conversation and all update
bindings agree with the enclosing task. Normalized usage permits a null window
only with freshness unavailable; freshness unavailable with a positive window
is also permitted when the validated report is no longer reliable. Confirmed
settings require nonnull model and effort. Catalog model and effort IDs are
unique and a nonnull default must name a supported effort.

Artifact fixture manifests name the schema and trusted semantic context for
each case. Stateful comparisons (duplicate/terminal replay) validate against
an explicitly supplied prior record and frozen binding; they do not claim to
prove persistence or provider execution behavior. Raw task/thread/turn usage
binding is exercised by a fixture validation context, while runtime telemetry
normalization remains Task 4's responsibility.

## Approved defaults-discovery amendment — 2026-10-07

The maintainer approved the [visible server defaults design](https://github.com/thoughtkhoral/thought-khoral-codex-agent/blob/main/.ai/specs/how/default-settings-discovery-proposal.md) in
this conversation on 2026-10-07 after an explicit specification approval request.
It authorizes coordinated local implementation and synthetic verification of
the additive authenticated defaults query and independently optional model/effort
controls, including the F1 initial/reset effort-only deadlock. The accepted
design is the governing amendment to earlier default-visibility wording.

The contracts owner defines `ResolvedSettingsView` at
`GET /api/agent-conversations/v1/rooms/{roomId}/agents/{agentId}/defaults` in
new immutable artifact `thought-khoral-agent-conversation-v1.1.0`, retaining the
v1 profile/namespace and all existing published v1.0 schema/fixture bytes.
The broker validates authenticated room/agent authority, current admission,
catalog revision, policy-default pair and five-second bound before responding.
The read has no task/event/conversation/lease/native-state mutation, exposes no
effective-settings confirmation, credentials or private/native identifiers,
uses the existing safe ProfileError/HTTP mapping and `Cache-Control: no-store`.
There is no inferred catalog-order model or inference fallback.

The UI resolves and displays the concrete explicit next-turn pair when absent
or explicitly New/reset; restored continuation uses accepted shared settings.
Both capabilities allow both controls; effort-only keeps the resolved model
read-only; model-only keeps the displayed model-specific catalog default effort
read-only; neither capability retains the settings-free path. Unsupported
controls stay uneditable and no hidden control blocks a valid required choice.
Catalog/pair mismatch requires bounded refresh or an explicit unavailable state.
A still-valid explicit pair is not replaced after a deployment-default-only change.

As a scoped exception to the earlier published-artifact-first execution order,
isolated consumers may pin a reproducible local candidate from an exact committed
contracts revision, verified archive and per-file SHA-256 values, clearly marked
unreleased. This exception is only for this amendment's local pre-publication
development and synthetic testing. Published v1.0 provenance/bytes remain intact.
The reviewed source was merged to local `main` under explicit user
authorization; this does not authorize release publication, shipped
interoperability, push, provider use or service activation. Whole milestone/Task9
acceptance remains open.

### Local contract implementation annex

The additive schema is `schemas/agent-conversation-v1/resolved-settings.schema.json`.
`ResolvedSettingsView` is the closed object {profileVersion, roomId, agentId,
selectedSettings}, with every field required. UUIDs use the existing canonical
lower-case definitions; selectedSettings references the existing model,
reasoningEffort and catalogRevision definition without changing any old schema.
The authenticated defaults endpoint accepts no body or query and returns HTTP
200 only after trusted room/agent binding, catalog revision and supported-pair
validation. Existing ProfileError maps malformed IDs to 400, authentication to
401, authority denial to 403, unavailable scope to 404, and admission/catalog/
configured-pair failure to 503 runtime_unavailable. It never creates a task or
terminal failure. Cache-Control is no-store and validation remains five seconds.

The unchanged original 125-case manifest and retained fixtures are accompanied
by an independent 16-case defaults manifest. Its semantic oracle checks
room-binding, agent-binding, catalog-stale and unsupported-settings separately
from JSON Schema and strict raw-JSON duplicate-key rejection. Trusted model
data may list the policy-selected model after other models.

The local builder archives full repository committed bytes using git archive;
its candidate directory is the exact full commit and cannot be overwritten.
The vendor payload preserves source-relative paths for the complete conversation
schema directory, original and additive fixture directories, semantic oracle and
both fixture runners. The closed lock records profile, unreleased-local-candidate
status, proposedTag, repository, exact commit, archive filename/digest/prefix,
original baseTag/baseCommit/baseArchiveSha256 and sorted per-file SHA-256 values.
The lock digest is a separate sidecar and must also be anchored in consumer code.
Verification requires the external anchor and rejects altered metadata, archive,
payload, symlinks and unexpected files. Two builds of one commit must be byte
identical, and the extracted full archive must run its own npm fixture/test suite.
These implemented contract artifacts do not establish published interoperability
or any broker/UI/runtime acceptance.

## Local main integration checkpoint — 2026-10-07

The reviewed v1.1 defaults candidate source is merged into local `main`; its
proposed release remains unpublished. The existing v1.0 release/tag, artifact,
and fixture bytes remain unchanged. Contract tests passed from the reviewed
candidate source, and exact merge/source commits are recorded in the local spec
index and coordinated parent plan. No push, provider use, or service activation
is authorized by the merge.

## Pushed POC checkpoint — 2026-10-07

The reviewed v1.1 defaults candidate source is pushed to GitHub `main` in
`b930b225ea7de12bb124f4cc4cdf7a87a27c7a50`. This does not create a v1.1.0
release/tag or change the published v1.0.0 artifact. The source remains an
experimental candidate; its fixture and integrity tests passed in provider-free
review, while release publication and consumer activation remain separate gates.
