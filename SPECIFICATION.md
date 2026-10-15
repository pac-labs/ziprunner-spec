# ZipRunner Interchange Specification — v2.3.0

*Revised 2026-10-15. Version 2.3.0 adds functional verification and correlated result feedback contracts. The established Work board v1 intake, direct ZIP handoff, optional Looprd extension, and release approval boundaries remain unchanged. Consumer implementation support may vary.*

**Versioning:** v2 is a major revision because it adds a mandatory source ZIP file that v1 producer packages did not need. See [workboard contract](docs/WORKBOARD_UPDATE.md). The published `ziprunner.workboard-update.v1` schema and reference example define the mandatory producer-side workboard document. Exact consumer support is version-specific; see [compatibility](docs/COMPATIBILITY.md).

## 1. Scope and language

This specification defines an interoperable contract between an **artifact producer** (AI model, build system or developer), a **package validator**, a **ZipRunner operator**, and a **ZipRunner-compatible consumer**. It intentionally does **not** prescribe the application's internal Python/Tkinter architecture.

**MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY** express requirement levels. The terms **reported** (producer assertion), **observed** (consumer-collected result), **verified** (evidence evaluated against acceptance criteria), and **approved** (explicit operator decision) are distinct; they MUST NOT be conflated.

Consumers implementing only the pre-v1 package conventions MUST NOT advertise ZipRunner Interchange v1 compliance.

## 2. Specification identity

- The published specification version is `2.3.0`; major versions can change required source ZIP contents. The standalone `ziprunner-manifest.json` JSON schema retains its independent `spec_version: "1.x.y"` identity as a proposed supplemental protocol.
- **Every source update ZIP MUST contain an effective-source-root `.ziprunner-workboard-update.json`** with `schema: "ziprunner.workboard-update.v1"`. This is the currently enforced workboard gate and must never be replaced by a different manifest name or schema ID.
- The separate supplemental work manifest `ziprunner-manifest.json` retains schema `ziprunner.update-manifest/v1` and `spec_version: "1.x.y"`; it is still required for **full interchange v2 producer conformance**, but ZipRunner 1.2.304.55 must not be assumed to parse it. The workboard gate itself does **not** require the supplemental manifest.
- Project identity MUST be explicit and stable, independent of the ZIP filename or an application's current user-interface selection.
- An update MUST declare a unique project-scoped `update.id` for replay deduplication and lineage. Retrying the exact same artifact SHOULD preserve this ID; changing payload content requires a new revision/ID.
- Consumer state MUST record artifact SHA-256, imported manifest content or digest, processing time, resulting state, and any human approvals.
- Package records MUST use UTF-8 JSON with no executable directives hidden in free text.

## 3. Existing ZipRunner artifacts: preserve, do not replace

| File | Implementation status / reference baseline | Intended use |
| --- | --- | --- |
| `project.zr` / externally provided `.zr` | Present, schema `ziprunner.zr/v1` | Project identity, filename matching, commands, paths, safety and release mechanisms |
| `ziprunner.project-state.json` | Present, accepted by project progress reader | Durable project history, passes, roadmap items and local operator status overrides |
| `.ziprunner-post-update-tests.json` | Present, schema `ziprunner.post-update-tests.v1` | Bounded checks after an update is usable; results owned by ZipRunner |
| `.ziprunner-package-manifest.json` | Present in ZipRunner self-source package, schema `ziprunner.source-package-manifest.v1` | Per-file hashes, sizes, modes and complete-source integrity; **not** work progress |
| `ZIPRUNNER_HANDOFF.md` | Existing human-readable handover convention | Release summary and outstanding checks; not a machine-enforced status directive |
| `.ziprunner-workboard-update.json` | Required workboard intake convention documented for ZipRunner 1.2.304.55; installed-version conformance should be verified separately | Implementation evidence and operator checks; imported into durable Work board only after successful build |
| `ziprunner-manifest.json` | Supplemental interchange contract; runtime support varies | Richer planned/done/todo, source evidence and handover; distinct from the enforced workboard gate |
| `ziprunner-verification-plan.json` | **New full v2.3 producer conformance extension; not established as a legacy runtime gate** | Stable-task acceptance criteria mapped to trusted automated/manual checks; not an instruction to execute commands |

Producers SHOULD include already-supported artifacts appropriate for the managed project. New files MUST NOT silently redefine semantics of these older formats. In particular, `gating: true` in a `.ziprunner-post-update-tests.json` example MUST NOT be treated as proof that current ZipRunner gates installation; source code describes these checks as **non-gating after application readiness**. Build-time test commands configured in the `.zr` recipe are a separate mechanism.

