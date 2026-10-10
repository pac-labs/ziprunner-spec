# Package format and compatibility

## Existing source packages

ZipRunner 1.2.304.49 matches configured ZIP filename patterns and supports `project.zr` project recipes (`schema: ziprunner.zr/v1`). Current `project.zr` uses keys such as `project_key`, `match`, `command_subdir`, `stop`, `stop_ports`, `build`, `start`, `build_window`, `start_window`, `strip_single_root`, `delete_missing`, `protected_paths`, `post_build_mechanisms` and `git`. See `examples/project.zr` for a minimal *reference example*, not a promise every field can be used without review.

The application also recognizes `.ziprunner-post-update-tests.json` with `schema: ziprunner.post-update-tests.v1`. These are post-availability checks (non-gating in 1.2.304.49), and the internal code has a maximum of 20 tests in one plan. Do not rely on `gating:true` in a consumer's test stamp to block installation. For tests that MUST block a release, use a trusted build/check gate or operator approval.

ZipRunner self-source packages also use `.ziprunner-package-manifest.json` (`ziprunner.source-package-manifest.v1`) with `entries` `{path, sha256, size, mode}`, `file_count`, `project`, `version`, `package_kind`, `required_source_paths`, `retired_source_paths`, and `managed_task_id`. This existing format must remain intact for self-update compatibility. The new `ziprunner-manifest.json` is **separate** and never replaces the per-file inventory.

## Proposed v1 producer ZIP

```text
my-project-1.2.3-ziprunner.zip
  project.zr
  ziprunner-manifest.json
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

## Proposed metadata-only progress ZIP

```text
my-project-progress-20261010.zip
  ziprunner-manifest.json            # update.kind=progress_update
  ziprunner.project-state.json       # optional proposal, not trusted local state
  ZIPRUNNER_HANDOFF.md               # optional
  docs/...                           # non-executable planning docs
```

As of 1.2.304.49 this is **not an implemented ZipRunner import path**. Implement separately; do not drop such packages into a production inbox expecting automatic metadata-only handling. A compatible consumer must refuse build/start and require a project match and appropriate review.

## Consistency and installation

1. Validate ZIP safety, archive integrity and new work manifest.
2. Identify target by configured explicit matching AND manifest/project identity; conflicts and mismatches are attention states, not silent overrides.
3. Wait for complete download, validate safe paths, stage to temp, then inspect the staged tree.
4. Preserve protected config, runtime state and local overrides. Back up the project before overlay.
5. Apply source update under the existing transactional/update policy; run trusted stop/build/start commands as configured. Provide copyable live logs.
6. Record checks, evidence and per-update results in independent durable state.
7. Keep release steps gated and individually visible to the operator.

Do not embed a project's active `ziprunner.config.json` in any package. ZipRunner self-source MUST contain only `ziprunner.config.sample.json` for configuration; a later malicious or mistaken ZIP must not overwrite the installed active config.
