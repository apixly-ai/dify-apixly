# Publishing Apixly Media

## Current approved distributions

The production Marketplace entries remain [Apixly Media 0.2.0](https://marketplace.dify.ai/plugin/apixly-ai/apixly_media) and [Creative Controls 0.1.0](https://marketplace.dify.ai/plugin/apixly-ai/apixly_creative). Their accepted submissions are [#3506](https://github.com/langgenius/dify-plugins/pull/3506) and [#3497](https://github.com/langgenius/dify-plugins/pull/3497). The earlier closed #3481 is retained history, not a submission to replace or reopen.

The checked-in workflows pin their actual signed Marketplace identities:

- Media: `apixly-ai/apixly_media:0.2.0@eb3120042ccd0132f0162fcbc7d8dc9b77fab0b1c2d21965b3d20c136f39701f`
- Creative Controls: `apixly-ai/apixly_creative:0.1.0@4a912551810fdf4df18314e316600376b01e5b43fbf230fd067d9c9ef4e802c6`

Official signing adds verification metadata and a ZIP signature. Its content checksum can differ from an unsigned GitHub package. Never substitute a new GitHub checksum into a Marketplace dependency before that exact signed version exists publicly. Do not overwrite approved packages, release assets, tags or merged PR history.

## Documentation updates

The `docs-2026-10-27` source release is explicitly a documentation prerelease, with no `.difypkg` asset and no change to manifest versions or runtime. It must not become GitHub's latest production package release. Existing `/releases/latest` download links must keep resolving to the production version.

Source READMEs and the standalone platform guide can evolve independently of historical package README bytes. Keep that distinction explicit; a GitHub documentation release does not update the Marketplace listing or establish new native qualification.

The current official [Development Guidelines](https://docs.dify.ai/en/develop-plugin/publishing/standards/contributor-covenant-code-of-conduct) require meaningful version updates and prohibit promotional Marketplace README content. Do not create a metadata-only Marketplace version or invent unrelated functionality to satisfy that rule. Keep README content useful for installation, credentials, usage, privacy and support. A normal documentation/metadata correction route must be confirmed with the platform if it is not documented; do not assume a staff-only editing endpoint is available to publishers.

## A future functional Marketplace release

1. Maintain and commit source on the existing `apixly` branch; push only through the SSH origin. Follow the repository's test-first requirements for behavioral changes.
2. Define the real capability, compatibility, security or upstream-service change and its relevant tests. Only then select a new manifest version. A release User-Agent, if present, follows that version; changing it alone is not a functional feature.
3. Keep workflow-builder defaults and checked-in DSLs on publicly available signed versions until the new Marketplace version is approved and its signed download is verified. Manifest and published workflow dependency versions are different release contracts.
4. Package only the required runtime, metadata, dependency pins, icon, privacy policy and localized READMEs. `.difyignore` excludes tests, examples, standalone docs, environments, caches and credentials. Inspect the actual ZIP, SHA256 and Dify content checksum.
5. Use the current official [PR template](https://github.com/langgenius/dify-plugins/blob/main/.github/pull_request_template.md), [submission requirements](https://github.com/langgenius/dify-plugins/blob/main/docs/plugin-submission-requirements.md) and [review guidelines](https://github.com/langgenius/dify-plugins/blob/main/docs/plugin-review-guidelines.md). Read the linked Development/Privacy requirements rather than relying on an old checkbox label.
6. Run the canonical PR-body validator separately from package validation. Run the package, secrets, binaries, manifest/README, dependency and sensitive-capability checks on the final ZIP. Online pinned-dependency lookup is not a complete transitive audit; local checks do not replace official installation/packaging CI or human review.
7. Submit one new-version package per update PR from a clean current upstream base. Do not reuse an already merged head with unrelated accumulated changes. Source repository branch rules and contribution-fork branch setup must both be respected.
8. Preserve errors and unknown outcomes; reconcile before repeating any publication request. After merge, verify the active version, public Install link, actual signed download, official signature and payload differences. Merging is not itself proof of listing.
9. Migrate exact workflow dependency/node pins only after that signed identity is public. Use a failing regression from the independently verified distribution identity, then verify normalized DSLs and bindings and qualify the final installed combination as appropriate. Do not repeat paid requests just to validate documentation.

## Qualification and scope

Media handles authentication data and is declared **High risk**. Creative Controls is an independent credential-free formatter, declared **Low risk**. Neither classification is lowered for a documentation update.

The retained evidence covers Community 1.17.1, original image/edit/video delivery and unique billing, the later connection-error repair, official signed-package installation with signature verification required, twelve imported workflows/53 parameter bindings and five actual free-tool executions. See [QA](docs/QA.md). These stages are distinct; a docs update does not claim a new paid run, Cloud installation, untested host version or mobile browser feature.

For a future authorized functional candidate, use the existing toolchain and `.difyignore`; record the actual commands and source revision. The previously used SDK is pinned to 0.10.2. Do not silently upgrade it during unrelated publishing work.

Support: source issues or [support@apixly.ai](mailto:support@apixly.ai). Detailed credentials, job IDs, signed URLs, local workflow runs and financial records remain private.
