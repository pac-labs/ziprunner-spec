# Correlated verification feedback to the originating conversation

**Contract:** ZipRunner Interchange v2.3.0; consumer-owned `ziprunner.origin-feedback/v1` records. This is a public integration specification, not a claim that a particular browser, API or desktop application provides a supported send capability.

## Binding the original request

A consumer MAY support a reply-to-origin adapter for a browser conversation, issue, thread, or other messaging destination. Its **trusted intake metadata** MUST bind `project`, request/correlation ID, artifact identity (or request-scoped artifact lineage), origin destination, and channel/session identity when available. The binding MUST be captured when the source request is initiated or artifact is associated with it, *not inferred from the currently active tab*, an archive filename, model text, or an untrusted ZIP field.

The origin URL and access credentials are consumer-private data. An untrusted package may offer a correlation hint but MUST NOT authorize choosing the recipient or overriding an existing binding. If no verified mapping exists, delivery MUST remain `waiting_for_origin` and the operator can select/confirm the correct destination. Never post to a plausible but unverified conversation.

## Feedback envelope and timing

Following a completed verification attempt—including a failed build, failing check, interrupted run, or successful approval—the consumer MUST produce a durable, sanitized feedback report containing exact project/version, artifact hash, run ID, original request ID, check outcome summary, original task IDs and lifecycle states, relevant evidence/log references, blockers, next actions, and the **actual** verified Done count. The feedback record is stored outside the source ZIP.

`ziprunner.origin-feedback/v1` is a minimum interoperable envelope for these facts. The accompanying human-readable report SHOULD be concise and copyable and MUST label not-run tests, approvals pending, and any failed delivery honestly. A handoff's direct ZIP link remains governed separately by [delivery requirements](DELIVERY.md); no file path or external URL is invented merely to populate a message. Evidence links must be sanitized and accessible to the intended recipient.

## Reliable delivery state

Queue feedback only through an adapter explicitly authorized for that destination. On each submission, retain the deterministic message ID / idempotency key, destination binding, and report revision. A transport call returning without error is not sufficient proof that a message appeared in the original window. Distinguish:

- `queued`: ready for safe attempted delivery.
- `waiting_for_origin`: no verifiable return destination yet.
- `submitted`: transport requested submission but final acknowledgement is unavailable.
- `acknowledged`: the destination provider/adapter confirmed the message was accepted or appeared, according to its published acknowledgement semantics.
- `retryable_failure`: bounded retry may be attempted; show the cause.
- `blocked`: permission, correlation, review or transport policy prevents submission.

Only an explicit acknowledgement MAY set `acknowledged`; do not report "sent" based on selecting a tab or typing text. Retry with idempotency or an acknowledgement lookup to avoid duplicate posts. Apply browser rate budgets, token/permission checks, and bounded backoff. If the original tab is closed, replaced, or ambiguous, park the response for review; do not redirect it to the currently selected project/tab. Operator controls MUST expose Copy, Retry, Open verified origin (when supported), and Mark for review. Manual copy is the fallback when no supported transport exists; it MUST NOT be misreported as an automated message.

Feedback delivery is **not** permission to initiate another development pass, paste executable commands, publish source, force a Git push, or approve a release. Any next-pass automation needs its own project policy and an explicit bounded request. Confidential logs and credentials MUST be redacted before feedback transmission, and the recipient must be allowed to access the relevant information.

## Recovery and deduplication

Persist the correlation, final report, queued envelope, attempt history, acknowledgement, and last error transactionally. Reconcile after restart without replaying an already acknowledged message. Expire or flag unresolved attempts according to configured retention; failed sending MUST NOT silently discard test results or Work board state.

**Implementation support:** The reference schema and tests validate portable records only. They do not access ChatGPT, control Chrome, send messages, or connect to live ZipRunner processes. Such adapters require explicit consumer implementations and permissions.
