# 通用提示词模板

优先运行 `scripts/build_prompt.py`，让脚本根据 `style-registry.json` 和独立动作资产注册表 `assets/shared/gestures/registry.json` 填充风格、动作、比例和资产路径。手工构造时必须保留下面的参考优先级。

```text
Use case: compositing
Asset type: Chinese social-media video cover
Selected style: {style_display_name} ({style_slug})

Reference roles:
- Image 1 is the ratio-specific clean base and controls layout and graphic structure.
- Image 2 is the only identity reference and controls face, hair, skin tone and clothing.
- Image 3 controls gesture only; it must not change identity.
- When the selected gesture manifest provides a ratio-specific framing reference, Image 4 controls
  presenter position, scale and visible body range only, and Image 5 is style calibration.
- Otherwise Image 4 is style calibration only.

{style_prompt_core}
{ratio_composition}

Render text verbatim with no extra characters:
Tag: "{tag}"
Title: "{title}"
Subtitle: "{subtitle}"

Keep the presenter identity, hands, mobile-thumbnail legibility and safe margins correct.
No watermark, logo, platform UI, old text, pseudo-text or random glyphs.
```

动作 manifest 的比例构图规则优先于风格合同中的通用人物范围；风格仍控制背景、纸张、文字区和整体视觉层级。

若副标题为空，写：`Do not render a subtitle; keep the subtitle zone blank.`

修改错字时只做单点编辑：

```text
Change only the incorrect text to "{exact_text}". Keep the selected style, presenter identity,
pose, hands, background, layout, colors, paper, shadows and every other element unchanged.
Remove the incorrect characters completely. Add no other text.
```

## 参考封面换人换字

使用 `scripts/build_prompt.py --reference-cover ... --identity-image ...` 生成，参考顺序固定：

```text
Use case: identity-preserve compositing
Image 1: style/layout only; never copy its person or old text.
Image 2: the only identity reference; preserve face, hair, skin tone and clothing.

Create an independent exact {ratio} redesign.
Replace all old copy with the exact tag/title/subtitle.
No inherited person, glasses, clothing, old words, pseudo-text or random glyphs.
```

项目数字人身份帧应来自原始 master，并先用 `scripts/extract_avatar_frames.py` 生成候选帧和 contact sheet。
