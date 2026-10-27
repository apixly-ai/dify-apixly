# Apixly AI API: platform, access and pricing context

[Apixly AI API](https://apixly.ai/) provides API access to GPT, Gemini and Claude text models and to image/video models. Availability and supported operations depend on the model and the account's Key. This is a description of the wider platform, not a claim that one Dify plugin exposes every model family or capability.

## Choose the relevant integration

- **Apixly Media for Dify** submits image generation, reference-image edits and video tasks, refreshes the account's media catalog, and retrieves original task files. It does not add a Dify text-model provider.
- **Apixly Creative Controls for Dify** formats viewpoint, lighting and camera-look instructions. Its five free tools require no Apixly account, Key or generation call. A later generation tool is optional and has its own credentials and costs.
- Separate text integrations should follow the [OpenAI-compatible API guide](https://apixly.ai/docs/openai) or [Anthropic API guide](https://apixly.ai/docs/anthropic).

For media request formats, see [image generation](https://apixly.ai/docs/images) and [video tasks](https://apixly.ai/docs/video). Start with the [API quickstart](https://apixly.ai/docs), manage Keys in the [console](https://platform.apixly.ai/keys), and check [models and current prices](https://platform.apixly.ai/models).

## What the earlier “from 10%” price example means

The public offer checked on **2026-10-25** for `gpt-6.1-sol`, at the standard tier up to 272K input tokens, was **US$0.20 input / US$1.00 output per million tokens**. The [official model reference](https://developers.openai.com/api/docs/models/gpt-6.1-sol) checked for the same tier was US$2.00 / US$10.00. That particular comparison equals 10% of the reference input/output rates.

This is a dated example for a selected GPT text-model offer. It does **not** state that Gemini, Claude, every GPT tier, cached input, images or videos all cost 10% of official rates. Current model, tier and Key prices can differ; use the current catalog before sending a request. The Dify media plugin is not a text-model entry point, and the free formatter makes no billable model request.

## Service and support boundaries

The plugin is maintained by Apixly. Model names describe the service's model access and do not imply affiliation with the underlying model developers. No SLA, universal model coverage or guaranteed image/camera behavior is asserted here. The source repositories document their own tested scope and privacy behavior.

- [Apixly website](https://apixly.ai/)
- [API console](https://platform.apixly.ai/)
- [Apixly service privacy policy](https://apixly.ai/legal/privacy)
- [中文说明](ABOUT_APIXLY_zh_Hans.md)
- Support: [support@apixly.ai](mailto:support@apixly.ai)

This standalone GitHub document is not bundled into the currently approved Marketplace packages. It does not change their manifest versions, signed identities or runtime behavior.
