# Apixly AI API：平台、接入与价格范围

[Apixly AI API](https://apixly.ai/) 提供 GPT、Gemini、Claude 文本模型及图片、视频模型的 API 接入。可用型号与支持的操作取决于模型和账号 Key。这是对完整平台的介绍，不表示单个 Dify 插件提供了所有模型家族或能力。

## 选择对应集成

- **Apixly Media for Dify** 用于生图、参考图编辑、视频任务、账号媒体目录刷新与原任务文件取回，不新增 Dify 文本模型提供商。
- **Apixly Creative Controls for Dify** 组合视角、打光与相机镜头观感指令。五个免费工具无需 Apixly 账号、Key 或生成调用；后续生成工具为可选，其凭据和费用独立。
- 独立文本集成请查看 [OpenAI 兼容 API](https://apixly.ai/docs/openai)或 [Anthropic API](https://apixly.ai/docs/anthropic)指南。

媒体请求格式见[生图指南](https://apixly.ai/docs/images)与[视频任务指南](https://apixly.ai/docs/video)。从 [API 快速入门](https://apixly.ai/docs)开始，在[控制台](https://platform.apixly.ai/keys)管理 Key，并查看[模型与当前价格](https://platform.apixly.ai/models)。

## 之前“低至官方 1 折”的示例范围

**2026-10-25** 核验的 `gpt-6.1-sol` 公开报价，在输入不超过 272K Token 的标准档位，为每百万 Token **输入 US$0.20、输出 US$1.00**；当时同档位的[官方模型参考](https://developers.openai.com/api/docs/models/gpt-6.1-sol)为 US$2.00 / US$10.00。该特定输入、输出费率对比为参考价格的 10%。

这是有日期的指定 GPT 文本型号报价示例，不代表 Gemini、Claude、全部 GPT 档位、缓存输入、图片或视频都统一为官方 1 折。当前型号、档位和 Key 的费用可能不同，请在发送请求前查看当前目录。Dify 媒体插件不是文本模型入口；免费格式化工具不发起收费的模型调用。

## 服务与支持边界

插件由 Apixly 维护。模型名称描述平台提供的型号接入，不代表与底层模型开发商存在隶属关系。本说明不承诺 SLA、覆盖所有模型或确定的图像、相机效果；各源码仓库记录自己的实测范围和隐私行为。

- [Apixly 官网](https://apixly.ai/)
- [API 控制台](https://platform.apixly.ai/)
- [Apixly 服务隐私政策](https://apixly.ai/legal/privacy)
- [English](ABOUT_APIXLY.md)
- 支持：[support@apixly.ai](mailto:support@apixly.ai)

这份独立 GitHub 文档不打入当前已批准的 Marketplace 包，不改变其 manifest 版本、签名身份或运行行为。