## 4. Archive contract

A conforming new source update contains:

```text
project.zr                            # existing recipe (or previously configured equivalent)
.ziprunner-workboard-update.json       # REQUIRED runtime gate for all source ZIPs
ziprunner-manifest.json               # supplemental v2 interoperability manifest
ziprunner.project-state.json          # recommended existing progress bridge
.ziprunner-post-update-tests.json     # when post-update checks apply
ziprunner-verification-plan.json        # full v2.3 functional-verification extension
README.md                             # project instructions
...source files, tests, documentation, evidence...
```

The workboard file MUST be validated after safe extraction but **before stopping processes, backups, or source overlay**. Missing, malformed, wrong-project, empty or oversized workboard files MUST reject a source update. ZIPs MUST identify the intended project and MUST NOT trust naming patterns as sole authority. If a package also has an explicit source integrity inventory, all declared files MUST match hashes/sizes and ZIP contents. The `ziprunner-manifest.json` metadata does not by itself authorize extraction, execution, repository access or publication.

Source archives MUST use portable relative POSIX-style paths. Reject traversal, absolute/drive/UNC paths, collisions under Windows case folding, symlinks/hardlinks/device entries, unsafe names and decompression bombs. Validate contents before writing into a target; compare canonical paths, not string prefixes. See [security](docs/SAFETY.md).

## 5. Mandatory source ZIP Work board update (implemented intake contract)

For every source ZIP, including managed projects other than ZipRunner and ZipRunner self-updates:

- Include exactly one **effective-source-root** `.ziprunner-workboard-update.json` (ZIP root, or the one configured `strip_single_root` source folder), UTF-8 JSON, at most **256 KiB (262,144 bytes)**.
- Its `schema` MUST be exactly `ziprunner.workboard-update.v1` (period before `v1`, not slash). Its `project` MUST match the configured ZipRunner project key; `version` MUST describe the delivered project version; `summary` MUST describe actual work delivered.
- `implemented` MUST be a nonempty array of objects with nonempty `id`, `title`, `summary`, and a nonempty array of meaningful `operator_checks` strings.
- `remaining` MUST be present, even if `[]`; each item MUST provide `id`, `title`, `summary`; optional `priority` values are only `critical`, `high`, `medium`, or `low`.
- Task IDs MUST start with an ASCII alphanumeric character and thereafter contain only ASCII letters, numbers, underscores, hyphens, periods or colons. IDs MUST be unique across `implemented` and `remaining`, stable between releases, and never placed in both lists in one update.
- Report implemented code truthfully. Preserve previously completed work and existing acceptance criteria; workboard import is a merge, not a destructive replacement.
- Validation occurs after safe extraction and **before stop/backup/overlay**. Invalid packages are rejected, not silently fixed or retargeted. After a successful build ZipRunner imports author-reported implementation evidence into durable Work board history, keyed idempotently by the ZIP hash. **Build success does not mark tasks Done.** Once manager/QA review and operator acceptance verify all required criteria, ZipRunner MUST transition the *existing* task to **Done** under its stable ID, preserving evidence and prior history. A verified task that remains unresolved is a reconciliation defect and blocks release verification.
- On build failure, implementation is **not recorded as delivered**; do **not** claim the source overlay was automatically rolled back.
- Do not put credentials, private keys, active local configuration, or runtime state in either workboard metadata or source ZIPs. ZipRunner self-update ZIPs MUST NOT include active `ziprunner.config.json` (sample only).
- **RoboScope `.patch` / `.diff` deliveries are excluded** and retain their separate contract.

The required v1 structure is defined in the [published JSON Schema](schemas/ziprunner-workboard-update.schema.json) and [reference example](examples/ziprunner-workboard-update.reference.json). The [workboard lifecycle](docs/WORKBOARD_UPDATE.md), [verification semantics](docs/WORK_PROGRESS.md), and [compatibility guide](docs/COMPATIBILITY.md) describe the distinction between format conformance and runtime support.

## 5A. Verified closure and reconciliation (normative consumer behavior)

Every source update MUST be reconciled against the existing project Work board **by original task ID**, never by appending another task for the same work. Implemented tasks are producer-reported until built and independently verified. A successful build only creates or updates an **awaiting-verification** candidate. Once manager/QA review and operator acceptance confirm all original acceptance criteria, the consumer **MUST move that original work item to Done** and persist authorized verification evidence, reviewer and timestamp in trusted local state. The human operator must not have to drag a second duplicate card to Done.

