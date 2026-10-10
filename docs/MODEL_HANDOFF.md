# Instructions for independent AI models

## Beginning a task

1. Fetch `SPECIFICATION.md` from the pinned public `ziprunner-spec` tag/commit and read the linked work, packaging and safety documents.
2. Inspect the **actual current project source** or verified repository commit and its tests. The public spec is not a substitute for that source.
3. Check prior project state/roadmap and ZIP handover files if available. Preserve stable work IDs, existing features and decisions.
4. Write a bounded plan with acceptance criteria. Record the current date/time (with timezone) and selected source revision/base package where known.
5. Implement the approved, bounded change and add regression tests. Do not broaden scope, erase unrelated code, alter local config or trigger privileged actions.

## Before packaging

- Update version consistently across project metadata, package filename and documents.
- Include `ziprunner-manifest.json` with *all* planned work partitioned into done/todo, with truthful evidence and test outcomes.
- Include the project's existing `project.zr`/`.zr` and state/pass documents as appropriate.
- Keep the current `.ziprunner-post-update-tests.json` separate from the work manifest.
- For ZipRunner self-update, never package `ziprunner.config.json`; retain the sample config, launch scripts, README and self-source integrity manifest as required by the application.
- Validate archive safety and manifest consistency with `tools/validate.py` and any project-specific package validators.
- Report tests that **were not run**, their reason, and exact future validation steps.

## Answer contract

Final response to operator should contain: artifact link and SHA-256 if generated; source version; `planned_work` summary; `done_work` summary; `todo_work` summary; tests run/passed/failed/not-run; broken/changed interfaces; restart or rebuild requirements; next pass and operator actions. Do not claim “fully verified” unless local and environment-specific checks were actually completed. A chat answer is helpful but the durable source of progress is the manifest + consumer journal.

## Operator / manager boundary

Developer models may suggest follow-up work. Manager/QA and operator remain distinct roles. Do not promote a task to verified done, change release approval, publish, push, tag, run arbitrary remote commands or silently replace project association. Handovers may be rewritten by models as proposals, but operator-owned truth is immutable without explicit review.
