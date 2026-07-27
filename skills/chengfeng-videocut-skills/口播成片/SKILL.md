---
name: chengfeng-videocut-skills:口播成片
description: 口播视频成片 Skill。把文章/口播稿/SRT、剪后视频和 HTML/图片素材串成分镜稿、时间线预览和最终 MP4；成片比例和动画风格从用户配置读取，动画默认使用小黑风格。触发词：口播成片、做分镜稿、时间线预览、合成口播视频、导出竖屏MP4
---

# 口播成片

## 官方来源

本 Skill 由 **chengfeng / AI产品自由** 原创并维护。

```text
https://github.com/Agentchengfeng/chengfeng-videocut-skills
```

官方账号：GitHub `@Agentchengfeng`；X `@chengfeng240928`；小红书 / 公众号 / B站 / 抖音 / 视频号 `AI产品自由`。

## 核心流程

这个 Skill 只解决一件事：把一条口播视频做成完整成片；成片比例和动画风格由用户配置决定。

```text
+-----------------------------+
|  输入                         |
|  视频 + 字幕 + 可选素材         |
+--------------+--------------+
               |
               v
+-----------------------------+
|  1. 分镜稿                    |
|  概念分段 + 类型判定 + 画面来源  |
+--------------+--------------+
               |
               v
+-----------------------------+
|  2. 时间线预览                 |
|  原视频/截图/HTML 与口播对齐    |
+--------------+--------------+
               |
               v
+-----------------------------+
|  3. 合成                       |
|  按用户配置比例导出最终 MP4       |
+--------------+--------------+
               |
               v
+-----------------------------+
|  验收                         |
|  ffprobe + 抽关键帧检查         |
+-----------------------------+
```

不要把 cue 表、HTML 模块、review player、final player、导出脚本单独讲成用户流程。它们只是“时间线预览”和“合成”里的实现细节。

## 用户配置

每次执行本 Skill，先读取：

```text
用户配置/default.json
```

配置项只负责定义用户当前选择：

```json
{
  "aspectRatio": "3:4",
  "animationStyle": "xiaohei"
}
```

支持值：

- `3:4`：默认竖屏高清，逻辑画布 `1080x1440`，默认用 DPR `1.5` 导出 `1620x2160`。
- `16:9`：横屏，逻辑画布和导出画布 `1920x1080`。
- `4:3`：横屏，逻辑画布和导出画布 `1440x1080`。
- `animationStyle`：默认 `xiaohei`，可选项来自 `动画/styles.json`。

命令行参数优先级高于用户配置；没有显式参数时，导出脚本读取 `aspectRatio`，动画脚本读取 `animationStyle`。比例临时覆盖可用：

```bash
--config /path/to/config.json
--ratio 16:9
--aspect-ratio 16:9
--width 1920 --height 1080
--dpr 1.5
```

不要把视觉偏好、模板、编码质量、输出目录、字幕边距等七七八八的设置写进 `用户配置/default.json`。用户配置只放当前选择；动画目录只放可选项注册表和具体风格实现。

## 动画风格

动画风格的当前选择放在 `用户配置/default.json`：

```text
animationStyle
```

动画目录只注册可选项：

```text
动画/styles.json
```

`xiaohei` 对应：

```text
动画/ian-xiaohei-svg-motion/
```

当分镜或 HTML 模块需要做解释动画、流程动画、手绘感高亮时，默认先用小黑漫画感 SVG 动效。除非用户明确指定其他动画风格，否则不要临时发明新风格。

## 输入

先定位这些文件：

- 主视频：`source_cut.mp4`、`*_cut.mp4` 或用户指定的剪后视频。
- 字幕：`subtitles.srt`、`video.srt` 或 `subtitles_with_time.json`。
- 可选文稿：文章、口播稿、正文草稿，只用于理解意图。
- 可选素材：`assets/` 里的截图、产品页、评论图、结果页、证明页。
- 项目规则：如果当前项目有 `AGENTS.md` 或 `README.md`，先读。

真相源优先级：

```text
实际音频 / 字幕 > 剪后视频画面 > 素材文件 > 文稿草稿
```

