# Changelog

Version numbers describe the ZipRunner Interchange specification, not the installed ZipRunner application or the separate Looprd runtime.

## 2.1.1 — 2026-10-14

**Documentation-only revision; no schema, validator, or normative package-format changes.**

- Reorganized documentation for an international public audience of developers, project maintainers, integrators, and tooling authors.
- Replaced internal development plans and agent-specific prompts with public producer, conformance, and compatibility guides.
- Clarified which behaviors are existing conventions, required by the specification, or optional extensions.
- Preserved mandatory Workboard v1 intake, stable-ID verified closure, independent release approvals, and optional Looprd/DAPI integration.

## 2.1.0 — 2026-10-14

- Introduced optional Looprd/DAPI data-model interoperability through a project/component identity and SHA-256 link.
- Kept the upstream `looprd/v1` specification authoritative for database models, APIs, authentication and migrations.
- Specified distinct verification for build, source validation, component activation, live API behavior, and acceptance.

## 2.0.0 — 2026-10-14

- Introduced a mandatory `.ziprunner-workboard-update.json` for all managed source ZIPs.
- Added stable task IDs, `implemented` and `remaining` work classification, operator verification checks, and validation before modifying the target.
- Defined build-gated evidence import, verified closure of existing tasks to Done, release reconciliation, and duplicate-import prevention.
- Preserved separate RoboScope patch/diff rules and local configuration protections.

## 1.0.0 — 2026-10-10

- Established the original standalone interchange specification for source updates, project identity, planning and evidence.
- Documented existing project recipes, project-state files, post-update tests, and package integrity manifests as distinct formats.
- Added independent schema validation, examples, and regression tests.
