# Conformance and interoperability

Conformance is evaluated at the interface between an artifact producer and a consumer. Consumer support can differ by application version; unsupported optional extensions do not become active simply because a ZIP includes metadata for them.

## Conformance levels

| Level | Criteria |
| --- | --- |
| Source ZIP format | Safe portable archive, consistent project identity, required root-level workboard document, valid work items and operator checks |
| Full v2 producer interchange | Source ZIP format plus supplemental `ziprunner-manifest.json`, work classification, validation provenance, and handover fields |
| Workboard lifecycle consumer | Stable-ID merge, build-gated evidence import, verified/approved closure to Done, replay deduplication, durable audit history |
| Release readiness consumer | Prevents finalizing delivered scope with unresolved or unverified associated tasks; approval for push/tag/publish remains independent |
| Looprd link extension | Optional `ziprunner.looprd.json` is structurally valid and matches packaged Looprd YAML identity and SHA-256; DAPI semantic validation is separate |

## Consumer behavior

1. **Safe intake.** Archive paths, project matching and the workboard file are verified before stop, backup or overlay. Invalid source archives are rejected without changing the target.
2. **Trusted execution.** Commands come from approved local policy, never from untrusted handover text or metadata alone.
3. **Build-gated import.** Only a successful build establishes that the current package's implementation evidence can be imported as delivered. Failed builds remain visible and are not presumed rolled back.
4. **Persistent identity.** Each task is matched to its stable existing ID, and repeated artifact hashes do not append duplicates.
5. **Verified closure.** Build success can lead to review; it does not confer Done. Authorized acceptance of all required criteria closes the original task under the same ID.
6. **Release reconciliation.** Completed release scope must be independently verified and closed. Unrelated future backlog need not be completed to release an approved, bounded scope.
7. **Preserved trust boundaries.** Secrets, local configuration, release permissions, and database migrations are protected by their established controls.

## Reporting conformance

A useful conformance report includes specification revision, consumer version, relevant schema identifiers, validation commands and results, known exceptions, and independently executed runtime tests. Producer-reported test results must not be presented as consumer-observed results.

The repository's tests and standard-library validator establish behavior of the bundled reference tooling; they are not a certification of third-party consumers.
