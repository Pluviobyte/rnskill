# 生图提示词模板

每张图单独生成。根据正文内容替换变量，不要把多张图拼在一起。

```text
Generate one standalone 16:9 horizontal Chinese article illustration.

Visual DNA:
Pure white background. Minimalist black hand-drawn line art. Slightly wobbly pen lines. Lots of empty white space. Sparse red/orange/blue handwritten Chinese annotations. Clean absurd product-sketch feeling. No gradients, no shadows, no paper texture, no complex background, no commercial vector style, no PPT infographic look, no cute mascot poster, no children's illustration, no realistic UI.

Input image role:
Use `assets/ip-reference/00-source-safety-audit-cat.png` as the authoritative character identity reference. Match the cat closely, but do not copy its clipboard, control knob, machine, text, or composition. Use `assets/ip-reference/01-approved-simple-funnel-cat.png` only if a second reference is needed for sparse layout and white space, never for identity.

Recurring IP character required:
小黑猫, the same working cat from the authoritative reference: a large slightly asymmetric solid-black cat head about 1.25-1.5 times the torso width, a smaller narrow black body, one pointed ear taller and more upright while the other is slightly lower and angled outward, two enormous close-set vertical white oval eyes filling about half the face, black oval pupils occupying about one third of each white eye and both shifted in the same looking direction, compact thick arms no longer than the torso, short legs, mitten-like paws, blank serious deadpan expression, and a slightly uneven hand-drawn outline. No mouth, no smile line, no nose, no whiskers, no highlights, no eyelashes. Preserve the recognizable large-head/small-body ratio; do not merge the head and torso into a rounded bean mascot or enlarge the head to twice the torso width. 小黑猫 must perform the core conceptual action, not decorate the scene. Keep the scene simple without weakening character identity.

Theme:
{正文配图主题}

Structure type:
{结构类型：Workflow / 系统局部 / 前后对比 / 角色状态 / 概念隐喻 / 方法分层 / 地图路线 / 小漫画分镜}

Core idea:
{这张图要表达的核心意思}

Composition:
{具体画面：小黑猫在哪里、正在做什么、主要物件是什么、信息如何流动}

Suggested elements:
{元素1} / {元素2，最多 1-2 个主要物件}

Chinese handwritten labels:
{标注词1} / {标注词2} / {标注词3} / {可选标注词4} / {可选标注词5}

Color use:
Black for main line art and 小黑猫. Orange for main flow/path/arrows. Red only for key warnings/problems/results. Blue only for secondary notes or feedback/system state.

Constraints:
One image explains only one core structure. Use one 小黑猫 by default; use 2-3 only for before/after or comic panels. Keep the main subject around 35%-55% of the canvas. Preserve at least 45% blank white space. Use at most 3-5 short handwritten Chinese labels. Use only 1-2 main props. Character identity matters more than prop detail. Match the authoritative reference on silhouette, eye geometry, head/body ratio, limbs, expression, and black-fill hand-drawn treatment. Avoid generic black cats, rounded bean mascots, same-width head and torso, perfectly symmetric ears, small or circular eyes, centered pupils, mouth or smile lines, nose, whiskers, highlights, long limbs, four-legged posture, complex machines, multi-screen dashboards, lab scenes, office desk scenes, dense panels, many arrows, many nodes, and full video-page compositions. Do not write a title in the top-left corner. Do not write the structure type on the image. Do not make it a formal diagram, course slide, or dense explainer. Do not copy prior examples or reuse known case compositions unless explicitly requested; invent a fresh visual metaphor for this specific article. It should be clear but not instructional, interesting but not childish, strange but clean.
```

## 图像编辑提示

去掉左上角标题：

```text
Edit the provided image. Remove only the handwritten title "{要删除的文字}" and its underline from the top-left corner. Fill that area with the same clean white background, matching the surrounding blank paper. Preserve everything else exactly: characters, labels, paths, line style, composition, aspect ratio, and image quality. Do not add any new text or objects.
```

增强怪诞感：

```text
Regenerate this illustration with the same core meaning and a much simpler layout. Match the character in `assets/ip-reference/00-source-safety-audit-cat.png`: large slightly asymmetric black cat head, smaller narrow body, enormous close-set vertical white oval eyes, same-direction offset black pupils, short thick limbs, no mouth/nose/whiskers, deadpan working-cat posture. Keep 1-2 props, 3-5 short labels, large blank space, and do not copy the reference scene.
```