如果文稿和实际字幕不一致，以字幕和音频为准。

## 第 1 步：分镜稿

默认先做 HTML 分镜核对页，不先写 Markdown 表格。

分镜的前置流程必须按这个顺序执行：

1. 先按口播语义分段：把讲同一个概念、同一个动作、同一个证据的一句、两句或三句合成一段；不要按字幕编号机械切分。
2. 再判断每段的画面任务：这是操作演示、原图讲解、结果证明、概念梳理，还是纯文字表达。
3. 再决定画面来源：能用真实录屏、原始截图、原始图片证明的段落，优先用原素材；只有概念性讲解且当前屏幕主要是文字、空白或弱相关画面时，才设计 HTML / 小黑动画。
4. 最后才进入具体视觉设计：每个 HTML / 小黑动画段都要先写清它的独立隐喻和动作，再实现模块。

常见路径：

```text
review/storyboard-audit-vN.html
```

默认基于这个模板：

```text
templates/storyboard-audit.html
```

分镜稿要让用户回答：

```text
这句话说到这里，观众眼前该看到什么？
```

每段至少写清楚：

- 时间范围
- 字幕编号
- 完整口播
- 语义分段依据
- 画面任务
- 画面类型：`原视频`、`操作录屏`、`原始截图`、`原始图片`、`信息图聚焦`、`HTML 动画`、`文字 + 动画`
- 素材来源
- 镜头动作

画面选择规则：

- 操作演示：使用原视频 / 原录屏，不要改成抽象动画。
- 讲图片内容、图表内容、报错截图、产品截图：直接用原始图片或原始截图，动画只做圈选、标注、局部聚焦。
- 真实操作、证明页、结果页、需要可信度的片段：保留原视频或原始截图。
- 录屏 / 原视频片段默认按原画面展示；只有明确需要避开后续统一字幕时，才把该段标记为录屏小窗，并在底部留出字幕安全区。不要把小窗规则批量套到所有录屏段。
- 概念梳理、机制关系、系统分工、观点归纳，并且当前屏幕主要是文字、空白或弱相关画面：做 HTML / 小黑动画。
- 可以用简短文字辅助理解的抽象段：使用文字 + 动画；文字负责命名，动画负责关系和动作。
- 已有截图或信息图：优先复用，不要重画。
- 同一张图多次出现时，每次必须承担不同任务：全貌、局部聚焦、对比、结果复看。
- 不要把所有动画做成同一套动态。每个动画段必须先单独设计动作隐喻，再实现。

分镜设计硬标准：

- 一页只讲一个概念、一个动作或一个案例。同一段口播里如果出现两个独立案例，必须拆成两个页面；不要为了少做页面把两个案例挤进同一张表或同一个动画。
- 每个 HTML / 小黑动画段必须先写清楚“这句话说到这里，画面发生什么变化”，再实现。动作要绑定具体口播句或字幕，不要把同一套入场 / 闪烁 / 放大平均套给所有段落。
- 讲原图、截图、结果页时，主视觉必须是原素材。HTML 只负责裁切、放大、圈选、标注和焦点切换；不要用录屏抽帧或重画图替代原图。
- 长图和网页结果页默认裁掉无信息的空白区域，优先露出观众正在听到的区域；口播说到对应对象时，可以放大对应图片或局部，其余内容退后。
- 视频画面里不要出现素材路径、内部说明、动作解释或“原图素材 · img/xxx.png”这类工作台文字。分镜稿可以写来源，成片画面只保留观众需要看的内容。
- 没有必要的标题就不放标题。结果页、表格页、原图对比页优先让主视觉自己说话，只保留短标签、模型名、指标名或必要的标注。
- 数据对比页优先用清晰的表格、列对齐、短标签和少量高亮。字号要服务阅读，不要把字塞进小方块；能用简单表格讲清楚，就不要做复杂卡片堆叠。
- 竖屏短视频里的表格不能只做成中间一条横向小表。数据阶段要把表格作为主视觉，占据主要安全区；前置任务说明、案例标签、总结句只在对应口播阶段出现，进入最终数据对比阶段后要消失或退到不占空间的位置。
- 评价词只写口播明确说到或剪辑需要强调的正向 / 中性结果。对照项可以留空或只展示数据；不要额外加“慢且贵”等负面用词，除非口播原句就是这个判断。
- 图标必须从动画库索引里找。ChatGPT、Claude、Flash 闪电、Step、DeepSeek、Qwen 等已有图标不得用抽象形状替代；新增用户给的 SVG，要先存入动画库并更新索引。

