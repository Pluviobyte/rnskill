# Provider Boundaries

## 本地默认路径

- 静帧：加载 `imagegen` Skill，固定优先使用 Codex 内置 `image_gen`；用户提供图片时记录为 `user-supplied`。
- 透明图层：仍使用内置 `image_gen` 生成纯色 chroma-key 版本，再用 `$CODEX_HOME/skills/.system/imagegen/scripts/remove_chroma_key.py` 本地抠像并验证 alpha。
- 动画：使用 `local-ffmpeg` 或 HyperFrames。
- 上传：默认无外部上传。
- 来源声明：写明 `compatible_render: true`，不要声称 Arcads、Nano Banana、Seedance 或 Kling 原生输出。

默认链路固定为：参考解码 → Codex `image_gen` 完整静帧 → 用户确认 → Codex `image_gen` 独立图层 → 本地抠像 → FFmpeg/HyperFrames 组装 → QC 和 manifest。

Codex 内置 `image_gen` 生成的项目素材必须复制到项目目录，不能让工程长期引用 `$CODEX_HOME/generated_images/`。内置工具失败时不得自动切换 CLI/API；只有用户明确同意且本机已有 `OPENAI_API_KEY` 才能使用 fallback。

## Arcads 或其他外部路径

只有同时满足以下条件才执行：

1. 用户明确要求使用该提供方或模型。
2. 当前会话实际暴露对应连接器或工具。
3. 已核对当次工具 schema、模型名称、价格和限制。
4. 上传本地文件前已告知用户目的、上传位置和可能费用，并取得确认。

如果只具备提示词，没有连接器，只输出可复制的提示词和 JSON，不伪造调用结果。

## 来源记录

每次交付记录：

```json
{
  "actual_still_provider": "codex-image-gen | user-supplied | arcads-nano-banana-2 | other",
  "actual_motion_provider": "local-ffmpeg | hyperframes | arcads-seedance-2.0 | arcads-kling-3.0-pro | other",
  "external_uploads": false,
  "compatible_render": true,
  "compatible_with": "editorial-collage-motion visual contract"
}
```

只记录实际发生的调用。目标提示词和计划模型放在单独字段，不能覆盖 `actual_*`。
