---
name: chengfeng-videocut-skills:剪口播
description: 口播基础素材包生成。转录口播、识别口误、生成审核页；用户确认后剪出新视频，Agent 再基于剪后视频重新转写、AI 校对字幕，输出后续口播成片可用的 source_cut.mp4 和 subtitles.srt。触发词：剪口播、处理口播素材、准备口播素材、识别口误、基础素材包
author: chengfeng / AI产品自由
source: https://github.com/Agentchengfeng/chengfeng-videocut-skills
official_accounts: GitHub @Agentchengfeng；X @chengfeng240928；小红书/公众号/B站/抖音/视频号 @AI产品自由
---

<!--
input: 视频文件 (*.mp4)
output: subtitles_words.json、auto_selected.json、review.html、剪后视频、video.raw.srt、AI 校对后的 video.srt/subtitles.srt
pos: 口播素材准备入口；默认完成粗剪 + 剪后字幕校对

架构守护者：一旦我被修改，请同步更新：
1. ../README.md 的 Skill 清单
2. /CLAUDE.md 路由表
-->

# 剪口播 v3

> 火山引擎转录 + AI 口误识别 + 网页审核 + 剪后重转写 + AI 字幕校对

## 快速使用

```
用户: 帮我剪这个口播视频
用户: 处理一下这个视频
用户: 把这条录屏做成基础素材包
```

不要再把字幕生成拆成单独 Skill。`剪口播` 是口播基础素材包的唯一入口。

用户给一条口播录屏后，本 Skill 默认产出后续 `口播成片` 可直接使用的基础素材包：

```text
source_cut.mp4       # 剪后口播视频
subtitles.srt        # 基于剪后视频重新转写并 AI 校对后的字幕
assets/              # 可选截图、评论图、结果页
```

审核页只负责让用户确认“删哪里”并剪出新视频。字幕不能沿用原始视频字幕，也不能把火山转写初稿直接当最终字幕；Agent 必须基于剪后视频重新转写，并做 AI 校对后，才能写入 `subtitles.srt`。

## 输出目录结构

```
output/
└── YYYY-MM-DD_视频名/
    ├── 剪口播/
    │   ├── 1_转录/
    │   │   ├── audio.mp3
    │   │   ├── volcengine_result.json
    │   │   └── subtitles_words.json
    │   ├── 2_分析/
    │   │   ├── readable.txt
    │   │   ├── auto_selected.json
    │   │   └── 口误分析.md
    │   └── 3_审核/
    │       ├── review.html
    │       └── video.mp4 → 源视频(符号链接)
    └── 字幕/
        ├── 1_转录/
        │   ├── audio.mp3
        │   └── volcengine_result.json
        ├── subtitles_with_time.json
        └── 3_输出/
            ├── video.raw.srt
            └── video.srt
```

**规则**：已有文件夹则复用，否则新建。

## 流程

```
0. 创建输出目录
    ↓
1. 提取音频 (ffmpeg)
    ↓
2. 调用火山引擎录音文件识别 2.0（Seed ASR v3）
    ↓
3. 生成 volcengine_result.json
    ↓
4. 生成字级别字幕 (subtitles_words.json)
    ↓
5. AI 分析口误/静音，生成预选列表 (auto_selected.json)
    ↓
6. 生成审核网页 (review.html)
    ↓
7. 启动审核服务器，用户网页确认
    ↓
【等待用户确认】→ 网页点击「执行剪辑」
    ↓
8. 服务器只剪出新视频
    ↓
9. Agent 监听剪后视频生成完成
    ↓
10. 基于剪后视频重新提取音频，发火山转写，生成 video.raw.srt
    ↓
11. Agent 对照原稿/正文做 AI 校对，写 video.srt
    ↓
12. 整理基础素材包：source_cut.mp4 + subtitles.srt + 可选 assets/
```

剪后字幕硬规则：

- 必须基于剪后视频重新转写，不能用原始视频字幕反推。
- 火山转写只是初稿，输出到 `video.raw.srt`。
- `video.srt` / `subtitles.srt` 只能是 Agent AI 校对后的最终字幕。
- 校对时对照用户给的口播稿、正文、专名和上下文，修正术语、同音误识别、断句；不能添加视频里没说的话。

