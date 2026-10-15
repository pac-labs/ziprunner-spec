# Guide for package producers

ZipRunner source packages can originate from manual development, CI pipelines, automated coding tools, or other build systems. All producers use the same published file formats and are evaluated under the same validation rules.

## Package identity

The recipient project is identified by its configured project key. Filename conventions are useful for discovery, but a filename alone does not authorize installing an update into a project. Project/version metadata must be consistent across the archive, project recipe, and workboard record.

## Workboard declaration

Every source ZIP includes the mandatory `.ziprunner-workboard-update.json`. Its `implemented` list describes delivered functionality and meaningful operator checks; its `remaining` list accounts for unfinished work. Task IDs refer to durable work items, not to individual package attempts. Reusing an existing ID allows subsequent updates and verification events to affect the same task rather than accumulating duplicates.

A successful author-side test and an accepted task are different events. The source package declares implementation evidence, but it cannot approve its own verification or release. Consumer-generated state records builds, independent checks, and authorized acceptance separately.

## Supplemental interchange information

For full v2 interchange conformance, `ziprunner-manifest.json` describes the update's plan, implementation claims, outstanding work, test results, source provenance, and handover information. Its schema is distinct from the required workboard document. Existing `.zr` recipes, project-state data, package integrity manifests, and post-update test plans keep their original meanings.

## Test reporting

| Result | Interpretation |
| --- | --- |
| `passed` | The named check was actually executed and succeeded |
| `failed` | Execution finished unsuccessfully |
| `not_run` | The check was not executed; no success is implied |
| `blocked` | A recorded prerequisite prevented execution |

Test records should identify the environment and command when those details are relevant to reproducibility. A static package check does not establish application startup or live API/database correctness.

## Package handover

A completed ZIP delivery MUST include a **clickable direct download link** to the actual ZIP in its delivery message, plus the exact ZIP filename, project key, version and SHA-256. The link must be available to the intended recipient, not guessed or inferred from a local file path. If a downloadable artifact is not actually accessible, the producer MUST explicitly mark the delivery **incomplete**, rather than suggesting a nonworking link is available.

A `ZIPRUNNER_HANDOFF.md` document inside the ZIP can summarize the version, work-item IDs, completed checks, limitations, and outstanding acceptance steps. Integrations that consume a `ZIPRUNNER_HANDOFF v1` response block retain that existing convention and provide its download link in the **external handoff**; packaging a link to the ZIP inside itself is not required. Human-readable material is supplementary to machine-readable manifests and consumer-owned records. See the [delivery contract](DELIVERY.md) and the [example handoff](../examples/DELIVERY_HANDOFF.md).

## Optional API and database specifications

Packages serving APIs through Looprd may include the authoritative `looprd.yaml` plus an optional `ziprunner.looprd.json` mapping. The latter carries only project/component identity and file integrity; it does not include credentials, database content, or activation privileges. See [Looprd interoperability](LOOPRD.md).

## Validation interfaces

The bundled [validator](../tools/validate.py) provides the `workboard`, `manifest`, `package`, and `looprd` checks demonstrated in the root README. The independent workboard lifecycle [reference implementation](../tools/workboard_lifecycle.py) and [tests](../tests/) illustrate expected reconciliation behavior. No local ZipRunner process is required to use these tools.

## Feature-level verification evidence (v2.3)

For full v2.3 producer conformance, include `ziprunner-verification-plan.json` alongside mandatory v1 Work board metadata. Declare criteria for each delivered task, link to explicit check IDs, and state assertions for automated checks and instructions for manual checks. Preserve original board IDs and acceptance criteria; unknown historical acceptance scope must remain for operator review. Include the actual automated test source files, linked by safe `test_ref` paths; an assertion string alone does not prove the function is implemented. Refer to trusted runner **identifiers**, never insert privileged shell commands or secrets. The test runner and outcome report are owned by the consumer, not the source ZIP. See [functional verification](FUNCTIONAL_VERIFICATION.md).
