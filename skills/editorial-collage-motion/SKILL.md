---
name: editorial-collage-motion
description: 将参考图或简要描述解码为可编辑的半色调纸张拼贴规范，默认使用 Codex 内置 image_gen 生成品牌一致的静帧和透明图层，再用本地 FFmpeg 或 HyperFrames 制作“从空背景逐件组装”的确定性动态视频。用户提到半色调拼贴、纸张拼贴、剪纸拼贴、编辑式拼贴、杂志拼贴、复古印刷拼贴、拼贴动效、拼贴动画、剪纸动画、纸片组装、逐层组装、从无到有、元素飞入拼装、定格拼贴、定格动画、Arcads 风格、参考图拆解、风格拆解、反向拆解视觉、照这个风格做、做类似的、生成拼贴静帧、让这张图动起来、让这些元素组装起来、制作拼贴广告或拼贴解释视频时使用。英文触发语义包括 editorial collage、halftone collage、paper collage、paper-cut motion、stop-motion graphic、assemble from empty、build-on motion、analyze this、break this down、reverse-engineer this look、generate the stills、animate this、make these move。默认不调用 Arcads、Nano Banana、Seedance 或 Kling；只有用户明确要求且对应连接器可用时才进入外部生成路径。
---

# 半色调拼贴动效

把创作分成两段：先将视觉解码为可编辑规范，再从获批静帧或透明图层构建动画。默认使用本地兼容工作流，真实记录每个生成器和渲染器。

## 选择交付范围

先判断用户要哪一层：

1. 仅分析：交付拆解、通用提示词和 JSON 视觉规范。
2. 仅静帧：完成分析并生成、筛选静帧。
3. 拼贴动效：完成静帧审批后制作无声动画底片。
4. 完整视频：把本 Skill 作为视觉阶段，继续服从视频生产契约、字幕、配音、数字人和归档规则。

缺参考图但用户明确要求“照这张图分析”时，先索取图片。只有简述时，直接草拟规范，不重复询问已知信息。

## 选择执行路径

默认采用本地路径：

- 静帧或图层：加载 `imagegen` Skill，使用 Codex 内置 `image_gen`。不得默认切换到 OpenAI API、CLI 或其他生图模型。
- 简单逐层组装：使用 `scripts/render_assembly.py`。
- 复杂排版、多个转场或组件级时间轴：加载 `hyperframes` Skill，沿用本规范和来源声明。

只有用户明确要求 Arcads、Nano Banana、Seedance 或 Kling，并且对应工具在当前会话可调用时，才读取 `references/provider-boundaries.md` 并进入外部路径。上传本地品牌图、产品图或人物图前，必须说明上传位置、费用和用途并取得用户确认。

不得根据提示词、文件名或预期模型推断实际提供方。未实际调用的模型只能写成“目标提示词”或“兼容风格”，不能写成输出来源。

## 默认生产链路（硬默认）

严格按以下顺序执行：

1. 解码参考图或简述，生成拆解、通用提示词和 JSON 视觉规范。
2. 使用 Codex 内置 `image_gen` 为每幕单独生成完整静帧。品牌图、产品图或人物参考要在所有相关调用中保持可见。
3. 把生成结果从 Codex 默认生成目录复制到工程 `assets/stills/`，不得让工程长期引用 `$CODEX_HOME/generated_images/` 下的文件。
4. 向用户展示完整静帧。用户未明确确认静帧前，禁止生成动画、FFmpeg 组装计划或正式视频。
5. 静帧确认后，使用 Codex 内置 `image_gen` 生成各独立剪纸元素。需要透明 PNG 时，先生成纯色 chroma-key 背景，再调用 `imagegen` Skill 指定的 `remove_chroma_key.py` 本地抠像，并通过 alpha 预检。
6. 使用获批静帧锁定最终构图，用透明图层建立 `assembly-plan.json`，再用本地 FFmpeg 或 HyperFrames 从空背景逐件组装。
7. 完成媒体探针、关键帧检查和来源 manifest。默认记录 `actual_still_provider: codex-image-gen`、`actual_motion_provider: local-ffmpeg` 或 `hyperframes`、`external_uploads: false`。

如果用户直接提供全部静帧或透明图层，把 `actual_still_provider` 改为 `user-supplied`。只有真实发生外部调用时才能填写 Arcads、Nano Banana、Seedance 或 Kling。

## 阶段 A：解码参考

首次解码时完整阅读 `references/visual-contract.md` 和 `references/schemas.md`。按以下顺序输出：

1. `### 拆解`：媒介与工艺、色场、元素与切边、构图与层级、单幕创意、文字、安全区、情绪。
2. `### 通用提示词`：写成不依赖“上图”的自包含自然语言提示词。
3. `### JSON 规范`：从 `assets/templates/collage-spec.json` 复制并填写，保持有效 JSON。

