# Publishing and verification handoff

This repository is maintained on branch `apixly`, with SSH origin `git@github.com:apixly-ai/dify-apixly.git`. Publish reviewed source commits only. Keep virtual environments, validation reports, build packages, screenshots, signed URLs, private fixtures and API keys outside Git. The release owner handles Marketplace submissions and credential cleanup.

## Build and checks

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
mkdir -p dist
dify plugin package . -o dist/apixly_media-0.1.1.difypkg
python3 /path/to/dify-marketplace-toolkit/validator/validate-difypkg.py \
  dist/apixly_media-0.1.1.difypkg --offline --output-dir validation/offline
```

The package must exclude development state according to `.difyignore`. Inspect the archive before publication. A package generated on 2026-10-23 passed all blocking official local checks using CLI `v0.6.11`, SDK `0.10.2`, and Marketplace Toolkit commit `57a21d1304b1108df3e6b90a15a4f5dd9f0915f9`. Rebuild and rerun after any edit; only the final package hash identifies the release being reviewed.

## Review scope and warnings

- Proposed review risk: **Medium**. User prompts and media references are transmitted to Apixly. Optional result bytes are downloaded from signed Apixly content endpoints. The plugin does not execute commands, access a filesystem/database, crawl arbitrary URLs, or fetch arbitrary input URLs.
- API-key headers are created internally and sent only to fixed `https://apixly.ai/v1` API routes. The static Python safety check may flag `_headers()` returning an Authorization dictionary; this return value is not emitted as a Dify tool result. Tests assert no Authorization on content downloads, no third-party destinations, and no redirects.
- Expected domains: `apixly.ai`, `platform.apixly.ai`. The latter was observed in real image result URLs and is only allowed for signed content downloads.
- `meta.minimum_dify_version` remains unset: Community 1.17.1 was tested, but this does not establish the oldest supported release. The official validator treats the missing minimum as a recommendation warning.
- Offline vulnerability checking does not query OSV. Run the online dependency vulnerability check before publication. Local validator success does not cover real plugin installation, remote debugging, PR metadata/language, namespace ownership, duplicate versions, or Marketplace approval.
- Only an actual installed-plugin Dify workflow run establishes Dify-host compatibility. Local SDK tool execution is a separate, narrower result.

## Release gates

1. Run tests and inspect the final `.difypkg`; verify no credentials or development assets.
2. Publish the public source, English README, MIT license, Apixly icon and privacy notice under the authorized organization. Confirm support@apixly.ai is monitored and the organization's publisher identity is controlled by the owner.
3. Install/remote-debug the exact package in a real Dify Cloud or current Community Edition workspace. Confirm credential validation, tool discovery, task ID variable output, bounded polling and result file output. Disable Dify retries on every submit node.
4. Reconcile the authorized real API probes to unique usage/billing records and revoke the temporary test key. Keep billing/cleanup evidence in private release records.
5. Complete the **current** `langgenius/dify-plugins` PR template from the official repository, declare Medium risk and data flow, provide source and validation evidence, and submit one `.difypkg` per PR. Do not claim a signed/verified Marketplace release until approval/merge and installation are confirmed.
6. Register a Creator Center publisher organization and monitor feedback, failures and API changes. Plugin installation remains free; Apixly API usage follows the customer's own account billing.

## Verification baseline on 2026-10-23

Three authorized paid SDK probes used `grok-imagine-image` for generation, `gemini-3.1-flash-image` for reference editing, and `grok-imagine-video` for text-to-video. All three reached a successful terminal state and produced downloadable media that decoded correctly. The image and reference edit were compared visually; the original blue cup was retained and the requested background change was visible. These are bounded probes of those exact routes and parameters, not qualification of every model exposed by the gateway.

One video probe requested exactly `seconds: 1`, `resolution: 480p`, `aspect_ratio: 16:9`. Capabilities advertised 480p/720p, but the resulting H264 file was 1280×720 and the public task query did not supply adjustment metadata. This is a documented service capability discrepancy. The plugin forwards parameters unchanged and preserves public `effective_parameters` / `parameter_adjustments` when available; inspect downloaded media rather than assuming dimensions from a successful task state.

The first image probe exposed the production signed-content hostname `platform.apixly.ai`. An initial strict download rejection was fixed by an explicit allowlist regression test; the existing task was downloaded without replaying its generation. SDK registration also has a regression test for the single-subclass-per-entrypoint requirement.

Detailed task/request IDs, billing evidence, signed URLs, raw queries, media hashes and screenshots remain in private verification receipts outside the repository. Do not publish them in Marketplace descriptions or PRs. Native self-hosted verification is recorded below. Successful SDK or Community probes do not establish a Dify Cloud result.

## Native Community host verification on 2026-10-23

The exact released runtime was installed as a local package in official Dify Community 1.17.1, Python plugin daemon 0.6.10-local. All four example DSLs imported successfully. Provider credential validation, tool discovery, submit-once behavior, bounded delayed querying, task variables and native file output were exercised through Dify's installed-plugin workflow engine. The connected image-to-video example also requires Dify's standard sandbox service for its JSON-safe template node.

Successful real API workflows covered `grok-imagine-image` text-to-image, `gemini-3.1-flash-image` editing with two references (one HTTPS image and one PNG data URL), `grok-imagine-video` text-to-video at 1 second / 720p / 16:9, and the connected image-to-video workflow with `grok-imagine-video-1.5-preview` at 3 seconds and a signed HTTPS source image. Native image/video files were downloaded, decoded and visually checked. The reference video retained the source product and its square geometry; no resolution/aspect controls were sent on that route. These are exact-model probes, not a guarantee of every model or parameter combination.

A separate single-reference edit failed because its expired reference image URL returned 404 when the gateway tried to fetch it. The image provider was never called and the recorded final charge was zero. The plugin returned the original task as unsuccessful without resubmitting. The original failure remains in the private record. Two early connected-flow attempts stopped after successful image delivery because the test host's sandbox was missing or misconfigured; those images were retained, and no video was submitted by those failed runs. Correcting the standard sandbox configuration allowed the full connected workflow to complete.

An expired Dify file link returned 403. A query-only native workflow recovered the same original image task and downloaded its file without another generation. Controlled HTTP fixtures, using the released runtime inside a separate private QA plugin, exercised submit/query timeouts, no-media success, unknown statuses, ID mismatch, download failure, same-ID download recovery and a bounded query stop. These fault cases made no real Apixly generation calls and are not evidence of natural supplier recovery. The released plugin also rejected unsupported masks, NaN JSON, inline Grok preview references and explicit preview geometry before submission.

Dify Cloud installation was not completed: its normal login security verification failed. Marketplace approval/signing and Cloud compatibility remain release-owner checks. Detailed native run events, negative results, request IDs, media hashes, billing and cleanup records remain private outside Git.

## First real Dify workflow setup

Select **Generate image**, exact model `grok-imagine-image`, prompt `A single blue ceramic cup on a clean white table, studio product photograph, no text.`, and `parameters_json: {"n":1,"aspect_ratio":"1:1"}` as a JSON **string**. Submit once with retries disabled. Feed `task_id` to **Query media task**, `kind: image`, `download: true`, with bounded delayed querying of that same ID. This reproduces the tested model/parameter combination; changing a model requires its own capability and price check.

For reference editing, the live SDK quality check used `gemini-3.1-flash-image`, one signed URL from the successful image, and empty model parameters. This is the recommended first edit example. It is an explicit user/developer selection, never a silent fallback from another model.
