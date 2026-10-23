# Apixly 媒体插件：在 Dify 中生成图片和视频

用自己的 Apixly API Key 在 Dify 工作流、Chatflow 或 Agent 中生成图片、编辑参考图、创建视频和查询任务。**插件免费，API 调用按 Apixly 账号实际用量计费。** 本插件由 Apixly 维护，不代表底层模型开发商。

[官网](https://apixly.ai/) · [控制台](https://platform.apixly.ai/) · [创建和管理 Key](https://platform.apixly.ai/keys) · [模型与价格](https://platform.apixly.ai/models) · [API 文档](https://apixly.ai/docs) · [调用明细](https://platform.apixly.ai/usage/logs) · [源码](https://github.com/apixly-ai/dify-apixly)

## 安装和连接

1. 登录 Apixly 控制台，按需充值，在 Key 页面创建具有所需图片/视频模型权限的 API Key。运行前先查看模型价格和能力。
2. 在 Dify 插件页面安装发布的 `.difypkg`，或安装经过市场审核的版本。自行上传的开发包不等于已通过 Marketplace 审核；自托管 Dify 默认会校验签名，按 Dify 官方说明为自己的受控环境配置签名。
3. 在 Apixly 媒体提供商中填写 **Apixly API Key**。这是 secret credential，不要放进提示词、JSON 参数或公开 DSL。验证只查询模型列表，不会生成收费素材。
4. 允许访问 `apixly.ai:443`；签名素材下载还可能访问 `platform.apixly.ai:443`。插件直连 `https://apixly.ai/v1`，不需要 MCP 凭证。

## 四个工具

| 工具 | 用法 | 返回 |
| --- | --- | --- |
| 生成图片 | 选择精确模型、写提示词，可设数量、比例、尺寸、质量 | 原图片任务 ID |
| 参考图编辑 | 粘贴一张 URL 或 base64 data URL，可补更多参考图 | 原图片任务 ID |
| 生成视频 | 设置模型、秒数、分辨率、画幅；额外参数可用 JSON | 原视频任务 ID |
| 查询媒体任务 | 使用原任务类型与 ID，可选择返回 Dify 文件 | 状态、成功标记、链接或文件 |

常用字段有中英文名称和默认值。默认模型在 UI 中可见；改变模型后，请根据该模型能力调整参数。模型 ID 原样发送，失败时不会自动换模型。高级 JSON 与界面同名字段如有冲突，会在收费提交前明确报错。

编辑时，`reference_image` 可直接粘贴一张图；`reference_images` 是补充图片的 JSON 数组，如 `["https://example.com/second.png"]`。base64 必须带 MIME 前缀，例如 `data:image/png;base64,...`；不能填本地路径。每张 base64 图片最多 20 MiB，插件最多传 16 张，各模型可能支持更少。

## 导入工作流

`examples/` 提供文生图、参考图编辑、视频生成，以及图片衔接图生视频四份 `.yml`。先安装对应包并设置 secret Key，再从 Dify 的 **导入 DSL 文件** 导入。

每份流程均为：**只提交一次 → 有任务 ID 才继续 → 最多查询 60 次，每次先等 5 秒 → 查询并返回原任务文件**。生成节点关闭自动重试。到达上限仍未完成时，返回原任务的当前状态和 ID，不会重新生成。宿主导入与运行记录见源码 `PUBLISHING.md`；仅解析 YAML 或本地测试不代表宿主验收。

组合流程先生成图片，将其签名 HTTPS URL 以 JSON 安全编码衔接到显式选择的 `grok-imagine-video-1.5-preview`（3 秒、720p）。图片未交付则停止。此流程有两次按量计费的生成调用，每阶段各提交一次，不自动换模型。默认 `grok-imagine-video` 仅文生视频；1.5 preview 参考图只收公开 HTTPS URL，不支持内联 base64。

## 理解结果与恢复

- `pending`：稍后继续查同一 ID。
- `generation_success`：生成成功且已有素材链接。
- `success`：本次要求的交付成功；要求下载但下载失败时为 `false`。
- `download_error`：保留原任务与链接，恢复下载或再查原 ID，不要重新生成。
- `result_unavailable`：网关报成功但没有素材，继续查原 ID 或联系支持。
- `query_error`：本次查询没有可靠状态，不代表原生成失败。
- `unknown_submission`：提交超时、异常响应或没拿到 ID，远端可能已创建收费任务。先查 Apixly 记录，不能自动重发。

文件输出支持 PNG、JPEG、WebP、MP4、WebM，每个最多 32 MiB。只下载 Apixly 签名素材地址，不附 API Key、不跟随重定向。链接有有效期，应及时保存到自己的素材库。

视频参数原样发送。一次真实测试请求 `480p`，实际给出 `1280×720`，且网关没有调整说明；应以下载文件解码结果核验交付，不以任务成功推断分辨率。网关返回 `effective_parameters` 或 `parameter_adjustments` 时，插件会保留。

## 数据与支持

插件不增加独立统计、广告、遥测、数据库或本地持久化。Dify 与 Apixly 会按各自政策处理配置、任务、素材和账务。提示词和素材会发给 Apixly，并可能交给实际服务该模型的上游；详见 [隐私说明](PRIVACY.md)。不要提交无权分享的内容。

支持：[support@apixly.ai](mailto:support@apixly.ai)。反馈请带原任务 ID、模型和时间，不要附 API Key。开发和发布步骤见 [英文说明](README.md) 与 `PUBLISHING.md`。
