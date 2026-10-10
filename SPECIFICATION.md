# ZipRunner Interchange Specification — v1.0.0

*Dated 2026-10-10. Status: proposed interoperable standard, not an assertion that ZipRunner 1.2.304.49 implements every requirement.*

## 1. Scope and language

This specification defines an interoperable contract between an **artifact producer** (AI model, build system or developer), a **package validator**, a **ZipRunner operator**, and a **ZipRunner-compatible consumer**. It intentionally does **not** prescribe the application's internal Python/Tkinter architecture.

**MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY** express requirement levels. The terms **reported** (producer assertion), **observed** (consumer-collected result), **verified** (evidence evaluated against acceptance criteria), and **approved** (explicit operator decision) are distinct; they MUST NOT be conflated.

Consumers implementing only the pre-v1 package conventions MUST NOT advertise ZipRunner Interchange v1 compliance.

## 2. Specification identity

- The semantic specification version is `1.0.0`; major-version changes can break interoperability, minor versions extend fields, patch versions clarify without breaking valid packages.
- The new work manifest at package root MUST be named `ziprunner-manifest.json`, with `schema: "ziprunner.update-manifest/v1"` and `spec_version: "1.0.0"` (or a compatible v1.x version after publication).
- Project identity MUST be explicit and stable, independent of the ZIP filename and chat tab.
- An update MUST declare a unique project-scoped `update.id` for replay deduplication and lineage. Retrying the exact same artifact SHOULD preserve this ID; changing payload content requires a new revision/ID.
- Consumer state MUST record artifact SHA-256, imported manifest content or digest, processing time, resulting state, and any human approvals.
- Package records MUST use UTF-8 JSON with no executable directives hidden in free text.

## 3. Existing ZipRunner artifacts: preserve, do not replace

| File | Status in ZipRunner 1.2.304.49 | Intended use |
| --- | --- | --- |
| `project.zr` / externally provided `.zr` | Present, schema `ziprunner.zr/v1` | Project identity, filename matching, commands, paths, safety and release mechanisms |
| `ziprunner.project-state.json` | Present, accepted by project progress reader | Durable project history, passes, roadmap items and local operator status overrides |
| `.ziprunner-post-update-tests.json` | Present, schema `ziprunner.post-update-tests.v1` | Bounded checks after an update is usable; results owned by ZipRunner |
| `.ziprunner-package-manifest.json` | Present in ZipRunner self-source package, schema `ziprunner.source-package-manifest.v1` | Per-file hashes, sizes, modes and complete-source integrity; **not** work progress |
| `ZIPRUNNER_HANDOFF.md` | Present in Bozja example | Human-readable handover; name/content not a formal parser protocol |
| `ziprunner-manifest.json` | **NEW, NOT CURRENTLY INGESTED** | Work plan, producer declarations, evidence and next-pass data |

Producers SHOULD include already-supported artifacts appropriate for the managed project. New files MUST NOT silently redefine semantics of these older formats. In particular, `gating: true` in a `.ziprunner-post-update-tests.json` example MUST NOT be treated as proof that current ZipRunner gates installation; source code describes these checks as **non-gating after application readiness**. Build-time test commands configured in the `.zr` recipe are a separate mechanism.

## 4. Archive contract

A conforming new source update contains:

```text
project.zr                            # existing recipe (or previously configured equivalent)
ziprunner-manifest.json               # new required work manifest
ziprunner.project-state.json          # recommended existing progress bridge
.ziprunner-post-update-tests.json     # when post-update checks apply
README.md                             # project instructions
...source files, tests, documentation, evidence...
```

ZIPs MUST identify the intended project and MUST NOT trust naming patterns as sole authority. If a package also has an explicit source integrity inventory, all declared files MUST match hashes/sizes and ZIP contents. The `ziprunner-manifest.json` metadata does not by itself authorize extraction, execution, repository access or publication.

Source archives MUST use portable relative POSIX-style paths. Reject traversal, absolute/drive/UNC paths, collisions under Windows case folding, symlinks/hardlinks/device entries, unsafe names and decompression bombs. Validate contents before writing into a target; compare canonical paths, not string prefixes. See [security](docs/SAFETY.md).

## 5. Work manifest requirements

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

## 6. Persistent progress projection

A consumer SHOULD import the new work manifest as an immutable **update record**, then project it onto existing `ziprunner.project-state.json` passes/roadmap with stable IDs. It MUST preserve prior pass history, operator-owned status overrides, approvals, negative test results and evidence. It MUST NOT treat a repeated imported ZIP as a new pass or overwrite newer verified records with older model claims.

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

## 7. Package kinds

- `source_update`: source changes plus metadata. The consumer may follow its existing stop, backup, overlay, build, post-update check and optionally start sequence, under project policy and operator gates.
- `progress_update`: **proposed future consumer support**. Metadata-only package with no source overlay/build/start or privileged actions. The consumer validates identity/provenance and imports planning updates only after explicit project matching and review. Current 1.2.304.49 MUST NOT be assumed to support it.

Both formats MUST preserve local configuration and protected state. A progress-only import can carry only the work manifest, an optional project-state proposal and handover/docs; it MUST NOT contain shell commands, executables, project recipe changes, or release operations.

## 8. Test and evidence rules

Verification layers are deliberately separate:

1. **Static/schema checks:** well-formed JSON, package safety, identity, cross-reference and file hashes.
2. **Author checks:** tests the producer actually ran; record command, result and environment. Where tests could not run, record `not_run` and reason.
3. **ZipRunner build checks:** commands specified by the trusted project configuration or reviewed recipe; log exit code/output in durable consumer state.
4. **ZipRunner post-update checks:** non-gating follow-up tests, not proof of prior build success or live health.
5. **Runtime/operator acceptance:** smoke, GUI, external-device/application and approval checks performed in the correct environment.

Evidence references MUST refer to real package-relative files or complete HTTPS URLs. Do not forge test logs or treat self-asserted evidence as independent proof. A producer MUST distinguish source-only checks from target environment or live application tests.

## 9. Command/release safety

Untrusted metadata MUST NOT expand the trusted command set; `operator_actions` are informational. The established recipe/config system is the only command authority, subject to operator review and local policies. Push, commit, tag, GitHub release, publication, deployment, deleting user data and privileged recovery MUST remain explicitly gated, independently of manifest settings. Unknown/conflicting project matches require operator resolution.

Protected local files (including the active ZipRunner `ziprunner.config.json`, per-project secrets and protected state) MUST never be overwritten, even if an archive accidentally contains them. ZipRunner self-updates MAY include only `ziprunner.config.sample.json` as the configuration template and MUST NOT include an active `ziprunner.config.json`.

## 10. AI-model interoperability and publication

When asked to “follow the ZipRunner specification,” a model can fetch the public pinned specification and generate conforming files without having ZipRunner installed. It MUST still obtain the actual project source from a provided ZIP/repository before claiming implementation, and MUST NOT infer local app behavior from this specification alone. The resulting ZIP is **producer-conformant**, not automatically **consumer-verified**.

Reference prompt and handover contract: [MODEL_HANDOFF.md](docs/MODEL_HANDOFF.md). Integration milestones: [ADOPTION.md](docs/ADOPTION.md).