## 执行步骤

### 步骤 0: 创建输出目录

```bash
# 变量设置（根据实际视频调整）
VIDEO_PATH="/path/to/视频.mp4"
VIDEO_NAME=$(basename "$VIDEO_PATH" .mp4)
DATE=$(date +%Y-%m-%d)
BASE_DIR="output/${DATE}_${VIDEO_NAME}/剪口播"

# 创建子目录
mkdir -p "$BASE_DIR/1_转录" "$BASE_DIR/2_分析" "$BASE_DIR/3_审核"
cd "$BASE_DIR"
```

### 步骤 1-3: 转录

```bash
cd 1_转录

# 1. 提取音频（文件名有冒号需加 file: 前缀）
ffmpeg -i "file:$VIDEO_PATH" -vn -acodec libmp3lame -y audio.mp3

# 2. 调用火山引擎录音文件识别 2.0（默认 resource_id=volc.seedasr.auc）
SKILL_DIR="/Volumes/成峰/代码/剪辑Agent/.claude/skills/剪口播"
"$SKILL_DIR/scripts/volcengine_transcribe.sh" audio.mp3
# 输出: volcengine_result.json
```

转录脚本默认使用火山 v3 Seed ASR 2.0：

```text
POST /api/v3/auc/bigmodel/submit
POST /api/v3/auc/bigmodel/query
X-Api-Resource-Id: volc.seedasr.auc
```

如果要临时回退或对比其他资源，可用环境变量覆盖：

```bash
VOLCENGINE_ASR_RESOURCE_ID=volc.bigasr.auc "$SKILL_DIR/scripts/volcengine_transcribe.sh" audio.mp3
```

### 步骤 4: 生成字级时间轴

```bash
node "$SKILL_DIR/scripts/generate_subtitles.js" volcengine_result.json
# 输出: subtitles_words.json

cd ..
```

时间戳规则：

- `generate_subtitles.js` 必须兼容 `result.utterances`（v3）和旧版 `utterances`。
- v3 结果里的无效时间戳 token（常见为空格，`start_time/end_time = -1`）必须过滤，否则会制造假静音。
- 2026-06-25 的 180 秒样本评估：Seed ASR 2.0 相对校对字幕时间窗的词级边界偏移中位数约 80ms，P90 约 240ms，最大约 620ms；可作为默认剪口播时间轴，但长句仍需按词级时间戳重新切成字幕行。

### 步骤 5: 分析口误（脚本+AI）

#### 5.1 生成易读格式

```bash
cd 2_分析

node -e "
const data = require('../1_转录/subtitles_words.json');
let output = [];
data.forEach((w, i) => {
  if (w.isGap) {
    const dur = (w.end - w.start).toFixed(2);
    if (dur >= 0.2) output.push(i + '|[静' + dur + 's]|' + w.start.toFixed(2) + '-' + w.end.toFixed(2));
  } else {
    output.push(i + '|' + w.text + '|' + w.start.toFixed(2) + '-' + w.end.toFixed(2));
  }
});
require('fs').writeFileSync('readable.txt', output.join('\\n'));
"
```

#### 5.2 读取用户习惯

先读 `用户习惯/` 目录下所有规则文件。

#### 5.3 生成句子列表（关键步骤）

**必须先分句，再分析**。按静音切分成句子列表：

```bash
node -e "
const data = require('../1_转录/subtitles_words.json');
let sentences = [];
let curr = { text: '', startIdx: -1, endIdx: -1 };

data.forEach((w, i) => {
  const isLongGap = w.isGap && (w.end - w.start) >= 0.5;
  if (isLongGap) {
    if (curr.text.length > 0) sentences.push({...curr});
    curr = { text: '', startIdx: -1, endIdx: -1 };
  } else if (!w.isGap) {
    if (curr.startIdx === -1) curr.startIdx = i;
    curr.text += w.text;
    curr.endIdx = i;
  }
});
if (curr.text.length > 0) sentences.push(curr);

sentences.forEach((s, i) => {
  console.log(i + '|' + s.startIdx + '-' + s.endIdx + '|' + s.text);
});
" > sentences.txt
```

#### 5.4 脚本自动标记静音（必须先执行）

