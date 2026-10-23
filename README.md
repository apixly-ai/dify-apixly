<p align="center">
  <img src="https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/cover.png" alt="Apixly Media for Dify: generate images, edit references, create video and retrieve task files" width="1200" />
</p>

# Apixly Media for Dify

Generate images, edit references and create videos inside Dify. Connect an Apixly account or use your own API key, submit a task once, and retrieve its result as a native Dify file.

**[Download plugin and workflows](https://github.com/apixly-ai/dify-apixly/releases/latest)** · **[Create an API key](https://platform.apixly.ai/keys)** · **[Models and prices](https://platform.apixly.ai/models)** · **[Open the console](https://platform.apixly.ai/)**

[Website](https://apixly.ai/) · [API documentation](https://apixly.ai/docs) · [Chinese documentation](readme/README_zh_Hans.md) · [Support](mailto:support@apixly.ai) · [Marketplace submission](https://github.com/langgenius/dify-plugins/pull/3481)

The plugin is free. API usage is billed to your Apixly account. Maintained by Apixly; this integration is not affiliated with the underlying model developers.

## From a product photo to a finished asset

These are actual results from the authorized API verification, not interface mockups. In this reference edit, `gemini-3.1-flash-image` retained the blue cup and handle while changing the background to a neutral gray studio setting.

| Reference image | Edited result |
| --- | --- |
| <img src="https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/reference-cup.jpg" alt="Original blue ceramic cup on a light table" width="420" /> | <img src="https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/edited-cup.png" alt="Actual reference edit: blue ceramic cup retained against a gray studio background" width="420" /> |

| Text to video | Image to video |
| --- | --- |
| <img src="https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/text-video-still.png" alt="Still from the verified text-to-video clip: lighthouse at sunset" width="420" /> | <img src="https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/image-video-still.png" alt="Still from the verified image-to-video clip retaining the source blue glass vase" width="420" /> |
| [Watch the actual text-to-video clip](https://github.com/apixly-ai/dify-apixly/blob/apixly/docs/assets/text-video.mp4) · 1280 × 720, about 1 second | [Watch the actual reference-video clip](https://github.com/apixly-ai/dify-apixly/blob/apixly/docs/assets/image-video.mp4) · 960 × 960, about 3 seconds |

Video images above are still frames from the linked generated clips. Results depend on the selected model, prompt and supported parameters. The reference-video example follows the source image geometry. [Asset sources and SHA256 hashes](https://github.com/apixly-ai/dify-apixly/blob/apixly/docs/assets/provenance.json).

## Pick one of four starting workflows

<img src="https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/workflow-map.png" alt="Illustrated overview of the four importable workflows: text to image, reference editing, text to video and connected image to video" width="1200" />

| Workflow | Start with | Billable submissions per run |
| --- | --- | --- |
| [Text to image](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-image-workflow.yml) | A product or creative brief | 1 image generation |
| [Reference edit](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-edit-workflow.yml) | One image, optional extra references, and an edit instruction | 1 image edit |
| [Text to video](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-video-workflow.yml) | A scene and its supported duration | 1 video generation |
| [Image to video](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-image-to-video-workflow.yml) | An image brief connected to a video instruction | 1 image + 1 video generation |

Each DSL submits once per stage, checks the returned task ID, polls within a limit, and returns the original task's files. Read-only queries and download recovery do not create another generation. Check the current model catalog for API prices.

## Creative controls, with a free first step

Install the separate [Apixly Creative Controls companion](https://github.com/apixly-ai/dify-apixly-creative) to preview angle, lighting and camera/lens-look instructions inside Dify without an account, Key or generation call. **Enable a group → choose its preset or values → inspect `final_prompt` → connect Generate/Edit when ready.** All groups default off; the original prompt is preserved exactly when no instruction is added. These are AI art-direction instructions.

| Additional workflow | What it does | Billable submissions |
| --- | --- | --- |
| [Free creative preview](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-creative-preview-workflow.yml) | Compose and show the final prompt; companion only | 0 |
| [Creative image](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-creative-image-workflow.yml) | Compose → validate → generate → retrieve files | 1 image |
| [Creative reference edit](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-creative-edit-workflow.yml) | Compose an edit instruction preserving unrelated subject details | 1 edit |
| [Creative text video](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-creative-video-workflow.yml) | Compose → validate → create video → retrieve files | 1 video |

The three media examples require both exact plugin packages. Invalid composition stops before the paid node. Structured sections remain available on the compose node for downstream wiring; the preview result shows the prompt or its safe validation error.

## Setup and connection requirements

1. Create or sign in to your [Apixly console account](https://platform.apixly.ai/), fund it as needed, and [create an API key](https://platform.apixly.ai/keys) in a group with access to your intended image/video models. The plugin is free; you bring your own key and pay Apixly for API usage. Check model capabilities and prices before running.
2. Install the plugin from a released `.difypkg` through Dify's Plugins page. Self-hosted Dify enables signature verification by default: use an appropriately signed release, or the development signing procedure documented by Dify for an environment you control. A local package is not a Marketplace-approved installation.
3. Add **Apixly API key** to the provider's secret credential. Do not put it in prompts, tool parameters, exported workflows, URLs, or JSON model parameters. Validation only performs `GET https://apixly.ai/v1/models`; it does not submit a generation. This endpoint may reject keys whose account balance or group does not allow access.
4. Allow outbound HTTPS to `apixly.ai:443` for API calls and `platform.apixly.ai:443` for signed media downloads. There is no custom API base URL. The plugin does not call MCP endpoints or accept signed MCP credentials. Manual-key mode uses `https://apixly.ai/v1`; OAuth account mode uses the fixed scoped relay at `https://apixly.ai/api/integrations/v1`.
5. Add the tools to a Workflow, Chatflow or Agent. Set exact model IDs from the catalog available to your key. Names are forwarded unchanged; there is no automatic model substitution.

### Optional account connection

This development candidate includes OAuth account connection; deployment and real authorization acceptance remain release gates. A workspace administrator registers a Dify application in [Apixly connection settings](https://apixly.ai/integrations), using the **exact callback URI shown by Dify**, then enters the issued client ID and one-time secret in Dify's private OAuth client settings. No shared client secret is bundled.

Users choose **Authorize**, sign in through the normal Apixly website and select **Studixly Key (default)** or another existing active Key. The plugin receives a revocable scoped connection token, rather than a website password, login JWT or raw API key. The website authorization page provides the complete Key dropdown. Dify's credential selector switches saved connections. Dify initially names OAuth credentials automatically; you can rename one to `Apixly · studixly-key`. Account and masked Key details are stored with the connection.

### Choose and refresh models

Open a media node to load the catalog for its selected credential. Choose **Model catalog**, or enter **Manual exact ID (overrides picker)**. A nonempty manual ID takes explicit precedence and is sent unchanged. Both blank returns a clear error before submission; existing example DSLs supply explicit model IDs.

**Refresh model catalog** is a separate read-only tool. It updates model options and reports stale/error status without generating media. Reopen the media node to view refreshed options. Catalogs refresh lazily with a ten-minute cache and background refresh; saved options remain marked when a refresh fails. Image models use the API's explicit type. Video models without capability data remain visible with that limitation; the plugin does not invent supported parameters. Caches are credential-scoped and process-local; other plugin workers refresh independently.

For a checked price example, `gemini-3.1-flash-image` 1K image generation was US$0.02 per image on 2026-10-23. Consult the [current model catalog](https://platform.apixly.ai/models) for your selected model and parameters.

Runtime: Python 3.12, `dify-plugin==0.10.2`. The plugin and example workflows were installed and exercised on self-hosted Dify Community 1.17.1. Other versions and Dify Cloud remain unverified. See `PUBLISHING.md` for the bounded verification record.

## Inside the native Dify editor

<img src="https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/dify-reference-editor-en.png" alt="Actual Dify Community workflow editor showing the Apixly reference-edit tool and its fields" width="1200" />

The fields above are the actual installed plugin UI. English and Chinese labels are included. The original media plugin and four media DSLs were installed, run and published in self-hosted Dify Community 1.17.1; Dify Cloud remains unverified. [View the connected workflow screenshot](https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/dify-image-video-workflow.png).

## Tools and usage

| Tool | API operation | Result |
| --- | --- | --- |
| Generate image | `POST /v1/images/generations`, `async: true` | Image task ID |
| Edit image | `POST /v1/images/edits`, JSON `images[].image_url`, `async: true` | Image task ID |
| Create video | `POST /v1/videos`, JSON with flat model parameters | Video task ID |
| Query media task | `GET /v1/images/generations/{id}` or `GET /v1/videos/{id}` | Current status, terminal/success flags, media URLs, numeric usage when returned |
| Refresh model catalog | Read-only model list and video capabilities | Current or saved options, stale/error flags; no inference |

Every submit performs exactly one POST. A timeout, redirect, server error or missing task ID produces `unknown_submission`. It may already have created a billable task. Check the original task in Apixly before manually submitting another one. **Disable Dify node-level retries on all three submit tools.** Do not configure an Agent to retry or regenerate after an ambiguous result.

Query is a single read, without an internal polling loop. Reuse the original task ID in a bounded workflow loop with a delay and attempt/time limit. A query network/HTTP failure is `query_error`; it does not prove the task failed. Unknown statuses stop automatic polling. Never restart generation to wait for an existing task.

Successful query outputs include the complete normalized JSON plus named workflow variables: `task_id`, `status`, `terminal`, `success`, `generation_success`, `result_state`, and `urls`. The submission output is not proof of completion or billing. `generation_success: true` requires a successful server status and at least one media URL. If file download is requested, `success` becomes true only after every requested download succeeds. A successful server status with no media is `result_unavailable`; retry the same query or contact support.

`download: false` (default) emits signed media links. `download: true` additionally returns Dify file/blob outputs, limited to 32 MiB per file and PNG/JPEG/WebP/MP4/WebM formats. Downloads only accept signed Apixly image/video content URLs, follow no redirects, and send **no API key**. A download failure returns `download_error` and `success: false`, retaining `generation_success` and the original task ID/URL; it never regenerates. Save completed files in your own storage before their links expire. Query the same task for a fresh link while the task's media remains retained.

## Importable workflows

The source includes four workflows in `examples/`: image generation, reference editing, video generation, and a connected image-to-video workflow. Install the matching plugin package and authorize its provider, then import a `.yml` using Dify's **Import DSL file** action. Each workflow submits once with retries disabled, stops if no task ID is returned, and queries that same task at most 60 times with a five-second delay. A final query returns Dify files and explicit status variables. At the attempt limit, the original task state is returned; no new generation is started.

Examples reference the exact identifier produced by `dify plugin checksum`, which differs from ZIP SHA256. Regenerate them after package changes. Native host import/run status is recorded in `PUBLISHING.md`; parsing YAML or passing safety tests alone is not described as a successful host run.

The connected workflow requires Dify's standard code sandbox for its JSON-safe template node. The connected image-to-video workflow generates an image, takes its signed HTTPS URL through a JSON-safe template, and explicitly submits `grok-imagine-video-1.5-preview` for 3 seconds, using the source image geometry. It stops if the image is not delivered. This workflow makes two billable generation calls, each attempted once; neither stage silently substitutes a model.

Named fields cover image count, aspect ratio, size and quality; video seconds, resolution and aspect ratio; a single reference image URL/data URL and additional references. Advanced JSON remains available for model-specific fields. Conflicting values stop before submission. Visible default model IDs are never substituted on failure. Query offers a 0–15 second delay before its single read for bounded loops.

## First task: image generation

Use **Generate image** with these tool parameters after confirming the exact model is available to the key:

```json
{
  "model": "grok-imagine-image",
  "prompt": "A single blue ceramic cup on a clean white table, studio product photograph, no text.",
  "parameters_json": "{\"aspect_ratio\":\"1:1\",\"n\":1}"
}
```

Store its returned `task_id`. Use **Query media task** with `kind: image`, that same `task_id`, and `download: true`. If the result is pending, query again later under a bounded loop. The example is an explicit model choice, not a fallback; account permissions, upstream availability and supported parameters must be checked for your account.

## Reference edit and video examples

**Edit image** accepts one image directly in `reference_image`. Optional `reference_images` is a JSON array string for additional images. Each item is a public HTTPS image URL or an explicit PNG/JPEG/WebP base64 data URL, for example:

```json
{
  "model": "gemini-3.1-flash-image",
  "prompt": "Preserve the product and replace its background with a blue studio backdrop.",
  "reference_images": "[\"https://your-public-storage.example/product.png\",\"data:image/png;base64,...\"]",
  "parameters_json": "{}"
}
```

Replace the illustrative URL/base64 with accessible image data. The starter edit DSL allows up to 1,048,576 characters per reference input field; use HTTPS references or upstream file/variable nodes for larger media. Raw base64 without a MIME-prefixed data URL, local paths, private-network URLs and embedded URL credentials are rejected. Each data URL is limited to 20 MiB; up to 16 references can be passed, with lower limits enforced by individual models. References are sent to Apixly; this plugin never fetches arbitrary reference URLs itself.

For **Create video**, choose an exact enabled ID and supported parameters. For example, after verifying its capabilities:

```json
{
  "model": "grok-imagine-video",
  "prompt": "A slow cinematic pan across the product on a studio table.",
  "parameters_json": "{\"seconds\":1,\"resolution\":\"720p\",\"aspect_ratio\":\"16:9\"}"
}
```

This video example is text-to-video. The default `grok-imagine-video` is text-only. For `grok-imagine-video-1.5-preview`, reference images must be public HTTPS URLs; inline base64 data URLs are rejected before submission on that route. Its reference-video output follows source image geometry. Leave resolution/aspect ratio/size empty for this model: explicit geometry controls are rejected rather than silently ignored. Text-only examples continue to specify their tested 720p/16:9 settings. For a model whose capabilities include reference images, `images` accepts HTTPS image URLs or image data URLs. Reference `videos` and `audios`, if the chosen model supports them, use HTTPS URLs. All values retain their JSON types. Inspect `GET /v1/video/config` with your own API client for model capability details; unsupported combinations are reported by the gateway. The plugin does not silently replace IDs, durations, resolutions, reference count or other parameters. Public `effective_parameters` and `parameter_adjustments`, when returned by the gateway, are preserved in the JSON output. Decode actual media to verify delivered dimensions: one live test requested 480p but received a 1280×720 video without adjustment metadata.

## Known use case

An e-commerce workflow can take a product photo and campaign brief, edit the product image, let a person review the resulting image, create a short video from the approved image, query the same task until terminal, and save the resulting media. The tools cover generation and retrieval; publishing to advertising/social platforms is a separate workflow step. The included minimal workflows make each generation type independently testable before combining them; native host import/run evidence is recorded separately in PUBLISHING.md.

## Errors, privacy and limits

- `pending`: query the same ID later.
- `completed`: media URLs available; optional download may still fail independently.
- `failed`: explicit provider failure, expiry or cancellation. Inspect the message; do not automatically submit another paid task.
- `result_unavailable`: server success without media. Query the same ID or contact support.
- `query_error`: status could not be established. Check access/connectivity; query the same ID.
- `unknown_status`: unrecognized server state; stop polling and inspect with support.
- `validation_error`: malformed input or explicit submit rejection; inspect HTTP status/key/model settings.
- `unknown_submission`: submit may have succeeded remotely; check task history before any manual resubmission.

The plugin collects no independent analytics and writes no user data to local files, logs, databases or plugin KV storage. Dify and Apixly process/store data according to their own policies. Signed media URLs grant temporary access and should be treated as sensitive. Read [PRIVACY.md](PRIVACY.md) before use.

## Local development and verification

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
dify plugin package . -o dist/apixly_media-0.1.1.difypkg
```

Use the official [Dify Marketplace Toolkit](https://github.com/langgenius/dify-marketplace-toolkit) to validate the package. Offline checks do not query dependency vulnerability databases and do not constitute Marketplace approval or production API E2E verification. Full release instructions and outstanding gates are in `PUBLISHING.md` in the source repository.
