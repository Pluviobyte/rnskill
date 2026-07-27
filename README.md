# rnskill

[English](README.en.md)

雪踏乌云维护的 AI Agent Skill 全集，适用于 Codex、Claude Code 等支持 `SKILL.md` 的 Agent 工作流。

当前共 **54 个 Skill**，分为两大类：

### 🎬 内容创作（视频 / 图文 / 文章）

用这套 Skill + Codex + HyperFrames + HeyGen + IndexTTS2，过去一个月总投入不到 10 小时，在抖音涨粉 2k 并接到第一个商单。覆盖选题策划、脚本洗稿、AI 配音、数字人、视频编辑、字幕、视觉封面、图文制作、制作调度、视频动效和商业诊断。

### 💻 编码开发

通用编码 Skill，持续补充中。

## RN Cover Skill

`rn-cover-skill` 用标题和主题直接生成 `5:2` 编辑图解风封面，不需要提供参考图。它把创作分成两层：ImageGen 每次重新设计右侧概念图，脚本负责精确排版、暖白背景与可编辑 SVG，因此既能保持家族气质，也不会把某张参考封面的节点和构图反复复制。

![RN Cover Skill 示例](docs/assets/rn-cover-skill-example.png)

- 固定干净的 `#FAF9F5` 暖白画布，中文或混合标题优先
- 左侧文字整体垂直居中；右侧图形根据标题长度主动让位
- 右侧默认保留缩略图可见的细网格；起点、格距、强度和图形位置仍可按内容调整
- 每个新封面重新生成独立图形，最终输出自包含 SVG 与 PNG

调用示例：

```text
使用 $rn-cover-skill 制作 5:2 封面，标题为「开源 Claude 风格封面 Skill」
```

## 前置要求

- 已安装 Codex、Claude Code 或其他支持项目级 Skill 的 Agent
- 目标项目可以读取 `.agents/skills/<skill-name>/SKILL.md`

## 安装

### Claude Code 插件市场

```bash
claude plugin marketplace add Pluviobyte/rnskill
claude plugin install ra-人话@rnskill
```

### 通用安装（Codex / Claude Code）

```bash
npx -y skills add Pluviobyte/rnskill -g --all
```

安装单个 Skill：

```bash
npx -y skills add Pluviobyte/rnskill --skill ra-人话
```

### 手动安装

```bash
# Codex
mkdir -p <project>/.agents/skills
cp -R skills/ra-人话 <project>/.agents/skills/ra-人话

# Claude Code
mkdir -p <project>/.claude/skills
cp -R skills/ra-人话 <project>/.claude/skills/ra-人话
```

## 全部技能一览

