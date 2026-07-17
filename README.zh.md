# rnskill

中文 | [English](README.md)

雪踏乌云维护的 AI Agent Skills 集合，适用于 Codex、Claude Code 等支持 `SKILL.md` 的 Agent 工作流。

当前覆盖中文写作、内容提取、固定角色插画生成、动效导演、原创参考动效复刻、半色调拼贴动效、风格化视频、片头包装和带逐帧证据的复刻质检。

## 前置要求

- 已安装 Codex、Claude Code 或其他支持项目级 Skill 的 Agent。
- 目标项目可以读取 `.agents/skills/<skill-name>/SKILL.md`。

## 安装

### Claude Code 插件市场

```bash
claude plugin marketplace add Pluviobyte/rnskill
claude plugin install rn-renhua@rnskill
```

### 通用安装（Codex / Claude Code）

```bash
npx -y skills add Pluviobyte/rnskill -g --all
```

安装单个 Skill：

```bash
npx -y skills add Pluviobyte/rnskill --skill rn-editorial-collage-motion
```

### 手动安装

只把需要的 Skill 复制到目标项目即可：

```bash
# Codex
mkdir -p <project>/.agents/skills
cp -R skills/rn-renhua <project>/.agents/skills/rn-renhua
cp -R skills/rn-motion-replica <project>/.agents/skills/rn-motion-replica
cp -R skills/rn-editorial-collage-motion <project>/.agents/skills/rn-editorial-collage-motion
cp -R skills/rn-ian-xiaohei-cat-illustrations <project>/.agents/skills/rn-ian-xiaohei-cat-illustrations

# Claude Code
mkdir -p <project>/.claude/skills
cp -R skills/rn-renhua <project>/.claude/skills/rn-renhua
cp -R skills/rn-motion-replica <project>/.claude/skills/rn-motion-replica
cp -R skills/rn-editorial-collage-motion <project>/.claude/skills/rn-editorial-collage-motion
cp -R skills/rn-ian-xiaohei-cat-illustrations <project>/.claude/skills/rn-ian-xiaohei-cat-illustrations
```

## 可用技能

### 写作精修

| Skill | 说明 |
|-------|------|
| [`rn-renhua`](skills/rn-renhua/) | 中文 AI/技术写作去 AI 味精修。去除二元对比壳、伪洞察标记、冒号讲义腔等 AI 写作模式，保留作者判断和具体事实。 |

### 内容提取

| Skill | 说明 |
|-------|------|
| [`rn-wechat-extract`](skills/rn-wechat-extract/) | 微信公众号文章全文提取。通过 MicroMessenger UA 伪装绕过微信访问控制，纯标准库，无需 API key。 |

### 图像生成

| Skill | 说明 |
|-------|------|
| [`rn-ian-xiaohei-cat-illustrations`](skills/rn-ian-xiaohei-cat-illustrations/) | 为中文文章生成 16:9 白底手绘正文配图，以死认真、略怪诞的小黑猫为固定角色，并通过权威参考图和角色一致性评分保持 IP 稳定。 |

### 视频制作

| Skill | 说明 |
|-------|------|
| [`rn-motion-director`](skills/rn-motion-director/) | AI 动效导演元 Skill。把选题/脚本转化为动效视频概念：视觉隐喻、运动语法、场景节拍图、Anti-PPT 质量门。 |
| [`rn-motion-replica`](skills/rn-motion-replica/) | 从获授权的参考片段构建原创、可编辑的 HyperFrames 动效工程，附参考分析证据和最终 MP4 质检。 |
| [`rn-editorial-collage-motion`](skills/rn-editorial-collage-motion/) | 将参考图或简述拆成可编辑的半色调纸张拼贴规范，使用 Codex 生成并审批静帧，再用本地 FFmpeg 或 HyperFrames 制作“从空背景逐件组装”的确定性动画。 |
| [`rn-dark-saas-video`](skills/rn-dark-saas-video/) | 暗色 SaaS 魔术短片。黑色星空舞台 + 紫色底光 + 大字动效 + 渐变 CTA。8 套场景蓝图、3 种时长预设。 |
| [`rn-bw-text-opener`](skills/rn-bw-text-opener/) | 黑白文字打字机开场动画。纯黑背景 + 白色逐字打字 + 同步音效 + 文字替换效果。3 种时长预设，附带 Python 时序规划脚本。 |

