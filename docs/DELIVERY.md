# Downloadable ZIP delivery and handoff

This document specifies the **external delivery message** that accompanies a finished ZipRunner-compatible ZIP. It is separate from the source ZIP content, internal workboard manifest, CI evidence, and installation permissions.

## Required delivery fields

The human-readable handoff for **every delivered ZIP** MUST identify:

1. **Project:** the actual configured project key.
2. **Version:** the version of the delivered project/package.
3. **ZIP filename:** the exact name of the downloadable `.zip`, including extension.
4. **Download:** a clickable link to the **actual ZIP artifact** that the recipient can retrieve.
5. **SHA-256:** the full hexadecimal SHA-256 digest of the bytes at that link.
6. **Verification context:** reported tests, remaining work and required operator checks, using the existing Work board and `ZIPRUNNER_HANDOFF v1` conventions where applicable.

The filename in the handoff MUST identify the file actually delivered. Its checksum MUST match the distributed bytes and MUST NOT be reused from an earlier package. Do not give an archive directory path, build directory path, repository root or release-information page **as a substitute** for the downloadable ZIP. A source link or release page may be supplied in addition to, not instead of, the direct artifact link.

## Link quality and lifetime

- For lasting public distribution, use a stable HTTPS link to a downloadable asset (for example a versioned release asset).
- For an interactive delivery, a **verified platform-provided file link** may be used even if it is session-scoped. State any known expiration or access restriction. A session link is not a permanent public release URL.
- Check the uploaded/created artifact exists, and verify the exact filename and hash before presenting the link. Where possible, verify that the download resolves and the downloaded content matches the digest.
- Do not invent URLs, fabricate artifacts, or claim a link works when it was not created or checked. A placeholder example URL is documentation only and MUST NOT be used for an actual delivery.
- If a link cannot be provided or verified, state **delivery incomplete** and identify the unavailable artifact; do not claim the ZIP was delivered.

## Handoff placement

The downloadable link belongs in the **external delivery message** or final response, because the address may be assigned only after upload. A `ZIPRUNNER_HANDOFF.md` *inside* the package MAY include a stable known address, but is not required to include the final link. The download field is **not** a command, an install directive, or a consumer-authorized release action. It does not alter the `ZIPRUNNER_HANDOFF v1` project/version/filename fields or the workboard schema.

See [example delivery](../examples/DELIVERY_HANDOFF.md) for a sample form. The example link is intentionally illustrative and not a hosted ZIP.

## Example external handoff

A producer may use the existing human-readable `ZIPRUNNER_HANDOFF v1` convention, with the clickable link immediately alongside its identity fields:

**ZIPRUNNER_HANDOFF v1**

- **Project:** `example-project`
- **Version:** `1.2.3`
- **ZIP filename:** `example-project-1.2.3-ziprunner.zip`
- **Download:** [example-project-1.2.3-ziprunner.zip](https://example.org/releases/example-project-1.2.3-ziprunner.zip) *(illustrative URL only)*
- **SHA-256:** `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` *(illustrative digest only)*
- **Tests:** Source-only checks reported passing; target build and operator checks not run.
- **Remaining:** Target integration verification.

This example is **not** a completed delivery: it has a placeholder URL and digest. Real handoffs MUST use a verified accessible ZIP and its computed digest.

## Verification results returned to the originating request

Where supported, an importing consumer SHOULD return the completed run's results (including failures and unresolved checks) through the separately authorized [origin-feedback integration](ORIGIN_FEEDBACK.md). A producer's **direct ZIP download link** is still required in the delivery handoff even if a consumer also posts later test results. The two deliveries are independent, and neither may claim success without real artifacts or acknowledgements.
