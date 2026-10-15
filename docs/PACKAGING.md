# Package format and compatibility

## Established package conventions

ZipRunner 1.2.304.49 matches configured ZIP filename patterns and supports `project.zr` project recipes (`schema: ziprunner.zr/v1`). Current `project.zr` uses keys such as `project_key`, `match`, `command_subdir`, `stop`, `stop_ports`, `build`, `start`, `build_window`, `start_window`, `strip_single_root`, `delete_missing`, `protected_paths`, `post_build_mechanisms` and `git`. See `examples/project.zr` for a minimal *reference example*, not a promise every field can be used without review.

The application also recognizes `.ziprunner-post-update-tests.json` with `schema: ziprunner.post-update-tests.v1`. These are post-availability checks (non-gating in 1.2.304.49), and the internal code has a maximum of 20 tests in one plan. Do not rely on `gating:true` in a consumer's test stamp to block installation. For tests that MUST block a release, use a trusted build/check gate or operator approval.

ZipRunner self-source packages also use `.ziprunner-package-manifest.json` (`ziprunner.source-package-manifest.v1`) with `entries` `{path, sha256, size, mode}`, `file_count`, `project`, `version`, `package_kind`, `required_source_paths`, `retired_source_paths`, and `managed_task_id`. This existing format must remain intact for self-update compatibility. The new `ziprunner-manifest.json` is **separate** and never replaces the per-file inventory.

## v2 interoperable source ZIP

```text
my-project-1.2.3-ziprunner.zip
  project.zr
  .ziprunner-workboard-update.json  # MANDATORY runtime source ZIP gate
  ziprunner-manifest.json            # supplemental full spec conformance
  ziprunner.project-state.json
  .ziprunner-post-update-tests.json  # optional
  ZIPRUNNER_HANDOFF.md                # recommended
  README.md
  docs/...                           # as appropriate
  src/...                            # required for source_update
  tests/...
  evidence/...                       # evidence referenced by manifest
```

A project registration `.zr` file may also be distributed separately from the ZIP, as in the existing import workflow. The package is never allowed to silently install into a different project because its filename resembles another target.

For source updates, new producer metadata is expected in the source tree. The source and ZIP may contain additional project documentation, but not credentials, local config or generated runtime state.

The mandatory `.ziprunner-workboard-update.json` rule applies to **all source update ZIPs**, not to RoboScope text patches, and not to a future recognized `progress_update` package kind. The supplemental `ziprunner-manifest.json` is not an alternative to the mandatory Work board file.

## Proposed metadata-only progress ZIP

```text
my-project-progress-20261010.zip
  ziprunner-manifest.json            # update.kind=progress_update
  ziprunner.project-state.json       # optional proposal, not trusted local state
  ZIPRUNNER_HANDOFF.md               # optional
  docs/...                           # non-executable planning docs
```

The metadata-only format is a **proposed extension**, not an established general consumer intake path. Consumers that do not explicitly support it must reject the package kind. Compatible consumers must avoid source overlay/build/start, validate project identity, and require appropriate review.

## Optional Looprd component source

A source update for a Looprd-enabled project MAY ship its own `looprd.yaml` (under a declared path) with optional root-level `ziprunner.looprd.json` linking the configured ZipRunner project to the Looprd component and expected SHA-256. The actual DAPI YAML remains the data/API model source of truth; the sidecar is a **proposed ZipRunner producer convention**, not a deployed application interface. See [Looprd integration](LOOPRD.md). Do not ship database rows, connection URLs, API keys, admin credentials or node `sources.yaml` containing private deployment values. A ZIP containing Looprd files does not itself request a database migration or deployment. Non-Looprd projects do not need the sidecar.

## Artifact download and handoff

A package's embedded `ZIPRUNNER_HANDOFF.md` is optional supporting documentation. The **external delivery handoff** MUST provide a clickable, direct link to the exact packaged ZIP, its SHA-256, exact filename, project key and version. The link may only be supplied after it is known to exist, and an unresolvable or missing link makes artifact delivery incomplete even if the ZIP passes local validation. See [downloadable handoff](DELIVERY.md). No self-referential download URL is required inside the ZIP.

## Consistency and installation

1. Wait for a complete download, validate ZIP safety and safe paths, then extract to a bounded temporary staging area.
2. Match the configured project key and inspect **mandatory root-level Work board update** in staging. Missing, malformed, empty or mismatched workboard metadata rejects the source ZIP **before stop, backup or overlay**.
3. Validate remaining archive integrity, project-specific packaging, and supplementary manifests without allowing inferred or conflicting targets.
4. Preserve protected config, runtime state and local overrides. Back up the project only after mandatory workboard validation succeeds.
5. Apply source update under the existing transactional/update policy; run trusted stop/build/start commands as configured. Provide copyable live logs.
6. Record checks, evidence and per-update results in independent durable state.
7. After a successful build import the workboard evidence without marking Done; failed builds MUST NOT be imported as delivered (nor assumed rolled back). Deduplicate by ZIP hash. Keep release steps gated and individually visible to the operator.

Packages MUST NOT include a project's active `ziprunner.config.json`. ZipRunner self-source MUST contain only `ziprunner.config.sample.json` for configuration; a later malicious or mistaken ZIP must not overwrite the installed active config.

## Task closure after a release

Source ZIP authors MUST reuse existing Work board IDs for delivered functionality and supply the required `operator_checks`; the v1 file contains no authority to mark Done. The consuming ZipRunner implementation MUST associate imported implementation evidence with the existing task ID, request manager/QA and operator verification, and **move the same task to Done** after approved acceptance. A release readiness check fails for delivered scope not independently verified and closed. See [Work board lifecycle](WORKBOARD_UPDATE.md).

## Functional-verification v2.3 extension

A source ZIP claiming full v2.3 functional-verification conformance also carries `ziprunner-verification-plan.json` at the effective source root. This additional declarative file is schema-checked and cross-referenced against `implemented[]`. It does not remove the mandatory `.ziprunner-workboard-update.json` file, replace established runner configurations, or authorize command execution. The `ziprunner.verification-report/v1` and `ziprunner.origin-feedback/v1` records are generated and stored by the consumer **outside the downloaded ZIP**. The original conversation/window correlation is trusted intake state and not a producer-supplied target.
