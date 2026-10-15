# Functional verification and task-to-test traceability

**Contract:** ZipRunner Interchange v2.3.0. This is a public interoperability requirement for producers and consumers advertising **functional-verification v1** support. It does not claim every existing ZipRunner installation executes this extension.

## Problem and intended result

Compiling code proves only that a build succeeded. A feature is acceptance-verified when **each applicable existing acceptance criterion** is supported by reliable evidence from the corresponding source revision, reviewed under the project's trusted acceptance policy. A green build, a running process, a model claim, or a unit test unrelated to the feature MUST NOT silently close a work item.

## Producer plan

For **full v2.3.0 functional-verification producer conformance**, a source ZIP MUST include `ziprunner-verification-plan.json` at its effective source root. It supplements, but MUST NOT replace, `.ziprunner-workboard-update.json` (`ziprunner.workboard-update.v1`), `ziprunner-manifest.json`, and existing tests. Producers MUST NOT embed local approval decisions or automatically executable shell commands in the plan.

The plan uses `schema: "ziprunner.verification-plan/v1"`, an exact `project` and `version`, `tasks[]` using stable Work board IDs, and `checks[]` with stable check IDs:

- Every item in workboard `implemented[]` MUST have exactly one matching `tasks[]` entry. Tasks in `remaining[]` MAY have test plans in a later package, but MUST NOT be misrepresented as delivered in this update.
- Each delivered task MUST enumerate the intended acceptance criteria and which checks cover each criterion. Existing trusted board acceptance criteria take precedence; the producer MUST NOT weaken, replace, omit or silently rename them. If existing criteria cannot be obtained, the consumer MUST flag the gap for review, not claim complete coverage from self-authored criteria alone.
- A criterion MUST be explicitly `automated`, `manual`, or `mixed`. Each criterion requires at least one linked check of the matching kind; `mixed` requires both. A generic build command with no feature-specific assertions is insufficient proof.
- An automated check MUST declare `runner_ref`, a portable `test_ref` path to the **actual packaged test implementation**, and explicit, non-empty assertions. The referenced test file MUST exist inside the source ZIP for full conformance. A plan that merely describes a desired assertion without including test implementation is incomplete. `runner_ref` is an identifier resolved only against trusted, configured runners. It is **not** a shell expression, remote URL, elevated command, or installation instruction. Unknown runners remain `blocked` or `not_run` until reviewed; never execute arbitrary package metadata.
- A manual check MUST contain meaningful human-readable verification instructions. Unavailable manual checks remain `not_run` or `blocked`, never pass by default.
- All IDs MUST be unique within their domains and reference real, non-duplicated items. The static reference validator checks this linkage; verification quality and completeness against pre-existing Work board criteria require trusted consumer data.

Author-supplied test evidence remains producer-reported. The consumer SHOULD execute tests after trusted build readiness, using bounded configuration and isolated fixtures. For database/API components (including Looprd), apply separate migration and deployment approval gates. Tests MUST NOT perform irreversible operations on production data as an implicit consequence of loading a ZIP.

## Observed results

A consumer claiming v2.3 verification conformance MUST generate a durable **consumer-owned** `ziprunner.verification-report/v1` record **outside the untrusted ZIP**, covering the exact artifact SHA-256, plan SHA-256, project/version, run ID, environment/runner ID, observed build outcome, and results of every declared check.

Each check records `passed`, `failed`, `blocked`, or `not_run`, observation provenance (`consumer_observed`, `operator_observed`, or `producer_reported`), plus evidence references and hashes for passed checks. An author-supplied result MUST NOT be promoted to consumer observation. Unexecuted tests MUST NOT be reported as passed. A passed result with no evidence is invalid. Logs and artifacts MUST be attached to that exact run and source revision, not reused from another build.

The consumer MUST also compare results with **all existing trusted criteria**, including previously created and unresolved tasks. Missing coverage, flaky tests, unsupported runner settings, stale artifact hashes, or incomplete acceptance produce `awaiting_verification`, `in_progress`, or `blocked` with explicit reasons. A report marked complete despite a failing or missing required check is non-conformant.

## Lifecycle rules

1. Source ZIP is safely validated before modifications; the Work board file remains mandatory.
2. Trusted build runs; a failed build prevents new work from being recorded as delivered, but MUST NOT be mistaken for automatic rollback.
3. The consumer executes applicable trusted checks, persists immutable observations, and reconciles results against the existing task ID and original acceptance criteria.
4. Automated passing criteria move implementation to **awaiting review/verification** by default. After the project's required manager/QA review and operator acceptance (or an explicit pre-authorized acceptance policy that permits specific criteria to close automatically), **the same task ID MUST move to Done** and keep full audit provenance. No untrusted ZIP can grant itself automatic-acceptance permissions.
5. Failed tests keep the task unresolved; blocked checks record a reason and unblock condition when known; untested checks remain unknown, not passed.
6. Release readiness MUST reject an approved delivery whose included work items are not verified and correctly closed. Unrelated future backlog can remain open.

A check result is never a status-transition instruction in the ZIP. Work board decisions are durable, idempotent projections of trusted test and review events. Repeated artifact hashes, re-run reports and repeated delivery acknowledgments must not create duplicate work items or reopen verified Done tasks.

## Standalone validation

```sh
python tools/validate.py verification-plan examples/verification-plan.json --workboard examples/ziprunner-workboard-update.example.json --root examples --expected-project example-project
python tools/validate.py package path/to/source.zip --expected-project example-project --require-verification-plan
python -m unittest discover -s tests -v
```

Static validation checks structure and cross-references; it **does not execute arbitrary project code**, certify user-interface behavior, connect to external services, or approve deployment. See [origin feedback](ORIGIN_FEEDBACK.md) and [conformance](CONFORMANCE.md).