```bash
node -e "
const words = require('../1_转录/subtitles_words.json');
const selected = [];
words.forEach((w, i) => {
  if (w.isGap && (w.end - w.start) >= 0.2) selected.push(i);
});
require('fs').writeFileSync('auto_selected.json', JSON.stringify(selected, null, 2));
console.log('≥0.2s静音数量:', selected.length);
"
```

→ 输出 `auto_selected.json`（只含静音 idx）

#### 5.4b 头尾裁剪（转录盲区，必做）

> 🚨 火山只转语音，**结尾的未转录杂音/收尾动作不在字幕里，所有检测器都看不见**。必须比对视频时长补出来。见 `用户习惯/3-静音段处理.md`。

```bash
VDUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "file:$VIDEO_PATH")
node -e "
const fs=require('fs');
const w=require('../1_转录/subtitles_words.json');
const auto=require('./auto_selected.json');
const VDUR=$VDUR, last=w[w.length-1];
if(VDUR - last.end > 0.3){            // 结尾未覆盖 → 补尾元素并预选
  w.push({text:'',start:last.end,end:VDUR,isGap:true,reason:'结尾未转录(杂音/收尾)'});
  auto.push(w.length-1);
  fs.writeFileSync('../1_转录/subtitles_words.json',JSON.stringify(w));
  fs.writeFileSync('./auto_selected.json',JSON.stringify([...new Set(auto)].sort((a,b)=>a-b),null,1));
  console.log('补尾元素 idx',w.length-1,'['+last.end+'→'+VDUR+']');
} else console.log('尾部已覆盖');
if(w[0].start>0.3) console.log('⚠️ 开头',w[0].start,'s 未覆盖，考虑补头元素');
"
```

#### 5.5 AI 分析口误（追加到 auto_selected.json）

> 🚨 **核心原则：删前保后。所有重复/口误，删前面的，保后面的。**

**按检测类型分工，多 Agent 并行执行**：

每个 Agent 只负责一种检测，prompt 更短更精确，避免规则互相干扰。

| Agent | 输入 | 检测内容 | 删除范围 |
|-------|------|----------|----------|
| A-句间重复 | sentences.txt | 相邻/隔一句开头≥5字相同 | 删**前句**整句 |
| B-句内重复 | sentences.txt | 同一句内 A+中间+A 模式 | 只删前面**片段**，不删整句 |
| C-残句 | sentences.txt | 话说一半+静音+后面重说 | 删残句**整句** |

**脚本可直接处理（不需要 AI）**：
- 卡顿词（那个那个、就是就是）→ 正则匹配
- 语气词（嗯、啊、呃）→ 标记待人工确认

**复核（verify）—— 按风险投放，不要铺满**（见 `用户习惯/10-删除风险分层.md`）：

- **低风险免验**：静音、逐字子集重复（删的是保留内容的逐字开头，如删「我把同一句」保「我把同一句话」）、≤3字纯卡壳/语气词 → 直接进 auto_selected，交网页人工兜底。
- **高风险必验**：整句删除、"开头撞结尾岔"（如「超出了**预算**」vs「超出了**路线规划能力**」）、长片段重复 → 派对抗 reviewer 复核，确认没把独有内容删掉。
- 教训：曾对全部候选铺开 2× 复核，命中仅 ~4/91 且全落在高风险类（见 `log/`）。verify 很贵，砸在容易删错的地方就好。

**Agent prompt 模板**：

```
给每个 Agent 的 prompt 包含：
1. 只放该 Agent 对应的一条检测规则（从用户习惯/读取）
2. 完整的 sentences.txt 内容
3. 明确要求：返回要删除的 idx 范围列表
4. 🚨 强调"删前保后"：删前面的版本，保留后面更完整的版本
```

**Agent 返回格式**：

```
| 句号 | idx范围 | 类型 | 内容摘要 | 处理 |
|------|---------|------|----------|------|

删除idx列表: [所有要删除的idx]
```

**合并结果**：

```
收集所有 Agent 返回的 idx 列表 → 合并到 auto_selected.json → 去重排序
```

**范围整段删除规则**：标记口误时，从 startIdx 到 endIdx 之间的**所有元素**（含中间的 gap）全部加入 auto_selected。不要逐个挑选文字 idx 而跳过 gap。

