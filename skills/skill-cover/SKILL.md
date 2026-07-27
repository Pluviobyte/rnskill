---
name: skill-cover
description: "Create or revise Chinese social-media covers through the registered Skill-封面 asset system, reusable styles, presenter identities, ratio-specific layouts, and exact replacement prompts. Use only when the user explicitly says“skill-cover”“Skill-封面”“实战风格”, requests the registered style/gesture assets, asks for simultaneous 3:4 and 4:3 registered-layout output, replaces a reference cover's person with the current digital-human frame, or extends this registered cover system. Do not use for a generic“制作封面/生成封面”request; generic cover requests belong to dog-skill."
---

# Skill-封面

统一管理多种封面风格。每种风格拥有独立的双比例基底和视觉合同；人物身份与动作作为共享资产复用。目前已注册 `实战风格`。

## 输入契约

必须取得主标题。接受以下可选参数：

- `style`：风格名称或别名；未指定时使用注册表的 `default_style`。
- `subtitle`：副标题；缺省时保留副标题区域留白，不擅自编造结论。
- `tag`：左上角标签，默认 `AI 实测`。
- `highlight`：需要强调的词组，可重复传入。
- `gesture`：动作预设，默认 `zhengzuo`（正坐）。
- `reference_cover`：任意参考封面；提供时进入“参考封面换人换字”模式。
- `identity_image`：项目数字人/真人身份帧；参考封面模式必填。
- `avatar_video`：原始数字人 master；需要现场截取身份帧时使用。
- `output_dir`：用户指定路径优先。

默认同时输出 3:4 和 4:3。只有用户明确只要一种比例时才减少输出。

## 风格与动作路由

1. 读取 `references/style-registry.json`。
2. 将用户说出的风格名称与 `display_name`、slug 和 `aliases` 匹配。
3. 用户未指定风格时使用 `default_style`。如果参考图明显要求另一种已注册风格，则优先尊重参考图。
4. 读取注册项的 `reference_doc`，只加载所选风格的详细视觉合同。
5. 读取 `assets/shared/gestures/registry.json` 和对应动作的 `manifest.json`；风格只用 `default_gesture` 与 `allowed_gestures` 引用动作，不重复保存动作定义。
6. 未注册的新风格或动作不得假装已存在；分别按“新增风格”和“新增动作”流程建立资产包。

## 制作工作流

1. 判断使用“注册风格”还是“参考封面换人换字”；选择标题、副标题、标签和强调词。
2. 使用内置 `view_image` 查看脚本返回的基底、身份图、动作图和风格参考图。
3. 运行 `scripts/build_prompt.py` 生成每个比例的提示词与绝对参考图路径。例如：

   ```bash
   python3 scripts/build_prompt.py \
     --style shizhan \
     --title '史上最强国产开源模型，Kimi K3完全实测！' \
     --subtitle '真实项目全流程挑战｜综合能力超过 Opus' \
     --highlight 'Kimi K3' \
     --highlight '完全实测'
   ```

4. 使用内置 `imagegen` 能力，每个比例单独调用一次 `image_gen`。禁止将一种比例机械裁剪成另一种比例。
5. 严格按脚本返回的顺序传入参考图：比例基底负责整体构图，共享身份图负责脸、发型和黑 T，共享动作图只负责姿态；动作 manifest 若提供比例构图参考，则下一张图负责人物位置、尺寸和露出范围；最后一张风格参考图负责视觉校准。动作 manifest 的精确构图规则优先于风格中的通用人物范围。
6. 输出后逐张检查。文字错误时只做一次“仅修正文字”的定向编辑，并重新声明身份、动作、构图、背景和色彩不变。
7. 用户指定目录时保存到该目录。属于现有视频项目时保存到项目的 `封面/`，工程中间产物不得进入 `成片/`。
8. 运行 `scripts/validate_cover.py` 检查双比例与基础清晰度，再完成人工视觉质检。

## 参考封面换人换字

当用户要求“截取我的数字人替换图中人物”“照这张封面改成当前项目”或同义动作时：

1. 优先从项目的原始 HeyGen/avatar master 截帧，不从带圆形遮罩、字幕或其他 UI 的最终成片截取。找不到原始 master 时才使用最终成片，并记录降级。
2. 运行候选帧脚本并用 `view_image` 查看 contact sheet：

   ```bash
   python3 scripts/extract_avatar_frames.py <avatar-master.mp4> \
     --out-dir <项目>/封面/avatar-reference
   ```

