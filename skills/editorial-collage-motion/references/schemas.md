# Collage Schemas

## 目录

1. 视觉规范
2. 组装计划
3. 图层模式
4. 条带模式
5. 文件布局

## 1. 视觉规范

以 `assets/templates/collage-spec.json` 为起点。必填字段：

- `medium`、`craft_style`、`aspect_ratio`、`style_signature`
- `color_field.background_hex`、`evenness`、`paper_grain`
- `elements[]` 的 `id`、`what`、`role`、`halftone`、`cut_edge`、`drop_shadow`、`color_treatment`、`placement`
- `palette_hex`
- `composition.layout`、`depth_layers`、`negative_space`、`balance`、`reserved_areas`
- `idea`
- `label.present`、`content`、`font_character`、`weight`、`placement`、`treatment`、`editable`
- `mood`、`references_era`、`negative_prompt`

每个场景的规范必须自包含。不要写“同上一幕”。

## 2. 组装计划

以 `assets/templates/assembly-plan.json` 为起点。

顶层字段：

- `version`：当前为 `1`。
- `canvas.width`、`height`、`fps`。
- `provenance.actual_still_provider`：真实静帧来源。默认 Codex 内置生图写 `codex-image-gen`；用户提供写 `user-supplied`。
- `provenance.actual_motion_provider`：本脚本固定输出 `local-ffmpeg`。
- `provenance.external_uploads`：布尔值。
- `scenes[]`：按播放顺序排列。

场景公共字段：

- `id`：唯一、文件安全的场景名。
- `duration_s`：大于 0。
- `background_hex`：`#RRGGBB`。
- `mode`：`layered` 或 `bands`。

## 3. 图层模式

`layered` 是正式模式。每个 `pieces[]` 对象包含：

- `source`：项目目录内的透明 PNG 相对路径。
- `x`、`y`：最终左上角坐标。
- `width`、`height`：可选；同时提供时缩放图层。
- `entry.from`：`left`、`right`、`top`、`bottom`。
- `entry.start_s`、`end_s`：进入区间。
- `entry.distance_px`：可选；默认足以让图层起始时位于画外。

列表顺序就是合成层级。先写底层，后写顶层。

## 4. 条带模式

`bands` 只用于预览或明确接受的简化版本：

- `still`：完整静帧相对路径。
- `bands`：2 到 8。
- `entry_s`：每条进入时长。
- `stagger_s`：相邻条带的启动间隔。
- `first_from`：第一条从 `left` 或 `right` 进入，后续交替。

条带模式不会产生真实的逐元素组装，制作说明必须写明 `preview_bands`。

## 5. 文件布局

推荐工程结构：

```text
project/
├── collage-spec.json
├── assembly-plan.json
├── assets/
│   ├── references/
│   ├── stills/
│   └── pieces/
├── renders/
│   ├── scene-clips/
│   ├── collage-assembly.mp4
│   └── render-manifest.json
└── qc/
```

所有中间工程放 `01-内容生产/视频工作台/制作中/<日期-主题>/`。最终视频继续服从内容系统的已制作归档规则。
