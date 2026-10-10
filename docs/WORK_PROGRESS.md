# Work planning, completion and handover

## Two truthful views

**Model-authored view:** `planned_work` (what this pass intended), `done_work` (what the author reports finished), `todo_work` (everything from this pass not finished). An author can report completion on code changes without claiming Windows compilation or a live external-app test.

**ZipRunner-owned view:** archive/recipe validated, backup and overlay applied, build status, test results, live status with provenance, operator verification and release gates. These are never imported as authority from a model ZIP.

## Work item lifecycle

Stable IDs such as `ZR-UI-050` or `BF-030` identify **work**, not packaging attempts. An item can persist through many versioned updates. `planned_work` belongs to the current `update.id`; roadmap entries in the existing `ziprunner.project-state.json` can represent longer-term backlog.

- `todo_work.status`: `planned`, `in_progress`, `review`, `blocked`, `deferred`.
- `done_work` means *author reports code or documentation work finished*, not independent verification.
- `deferred` items remain visible in progress and next-pass handover.
- Verification may set consumer-reviewed task statuses (`review`, `done`, `blocked`) after collecting evidence; the producer cannot do so for the consumer.
- Any work-item scope amendment records its explanation under `plan_changes` and keeps the stable ID.

### Counting

For an update, `reported_done_count = len(done_work)`; `remaining_count = len(todo_work)`; `planned_count = len(planned_work)`. Percent reported = `reported_done_count / planned_count`, when nonzero. 'Verified completion' is an independent metric based on a separate consumer record. A blocked item is remaining, not completed. Do not add version numbers together or count test assertions as independent feature completions.

## Translation to currently supported project state

ZipRunner 1.2.304.49 reads `ziprunner.project-state.json` and merges passes/roadmap with local project-pass-state. It accepts `schema: ziprunner.project-state.v1` as its default; a Bozja package uses `schema: ziprunner.project-state/v1`. In v1, the normalized file SHOULD use `ziprunner.project-state.v1` for the code's default and interoperability; consumers SHOULD accept either legacy spelling at import. This standard **does not change** the current supported `project.zr` format.

For each new update, a consumer SHOULD append/update `passes[]` keyed by stable version/update ID and reconcile roadmap items by stable IDs. It SHOULD preserve an explicit local `ziprunner_status_override` unless an authorized transition/verified closure supersedes it. Malformed legacy roadmap statuses SHOULD remain visible as raw input/error rather than being falsely interpreted as confirmed completion. Treat imported pass descriptions as producer claims.

## Handover checklist

Every produced update requires a concise terminal response containing exact artifact/version, planned/done/todo, tests actually run and skipped, known blockers, next intended pass, rebuild/restart requirements, and operator decisions still needed. Include `ZIPRUNNER_HANDOFF.md` for humans where practical.

Do not state 'all passed' unless every named required test was actually observed passing in the correct environment. A source-only static validation cannot substitute for a Windows build or in-application testing.

## Durable history

The consumer stores a per-update immutable record with: SHA-256, project key, declared version, manifest digest, processing timestamp, recorded local events and final state. Imported revisions MUST be idempotent; prior failures are not erased by later unverified assertions. Human changes must be auditable. State files are written atomically and never maintained inside untrusted package root as the sole source of truth.
