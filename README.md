# ziprunner-spec

Describe the product goal, users, data boundaries, and first useful build target.

## Documentation
- `AGENTS.md` — agent entry point and required reading order.
- `INSTRUCT.md` — product intent and working context.
- `DESIGN.adoc` — architecture, data boundaries, and update flow.
- `PROJECT_PLAN.adoc` — milestones, decisions, risks, and roadmap context.
- `ENGINEERING_STANDARD.adoc` — size, design, dependency, and regression rules.
- `CODING.md` — coding defaults for developers and agents.
- `TESTING.md` — focused, full-suite, and package validation.
- `ziprunner.quality.json` — machine-readable thresholds and ratchet policy.
- `project.zr` — safe overlay, build, start, and source-publish recipe.

## Local build
Document the exact commands here after the project is configured.

## Release
Publish source only after local build/test succeeds. Prefer CI-built containers/software.
