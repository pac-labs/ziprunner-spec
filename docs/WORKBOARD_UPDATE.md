# Mandatory ZipRunner Work board update contract

**Applies:** Source update ZIPs for every ZipRunner-managed project. **Version reference:** workboard intake is documented for ZipRunner 1.2.304.55 following the 1.2.304.53+ baseline; consumer conformance is version-specific. **Exclusion:** RoboScope `.patch` and `.diff` files.

## Source ZIP file

A source ZIP MUST contain **`.ziprunner-workboard-update.json` at the effective source root** (the archive root or the single top-level directory when `strip_single_root` is configured). This is not a replacement for `ziprunner-manifest.json`, `.zr` project recipes, `ziprunner.project-state.json`, the post-update tests contract or self-source file inventory. It does not grant permission to run commands or approve a release.

File constraints: UTF-8 JSON, maximum **256 KiB (262,144 bytes)**. Required schema string is **`ziprunner.workboard-update.v1`**, with a period before `v1`; the legacy spelling `ziprunner.workboard-update/v1` is NOT compatible with this contract.

Required top-level properties:

| Field | Meaning |
| --- | --- |
| `schema` | Exactly `ziprunner.workboard-update.v1` |
| `project` | Configured ZipRunner project **key**, not a display name or guessed ZIP name |
| `version` | Project version actually delivered |
| `summary` | Description of the implemented change |
| `implemented` | Nonempty array of objects `{id, title, summary, operator_checks}`; checks must be a nonempty list of meaningful strings |
| `remaining` | Explicit array (may be empty) of objects `{id, title, summary, priority?}` |

`priority` is limited to `critical`, `high`, `medium`, `low`. IDs MUST be unique across the two arrays and match `^[A-Za-z0-9][A-Za-z0-9_.:-]{0,119}$` (1–120 characters). The authoritative schema also limits project to 120 characters, version to 100, summary to 4,000, each item title to 240, each item summary to 2,000, up to 150 implemented and remaining items each, and 1–20 operator checks of up to 500 characters each. Stable IDs identify the same work item in later versions, including deferred/unfinished work; never recycle an ID for unrelated work. A task MUST NOT appear as implemented and remaining in one ZIP.

### Example

The published [v1 JSON Schema](../schemas/ziprunner-workboard-update.schema.json), [reference example](../examples/ziprunner-workboard-update.reference.json), and [project-matched fixture](../examples/ziprunner-workboard-update.example.json) define the producer-facing format. Static validation and a consumer's installed-parser conformance are distinct; see [compatibility](COMPATIBILITY.md).

## Intake and state lifecycle

1. Wait for a complete ZIP; safely extract into staging, rejecting unsafe paths and ambiguous targets.
2. Validate the effective-source-root workboard file, format, size, content, nonempty implemented items, stable unique IDs and configured project key, **before stopping anything, taking a backup, or applying a source overlay**. Missing/malformed/wrong-project updates are rejected with a visible reason.
3. Run the existing trusted update lifecycle: stop/backup/overlay/build/start as configured, preserving protected files and gates.
4. **Only after successful build**, import reported implementation evidence into the project’s durable Work board. Record artifact hash and deduplicate imports on repeated identical ZIPs. Do not erase past Done items, acceptance criteria, operator review, failed attempts or reviewed states.
5. The build does **not** mark tasks Done; manager/QA review and operator verification decide that. When all required acceptance criteria have been verified and the authorized operator confirms acceptance, ZipRunner **MUST move the existing task to Done** (same stable ID, no duplicate), record provenance and preserve original criteria. A task verified complete but still left In Progress/To Do/review is a reconciliation defect. On build failure, do not record new implementation as delivered. A failed build is **not evidence of rollback** and the source overlay may remain.
6. Before any release is declared complete, verify that every work item representing delivered, approved scope is **Done** by its original ID. Fail the release readiness check on verified-but-unclosed or unresolved delivered items, mismatched IDs, or missing verification evidence. This is not permission to auto-publish; push, tag, publication and deployment stay operator-gated.

## Example command (preflight without running ZipRunner)

```powershell
python tools/validate.py workboard examples/ziprunner-workboard-update.example.json --expected-project example-project
python tools/validate.py package .\my-project-1.2.3-ziprunner.zip --expected-project my-project
```

The independent tool enforces this repository's interoperability contract; it does **not** prove the installed application accepts every extension. Consumer-specific validation can apply additional restrictions; installed-version acceptance is not implied by a successful standalone preflight.

## Handover and diagnostics

Package producers MUST provide the exact source ZIP filename and project/version, reported test results (passed/failed/skipped with reasons), and an outline of implemented and remaining tasks. Integrations using the `ZIPRUNNER_HANDOFF v1` response convention MUST retain its project/version/filename fields. Operator checks must be realistically executable. The manifest must describe the code actually in the ZIP, not planned intent. Never include active config, secrets, credentials, private keys or local runtime state.

## Mandatory lifecycle reconciliation (consumer requirement)

The v1 `.ziprunner-workboard-update.json` is **producer evidence**, not a status-transition directive. No new ZIP field or schema version is needed merely to require closure. After importing a built source ZIP, ZipRunner MUST match `implemented[]` and `remaining[]` against its *existing* project Work board by stable `id`; it MUST preserve existing acceptance criteria, operator notes, QA results and Done states. It MUST NOT create a second task to represent an existing ID, nor silently assume a newly invented ID replaces an existing equivalent task. Unknown task identities or competing scope should be flagged for operator resolution.

- **Implemented + build passed, not verified:** mark the original task `awaiting_verification` / review. Show `operator_checks` and outstanding original acceptance criteria. Never report this state as Done.
- **Verified and approved:** as soon as an authorized operator confirms all acceptance criteria passed (with QA approval where required), transition that *same original ID* to `done`. Record reviewer, verification evidence, artifact/version and timestamp in trusted local state, not inside the source ZIP. A separate manual drag/drop of the card MUST NOT be required.
- **Partially implemented:** keep `in_progress` with outstanding criteria visible; `remaining[]` does not grant the producer power to downgrade an already verified Done task.
- **Blocked:** a trusted manager/QA/operator action records `blocked`, reason and unblock condition in the durable board. The v1 `remaining[].summary` may explain a blocker but cannot itself command a trusted transition.
- **Not started:** keep `todo`.
- **Failed build or failed verification:** never convert producer-reported implementation to Done; retain the failure evidence and recovery state. Do not assume automatic overlay rollback.

The workboard history is append-only by immutable artifact SHA-256 and review event; the current task board is an idempotent projection of that history keyed by stable task ID. Replaying the same artifact hash MUST NOT duplicate tasks, reviews or status events. Prior verified Done tasks MUST NOT be reopened by later unverified source ZIPs. A release readiness gate MUST reject a task reported delivered as part of the release if it has not been independently verified and closed, or if a verified task is still shown as unresolved. Backlog explicitly outside release scope MAY remain To Do or Blocked. Keep release publishing/approval gates separate.

**Conformance scope:** lifecycle reconciliation is required for consumers claiming verified-closure support. The standalone [reference algorithm](../tools/workboard_lifecycle.py) demonstrates state transitions but does not operate on installed consumer state. See [conformance](CONFORMANCE.md).
