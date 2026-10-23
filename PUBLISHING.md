# Publishing Apixly Media

Maintain source on `apixly` and push through the SSH origin. Build from an immutable source commit, inspect its package, then identify the exact ZIP SHA256 and Dify content checksum in the release. README and privacy edits change the checksum even when behavior is unchanged.

## Build and package checks

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
mkdir -p dist
dify plugin package . -o dist/apixly_media-0.2.0.difypkg
python3 /path/to/dify-marketplace-toolkit/validator/validate-difypkg.py \
  dist/apixly_media-0.2.0.difypkg --output-dir validation/online
```

Use `.difyignore` to exclude virtual environments, tests, documentation assets, caches, local settings and generated packages. The distribution contains the runtime, manifest, dependency pins, Apixly icon, English/Chinese READMEs and privacy notice. Do not bundle keys, connection tokens, client secrets, local workflow runs or signed URLs.

The verified toolchain is Dify CLI 0.6.11, SDK 0.10.2 and Marketplace Toolkit `57a21d1304b1108df3e6b90a15a4f5dd9f0915f9`. The serial runtime suites passed 107 media tests and 29 companion tests. A documentation-only repack uses byte comparisons against that tested runtime; repeat the relevant tests when runtime behavior changes. Run the official package, secrets, binaries, metadata, Python and dependency checks on the final package. Online OSV results cover the pinned requirements set, not a fully resolved transitive audit.

## Installed-host qualification

[QA.md](docs/QA.md) records the bounded observations: official Community 1.17.1 installation, five media/catalog plus five independent creative tools, twelve workflow imports and 53 native editor panels, real confidential OAuth consent, default Studixly and explicitly selected owned Keys, saved-connection selection/rename, current model options, and real image/edit/video files.

Each paid stage submitted once with retries disabled. Terminal task success, native Dify file delivery, downloaded bytes, decoded media and unique billing were verified separately. Image results are temporary: current service observations show approximately ten minutes after completion. Save the files promptly. A later `expired` response is a retention outcome; it does not justify another generation.

Live paid delivery and existing-task retrieval qualify the request and success paths: expired images returned terminal negatives, and the retained video was downloaded with its original bytes. Final acceptance also exposed the first-party flat error envelope on revoked connections. A narrow fix in the media client and catalog adapter recognizes flat/nested public connection codes, distinguishes revoked connections from selected-Key failures, and retains safe generic handling for unknown HTTP 401 responses. Successful request construction and HTTP 200 parsing are unchanged and covered by 53 related tests. The final package is installed again for the changed revocation path, and twelve pinned DSLs/53 parameter bindings are read back without paid replay. Release notes distinguish the paid-tested build, unchanged success paths and final error-path qualification.

## Marketplace submission

Apixly Media is **High risk** under the current authentication-data classification: it handles manual secrets, confidential-client proof and a scoped connection token in Dify-managed credentials. Requests use fixed Apixly HTTPS destinations. It provides no shell, SQL, filesystem, arbitrary URL proxy or payment action. The separate Creative Controls plugin is **Low risk** and works without Apixly API/auth access; its formatter is useful independently of Media.

Use the current official [PR template](https://github.com/langgenius/dify-plugins/blob/main/.github/pull_request_template.md), [submission requirements](https://github.com/langgenius/dify-plugins/blob/main/docs/plugin-submission-requirements.md), [Marketplace Agreement](https://dify.ai/legal/marketplace-agreement), [Development Guidelines](https://docs.dify.ai/en/develop-plugin/publishing/standards/contributor-covenant-code-of-conduct), and [Privacy Guidelines](https://docs.dify.ai/en/develop-plugin/publishing/standards/privacy-protection-guidelines). Describe the observed Community result and the Cloud limitation accurately.

The existing unmerged new-plugin PR [#3481](https://github.com/langgenius/dify-plugins/pull/3481) should contain only `apixly-ai/apixly_media/apixly_media-0.2.0.difypkg` in its final diff. Replace its earlier candidate, rewrite its title/body around this release and declare High risk. Submit the free companion in a separate new-plugin PR containing only `apixly-ai/apixly_creative/apixly_creative-0.1.0.difypkg` and declare Low risk. One package per PR is required.

Verify public source links, README PNGs and actual downloaded release bytes before submitting. A local package or GitHub release does not establish Marketplace signing, approval or listing. Dify Cloud installation remains unverified because its normal login security verification could not be completed. Support is provided through the source repository and support@apixly.ai.

## Warnings and limits

The validator may report internal Authorization dictionary returns, the fixed token URL and an unset `minimum_dify_version`. Authorization is not a tool output; downloads receive no inference credential and follow no redirects. The oldest compatible Dify version is not inferred from one tested host. No camera/light physical simulation, complete model-wide qualification, browser-engine compatibility or mobile workflow-editor support is asserted. Detailed task/request identifiers, signed URLs, billing and owner-cleanup records stay private.
