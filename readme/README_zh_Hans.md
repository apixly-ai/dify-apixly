<p align="center">
  <img src="https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/cover.png" alt="Apixly 媒体插件：在 Dify 中生成图片、编辑参考图、创建视频并下载原任务文件" width="1200" />
</p>

# Apixly Media：把图片和视频接进 Dify 工作流

用自己的 Apixly API Key 在 Dify 中生图、编辑参考图和生成视频。每个生成阶段只提交一次，再查询原任务，将成品作为 Dify 文件交给后续节点。

**[下载插件与工作流](https://github.com/apixly-ai/dify-apixly/releases/latest)** · **[创建 API Key](https://platform.apixly.ai/keys)** · **[模型与价格](https://platform.apixly.ai/models)** · **[打开控制台](https://platform.apixly.ai/)**

[官网](https://apixly.ai/) · [API 文档](https://apixly.ai/docs) · [English](../README.md) · [支持邮箱](mailto:support@apixly.ai) · [Marketplace 提交记录](https://github.com/langgenius/dify-plugins/pull/3481)

**插件免费，API 按 Apixly 账号实际用量计费。** 本插件由 Apixly 维护，不代表底层模型开发商。

## 看实际效果

下面是已授权 API 验收的真实产物。在这次 `gemini-3.1-flash-image` 参考图编辑中，蓝杯的颜色、形状和把手得到保留，背景改为灰色摄影棚场景。

| 参考图 | 编辑结果 |
| --- | --- |
| <img src="https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/reference-cup.jpg" alt="原始蓝色陶瓷杯，浅色桌面背景" width="420" /> | <img src="https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/edited-cup.png" alt="真实编辑结果：保留蓝杯与把手，替换为灰色摄影棚背景" width="420" /> |

| 文生视频 | 图生视频 |
| --- | --- |
| <img src="https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/text-video-still.png" alt="真实文生视频的静帧：落日中的海边灯塔" width="420" /> | <img src="https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/image-video-still.png" alt="真实图生视频的静帧：保留源图中的蓝色玻璃花瓶" width="420" /> |
| [查看真实文生视频](https://github.com/apixly-ai/dify-apixly/blob/apixly/docs/assets/text-video.mp4) · 1280 × 720，约 1 秒 | [查看真实图生视频](https://github.com/apixly-ai/dify-apixly/blob/apixly/docs/assets/image-video.mp4) · 960 × 960，约 3 秒 |

上方视频图片是对应成品的静帧；实际效果取决于所选模型、提示词与支持的参数。该图生视频模式跟随参考图尺寸。[素材来源与 SHA256](https://github.com/apixly-ai/dify-apixly/blob/apixly/docs/assets/provenance.json)。

## 选择一份入门工作流

<img src="https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/workflow-map.png" alt="四份可导入工作流示意图：文生图、参考图编辑、文生视频、图片衔接图生视频" width="1200" />

| 工作流 | 准备什么 | 每次运行的生成提交 |
| --- | --- | --- |
| [文生图](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-image-workflow.yml) | 产品或创意描述 | 1 次图片生成 |
| [参考图编辑](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-edit-workflow.yml) | 一张图、可选更多参考图、修改要求 | 1 次图片编辑 |
| [文生视频](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-video-workflow.yml) | 场景描述与模型支持的时长 | 1 次视频生成 |
| [图片衔接图生视频](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-image-to-video-workflow.yml) | 图片描述与后续视频要求 | 1 次图片 + 1 次视频生成 |

每阶段均为：只提交一次 → 得到任务 ID → 有界查询 → 返回原任务文件。只读查询与恢复下载不会重新生成；API 费用以当前模型价格为准。

## 创作控制：先免费预览

另行安装 [Apixly Creative Controls](https://github.com/apixly-ai/dify-apixly-creative)，即可在 Dify 中免费预览角度、打光和相机镜头观感，无需账号或 Key，不发起生成。**启用所需组 → 选择预设或数值 → 查看 final_prompt → 确认后连接生成/编辑。** 推荐 Studio 流程拆为 **视角、打光、相机与镜头** 三张小卡，再连接 **组合提示词**，每张卡只显示自身字段。三组默认关闭；没有有效指令时逐字保留原文。这些参数形成 AI 创作指令。

<img src="https://raw.githubusercontent.com/apixly-ai/dify-apixly-creative/apixly/docs/assets/studio-workflow-desktop.png" alt="真实 Dify 免费预览：视角、打光、相机镜头连接组合提示词与成功判断" width="1200" />

*真实 Community 1.17.1 免费预览编辑器，控制组默认关闭。[原生 UI 验证与宿主限制](https://github.com/apixly-ai/dify-apixly-creative/blob/apixly/docs/QA.md)。此截图不代表账号授权或付费媒体效果已经通过。*

| 新增工作流 | 作用 | 生成提交 |
| --- | --- | --- |
| [免费创作预览](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-studio-preview-workflow.yml) | 只展示最终提示词；仅依赖免费伴随插件 | 0 |
| [创作生图](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-studio-image-workflow.yml) | 合成指令 → 校验 → 生图 → 返回文件 | 1 次生图 |
| [创作编辑](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-studio-edit-workflow.yml) | 明确修改要求，并保留未请求修改的主体细节 | 1 次编辑 |
| [创作视频](https://github.com/apixly-ai/dify-apixly/blob/apixly/examples/apixly-studio-video-workflow.yml) | 合成指令 → 校验 → 视频 → 返回文件 | 1 次视频 |

后三份依赖两个精确版本的插件。无效指令在收费节点前停止；结构化分组仍保留在预览节点供后续接线，用户结果页只显示最终提示词或安全错误提示。

原单面板创作工具及其四份旧创作流程继续兼容，原四份媒体流程也保留。打光明确选择命名光向或坐标模式，空坐标不会自动变成 0。

## 安装和连接

1. 登录 Apixly 控制台，按需充值，在 Key 页面创建具有所需图片/视频模型权限的 API Key。运行前先查看模型价格和能力。
2. 在 Dify 插件页面安装发布的 `.difypkg`，或安装经过市场审核的版本。自行上传的开发包不等于已通过 Marketplace 审核；自托管 Dify 默认会校验签名，按 Dify 官方说明为自己的受控环境配置签名。
3. 在 Apixly 媒体提供商中填写 **Apixly API Key**。这是 secret credential，不要放进提示词、JSON 参数或公开 DSL。验证只查询模型列表，不会生成收费素材。
4. 允许访问 `apixly.ai:443`；签名素材下载还可能访问 `platform.apixly.ai:443`。插件直连 `https://apixly.ai/v1`，不需要 MCP 凭证。

### 可选账号授权

当前开发候选版包含 OAuth 账号连接；部署和真实授权验收仍是发布门槛。工作区管理员先在 [Apixly 连接设置](https://apixly.ai/integrations) 注册 Dify 应用，填写 **Dify 显示的精确回调地址**，再把客户端 ID 与一次性密钥填入 Dify 的私有 OAuth 客户端设置。插件不内置共享密钥。

用户点击 **Authorize**，通过 Apixly 正常网站登录，选择 **Studixly Key（默认）** 或自己已有的其他有效 Key。插件只接收可撤销的连接凭据，不保存网站密码、完整登录 JWT 或底层裸 Key。完整 Key 下拉在网站授权页；Dify 原生凭据选择器用于切换已保存的连接。要绑定不同或新的 Key，请重新授权，在 Apixly 中选择该 Key，然后在 Dify 中选择对应的已保存连接。Dify 会自动命名 OAuth 凭据，可手动改为 `Apixly · studixly-key`，账号与脱敏 Key 信息保留在详情中。

### 选模型与刷新

打开媒体节点时，按当前凭据加载 **模型目录**；也可以填写 **手填精确 ID（优先于下拉）**。手填非空时明确优先、原样发送；两个都未填则在提交前报错。现有示例 DSL 始终显式指定型号。

独立 **刷新模型目录** 工具只读更新型号和能力，返回旧数据/错误状态，不创建生成任务；刷新后重新打开媒体节点可查看新选项。目录按需加载，十分钟缓存并后台更新，失败时保留并标明旧数据。图片按 API 的明确类型筛选；缺少能力数据的视频型号仍显示该限制，不编造参数支持。缓存按凭据隔离、每个进程独立，其他工作进程各自更新。

价格示例：2026-10-23 核验的 `gemini-3.1-flash-image` 1K 生图为每张 US$0.02。请按所选模型与参数查看[当前模型价格](https://platform.apixly.ai/models)。

本插件与示例工作流已在自托管 Dify Community 1.17.1 安装运行；其他版本和 Dify Cloud 尚未完成验收。运行时为 Python 3.12、`dify-plugin==0.10.2`。

## 原生 Dify 界面

<img src="https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/dify-reference-editor-zh-Hans.png" alt="真实 Dify Community 中文工作流编辑器，展示 Apixly 参考图编辑字段" width="1200" />

截图来自已验收的原媒体插件，包含中英文字段名称。原媒体插件与四份媒体 DSL 已在自托管 Dify Community 1.17.1 安装、运行和发布；Dify Cloud 尚未完成验收。[查看图片衔接视频的真实工作流截图](https://raw.githubusercontent.com/apixly-ai/dify-apixly/apixly/docs/assets/dify-image-video-workflow.png)。

## 媒体与目录工具

| 工具 | 用法 | 返回 |
| --- | --- | --- |
| 生成图片 | 选择精确模型、写提示词，可设数量、比例、尺寸、质量 | 原图片任务 ID |
| 参考图编辑 | 粘贴一张 URL 或 base64 data URL，可补更多参考图 | 原图片任务 ID |
| 生成视频 | 设置模型、秒数、分辨率、画幅；额外参数可用 JSON | 原视频任务 ID |
| 查询媒体任务 | 使用原任务类型与 ID，可选择返回 Dify 文件 | 状态、成功标记、链接或文件 |
| 刷新模型目录 | 只读刷新当前凭据的模型和视频能力 | 型号、旧数据/错误状态；零推理调用 |

常用字段有中英文名称。可从目录选择或手填精确 ID；改变型号后，请根据该模型能力调整参数。模型 ID 原样发送，失败时不会自动换模型。高级 JSON 与界面同名字段如有冲突，会在收费提交前明确报错。

编辑时，`reference_image` 可直接粘贴一张图；`reference_images` 是补充图片的 JSON 数组，如 `["https://example.com/second.png"]`。base64 必须带 MIME 前缀，例如 `data:image/png;base64,...`；不能填本地路径。每张 base64 图片最多 20 MiB，插件最多传 16 张，各模型可能支持更少。入门编辑 DSL 的每个参考图输入字段最多 1,048,576 字符；更大素材请用 HTTPS URL，或从上游文件/变量节点传入。

## 导入工作流

`examples/` 提供文生图、参考图编辑、视频生成，以及图片衔接图生视频四份 `.yml`。先安装对应包并设置 secret Key，再从 Dify 的 **导入 DSL 文件** 导入。

每份流程均为：**只提交一次 → 有任务 ID 才继续 → 最多查询 60 次，每次先等 5 秒 → 查询并返回原任务文件**。生成节点关闭自动重试。到达上限仍未完成时，返回原任务的当前状态和 ID，不会重新生成。宿主导入与运行记录见源码 `PUBLISHING.md`；仅解析 YAML 或本地测试不代表宿主验收。

组合流程的 JSON 安全模板节点需要 Dify 标准 sandbox 服务。组合流程先生成图片，将其签名 HTTPS URL 以 JSON 安全编码衔接到显式选择的 `grok-imagine-video-1.5-preview`（3 秒，跟随源图尺寸）。图片未交付则停止。此流程有两次按量计费的生成调用，每阶段各提交一次，不自动换模型。默认 `grok-imagine-video` 仅文生视频；1.5 preview 参考图只收公开 HTTPS URL，不支持内联 base64；该参考模式跟随源图尺寸，分辨率、比例与 size 请留空，显式填写会报错而非静默忽略。文生视频示例仍明确填写已验的 720p、16:9。

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

插件不增加独立统计、广告、遥测、数据库或本地持久化。Dify 与 Apixly 会按各自政策处理配置、任务、素材和账务。提示词和素材会发给 Apixly，并可能交给实际服务该模型的上游；详见 [隐私说明](../PRIVACY.md)。不要提交无权分享的内容。

支持：[support@apixly.ai](mailto:support@apixly.ai)。反馈请带原任务 ID、模型和时间，不要附 API Key。开发和发布步骤见 [英文说明](../README.md) 与 `PUBLISHING.md`。
