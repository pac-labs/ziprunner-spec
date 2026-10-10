# Source audit and provenance

Inspected on **2026-10-10**. The source packages were read locally as ZIP archives; they have **not** been published to this repository, and public documentation does not copy private configuration or application code.

## Primary baseline

- File: `ziprunner-1.2.304.49-open-chat-project-correlation.zip`
- ZIP SHA-256: `14afcbe00a963f25c34f9b697c4b4c925634c6bef11c8b833844e229642205c0`
- 1,330 ZIP members, about 13.1 MB uncompressed.
- Relevant source: `ZR_SPEC.md`, `DESIGN.adoc`, `ENGINEERING_STANDARD.adoc`, `AGENTS.md`, `project.zr`, `ziprunner.example.zr`, `ziprunner_app/package_manifest.py`, `ziprunner_app/zip_intake.py`, `ziprunner_app/zip_processing.py`, `ziprunner_app/project_pass_state.py`, `ziprunner_app/project_progress.py`, `ziprunner_app/post_update_tests.py`, `ziprunner_app/gui_project_overview.py`, `ziprunner_app/chat_project_correlation.py`.

Observed actual formats:

- Root `project.zr` uses `ziprunner.zr/v1` with `project_key: ziprunner`; it protects active `ziprunner.config.json` and runtime paths.
- `.ziprunner-package-manifest.json` uses `ziprunner.source-package-manifest.v1`, declares `package_kind: complete_source`, `file_count: 1329` and hashes for packaged source files.
- `.ziprunner-post-update-tests.json` uses `ziprunner.post-update-tests.v1`; the post-update test implementation states these checks do not gate overlay/build/completion/restart/start.
- `ziprunner_app/project_pass_state.py` defines `CANONICAL_MANIFEST_NAME = "ziprunner.project-state.json"` and roadmap status values `suggested`, `planned`, `in_progress`, `review`, `done`, `deferred`, `removed`, `blocked`.
- `ziprunner_app/zip_intake.py` detects matching conflicts and validates ZIP entry destinations; v1 proposes **stronger cross-platform path normalization** beyond this baseline.
- The 1.2.304.49 design documents describe exact chat ID correlation and careful ownership of model conversations; a manifest must not use the active tab as project identification.

## Cross-check: recent managed project ZIP

- File: `bozjafrontline-0.1.0.3-ziprunner.zip` (25 files).
- Contains `project.zr`, `.ziprunner-post-update-tests.json`, `ziprunner.project-state.json`, `ZIPRUNNER_HANDOFF.md`, `AGENTS.md`, project source and tests.
- The project-state file declares `schema: ziprunner.project-state/v1`, while the Python normalizer defaults to `ziprunner.project-state.v1`. This specification explicitly acknowledges the legacy spelling difference.
- Bozja `project.zr` defines tests-before-build in its `build` commands. Its separate post-update file contains `gating: true`, whereas the current ZipRunner post-update runner is documented as non-gating. New consumers must not silently reinterpret that discrepancy.
- The handover distinguishes static/package checks from required Windows .NET/Dalamud compilation and live validation. That motivates mandatory evidence types and `not_run` checks in the new work manifest.

## Not established by the audit

- No proof that `ziprunner-manifest.json` is currently consumed by the app (it is new).
- No proof of general metadata-only ZIP installation support (it is new).
- No live end-to-end test of ZipRunner's GUI or behavior on the user's machine was performed.
- Nothing in this source audit establishes that any specific model can reach a private GitHub repository without access.

All proposed additions are called out as such in this repository.