🚨 **关键警告：行号 ≠ idx**

```
readable.txt 格式: idx|内容|时间
                   ↑ 用这个值

行号1500 → "1568|[静1.02s]|..."  ← idx是1568，不是1500！
```

**口误分析.md 格式：**

```markdown
## 句间重复 (Agent A)

| 句号 | idx范围 | 内容摘要 | 处理 |
|------|---------|----------|------|
| 5 | 212-233 | 与句6重复，句6更完整 | 删前句 |

## 句内重复 (Agent B)

| 句号 | idx范围 | 内容摘要 | 处理 |
|------|---------|----------|------|
| 16 | 492-510 | "很多人一提到CLI命令"前半重复 | 删片段 |

## 残句 (Agent C)

| 句号 | idx范围 | 内容摘要 | 处理 |
|------|---------|----------|------|
| 7 | 266-275 | "为了解释为了回答这个"未完成 | 删整句 |
```

#### 5.6 口播稿对齐补漏（有口播稿时）

若用户提供口播稿/原文稿（口播是照稿读的），用它做**句子级对齐**补漏 —— 见 `用户习惯/11-口播稿对齐.md`。

口播稿 = **语义** ground truth（措辞会变，如"两个模型"↔"两个大模型"，别逐字 diff）。把每个转录句对齐到口播稿句，抓纯文本检测漏掉的**整句级口误**：整句重说、残句、无对应口误 —— 尤其**技术名词卡壳**（Mindverse / δ-mem / LoRA 念错重来、"Delta Mam"、孤立单字"从"）。这类整句删除属高风险 → 走复核，确认保留版覆盖了口播稿原意。

### 步骤 6-7: 审核

```bash
cd ../3_审核

# 6. 生成审核网页（传入视频文件，自动创建符号链接）
node "$SKILL_DIR/scripts/generate_review.js" ../1_转录/subtitles_words.json ../2_分析/auto_selected.json "$VIDEO_PATH"
# 输出: review.html, video.mp4(符号链接)

# 7. 启动审核服务器
node "$SKILL_DIR/scripts/review_server.js" 8899 "$VIDEO_PATH"
# 打开 http://localhost:8899
```

> ⚠️ **必须用 review_server.js**，不能用 `python3 -m http.server` 替代。
> 原因：视频播放依赖 HTTP Range 请求（206），python 简易服务器不支持，会导致视频无法播放/无声音。
> 普通用户保持这个终端窗口开着即可；Claude Code / Codex 由 Agent 使用当前环境可用的后台任务能力托管。不要要求用户安装 tmux。

用户在网页中：
- 播放视频画面确认
- 勾选/取消删除项
- 左键按住滑过文字可批量标删/恢复，支持跨行滑动；拖过头时不松手往回拉，选区会实时收窄
- 点击「执行剪辑」

### 步骤 8: 监听剪后视频

用户点击审核页按钮后，`review_server.js` 只会剪出新视频，并在审核目录写入 `cut_done.json`。Agent 必须监听这个文件，确认剪后视频真实生成且大小稳定。

```bash
# 在另一个 Agent 任务/终端里等待用户确认后的剪辑结果
node "$SKILL_DIR/scripts/watch_cut_done.js" "output/YYYY-MM-DD_视频名/剪口播/3_审核"
```

监听结果会返回剪后视频路径：

```json
{
  "output": "output/YYYY-MM-DD_视频名/剪口播/3_审核/视频名_cut.mp4",
  "newDuration": "123.45",
  "outputSize": 12345678
}
```

把返回里的 `output` 记为 `CUT_VIDEO`，后续字幕必须基于这个视频重转写。

不要用 `curl /api/cut` 或脚本模拟点击，除非用户明确授权。

### 步骤 9: 基于剪后视频重新转写

```bash
"$SKILL_DIR/scripts/generate_srt_for_video.sh" "剪后视频.mp4" "output/YYYY-MM-DD_视频名/字幕"
```

字幕必须基于剪后视频重新转写，不能用原始视频字幕反推。

这一步只产出火山转写初稿：