3. 选择脸部清晰、头发完整、神态自然、无眨眼中间态的帧。身份帧只控制脸、发型、肤色和服装；参考封面只控制背景、材质、配色和编辑层级。
4. 运行参考封面模式：

   ```bash
   python3 scripts/build_prompt.py \
     --reference-cover <参考封面.png> \
     --identity-image <选中的数字人帧.png> \
     --title $'深度测评\nQwen3.8 最新实测' \
     --subtitle '三个真实项目｜能玩、能交互、能验收' \
     --highlight 'Qwen3.8' \
     --highlight '最新实测'
   ```

5. 按脚本返回顺序传图：Image 1 仅作风格/版式参考，Image 2 是唯一人物身份参考。不得继承 Image 1 的人物、眼镜、服装、标题或伪文字。
6. 3:4 与 4:3 必须分别调用一次 `image_gen` 并独立重排；禁止把竖版机械裁成横版。
7. 检查人物身份、全部文字、短边分辨率和精确比例；将最终图存入项目 `封面/`，身份候选帧留在工程归档，不进入 `成片/`。

## 共享资产

- 黑 T 身份：`assets/shared/avatar/black-t-identity.png`
- 动作总注册表：`assets/shared/gestures/registry.json`
- 默认动作“正坐”资产包：`assets/shared/gestures/zhengzuo/`
- 备选动作“摊手”资产包：`assets/shared/gestures/tanshou/`
- 动作规范：`references/gesture-presets.md`

身份图控制脸、发型、肤色和服装。动作资产包独立保存参考图、别名、用途、限制、比例兼容性与构图规则；动作图只能控制姿态，不得覆盖身份图的脸部控制权。比例构图参考只控制人物位置、尺寸和上身露出范围，不得复制其中的旧文字。

## 当前风格

### shizhan｜实战风格

- 风格合同：`references/style-shizhan.md`
- 3:4 基底：`assets/styles/shizhan/base/base-clean-3x4.png`
- 4:3 基底：`assets/styles/shizhan/base/base-clean-4x3.png`
- 3:4 参考：`assets/styles/shizhan/style-reference/style-reference-3x4.png`
- 4:3 参考：`assets/styles/shizhan/style-reference/style-reference-4x3.png`

## 新增风格

新增 `<style-slug>` 时完成全部步骤：

1. 在 `assets/styles/<style-slug>/base/` 放入独立的 3:4 和 4:3 空白基底。
2. 在 `assets/styles/<style-slug>/style-reference/` 放入两张已确认的风格成品。
3. 新建 `references/style-<style-slug>.md`，记录配色、构图、字体、人物位置和禁止项。
4. 在 `references/style-registry.json` 注册显示名、别名、资产路径、比例构图、共享身份、`default_gesture`、`allowed_gestures` 和核心提示语。
5. 用 `scripts/build_prompt.py --style <style-slug>` 测试双比例提示词。
6. 生成一次真实样例并通过比例、身份、文字、手部和视觉一致性质检。

不要复制一整套共享人物到每个风格目录。只有风格确实要求另一位人物时，才为该风格覆盖 `identity`。

## 新增动作

先生成或截取动作候选并交用户确认。确认后在 `assets/shared/gestures/<slug>/` 建立独立资产包，至少包含 `reference.png` 与 `manifest.json`；有明显比例差异时增加 `reference-3x4.png` 和 `reference-4x3.png`。随后登记到 `assets/shared/gestures/registry.json`，再由具体风格通过 `allowed_gestures` 引用。未确认动作不得标记为 `approved`，也不得注册为默认动作。

## 交付质检

至少检查：

1. 两张图分别为精确 3:4 和 4:3，且是独立排版。
2. 所选风格与注册表、风格合同和参考图一致。
3. 黑 T 人物身份一致，位置、比例、手部结构合理。
4. 所有文字逐字正确，无旧标题、伪文字或随机字符。
5. 3:4 建议 1440×1920，4:3 建议 1920×1440；短边不得低于 1000 像素。
6. 无水印、平台 UI、Logo 或未经用户授权的额外文案。
7. 参考封面模式必须确认 Image 1 的原人物、眼镜、服装和旧标题均未残留。

通用提示词规则见 `references/prompt-template.md`。