Partially implemented work remains In Progress with missing criteria listed; blocked work requires a documented reason and unblock condition from the trusted review/workboard workflow; unstarted work remains To Do. The author-supplied v1 `implemented`/`remaining` fields do **not** authorize status changes on their own. Retain current Done states and acceptance criteria when newer unverified ZIPs arrive. Stable task IDs MUST not be recycled, and already-completed functionality MUST not receive a fresh task ID merely to represent a new package. Unknown ID collisions/semantic duplicates require explicit review.

**Release readiness MUST fail** if any task declared delivered as part of the release is unverified or unresolved, or if an authorized verified-complete task has not actually been moved to Done under its original ID. Do not require unrelated planned backlog to be Done. Reimports of the same artifact hash and repeated review events are idempotent. Record and display created, updated, closed, blocked and still-awaiting-verification counts. This is a normative requirement for lifecycle-conformant consumers, not a claim that every installed version already implements it. All push/tag/release/publish actions remain operator-gated. See [full reconciliation rules](docs/WORKBOARD_UPDATE.md).

## 6. Supplemental work manifest requirements (producer conformance, *not* the runtime gate)

The JSON Schema is [`schemas/ziprunner-manifest.schema.json`](schemas/ziprunner-manifest.schema.json). Required information:

- `project.key`, `project.version` (and optional `base_version` / `source_revision`).
- `update.id`, `update.kind`, `update.created_at`, `update.summary`.
- `planned_work`: stable IDs, clear titles, acceptance criteria and scope for **this update**.
- `done_work`: references to planned IDs, descriptions and at least one real evidence reference per completed item. These remain **producer-reported** until independently checked.
- `todo_work`: references to uncompleted planned IDs, status, and next action; blocked items identify blockers.
- `validation`: author-declared checks with `passed`, `failed`, `not_run` or `blocked` outcomes, and an honest overall reported assessment.
- `handover`: context, risks, blockers, and the precise next intended pass.
- `operator_actions`: operator actions needed, never preapproved.
- `release`: explicit intent and `requires_operator_approval: true`; the field is a **request**, not permission.

`planned_work` IDs MUST be unique. The sets of `done_work` and `todo_work` IDs MUST be disjoint, and their union MUST equal planned IDs. For an update with zero planned work (e.g. a data-correction pass), all three arrays MUST be empty with an explanatory summary. Each update cannot quietly drop a planned item: move it to `todo_work` with `deferred` status, or revise the plan with a recorded change. Stable IDs MUST be reused across updates for the same task.

A done item with incomplete verification can be represented as producer-completed while the consumer still displays **awaiting verification**. Any genuinely unfinished implementation MUST remain in `todo_work`. Unexecuted validation MUST say `not_run`, never `passed`.

## 7. Persistent progress projection

A consumer supporting the supplemental richer work manifest SHOULD import it as an immutable **update record**, then project it onto existing `ziprunner.project-state.json` passes/roadmap with stable IDs. It MUST preserve prior pass history, operator-owned status overrides, approvals, negative test results and evidence. It MUST NOT treat a repeated imported ZIP as a new pass or overwrite newer verified records with older model claims.

Consumer-maintained state and event journal MUST be stored outside an untrusted source ZIP and updated atomically. The model can propose progress but cannot directly author consumer-verified or operator-approved fields.

Recommended progress semantics:

| Field or state | Owner | Meaning |
| --- | --- | --- |
| `planned_work`, `done_work`, `todo_work` | Artifact author | Declared intentions and progress |
| `validation.checks` | Artifact author | Claimed author-side test results |
| `package_validated`, `build`, `runtime`, `post_update_tests` | ZipRunner | Observed local execution outcomes |
| `verified_done` / `requires_review` | Consumer review pipeline / operator | Acceptance assessed independently |
| `release_approved`, `push_approved`, `tag_approved` | Operator | Explicit irreversible-action gate |

Progress percentages MUST label their basis (for example, '2 of 3 work items reported done' versus '1 of 3 verified'). Avoid fabricated metrics, “healthy” claims from a process PID, and treating warnings as green successes. A `not_run` test is unknown, not passed.

## 8. Package kinds

