# Instructions for agents using ziprunner-spec

1. Read `SPECIFICATION.md`, then `docs/SAFETY.md`, `docs/PACKAGING.md`, and `docs/WORK_PROGRESS.md`.
2. Do not treat the public protocol repository as the managed project's actual source code.
3. Create/update `ziprunner-manifest.json` for each update, retaining stable work IDs and all planned/done/todo records.
4. Describe author test results separately from ZipRunner-observed build/runtime verification.
5. Keep existing `project.zr`, `.ziprunner-post-update-tests.json`, `ziprunner.project-state.json`, and ZipRunner self-source integrity manifest conventions intact.
6. No active `ziprunner.config.json`, environment secrets, automatically authorized releases or ambiguous target routing.
7. Produce a download link for the package and report executed/skipped tests, unfinished work, next pass, and needed operator actions.
8. When editing this spec itself, increment the spec version and changelog; adjust schema/validator/examples/tests together.