### 视频质检

| Skill | 说明 |
|-------|------|
| [`rn-replica-qc`](skills/rn-replica-qc/) | SOP v2 复刻质检。五级保真度，加上素材、运行时、交付三道全帧门；逐帧重放与参数化动效分别入库。 |

## 目录结构

```text
rnskill/
├── skills/
│   ├── rn-renhua/              # 写作：去 AI 味精修
│   ├── rn-wechat-extract/      # 提取：微信公众号文章
│   ├── rn-motion-director/     # 视频：动效导演
│   ├── rn-motion-replica/      # 视频：原创可编辑动效复刻
│   ├── rn-editorial-collage-motion/ # 视频：半色调拼贴组装动效
│   ├── rn-ian-xiaohei-cat-illustrations/ # 图像：小黑猫正文配图
│   ├── rn-dark-saas-video/     # 视频：暗色 SaaS 风格
│   ├── rn-bw-text-opener/      # 视频：黑白打字开场
│   └── rn-replica-qc/          # 质检：参考视频复刻
├── docs/                       # 各 Skill 概览页
├── assets/                     # 展示图片和视频
├── tools/                      # 打包和构建脚本
├── .claude-plugin/             # Claude Code 插件市场清单
└── .github/workflows/          # 发布自动化
```

## 维护同步

四个镜像视频 Skill 以 `Pluviobyte/video-production-skills` 为开发源。下面的命令只刷新这些镜像，不会覆盖 `rn-renhua`、`rn-motion-replica` 等 `rnskill` 原生 Skill：

```bash
python3 tools/sync-video-skills.py --source /path/to/video-production-skills
python3 tools/sync-video-skills.py --source /path/to/video-production-skills --check
```

## 致谢与改编说明

### 小黑猫正文配图

`rn-ian-xiaohei-cat-illustrations` 来源于 Ian 的原版 [Ian Xiaohei Illustrations](https://github.com/helloianneo/ian-xiaohei-illustrations)，也就是原始 Xiaohei Skill（小黑 Skill）。当前版本保留了文章认知锚点分析、shot list、16:9 白底手绘视觉系统、构图方法和校准样例，并将原版黑色“小黑”角色进一步改造成固定“小黑猫”IP，增加权威角色参考图和更严格的身份一致性质检。原项目采用 MIT 许可，完整版权与许可证保留在 [`origin-and-license.md`](skills/rn-ian-xiaohei-cat-illustrations/references/origin-and-license.md)。本改编版不是 Ian 发布的官方版本。

### 半色调拼贴动效

`rn-editorial-collage-motion` 是基于 Vikash Kumar 原版 [Arcads Collage Motion Skill](https://buldrr.com/arcads-collage-motion-skill/) 思路制作的独立改编版。感谢 Vikash Kumar 提出的两阶段工作流：先把参考视觉解码为可编辑规范，再把获批的拼贴静帧做成“从无到有”的逐件组装动画。

原版工作流需要连接 Arcads MCP 并消耗 Arcads credits，静帧和视频分别使用 Nano Banana 2 与 Seedance 2.0。本仓库版本保留参考拆解、可编辑 JSON 规范、静帧审批和逐层组装逻辑，但将执行链路优化为 Codex 内置生图，加本地 FFmpeg 或 HyperFrames 渲染。因此它不需要 Arcads MCP，也不消耗 Arcads credits；对于已经可以使用 Codex 的用户，这是一个本地免费兼容版，但仍受用户自身 Codex 使用权限和本机算力条件影响。本改编版不是 Arcads 或原作者发布的官方版本。

## 许可证

除另有说明外，仓库采用 CC BY-NC 4.0，详见 [LICENSE](LICENSE)。改编自第三方的内容继续保留其上游许可；小黑 Skill 衍生文件中的 Ian MIT 许可见 [`origin-and-license.md`](skills/rn-ian-xiaohei-cat-illustrations/references/origin-and-license.md)。

## 作者

雪踏乌云 · [@Pluvio9yte](https://x.com/Pluvio9yte)