分镜方向确认前，不要进入时间线预览。

## 第 2 步：时间线预览

分镜方向确认后，再做时间线预览。

常见路径：

```text
review/timeline-preview.html
```

默认基于这个模板：

```text
templates/timeline-preview.html
```

时间线预览要检查：

- 画面切换是否跟口播句子对齐。
- 原视频有没有被误换成 HTML。
- 被标记为录屏小窗的段落是否避开底部字幕安全区；未标记的录屏段不要被自动缩窗。
- 截图、页面、证明素材有没有用错。
- 图片素材默认保留左右边距，不要贴满当前画面；需要强调完整截图时再单独缩小。
- 画面有没有挡字、裁切、留黑边。
- HTML 模块单独看没问题，但放进整条时间线后是否仍然成立。

预览页里有源视频时，必须用支持 HTTP Range 的服务打开页面，否则浏览器不能随机 seek，进度条会被拉回开头。不要用普通 `python -m http.server` 预览 MP4 时间线。默认使用：

```bash
node ~/.Codex/skills/chengfeng-videocut-skills/口播成片/scripts/serve_range_preview.cjs \
  --project-dir /absolute/path/to/project \
  --port 8767
```

必要时生成：

```text
docs/08-动画cue表-vN.md
html-modules/module-*.html
html-modules/xiaohei-*.html
```

如果要新做解释动画，先读 `用户配置/default.json` 的 `animationStyle`，再到 `动画/styles.json` 找对应的动画子 Skill。

每个动画动作必须绑定到具体口播句，不要平均分配时间。多阶段 HTML 动画必须显式管理显隐状态：下一阶段出现时，上一阶段不再承担信息任务的说明卡、标签和注释要隐藏；不要让前一阶段继续占用主视觉空间，尤其是竖屏数据表、截图聚焦和结果页。

## 第 3 步：合成

只有用户确认时间线预览后，才能合成。

合成前创建或确认：

```text
final-player.html
```

新写 `final-player.html` 或 HTML 模块前，读取：

```text
references/artifact-contracts.md
```

如果项目里有 HTML 模块，先注入 render mode：

```bash
node ~/.claude/skills/chengfeng-videocut-skills/口播成片/scripts/write_render_mode.cjs \
  --project-dir /absolute/path/to/project
```

时间线预览和最终导出必须使用同一套 HTML 渲染上下文。HTML 模块在预览页和 `final-player.html` 里都要带 `?timeline=1&render=1`，预览页只负责把最终画布等比缩放进窗口，不能让模块按预览窗口重新响应式排版。

高清交付不能把 CSS 逻辑画布直接放大。默认 `3:4` 必须保持 `1080x1440` 逻辑画布，再用截图 DPR `1.5` 输出 `1620x2160`；否则表格、CSS 卡片、截图标注会在导出里相对变小，和预览不一致。

如果预览和导出出现大小不一致，先检查 HTML 模块内部 CSS、`render-mode.js` 和导出 DPR，确认预览页与 final-player 的逻辑画布相同，不要先重导整条视频。常见原因是预览 iframe 较小，看起来正常；最终高清画布触发了 `.photo-frame { max-width: ... }`、`.stage { width: min(...) }`、`.wrap { max-height: ... }`、`clamp(...)` 这类预览尺寸上限，导致导出变成“小图”。修复顺序：