```text
output/YYYY-MM-DD_视频名/字幕/1_转录/volcengine_result.json
output/YYYY-MM-DD_视频名/字幕/subtitles_with_time.json
output/YYYY-MM-DD_视频名/字幕/3_输出/video.raw.srt
```

### 步骤 10: AI 校对字幕

Agent 必须读取 `video.raw.srt` 或 `subtitles_with_time.json`，对照用户给的口播稿/正文/专名上下文做 AI 校对。

校对规则：

- 保留原时间轴，优先只改字幕文字。
- 修正技术名词、工具名、人名、英文词、同音误识别。
- 调整明显不合理的断句。
- 不新增视频里没有说出的内容。
- 校对完成后写入 `字幕/3_输出/video.srt`。

### 步骤 11: 整理基础素材包

AI 校对完成后，再把剪后视频和最终字幕整理到项目根目录：

```bash
OUTPUT_ROOT="output/YYYY-MM-DD_视频名"
ln -sf "$CUT_VIDEO" "$OUTPUT_ROOT/source_cut.mp4"
ln -sf "$OUTPUT_ROOT/字幕/3_输出/video.srt" "$OUTPUT_ROOT/subtitles.srt"
```

最终产物至少包括：

```text
output/YYYY-MM-DD_视频名/字幕/3_输出/video.srt
output/YYYY-MM-DD_视频名/source_cut.mp4
output/YYYY-MM-DD_视频名/subtitles.srt
```

如果用户下一步要跑 `口播成片`，把产物整理成这个心智：

```text
source_cut.mp4  = 剪后口播视频
subtitles.srt   = AI 校对后的剪后字幕 SRT
assets/         = 可选素材
```

`source_cut.mp4` 和 `subtitles.srt` 可以是符号链接；给用户汇报时，要明确指出它们已经指向剪后视频和剪后字幕。

### 审核硬规则

到审核页这一步必须停下来，把链接交给用户。

用户确认前，Agent 只能做三件事：

1. 生成 `review.html`
2. 启动 `review_server.js`
3. 告诉用户审核页 URL

除非用户明确说“你帮我点执行”或“直接剪”，否则 Agent 不允许：

- 直接调用 `/api/cut`
- 用 curl / 脚本模拟点击
- 跳过审核页直接生成剪后视频

用户在审核页点击「执行剪辑」后，服务器只生成剪后视频。Agent 监听到剪后视频完成后，才能进入剪后重转写和 AI 校对字幕。

---

## 数据格式

### subtitles_words.json

```json
[
  {"text": "大", "start": 0.12, "end": 0.2, "isGap": false},
  {"text": "", "start": 6.78, "end": 7.48, "isGap": true}
]
```

### auto_selected.json

```json
[72, 85, 120]  // Claude 分析生成的预选索引
```

---

## 剪辑编码（硬性规则）

⚠️ **匹配原片参数重编码，帧级精确切割。**

`cut_video.sh` 的工作方式：
1. 自动检测原片编码参数（codec/profile/pix_fmt/bitrate）
2. 用 `filter_complex` trim+concat 帧级精确切割
3. 以相同参数重编码：`-profile:v high -b:v {原片码率} -pix_fmt yuv420p`

**关键**：重编码画质取决于是否匹配原片参数，不是 CRF 值。
- ✅ `-b:v {原片码率} -profile:v high -pix_fmt yuv420p` → 肉眼无区别
- ❌ 只指定 `-crf N` 不指定 profile/pix_fmt → 可能有偏差

---

## 配置

### 火山引擎 API Key

如果用户没有火山语音识别 API Key，先让用户打开火山控制台开通“录音文件识别 2.0”并创建 API Key：

```text
https://console.volcengine.com/speech/new/setting/activate?projectName=default
```

当前默认模型资源：

```text
录音文件识别 2.0 / Seed ASR
resource_id = volc.seedasr.auc
```

拿到 Key 后，再写入 Skills 根目录的 `.env`：

```bash
cd /Volumes/成峰/代码/剪辑Agent/.claude/skills
cp .env.example .env
# 编辑 .env 填入 VOLCENGINE_API_KEY=xxx
```

如果是通过 npm 安装，Skills 根目录通常是：

```bash
~/.claude/skills/chengfeng-videocut-skills
~/.codex/skills/chengfeng-videocut-skills
```
