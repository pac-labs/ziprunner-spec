# Adoption plan for ZipRunner application

This repository publishes a proposed standard; it does not patch ZipRunner itself.

## Pass A — contract publication (delivered here)

- Publish versioned specification, examples, JSON schemas and standalone validator.
- Validate producer ZIPs independently of ZipRunner source.
- Continue using current `.zr`, `project.zr`, `.ziprunner-post-update-tests.json`, source integrity manifest and project state.

## Pass B — importer, no GUI regression

- Add a parser for `ziprunner-manifest.json` to ZipRunner's ZIP intake. Retain old formats for backward compatibility.
- Reject invalid cross-references/identities and unsafe evidence paths with a reviewable error; never silently reclassify a target.
- Write an immutable, content-addressed update record and project-scoped journal outside the target source tree. Make importing the same ZIP idempotent.
- Reconcile author manifest planned/done/todo onto existing project progress without discarding local status overrides, historical passes or failure evidence.
- Add end-to-end regression fixtures for old packages, both project-state schema spellings and source-only + complete-source updates.

## Pass C — operator Overview

- Show planned/reported done/remaining, independently verified count, deferred and blocked work, latest update, author evidence and observed tests.
- Keep build/runtime/release separate and visibly time-stamped. Highlight unknown and incomplete checks.
- Add next-pass generation and a compare view showing delta between model claims and actual tests. Retain existing All Projects startup, right-panel navigation, activity and live logs.

## Pass D — metadata-only update mode

- Introduce `progress_update` as a distinct parsed package kind; never overlay source/run commands for it.
- Review pending changes to plan, evidence and blocked work; apply metadata atomically only after target matching and operator confirmation.
- Include task-level change history, stale-version handling and warnings about conflicting model/consumer state.

## Pass E — spec pinning and release gates

- Configure per-project accepted specification version/URL or SHA, with an offline/cache mode and clear trust boundaries.
- Bind generated model request files to a pinned revision and current project identity.
- Integrate package-schema validation into GitHub CI; keep GitHub push, tagging, release and publication independently gated.
- Add upgrade/rollback migration tests; do not overwrite active local config.

## Acceptance criteria for application implementation

A v1-capable ZipRunner must pass: (1) correct-project and ambiguous-project fixtures, (2) Windows path traversal/symlink/collision tests, (3) missing or dishonest work evidence handling, (4) idempotent import/restart recovery, (5) local override preservation, (6) 1.2.304.49 regression suite compatibility, (7) no accidental command execution from progress-only archives, (8) no auto-authorized release, and (9) a visible Overview that distinguishes model reports from verified status.
