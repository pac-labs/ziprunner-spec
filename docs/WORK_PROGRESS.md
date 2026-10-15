# Work planning, completion and handover

## Workboard requirement

Under the source ZIP workboard contract documented for ZipRunner 1.2.304.55, every source ZIP contains a root-level `.ziprunner-workboard-update.json` with `implemented` and `remaining` arrays. `implemented[].operator_checks` contains manual acceptance steps. Source ZIPs missing the file fail preflight **before** stop, backup or overlay. After a successful build, the importer records author-reported implementation evidence, but tasks do not automatically become Done. **After required manager/QA and operator acceptance, the same original task ID MUST transition to Done**, not remain perpetually in review or spawn a duplicate task. No delivery import occurs when build fails; the overlay may still have happened. Duplicate artifact hashes MUST NOT add duplicate history. See [WORKBOARD_UPDATE.md](WORKBOARD_UPDATE.md).

## Two truthful views

**Producer-declared view:** `planned_work` (what this pass intended), `done_work` (what the author reports finished), `todo_work` (everything from this pass not finished). An author may report source changes as implemented while accurately declaring platform-specific compilation or live testing as not run.

**Consumer-observed view:** archive/recipe validated, backup and overlay applied, build status, test results, live status with provenance, operator verification and release gates. These are never imported as trusted outcomes from producer-authored ZIP metadata.

## Work item lifecycle

Stable IDs such as `ZR-UI-050` or `BF-030` identify **work**, not packaging attempts. An item can persist through many versioned updates. `planned_work` belongs to the current `update.id`; roadmap entries in the existing `ziprunner.project-state.json` can represent longer-term backlog.

- `todo_work.status`: `planned`, `in_progress`, `review`, `blocked`, `deferred`.
- `done_work` means *author reports code or documentation work finished*, not independent verification.
- `deferred` items remain visible in progress and next-pass handover.
- Verification MUST set the existing work item to `done` once its acceptance criteria, required QA review and operator confirmation have succeeded, recording trusted evidence. The producer cannot do so for the consumer. If verification fails, keep the item unresolved with explicit outstanding criteria or blockers.
- Any work-item scope amendment records its explanation under `plan_changes` and keeps the stable ID.

### Counting

For an update, `reported_done_count = len(done_work)`; `remaining_count = len(todo_work)`; `planned_count = len(planned_work)`. Percent reported = `reported_done_count / planned_count`, when nonzero. 'Verified completion' is an independent metric based on a separate consumer record. A blocked item is remaining, not completed. Do not add version numbers together or count test assertions as independent feature completions.

## Project-state interoperability

`ziprunner.project-state.json` records progress and roadmap information using a separate established convention. Historical packages may contain `schema: ziprunner.project-state.v1` or `schema: ziprunner.project-state/v1`; legacy-compatible consumers SHOULD document and normalize the supported forms without discarding prior tasks. This specification does not redefine the `project.zr` project recipe.

For each new update, a consumer MUST append/update `passes[]` keyed by stable version/update ID and reconcile roadmap items by stable IDs. Once approval is recorded, the board projection MUST close the existing ID; keeping an approved task unresolved is an error and blocks release readiness. It SHOULD preserve an explicit local `ziprunner_status_override` unless an authorized transition/verified closure supersedes it. Malformed legacy roadmap statuses SHOULD remain visible as raw input/error rather than being falsely interpreted as confirmed completion. Treat imported pass descriptions as producer claims.

## Human-readable release information

Human-facing handover information may summarize the exact artifact/version, planned/delivered/unfinished work, executed and omitted tests, known blockers, compatibility notes, and outstanding verification or approval. `ZIPRUNNER_HANDOFF.md` is a supported human-readable convention. An externally delivered ZIP MUST additionally have a real, clickable download link, exact filename, project/version and SHA-256 in the delivery message (see [delivery contract](DELIVERY.md)); machine-readable status remains authoritative only within its defined trust boundary.

Do not state 'all passed' unless every named required test was actually observed passing in the correct environment. Static validation cannot substitute for a platform build or live application testing.

## Durable history

The consumer stores a per-update immutable record with: SHA-256, project key, declared version, manifest digest, processing timestamp, recorded local events and final state. Imported revisions MUST be idempotent; prior failures are not erased by later unverified assertions. Human changes must be auditable. State files are written atomically and never maintained inside untrusted package root as the sole source of truth.

## Feature tests and bounded feedback

The v2.3 [functional verification plan](FUNCTIONAL_VERIFICATION.md) links delivered stable IDs to real checks of acceptance criteria; a build is not a proxy for functional completion. Passing observed tests create evidence for review, but closure follows the trusted acceptance policy, preserving the existing Done gate. The [origin feedback contract](ORIGIN_FEEDBACK.md) returns the actual result to a verified originating request rather than the active browser tab; unsuccessful sending remains visible and retryable, and does not change Work board truth.
