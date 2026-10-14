# Looprd / DAPI integration — optional API and data-model companion

**Status:** Optional integration convention in ZipRunner Interchange v2.1.x. It does not establish automatic deployment or runtime monitoring support in existing consumers. Looprd is specified and run by [`pac-labs/dapi`](https://github.com/pac-labs/dapi). Its **own** `looprd.yaml` and `looprd/v1` format remain authoritative for its API, data model, authentication, and database lifecycle. This document does not fork or replace the DAPI specification.

**Inspected upstream baseline:** [`pac-labs/dapi` commit `e4d4b1b73746bf7f8843667ccad93c51091b2595`](https://github.com/pac-labs/dapi/commit/e4d4b1b73746bf7f8843667ccad93c51091b2595), 2026-10-12. Confirm against a pinned version when delivering a particular project.

## What belongs where

| Authority | Owns | Does not own |
| --- | --- | --- |
| ZipRunner project recipe/Work board | Project key, ZIP identity, implementation evidence, stable work-item IDs, local build/check execution, QA/operator gates | Runtime database schema or component API permissions |
| Looprd `looprd.yaml` (DAPI) | `apiVersion: looprd/v1`, stable component ID, `release`, model fields, CRUD resources, WebSocket events, auth/scopes, `database.schemaVersion`, ordered additive migrations | ZipRunner build or Work board approval |
| Looprd source index (`sources.yaml`) | Which component specification/repository/ref is loaded and enabled | ZipRunner project-to-ZIP matching |
| Looprd runtime | Active generation, API routes, retained database, database-backed API keys, migrations, availability and management endpoints | Source ZIP installation or Git/release approval |

Looprd's `component` ID (`[a-z][a-z0-9-]{0,47}`) determines the API namespace and durable database identity. It is **not inherently identical** to the ZipRunner `project_key`. Identity mapping MUST be explicit and MUST NOT be inferred from ZIP filenames or API URLs. Multiple projects MUST NOT silently claim one component.

## Opt-in linking convention

A managed project using Looprd SHOULD include its authoritative `looprd.yaml` in source control. For interoperability it MAY include one `ziprunner.looprd.json` alongside other project package metadata, with schema `ziprunner.looprd-link/v1`:

```json
{
  "schema": "ziprunner.looprd-link/v1",
  "project": "example-project",
  "component": "example-project",
  "specification": "looprd.yaml",
  "specification_sha256": "<SHA-256 of actual looprd.yaml>"
}
```

The **actual hash** (not the placeholder shown above) is mandatory when the optional link is used. See [schema](../schemas/ziprunner-looprd-link.schema.json), [example link](../examples/ziprunner.looprd.json), and [example DAPI specification](../examples/looprd.yaml). The link contains **only identity and integrity information**; it does not restate models, migrations, secret references, environments, API credentials, or routing. The link is an optional interchange convention. It is not part of DAPI's `looprd/v1` schema and does not itself activate a component or deploy a service.

- The linked YAML MUST be a regular packaged file referenced by a safe relative POSIX path within the effective source root, with the declared SHA-256 matching its bytes. A link to an absolute path, external URL, symlink, or missing file is invalid.
- The linked Looprd document MUST identify the declared `component`, and use `apiVersion: looprd/v1`. Validation of the full YAML, including duplicate keys, model references, auth and SQL migrations, belongs to `python -m looprd validate ...` in an environment with the matching pinned Looprd version.
- The existing mandatory `.ziprunner-workboard-update.json` and supplemental project progress documents remain unchanged. An optional Looprd link does **not** bypass the Work board gate or grant extra release permissions.
- Archive-level structural integrity can be checked with `python tools/validate.py looprd examples/ziprunner.looprd.json --root examples --expected-project example-project`. The standalone ZipRunner validator does **not** claim to validate all Looprd YAML semantics.

## Project changes that MUST appear on the Work board

When source updates modify a Looprd component's API, data model, permissions, event shapes, or migrations, the release Work board MUST identify the existing affected task IDs (or create a genuinely new scoped task) and provide meaningful operator checks. A successful build is producer evidence, not proof of the live component's activation. API/database changes remain pending operator verification until the actual target runtime is checked.

The producer SHOULD report, for each Looprd change: prior and proposed `release`, prior and proposed `database.schemaVersion` when a database exists, changed resource/handler/event paths and operation scopes, migration version(s) and compatibility limits, and checks performed/not performed. Values MUST be derived from the actual specifications and execution, not invented from the link.

## Verification and safety boundaries

1. Validate the source ZIP and Work board, then the optional link and its hash; reject inconsistent identities before any trusted stop/backup/overlay. This is the expected behavior of a consumer implementing the optional Looprd link extension, not evidence that all consumers already support it.
2. Run `python -m looprd validate path/to/looprd.yaml` (using the pinned DAPI toolchain). Run project-specific API/schema tests against disposable test databases. Never run migrations on a production database as part of static validation.
3. Assess additive migration sequencing, old-generation compatibility and rollback limitations before a release. Looprd restricts automatic migrations to additive `ALTER TABLE ... ADD COLUMN`, `CREATE TABLE` and `CREATE [UNIQUE] INDEX`; schema downgrades and destructive changes are not automated. A committed database migration is **not** undone by rolling back the application generation.
4. Keep all Looprd `secretRef`, PostgreSQL `connectionSecret`, component key material and node-specific configuration **out of** source ZIPs. Only safe *references* are allowed. Scoped database-auth keys are separate from the management key and GitHub source token. Never store actual keys in the linking sidecar, release manifest, Work board or project source.
5. Distinguish **ZipRunner built**, **Looprd source validated**, **Looprd component reloaded**, **live API verified**, and **operator accepted**. Never conflate process liveness (`/_looprd/health`) with a healthy application endpoint or database. Looprd's `/_looprd/status` and reconciliation controls require a management credential; access to them is not granted by the link.
6. Changes to `sources.yaml`, activation/disable/removal, deploy, or manual reconciliation are separate explicit operator actions. A missing/invalid source due to outage must not be interpreted as permission to remove a component. Looprd's **valid authoritative source index** controls removal while retaining data; source failures preserve the last working generation.
7. Before finalizing Work board tasks, operator checks SHOULD verify the live component identity, active release/revision, scoped API operations, expected database schema and migration outcome, and event behavior as applicable. Only after actual QA and operator approval does ZipRunner move that original ID to Done. Git push/tag/release, data migration, and deployment actions stay separately gated.

## Optional consumer capabilities

A Looprd-aware consumer may present component identity, API resources, declared models, schema version, and the differences between successive specifications. Such information is descriptive and does not by itself establish runtime health.

Live status inspection requires an explicitly configured endpoint, a suitable access policy, and appropriate credentials. The DAPI management API is sensitive; its management key MUST NOT be reused as a general read-only component key. Registration, source reconciliation, database migration, and deployment remain separately authorized operations.

Where the consumer correlates Looprd changes with Work board tasks, the same stable task IDs and artifact SHA-256 govern the evidence, verification, and closure history. Non-Looprd projects remain unaffected.

## Reference validation commands

For an API-bearing package, in addition to ordinary ZipRunner Work board and build checks:

```sh
python tools/validate.py looprd examples/ziprunner.looprd.json --root examples --expected-project example-project
# Requires a separately installed compatible DAPI CLI:
python -m looprd validate path/to/looprd.yaml
```

This document intentionally adds **no dependency on Looprd runtime, database connectivity, or credentials to ordinary non-Looprd ZIP validation**.
