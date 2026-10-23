# Community verification

Observed on 2026-10-23 using official self-hosted Dify Community **1.17.1**, plugin daemon **0.6.10-local**, Python 3.12 and SDK **0.10.2**. The QA host used unmodified official images. These observations establish this tested path; Dify Cloud compatibility and Marketplace approval are not established.

## Native tools, controls and account connections

| Check | Observed result |
| --- | --- |
| Package installation | Five Apixly Media/catalog tools and five independent Creative Controls tools coexisted, with one provider per package |
| Workflow library | All twelve formal DSLs imported; 53 native tool panels retained the original parameter types, values and variable bindings |
| Free compiler | Independent no-credential installation; all-off prompt bytes preserved; three-control and edit-mode composition matched the canonical compiler |
| Failure guards | Seven controlled-input cases ran in the actual installed workflow engine, including invalid/failed packets; unsafe composition stopped before media nodes |
| Familiar controls | Eight original inline lighting swatches decoded; a real Lens selection could be cleared to Unspecified and its canonical empty value |
| Account setup | Normal website application registration, native Dify confidential-client settings, real OAuth consent and callback produced a saved connection using the owner's default Studixly Key |
| Another owned Key | A second native Authorize flow selected an existing active Key in Apixly's real consent dropdown; Dify saved it separately, and its name was changed through the native Rename control |
| Explicit credential routing | Submit, poll and final-query nodes in the image/edit/video QA flows were each explicitly set through Dify's saved-connection selector; all nine IDs read back consistently, with retries disabled |
| Live model discovery | Both account connections returned 14 image and 11 video models at verification time; installed SDK refresh and native image/video pickers exposed these options without a generation |
| Native published runs | Actual local Publish and Run actions executed the saved graphs; final prompts and the requested models/parameters were checked against frozen intents |

The catalog is dynamic, so the observed counts are not a fixed product limit. Typed model membership is authoritative. Exact IDs are preserved; an explicit manual ID overrides the picker. Catalog caches are scoped to credentials and selected-Key revisions, with lazy ten-minute refresh and an independent manual refresh tool.

## Actual account-mode media delivery

Every row below used one native Run and one paid submission. Polling retained the original task. The selected owned Key, exact route, unique usage and the delivered files were reconciled in private records.

| Case | Exact request scope | Observed delivery | Observed charge (USD) |
| --- | --- | --- | --- |
| Three creative groups enabled | `grok-imagine-image`, 1:1, one image, model-default size; Viewpoint + Lighting + Camera & Lens | Native Dify JPEG file, 960×960; downloaded and decoded | 0.01 |
| Camera & Lens reference edit | `gemini-3.1-flash-image`, one retained JPEG data URL, `size: 1024x1024`, `aspect_ratio: 1:1`, one image; only Camera & Lens enabled | Native Dify JPEG file, 1024×1024; downloaded and decoded | 0.02 |
| Text-to-video | `grok-imagine-video`, one second, 720p, 16:9, no references, all creative groups off | Native Dify MP4 file, H264 1280×720, 24 fps, 25 frames, 1.041667 seconds | 0.025 |

The three stages produced three independent usage records, totaling US$0.055 for this owned QA Key. Prices are dated observations for those exact requests; check the current catalog before using other models or settings.

The video passed full-frame FFmpeg decoding. Clicking its Dify file link opened the native browser media player, which naturally played the complete 0–1.041666 second range with no media error. The first and last frames showed the requested camera push-in. Original submission IDs were never replayed to recover a download.

The lens edit retained the reference car's shape, blue roof, white bumper, yellow marking and cube positions, with softer background focus. The separate all-controls generation showed shallow depth of field; its requested blue key light was **not independently evident**. These are generative prompt directions. Named camera/lens looks do not establish physical optical simulation or exact rendered geometry. [Actual samples and hashes](assets/creative-samples.json).

## Retention and final distribution checks

Current image results are temporary, approximately **ten minutes after completion**; service retention can change. Download them promptly into Dify files or your own storage. The successful image outputs were saved during the original runs. Later task expiry does not invalidate those delivered files and does not authorize another paid submission. A video retention duration is not inferred from its remaining readable during verification. Model-catalog caching and media retention are separate lifetimes.

The paid-tested build delivered the files above. A subsequent installed build queried both expired image tasks as explicit terminal negatives and downloaded the retained original video with an identical SHA256. Final revocation acceptance then exposed the first-party flat error envelope, which is now supported alongside nested relay errors. Two error-branch files changed: known invalid/expired/revoked connections request authorization again; selected-Key rejection/unavailability preserves the connection and explains Dify saved-connection selection or a new authorization; unknown HTTP 401 errors are not mislabeled.

Successful request constructors, parameters, download handling and HTTP 200 parsing are unchanged by this fix; AST comparisons and 53 related regression tests verify that boundary. Remaining runtime/UI/dependency bytes are compared separately from the changed error branches and Markdown. Final-package installation and twelve DSL/53 parameter readbacks are repeated, and the two previously saved, now-revoked connections are checked through the installed read-only SDK for HTTP 401 / invalid_connection with no stale catalog or manual-key fallback. No paid call is repeated. Package hashes and the scope of these separate qualifications appear in the release notes.

## Scope and limits

The original four media workflows and compatibility creative tool remain available. Earlier manual-key verification covered multiple references and connected image-to-video; the new account-mode paid probes above cover these three exact requests. They do not certify every model, reference count or parameter combination in the live catalog. Masked inpainting remains unavailable.

Dify Cloud installation was not verified because its normal login security verification could not be completed. Other Dify versions are unverified. The native workflow editor remains desktop-oriented at 375px. The published free preview fits a 375×900 viewport, but Dify's native Run button is 32px high. Camofox viewport checks do not establish iOS Safari, touch-event, IME or soft-keyboard behavior. The plugin reuses Studio presets and swatches inside Dify's own widgets; it does not replace the host shell.

The prior complete serial suites passed 107 media and 29 creative tests. Shared compiler coverage included 169 valid and 24 invalid fixtures plus 1,000 source-language differential cases; the catalog parser matched 510 differential cases. These checks complement installed-host results. The official package validator covers archive contents, secrets, binaries, metadata, Python and pinned dependencies; it does not grant Marketplace approval or a complete transitive security guarantee.

Owned QA media were used for screenshots and samples. Private account identifiers, job/request IDs, connection tokens, signed URLs, billing and cleanup receipts are kept outside the source repository. The plugin adds no independent telemetry or content logging; Dify operators control their own workflow records. See [PRIVACY.md](../PRIVACY.md).
