# 动作资产治理

动作是独立于人物身份和封面风格的一等资产。机器可读真源为：

- 总注册表：`assets/shared/gestures/registry.json`
- 单动作资产包：`assets/shared/gestures/<slug>/`
- 单动作元数据：`assets/shared/gestures/<slug>/manifest.json`

本文件只记录治理规则，不重复维护动作别名、描述、构图和限制，避免与 manifest 产生双真源。

## 当前已批准

- `zhengzuo`｜正坐：默认动作，包含通用动作参考与 3:4、4:3 独立构图参考。
- `tanshou`｜摊手：包含通用动作参考，双比例共用。

风格不得复制动作定义，只能通过 `default_gesture` 和 `allowed_gestures` 引用动作 ID。

## 新动作注册流程

1. 从黑 T 数字人视频截取候选，或使用身份图生成姿态候选。
2. 保持脸、发型、黑 T 和体型不变，只改变手臂与手势。
3. 先输出动作候选预览，不直接写入 Skill。
4. 用户明确确认后，新建 `assets/shared/gestures/<slug>/`，保存 `reference.png`；如比例差异明显，再保存 `reference-3x4.png` 和 `reference-4x3.png`。
5. 建立 `manifest.json`，登记 ID、显示名、别名、状态、资产、用途、限制、构图规则、人物兼容性和支持比例。
6. 在 `assets/shared/gestures/registry.json` 注册 manifest。
7. 在需要使用该动作的风格中，把动作 ID 加入 `allowed_gestures`；需要时设为 `default_gesture`。
8. 运行 `scripts/build_prompt.py --list-gestures` 和真实双比例样例验证。

计划中的动作名称可以包括 `single-hand-emphasis`、`point-to-title`、`result-emphasis`，但在没有用户确认资产前均不可标记为 `approved` 或投入生产。