- `source_update`: source changes plus **mandatory workboard metadata** (and the supplemental interchange manifest for full spec conformance). The consumer may follow its existing stop, backup, overlay, build, post-update check and optionally start sequence, under project policy and operator gates.
- `progress_update`: **optional, proposed consumer support**, exempt from the source ZIP workboard gate. Metadata-only package with no source overlay/build/start or privileged actions. The consumer validates identity/provenance and imports planning updates only after explicit project matching and review. The presence of this definition does not establish support in existing consumers.

The `progress_update` proposal MUST NOT be confused with a source ZIP. A source ZIP with only the supplemental `ziprunner-manifest.json` is rejected by the 1.2.304.55+ workboard gate; adding the workboard file is mandatory even if the project supplies a `.zr` recipe or human handover. Both formats MUST preserve local configuration and protected state. A progress-only import can carry only the work manifest, an optional project-state proposal and handover/docs; it MUST NOT contain shell commands, executables, project recipe changes, or release operations.

## 9. Test and evidence rules

Verification layers are deliberately separate:

1. **Static/schema checks:** well-formed JSON, package safety, identity, cross-reference and file hashes.
2. **Author checks:** tests the producer actually ran; record command, result and environment. Where tests could not run, record `not_run` and reason.
3. **ZipRunner build checks:** commands specified by the trusted project configuration or reviewed recipe; log exit code/output in durable consumer state.
4. **ZipRunner post-update checks:** non-gating follow-up tests, not proof of prior build success or live health.
5. **Runtime/operator acceptance:** smoke, GUI, external-device/application and approval checks performed in the correct environment.

Evidence references MUST refer to real package-relative files or complete HTTPS URLs. Do not forge test logs or treat self-asserted evidence as independent proof. A producer MUST distinguish source-only checks from target environment or live application tests.

## 10. Command/release safety

Untrusted metadata MUST NOT expand the trusted command set; `operator_actions` are informational. The established recipe/config system is the only command authority, subject to operator review and local policies. Push, commit, tag, GitHub release, publication, deployment, deleting user data and privileged recovery MUST remain explicitly gated, independently of manifest settings. Unknown/conflicting project matches require operator resolution.

Protected local files (including the active ZipRunner `ziprunner.config.json`, per-project secrets and protected state) MUST never be overwritten, even if an archive accidentally contains them. ZipRunner self-updates MAY include only `ziprunner.config.sample.json` as the configuration template and MUST NOT include an active `ziprunner.config.json`.

## 10A. Optional Looprd / DAPI API and data-model integration

Projects defining API/database components through Looprd MAY provide the authoritative `looprd.yaml` and an optional root-level `ziprunner.looprd.json` producer link (`ziprunner.looprd-link/v1`) declaring project key, stable component ID, safe relative specification path and exact SHA-256. Non-Looprd projects MUST NOT be required to ship them. The link MUST NOT duplicate database models, secrets or Looprd's `sources.yaml` and MUST NOT authorize deployment, migration or reconciliation.

For a declared link, a v2.1-conforming producer/independent package validator MUST verify project identity, safe path, packaged-file existence and SHA-256. A Looprd-aware validator SHOULD use the pinned DAPI CLI for full YAML syntax/semantic checks; this spec's standard-library validator does not parse arbitrary YAML or run a database. ZipRunner `project_key` and Looprd `component` are distinct identity domains, and mapping MUST be reviewed rather than guessed. Data-model/API changes MUST appear in the mandatory Work board with stable tasks and operator checks. API activation, database migrations, and observed runtime health remain separate from ZipRunner build completion and release approval. See [Looprd / DAPI integration](docs/LOOPRD.md).

