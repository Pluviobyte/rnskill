# V5 透视网格背景

这是内容创作系统已验收的白底视频背景基线。

工作区的直接调用入口为 `05-视频组件/视频背景/透视网格背景/`；本目录是必须保持同 SHA-256 的 Skill 镜像和跨环境 fallback。

- 推荐循环：`perspective-grid-v5-loop.mp4`
- 可编辑源：`source/`
- 预览：`preview/contact-sheet.png`
- 参数与复用规则：`../../references/perspective-grid-v5.md`

普通视频直接复制 MP4 到项目资产目录，以 `1×` 速度作为全片连续的最底层循环。只有需要修改画幅、配色、几何或速度时才复制 `source/` 分叉；分叉后必须作为新版本重新做循环缝、几何、contact sheet 和媒体规格质检。