标记 `⬡` 的 Skill 来自或改编自外部开源项目，详见表中来源列和底部[致谢](#致谢与改编说明)。

### 选题与策划

| Skill | 说明 | 来源 |
|-------|------|------|
| [`ra-选题`](skills/ra-选题/) | 选题全生命周期：建卡、深化、推荐（对标+自有数据）、立项路由到视频/图文/文章工作台 | 原创 |
| [`ra-实操策划`](skills/ra-实操策划/) | 实操长片策划稿：测试题组、结构时间轴、出镜口播稿、录屏操作清单 | 原创 |
| [`ra-hook`](skills/ra-hook/) | 短视频钩子选型：7 种类型 × 3 大类，带前提条件、句型模板和常见错误 | 原创 |
| [`ra-video-title`](skills/ra-video-title/) | 视频标题生成：主题锁定 → 对标拆解 → 8-12 个两段式候选 + Top 3 推荐 | 原创 |

### 内容创作

| Skill | 说明 | 来源 |
|-------|------|------|
| [`ra-video-wash-pipeline`](skills/ra-video-wash-pipeline/) | 视频洗稿调度器：串联下载 → 逐字稿提取 → 洗稿 → 质量检查 → 排入待制作队列 | 原创 |
| [`ra-逐字稿提取skill`](skills/ra-逐字稿提取skill/) | 从抖音/小红书视频提取逐字稿，去水印 + Paraformer ASR | 原创 |
| [`ra-洗稿`](skills/ra-洗稿/) | 视频脚本洗稿：自动串联 ra-人话 → dbs-ai-check → dbs-hook → dbs-resonate → ra-video-title | 原创 |
| [`ra-人话`](skills/ra-人话/) | 中文去 AI 味写作：硬禁二元对比壳、伪洞察标记、冒号讲义腔，保留作者判断和事实 | 原创 |
| [`ra-公众号提取`](skills/ra-公众号提取/) | 微信公众号文章全文提取，MicroMessenger UA 伪装，纯标准库 | 原创 |

### 视频下载

| Skill | 说明 | 来源 |
|-------|------|------|
| [`ra-video-download`](skills/ra-video-download/) | 从抖音/YouTube/B站/Twitter/小红书下载视频，底层 yt-dlp + TikHub | 原创 |

### 配音

| Skill | 说明 | 来源 |
|-------|------|------|
| [`tts-skill`](skills/tts-skill/) | 本地 IndexTTS2 声音克隆配音，固定无损参考，禁止云端 fallback，留 voice_manifest.json | 原创 |

### 数字人

| Skill | 说明 | 来源 |
|-------|------|------|
| [`heygen-digital-avatar`](skills/heygen-digital-avatar/) | HeyGen Digital Twin 生成与合成：CLI OAuth 认证、圆形裁切布局、音频确认硬门 | 原创 |

### 视频编辑

| Skill | 说明 | 来源 |
|-------|------|------|
| [`ra-local-talking-head-cut`](skills/ra-local-talking-head-cut/) | 本地口播粗剪：ASR 转写 → 剪前校对 → 用户确认 → 语义编辑 → 响度/切点 QC | 原创 |
| [`video-use`](skills/video-use/) | 通用对话式视频编辑：转写、剪辑、调色、叠加动画、烧字幕 | ⬡ [Browser Use](https://cloud.browser-use.com) · MIT |
| [`ai-jian-koubo`](skills/ai-jian-koubo/) | 口播视频转录 + AI 口误识别 + 网页波形审核 + 导出 FCPXML | ⬡ 灵感源自 [chengfeng/videocut-skills](https://github.com/Agentchengfeng/chengfeng-videocut-skills)，重写扩展 · AGPL-3.0 |
| [`chengfeng-videocut-skills`](skills/chengfeng-videocut-skills/) | 乘风口播剪辑原版：转录 → 口误识别 → 审核页 → FCPXML 导出 | ⬡ [chengfeng / AI产品自由](https://github.com/Agentchengfeng/chengfeng-videocut-skills) · Apache-2.0 |

### 字幕

| Skill | 说明 | 来源 |
|-------|------|------|
| [`ra-audio-to-subtitles`](skills/ra-audio-to-subtitles/) | 火山 Doubao-ASR 词级时间戳字幕 + 对齐/碎片/连接词/阅读速度质检 | 原创 |
| [`skill-captions`](skills/skill-captions/) | 字幕外观渲染与烧录：anchor-dark / anchor-light 样式，4K 原生重绘，渲染 QC | 原创 |

### 视觉与封面

| Skill | 说明 | 来源 |
|-------|------|------|
| [`ian-xiaohei-illustrations`](skills/ian-xiaohei-illustrations/) | Ian（伊恩）原版小黑正文配图：纯白手绘、少量红橙蓝批注，把文章中的判断、流程和隐喻画成 16:9 插图 | ⬡ 原作者 [Ian / helloianneo](https://github.com/helloianneo/ian-xiaohei-illustrations) · MIT |
| [`skill-cover`](skills/skill-cover/) | 封面生成：注册风格、双比例资产、自动出图 | 原创 |
| [`editorial-dot-cover`](skills/editorial-dot-cover/) | 点阵编辑风封面：暖灰纸底 + 超大中文标题 + 留白 + 点阵矢量图标，输出 SVG + PNG | 原创 |
| [`editorial-collage-motion`](skills/editorial-collage-motion/) | 半色调纸张拼贴动效：参考拆解 → 静帧生成 → 逐件组装动画 | ⬡ 灵感源自 [Vikash Kumar / Arcads Collage Motion](https://buldrr.com/arcads-collage-motion-skill/)，本地免费兼容版 |

### 图文制作

| Skill | 说明 | 来源 |
|-------|------|------|
| [`xhs-article-to-images`](skills/xhs-article-to-images/) | Markdown 长文转小红书 3:4 图片组，5 套设计皮肤 + 3 个女性向主题 | 原创 |

### 制作调度与质检

| Skill | 说明 | 来源 |
|-------|------|------|
| [`ra-video-production-director`](skills/ra-video-production-director/) | 制作总导演：读交接稿契约 → 调下游 Skill → 管状态/归档/质检 | 原创 |
| [`ra-复盘`](skills/ra-复盘/) | 内容复盘：取数 → 爆款分级(R/M) → 归因 → 资产沉淀 → 选题卡回写 | 原创 |

### 视频动效（HyperFrames）

| Skill | 说明 | 来源 |
|-------|------|------|
| [`rn-motion-director`](skills/rn-motion-director/) | 动效导演：选题/脚本 → 动效视频概念、视觉隐喻、运动语法、Anti-PPT 质量门 | 原创 |
| [`rn-motion-replica`](skills/rn-motion-replica/) | 参考动效复刻：从获授权参考片段构建原创可编辑 HyperFrames 工程 + QC | 原创 |
| [`rn-dark-saas-video`](skills/rn-dark-saas-video/) | 暗色 SaaS 产品视频：8 套场景蓝图、3 种时长预设 | 原创 |
| [`rn-bw-text-opener`](skills/rn-bw-text-opener/) | 黑白打字机开场动画：3 种时长预设，附 Python 时序规划脚本 | 原创 |
| [`rn-replica-qc`](skills/rn-replica-qc/) | 复刻质检：五级保真度 + 素材/运行时/交付三道全帧门 | 原创 |
| [`rn-cover-skill`](skills/rn-cover-skill/) | 无参考图生成编辑图解风封面：自适应左文右图、每次重绘概念图，输出可编辑 SVG + PNG | 原创 |

### dbs 商业工具箱（22 个）

来自 [@dontbesilent](https://x.com/dontbesilent) 的 [dbskill](https://github.com/dontbesilent2025/dbskill) 开源项目，CC BY-NC 4.0 许可。

| Skill | 说明 |
|-------|------|
| [`dbs`](skills/dbs/) | 主入口：任务前路由 + 任务后导航 |
| [`dbs-hook`](skills/dbs-hook/) | 视频开头诊断：和 ra-hook 配对，ra-hook 选类型，dbs-hook 诊断执行 |
| [`dbs-resonate`](skills/dbs-resonate/) | 文稿共鸣诊断：传播心理学框架检查内容能否打中观众 |
| [`dbs-ai-check`](skills/dbs-ai-check/) | AI 写作特征扫描：检测文稿中的 AI 生成痕迹 |
| [`dbs-content`](skills/dbs-content/) | 内容创作诊断：选题通过后诊断怎么做成好内容 |
| [`dbs-spread`](skills/dbs-spread/) | 传播心理解码：5 个传播学理论分析内容为什么能引起共鸣 |
| [`dbs-diagnosis`](skills/dbs-diagnosis/) | 商业模式诊断：问诊（消解问题）和体检（拆解模式）两种模式 |
| [`dbs-benchmark`](skills/dbs-benchmark/) | 对标分析：五重过滤法找值得模仿的对标 |
| [`dbs-goal`](skills/dbs-goal/) | 目标清晰化：维特根斯坦语言哲学审计模糊目标 |
| [`dbs-deconstruct`](skills/dbs-deconstruct/) | 概念拆解：把模糊商业概念拆到原子级别 |
| [`dbs-action`](skills/dbs-action/) | 执行力诊断：阿德勒心理学框架 |
| [`dbs-slowisfast`](skills/dbs-slowisfast/) | 慢就是快诊断：找看起来更慢但长期更快的方法 |
| [`dbs-good-question`](skills/dbs-good-question/) | 好问题生成器：模糊问题 → Agent 可推理的问题说明书 |
| [`dbs-learning`](skills/dbs-learning/) | 交互式学习：按用户反馈调整深度和节奏的连续学习 |
| [`dbs-chatroom`](skills/dbs-chatroom/) | 定向聊天室：按话题推荐专家，模拟多角色对话 |
| [`dbs-chatroom-austrian`](skills/dbs-chatroom-austrian/) | 奥派经济学聊天室：哈耶克 × 米塞斯 × Claude |
| [`dbs-content-system`](skills/dbs-content-system/) | 内容结构化系统：把大量文稿搭成可复用内容工程 |
| [`dbs-decision`](skills/dbs-decision/) | 个人决策系统：长期跟踪领域的本地知识工程 |
| [`dbs-xhs-title`](skills/dbs-xhs-title/) | 小红书图文标题：75 个验证爆款公式 |
| [`dbs-save`](skills/dbs-save/) | 诊断存档：保存当前诊断状态到本地 |
| [`dbs-restore`](skills/dbs-restore/) | 诊断续读：拉取上次保存的诊断状态 |
| [`dbs-report`](skills/dbs-report/) | 诊断报告：打包多次诊断为可交付 Markdown |
| [`dbs-agent-migration`](skills/dbs-agent-migration/) | Agent 工作台迁移：整理成 Claude Code / Codex / Grok 三端一致的工作台 |

## 致谢与改编说明

### dbs 商业工具箱

`dbs` 及全部 `dbs-*` Skill 来自 [@dontbesilent](https://x.com/dontbesilent) 的开源项目 [dbskill](https://github.com/dontbesilent2025/dbskill)，CC BY-NC 4.0 许可。本仓库在原版基础上做了适配，用于视频生产流水线中的内容质量检查环节。

### Ian 原版小黑正文配图

`ian-xiaohei-illustrations` 直接收录原作者 **Ian（伊恩）** 的 [Ian Xiaohei Illustrations](https://github.com/helloianneo/ian-xiaohei-illustrations)，未改造“小黑”角色 IP，按 MIT 许可分发。原作者：[GitHub @helloianneo](https://github.com/helloianneo) · [X @ianneo_ai](https://x.com/ianneo_ai) · [www.ianneo.xyz](https://www.ianneo.xyz/opc)。

### 半色调拼贴动效

`editorial-collage-motion` 灵感源自 Vikash Kumar 的 [Arcads Collage Motion Skill](https://buldrr.com/arcads-collage-motion-skill/)。原版需要 Arcads MCP + Nano Banana + Seedance；本版替换为 Codex 内置生图 + 本地 FFmpeg/HyperFrames 渲染。

### 乘风口播剪辑

`chengfeng-videocut-skills` 来自 chengfeng / AI产品自由 的 [chengfeng-videocut-skills](https://github.com/Agentchengfeng/chengfeng-videocut-skills)，Apache-2.0 许可。

### AI 剪口播

`ai-jian-koubo` 灵感源自 chengfeng 的 videocut-skills，重写扩展了工程导出、前端交互、视频预览、剪辑逻辑和字幕功能。AGPL-3.0 许可。

### 通用视频编辑

`video-use` 来自 [Browser Use](https://cloud.browser-use.com) 的 video-use 项目，MIT 许可。

## 许可证

除另有说明外，仓库采用 CC BY-NC 4.0，详见 [LICENSE](LICENSE)。改编自第三方的内容保留其上游许可。

## 作者

雪踏乌云 · [@Pluvio9yte](https://x.com/Pluvio9yte)