`pac-labs/dapi` is the source of truth for `looprd/v1`: SQLite/PostgreSQL models, operations/scopes, WebSocket messages, additive migrations and runtime behavior. Its source index governs component registration. Consumers MUST NOT silently deploy a Looprd component, grant a management key to a client, treat a health endpoint as database verification, or assume a committed schema migration is undone by application rollback. See [`pac-labs/dapi`](https://github.com/pac-labs/dapi) and the versioned source reference in the integration guide.

## 10B. Downloadable artifact handoff

Whenever a producer delivers a downloadable ZIP, the accompanying human-facing handoff or release message **MUST** include a **direct clickable download link** to that exact ZIP. A filename, workspace-local path, source repository URL, release landing page, or a statement that a ZIP was created is insufficient by itself. The handoff **MUST** also state the configured project key, delivered version, exact ZIP filename and SHA-256 of the distributed ZIP. This obligation applies to managed source ZIPs and other ZIP deliveries, whether generated manually, by CI, or by an automated producer. It does not change the separate RoboScope `.patch`/`.diff` artifact contract.

A link **MUST** be established from a real uploaded/generated artifact and must be retrievable by the intended recipient. HTTPS direct-download URLs are preferred for lasting public distribution; a platform-provided artifact link is acceptable for a session delivery if the recipient can actually open it. Temporary links MUST NOT be presented as permanent release locations. The named download MUST reference the same bytes identified by the filename and checksum. Producers MUST NOT invent or guess URLs, and SHOULD verify reachability where technically possible. If an actual retrievable link cannot be provided, the handoff MUST say **delivery incomplete**, explain the blocker and MUST NOT claim the artifact was delivered.

The standard `ZIPRUNNER_HANDOFF v1` project, version and ZIP filename fields remain unchanged; the download link and SHA-256 are additional **human-facing delivery information**, not instructions to an archive parser or automatic install authorization. A package-embedded `ZIPRUNNER_HANDOFF.md` MAY record a known permanent URL, but the external delivery message MUST supply the currently valid link, since download addresses are often assigned after packaging. Handoff information MUST NOT contain access tokens, private credentials or protected local file paths. See [downloadable handoff](docs/DELIVERY.md).

## 10C. Functional verification, work item closure and original-request feedback

Full **v2.3 functional-verification producer conformance** requires an effective-root `ziprunner-verification-plan.json` (`ziprunner.verification-plan/v1`) in managed **source ZIPs**, in addition to the unchanged mandatory v1 Work board metadata. It MUST match the package identity/version, reference **every implemented Work board ID**, and map each delivered functional acceptance criterion to explicit automated, manual or mixed checks with nonempty assertions or operator instructions. Automated checks additionally MUST reference **real test implementations inside the source ZIP** via safe `test_ref` paths, never just assertion descriptions. Its configured `runner_ref` is an inert identifier, NEVER an executable command embedded in the untrusted archive. A consumer supporting only the older workboard gate MUST NOT be described as supporting this extension automatically. The package validator offers `--require-verification-plan` to check full v2.3 conformance.

Consumers claiming v2.3 verification support MUST execute trusted tests against the delivered artifact revision, capture the actual outcomes and logs, and persist a consumer-owned `ziprunner.verification-report/v1` with artifact/plan SHA-256, environment, run ID, per-check outcomes and provenance. A green build or producer claim alone is insufficient. All original accepted criteria MUST be checked; missing test coverage or required human verification remains **unresolved**. Once the required independent manager/QA and operator approval is recorded (or the trusted project has an explicit pre-authorized automated acceptance policy for those criteria), the consumer MUST move **the original stable task ID** to Done, idempotently and with evidence. Failing/blocked/not-run checks MUST NOT mark Done. Release-readiness checks MUST reject inconsistent delivered scope; all push/tag/deploy approvals stay separate.

Consumers implementing correlated origin feedback MUST bind each import to its initiating request and **verified destination** using trusted intake metadata, not the current tab or an untrusted ZIP-provided URL. After success, failure, or interruption they MUST persist a sanitized `ziprunner.origin-feedback/v1` result and queue it to the original authorized conversation/channel. They MUST distinguish queued, submitted and acknowledged delivery, use idempotent retries and bounded budgets, and never claim a message appeared without reliable acknowledgement. If the originating destination is unavailable or uncertain, park the report for operator review and provide a copyable fallback. Returning test results MUST NOT itself authorize more development passes or privileged actions.

A producer MUST NOT claim that a specification document alone enables the consumer to run test commands, close Work board cards, or control a browser. See [functional verification](docs/FUNCTIONAL_VERIFICATION.md), [origin feedback](docs/ORIGIN_FEEDBACK.md), and [conformance](docs/CONFORMANCE.md).

## 11. Independent producer and consumer interoperability

Source packages MAY be produced by people, build systems, or automated tooling using the public schema and reference validator without access to the ZipRunner application implementation. Producer declarations MUST describe the actual packaged source and observed tests; conformance of a ZIP does not establish that a particular consumer has built, installed or verified it.

Consumer implementations SHOULD publish their supported schema IDs, applicable specification revision, and verification behavior. Schema validation and acceptance evidence are separate concerns. For general guidance, see [producer information](docs/PRODUCERS.md), [conformance](docs/CONFORMANCE.md), and [compatibility](docs/COMPATIBILITY.md).