把观察写成可复现参数。例如写“黑白圆点半色调，约 65 lpi，白色细描边，右下 6px 柔和阴影”，不要只写“有纸感”。

多张参考图要分别解码，再补一段共同风格摘要。用户要求“保持外观，只改颜色”时，只改相应字段，但重新输出完整 JSON。

## 阶段 B：规划场景

每幕只保留一个核心创意。为每幕锁定：

- 背景色和画幅。
- 主要元素、辅助元素、层级和最终坐标。
- 文字内容、排版和可编辑方式。
- 从空背景到完整构图的进入顺序。
- 真人、数字人、字幕、Logo 和平台 UI 的避让区。

从 `assets/templates/assembly-plan.json` 建立组装计划。正式成片优先使用 `layered` 模式，每个元素提供一张带透明通道的 PNG。`bands` 模式只是将整张静帧切成条带滑入，只能用于快速预览或用户明确接受的简化版本。

## 阶段 C：生成与审批静帧

加载 `imagegen` Skill，使用 Codex 内置 `image_gen` 先生成或组合完整静帧，再展示给用户审批。保持品牌或产品参考在所有相关生成调用中可见。

本地正式模式按以下顺序工作：

1. 每幕发起一次独立的内置 `image_gen` 调用，生成完整构图静帧；不同场景不要用一次调用拼成大图。
2. 把选中的静帧复制到工程 `assets/stills/`，记录最终提示词和参考图角色。
3. 展示静帧并获得用户明确确认。未确认时只允许调整提示词和重新生成。
4. 确认后再生成独立拼贴元素。按 `imagegen` 的 chroma-key 加本地抠像路径取得透明 PNG，保留白色 keyline 和柔和阴影。
5. 用获批静帧校准图层的大小、坐标和层级。文字默认保留为 HyperFrames、HTML 或 Remotion 的可编辑文本层。
6. 导出场景静帧和图层清单，再进入动画阶段。

内置 `image_gen` 不可用或失败时，不得自动改用 CLI。先告知用户 CLI/API 路径需要 `OPENAI_API_KEY`，只在用户明确同意后切换。

如果只拿到一张完整静帧，可以先用 `bands` 模式做低成本运动预览，但不得把矩形条带滑入描述成真正的“逐元素组装”。

## 阶段 D：本地逐层组装

先验证规范和计划：

```bash
python3 .claude/skills/editorial-collage-motion/scripts/validate_collage.py \
  --spec /absolute/path/collage-spec.json \
  --plan /absolute/path/assembly-plan.json \
  --project /absolute/path/project
```

再渲染无声底片：

```bash
python3 .claude/skills/editorial-collage-motion/scripts/render_assembly.py \
  --project /absolute/path/project \
  --plan /absolute/path/assembly-plan.json \
  --output /absolute/path/project/renders/collage-assembly.mp4
```

动画必须从纯色空场开始，元素按计划从画面边缘进入并落位。禁止用镜头晃动、整图漂移或持续缩放冒充组装。落位后留足可读时间。

## 阶段 E：质检和来源声明

完整阅读 `references/qc-and-provenance.md`，至少完成：

- 媒体探针：尺寸、比例、帧率、时长、编码和可解码性。
- 首帧、每幕落位前后、幕中点和末帧抽查。
- 空场起步、逐件进入、阴影稳定、文字可读、安全区和画面密度检查。
- `render-manifest.json` 与实际输出、输入计划和生成器一致。

在制作说明中明确写出：

- `actual_still_provider`
- `actual_motion_provider`
- `external_uploads`
- 是否属于 `compatible_render`，以及兼容的是哪套视觉规范

当前会话没调用 Arcads MCP 时，固定使用“Arcads 风格兼容渲染”或“editorial collage 本地渲染”，不得写成 Nano Banana 或 Seedance 原生输出。

## 资源

- `references/visual-contract.md`：风格词汇、硬性视觉合同和反例。
- `references/schemas.md`：视觉规范与组装计划字段说明。
- `references/provider-boundaries.md`：本地和外部生成路径的权限与披露边界。
- `references/qc-and-provenance.md`：交付质检和来源记录。
- `assets/templates/collage-spec.json`：可复制的视觉规范模板。
- `assets/templates/assembly-plan.json`：可复制的本地组装计划模板。
- `assets/templates/assembly-plan-bands.json`：只有完整静帧时使用的条带预览模板。
- `scripts/validate_collage.py`：规范、计划和素材预检。
- `scripts/render_assembly.py`：FFmpeg 确定性逐层或条带组装器。