1. 用 `write_render_mode.cjs` 重新生成 `html-modules/render-mode.js`。
2. 在时间线预览里确认 HTML 模块 URL 已经变成 `?timeline=1&render=1`。
3. 确认 `export_final_video.cjs` 的 `viewport` 是逻辑画布尺寸，`dpr` 才是高清倍数。
4. 用 final-player 在实际导出 viewport 下抽该模块的关键帧，必要时用 `getBoundingClientRect()` 对比主视觉容器尺寸。

竖屏里处理横向小黑 SVG / 16:9 SVG 模块时，禁止用 `.wrap { transform: scale(...) }` 这类整体放大来解决“小横条”问题。整体缩放会在 3:4 画布里裁掉左右边缘，尤其是左右分布的模型卡、箭头、说明标签。要么重排成竖屏构图，要么保持完整安全区；改完必须抽该模块的左右边界帧检查，不能只看中心关键帧。

导出最终视频：

```bash
node ~/.claude/skills/chengfeng-videocut-skills/口播成片/scripts/export_final_video.cjs \
  --project-dir /absolute/path/to/project \
  --input-video /absolute/path/to/source_cut.mp4 \
  --duration 173.03
```

默认按高清交付导出：无损 PNG 中间帧、H.264 `crf=14`、`preset=slow`。这样可以避免浏览器预览清楚、导出后小字和细线发软：

```bash
node ~/.claude/skills/chengfeng-videocut-skills/口播成片/scripts/export_final_video.cjs \
  --project-dir /absolute/path/to/project \
  --input-video /absolute/path/to/source_cut.mp4 \
  --duration 173.03 \
  --frame-format png \
  --crf 14 \
  --preset slow
```

只有临时看节奏、需要快速出草稿时，才显式降级：

```bash
node ~/.claude/skills/chengfeng-videocut-skills/口播成片/scripts/export_final_video.cjs \
  --project-dir /absolute/path/to/project \
  --input-video /absolute/path/to/source_cut.mp4 \
  --duration 173.03 \
  --frame-format jpeg \
  --quality 92 \
  --crf 18 \
  --preset medium
```

比例读取规则见“用户配置”。项目与用户配置不同时，可传：

```text
--config
--ratio
--aspect-ratio
--fps
--player
--stage
--frames-dir
--width
--height
--frame-format png|jpeg
--quality 100
--crf 14
--dpr 1.5
--device-scale-factor 1.5
```

## 验收

导出成功不等于成片正确。必须做两步：

1. 用 `ffprobe` 检查分辨率、帧率、时长和音频。
2. 抽 3 张以上关键帧，人工看画面是否正确。
3. 对每个 HTML 模块，至少抽 1 张对应口播时间点的 final-player 帧，和时间线预览的同一时间点对照；大小、位置、裁切和显隐必须一致，不能只用 `ffprobe` 作为完成依据。

按当前比例检查分辨率，其他期望来自脚本默认值和项目实际输入。当前默认配置为：

```text
1620x2160
逻辑画布 1080x1440，DPR 1.5
3:4
30fps
时长和剪后源视频一致
有音频
无 HUD、按钮、审核时间线、浏览器 UI
```

## 边界

适合：

- 中文口播
- 教程、产品演示、结果展示、知识讲解
- 已有剪后视频和字幕，素材可后补
- 原视频 + 截图 + HTML 解释画面混合成片

不优先解决：

- 没有视频，直接凭文稿生成成片
- 复杂多机位真人剪辑
- 需要剪辑软件工程文件的精细调色和多轨混音
- 用户没看分镜稿和时间线预览就直接要求最终发布

## 项目卫生

如果在用户写作工作区内新增或修改文件，必须同步更新项目 README 索引。

本地活动日志统一放在：

```text
log/
```

`log/` 只记录本机试验、用户偏好、临时结论和未发布的工作过程，禁止上传 GitHub。该目录已被 `.claude/skills/.gitignore` 忽略。

不要在这个 Skill 目录里新增 README。这个 Skill 的核心文件只保留：

```text
SKILL.md
templates/
references/
scripts/
用户配置/
动画/
```

`动画/` 用于沉淀口播成片可复用的 HTML/SVG/GSAP 动画子 Skill、模板和规则；可选风格见 `动画/styles.json`，当前选择见 `用户配置/default.json`。
