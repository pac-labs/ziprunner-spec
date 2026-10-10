# ZipRunner Specification

**Version:** 1.0.0 (proposal, 2026-10-10)  
**Status:** Publication-ready specification; ZipRunner application integration still required.  
**Source baseline:** ZipRunner **1.2.304.49**, cross-checked against a **Bozja Frontline 0.1.0.3** managed update (see [source audit](docs/SOURCE_AUDIT.md)).

This is the standalone, publicly publishable **ZipRunner-compatible source update and development handover protocol**. AI models and build tools can follow it **without having the ZipRunner application source code**. It standardizes package identity, plans, work completed, work remaining, validation evidence, safe application boundaries, and operator handover.

> **Important:** `ziprunner-manifest.json` and metadata-only `progress_update` packages are **proposed for ZipRunner vNext**. ZipRunner 1.2.304.49 does *not* yet consume this new manifest. The existing `.zr`/`project.zr`, `ziprunner.project-state.json`, `.ziprunner-post-update-tests.json`, and (ZipRunner self-source only) `.ziprunner-package-manifest.json` already exist. Publishing the standard alone does not retrofit the installed application.

## Start here

1. [Normative specification](SPECIFICATION.md) — versioned requirements.
2. [Work and progress lifecycle](docs/WORK_PROGRESS.md) — planned/done/todo and truthfulness rules.
3. [Package layouts](docs/PACKAGING.md) — source vs progress-only ZIPs; compatibility.
4. [Security and gating](docs/SAFETY.md) — safe matching, protected paths, approvals.
5. [Independent AI-model instructions](docs/MODEL_HANDOFF.md) — what to read, produce, and report.
6. [Adoption roadmap](docs/ADOPTION.md) — staged implementation in ZipRunner.
7. [Source audit](docs/SOURCE_AUDIT.md) — exact evidence from the archived program.

## Structure

```text
SPECIFICATION.md
AGENTS.md
CHANGELOG.md
schemas/ziprunner-manifest.schema.json
schemas/project-state.schema.json
schemas/post-update-tests.schema.json
schemas/source-package-manifest.schema.json
examples/
tools/validate.py
tests/
.github/workflows/validate-spec.yml
docs/
```

## Use by any model

Copy this instruction to a fresh development conversation:

> Follow the ZipRunner Specification v1.0.0 at `<your published GitHub URL to SPECIFICATION.md>`. Read its referenced packaging, safety and model-handover documents. For my project, produce a full source ZIP containing `ziprunner-manifest.json` with planned_work, done_work, todo_work and evidence, alongside the existing `project.zr` and `ziprunner.project-state.json` contracts. Do not claim local or Windows tests were run if they were not. Do not authorize any release action. Return the ZIP and a concise work summary.

**Use a pinned tag or commit URL** in automation; mutable `main` is convenient for discovery but should not silently change the contract during a development pass.

## Validate

Python 3.10+; no nonstandard dependencies for the repository's validator:

```sh
python tools/validate.py manifest examples/ziprunner-manifest.json --root examples
python tools/validate.py package path/to/update.zip --expected-project my-project
python -m unittest discover -s tests -v
```

The included JSON Schema files follow Draft 2020-12 for tooling that supports full schema validation. The standard-library validator implements the required v1 consistency/safety checks, but does not purport to be a general JSON Schema engine.

## Publish to GitHub

Create an empty repository named `ziprunner-spec`, unpack this ZIP into the repository root, and commit its contents. Publish a stable tag `v1.0.0` after review. Before making a public repository, choose a license appropriate to your intended reuse; none has been assumed on your behalf. No active ZipRunner configuration or environment-specific credentials are bundled here.

## Contract status legend

- **Observed in 1.2.304.49:** identified by inspection of the packaged source and/or a real managed package.
- **Normative v1 proposal:** required of producers claiming conformance to **this** specification; may require ZipRunner changes before consumption.
- **Application implementation:** work for a later ZipRunner update, not included in this specification repository.
