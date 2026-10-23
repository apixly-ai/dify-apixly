# Repository presentation assets

These assets illustrate the real Apixly Media for Dify integration. They are repository documentation assets, excluded from `.difypkg` by `docs/**` in `.difyignore`. The main README uses public raw GitHub image URLs so a future package README can display these images without bundling screenshots or videos. Publish these repository assets before releasing a package that references them.

- `cover.svg` and `workflow-map.svg`: original code-native vector artwork and an explicitly illustrative workflow map, using the existing official Apixly icon and brand palette. The corresponding PNG files are exact browser renders of the SVGs for broad Markdown/social-preview compatibility. They are diagrams, not product screenshots.
- `reference-cup.jpg` and `edited-cup.png`: unchanged output bytes from authorized generation/reference-edit verification. The edit uses the exact `gemini-3.1-flash-image` model. The original content/provenance metadata is preserved.
- `text-video-still.png`, `image-video-still.png`, and corresponding `.mp4` clips: real generated video outputs and extracted stills from the previously completed verification. No new model calls were made for this presentation.
- `dify-reference-editor-en.png`, `dify-reference-editor-zh-Hans.png`, and `dify-image-video-workflow.png`: unchanged native screenshots from official self-hosted Dify Community 1.17.1. They do not establish Dify Cloud compatibility or Marketplace approval. The local account visible in the screenshots is a QA account.

The example prompts/assets were created for authorized testing and contain no customer uploads. Screenshots were visually reviewed for secrets and signed URLs; source task IDs, request IDs, private paths and billing receipts remain outside the repository. Generic public filenames are used here. Model IDs, source descriptions and SHA256 hashes are listed in `provenance.json`; private job/request IDs are deliberately omitted. Do not add raw workflow run events, private receipts, credentials or signed content links.

The published `v0.1.0` package, runtime, manifest, plugin icon and exact workflow dependencies remain unchanged by this documentation update. README changes can be included in a later reviewed package release.
