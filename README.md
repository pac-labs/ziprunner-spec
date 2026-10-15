# ZipRunner Interchange Specification

**Specification version: 2.3.0** · **Status: published-format specification with clearly identified extensions**

ZipRunner Interchange is an open, versioned format for distributing software source updates with consistent project identity, work tracking, verification evidence, and release controls. The standard is useful to individual developers, open-source maintainers, development teams, build systems, and automated tooling. Packages can be authored and validated without access to the ZipRunner application's source code.

The protocol distinguishes between **what a package author reports**, **what a build or runtime has demonstrated**, and **what a reviewer has accepted**. These are deliberately separate forms of evidence.

## At a glance

| Capability | Purpose | Status |
| --- | --- | --- |
| Source ZIP workboard (`.ziprunner-workboard-update.json`) | Names delivered work, remaining work, and human verification steps | Mandatory source-package format for the documented 1.2.304.55 gate |
| Workboard reconciliation | Tracks existing tasks by stable ID; moves verified and approved work to Done | Normative consumer conformance requirement; implementation support varies |
| Interchange manifest (`ziprunner-manifest.json`) | Richer planned/completed/remaining work and validation provenance | Supplemental v2 interchange contract; not part of the established 1.2.304.55 intake gate |
| Functional verification plan (`ziprunner-verification-plan.json`) | Links delivered tasks and original acceptance criteria to trusted feature tests and manual checks | New full v2.3 producer extension; not assumed to be an older consumer's runtime gate |
| Observed verification report (`ziprunner.verification-report/v1`) | Records exact artifact, runner, test outcomes and evidence without treating source claims as proof | New v2.3 consumer interoperability requirement |
| Return-to-origin feedback (`ziprunner.origin-feedback/v1`) | Queues results for the verified originating conversation with acknowledgment and retry semantics | New optional channel adapter; cannot send without consumer implementation and authorization |
| Protected packaging | Rejects unsafe archives and protects local configuration and secrets | Core safety contract |
| Looprd / DAPI link (`ziprunner.looprd.json`) | Optionally associates a project with an API/database specification | Optional interoperability extension, not a deployment instruction |
| Metadata-only progress package | Transfers planning information without a source overlay | Proposed package kind; consumer support must be established independently |

## Documentation

- [Specification](SPECIFICATION.md) — normative requirements and terminology.
- [Package format](docs/PACKAGING.md) — source package layout and compatibility.
- [Workboard update](docs/WORKBOARD_UPDATE.md) — required JSON structure, task identity, and import rules.
- [Progress and verification](docs/WORK_PROGRESS.md) — lifecycle semantics and reporting.
- [Functional verification](docs/FUNCTIONAL_VERIFICATION.md) — acceptance-criterion coverage, runner safety, and observed results.
- [Origin feedback](docs/ORIGIN_FEEDBACK.md) — correlation, acknowledgment, retries and copyable fallback.
- [Safety](docs/SAFETY.md) — archive validation, identity, configuration protection, and approvals.
- [Looprd integration](docs/LOOPRD.md) — optional API and data-model interoperability.
- [Producer guide](docs/PRODUCERS.md) — public guidance for people and tools generating packages.
- [Downloadable handoff](docs/DELIVERY.md) — required direct artifact download link, identity and checksum in the delivery message.
- [Conformance](docs/CONFORMANCE.md) — validation levels and interoperable consumer behavior.
- [Compatibility](docs/COMPATIBILITY.md) — supported conventions and implementation caveats.
- [Changelog](CHANGELOG.md) — specification revisions.

## Package delivery

A finished ZIP requires a **downloadable handoff**, not just a filename: the delivery message MUST include a clickable link to the exact delivered ZIP, its exact filename, project key, version and SHA-256 checksum. The link is created or verified **after** the ZIP is built and published; it does not have to appear inside the ZIP itself. The existing `ZIPRUNNER_HANDOFF v1` project/version/filename convention is preserved. See [downloadable handoff](docs/DELIVERY.md) and the [example](examples/DELIVERY_HANDOFF.md).

## Example source ZIP

```text
example-project-1.2.3-ziprunner.zip
├── project.zr
├── .ziprunner-workboard-update.json      # required for source update ZIPs
├── ziprunner-manifest.json               # supplemental interchange contract
├── ziprunner-verification-plan.json      # full v2.3 functional-verification extension
├── ziprunner.project-state.json          # optional compatible progress bridge
├── ZIPRUNNER_HANDOFF.md                  # human-readable release information
├── README.md
├── src/
└── tests/
```

For projects using [Looprd](https://github.com/pac-labs/dapi), the ZIP may also contain a `looprd.yaml` and an optional `ziprunner.looprd.json` identity-and-hash link. Other projects do not need Looprd.

## Validation

The repository includes a Python 3.10+ standalone validator and regression tests. The validator uses the standard library and does not execute packaged code.

```sh
python tools/validate.py workboard examples/ziprunner-workboard-update.example.json --expected-project example-project
python tools/validate.py verification-plan examples/verification-plan.json --workboard examples/ziprunner-workboard-update.example.json --root examples --expected-project example-project
python tools/validate.py manifest examples/ziprunner-manifest.json --root examples
python tools/validate.py package path/to/example-project-1.2.3-ziprunner.zip --expected-project example-project --require-verification-plan
python tools/validate.py looprd examples/ziprunner.looprd.json --root examples --expected-project example-project
python -m unittest discover -s tests -v
```

The JSON Schema documents use Draft 2020-12. The bundled standalone validator enforces the supported interoperability rules, not every feature of a general JSON Schema engine. Passing static checks does not establish build success, operator acceptance, or deployment health.

## Versioning and compatibility

The **specification version** (`2.3.0`) and the **embedded manifest schema versions** are separate. Version 2.3 adds optional-in-legacy, required-for-full-v2.3 functional-verification metadata, an independent observed-result contract, and correlation/acknowledgement requirements for consumers advertising origin-feedback support. The prior source ZIP Work board v1 format and its acceptance gates remain unchanged. A consumer must implement these extensions before advertising them as supported.

For reproducible builds, a project may pin the specification to a published tag or commit. Detailed compatibility notes distinguish observed consumer behavior from additional normative requirements and optional proposals.

## Repository

[github.com/pac-labs/ziprunner-spec](https://github.com/pac-labs/ziprunner-spec)

This repository defines an interoperability format. It is not the ZipRunner application, the Looprd runtime, a credentials store, or a deployment service. License terms depend on the license published in the repository.
