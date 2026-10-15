# Compatibility and implementation status

This document distinguishes interchange format requirements from support demonstrated by particular consumers. A specification describes interoperable behavior; it does not imply that every existing installation implements every extension.

## Consumer version reference

| Topic | Reference behavior | Interchange specification |
| --- | --- | --- |
| Project recipe `project.zr` | Existing `ziprunner.zr/v1` convention | Preserved |
| Project progress `ziprunner.project-state.json` | Existing project-state convention | Preserved, including historical schema spelling compatibility |
| Post-update tests | Existing `ziprunner.post-update-tests.v1` convention; historically non-gating after availability | Not treated as a substitute for build/release verification |
| Workboard intake | Required workboard gate documented for ZipRunner 1.2.304.55, following a 1.2.304.53+ baseline | Every source ZIP contains `.ziprunner-workboard-update.json` |
| Verified task closure | Not independently established for all installed versions | Existing IDs transition to Done after authorized acceptance; release readiness detects missed closures |
| Supplemental rich work manifest | No ingestion verified for 1.2.304.55 | `ziprunner-manifest.json` required for full v2 interoperability producer conformance |
| Metadata-only progress ZIP | No established general consumer support | Proposed package kind only |
| Optional Looprd link | No automatic deployment or status integration implied | `ziprunner.looprd.json` defined as an optional, producer-side integrity link |

The Workboard v1 schema and example in this repository are the supplied format references. Static validation against them does not establish exact parity with every installed application's parser. Consumer versions and integrations should publish their own conformance results.

## Package schema identifiers

- `ziprunner.workboard-update.v1` — required workboard record for source ZIPs.
- `ziprunner.update-manifest/v1` — supplemental interchange manifest.
- `ziprunner.zr/v1` — project recipe.
- `ziprunner.post-update-tests.v1` — post-update test plan.
- `ziprunner.source-package-manifest.v1` — complete-source file inventory where used.
- `ziprunner.looprd-link/v1` — optional Looprd link.
- `looprd/v1` — upstream DAPI specification, defined by [pac-labs/dapi](https://github.com/pac-labs/dapi), not by ZipRunner.

These identifiers are intentionally different. An implementation must not guess that one schema can replace another.

## Historical compatibility notes

The `ziprunner.project-state.json` format has appeared with both `ziprunner.project-state.v1` and `ziprunner.project-state/v1` spelling. Consumers supporting those legacy packages should document their normalization policy and preserve task history and operator-owned state.

A post-update plan's `gating` field is not proof that a historical runner treated it as a pre-installation gate. Source ZIP workboard intake validation is a separate, earlier requirement.

## Reproducibility

Validation results should identify the consumer version, specification revision, and reference fixtures used. A green schema check, build success, runtime health signal, and operator approval are distinct outcomes.

## Functional verification (specification v2.3)

The v2.3 `ziprunner-verification-plan.json` is a **supplemental full-conformance extension**. It does not supersede the runtime-enforced `.ziprunner-workboard-update.json` v1 gate. Older consumers may ignore or reject unknown metadata and MUST NOT claim they execute the tests or correlate feedback merely because the producer supplied a valid plan. Consumer-owned verification reports and origin-feedback records are generated **after** import and never treated as authority supplied by source ZIPs. The check-to-task mapping and return-to-origin adapters require explicit local implementation.
