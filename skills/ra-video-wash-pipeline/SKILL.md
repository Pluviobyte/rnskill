---
name: ra-video-wash-pipeline
description: End-to-end Chinese video washing pipeline. Use when the user provides a Bilibili, Douyin, Xiaohongshu, YouTube, web video URL, or local video file and asks for 视频洗稿, 视频二创, 洗稿并制作视频, 链接视频改写, 提取逐字稿后洗稿, or producing a new AI video from a source video. Orchestrates ra-逐字稿提取skill and ra-洗稿, ending at the 01-内容生产/视频工作台/待制作/ handoff queue; production continues through ra-video-production-director only on explicit request (直接制作/直接出片/一条龙).
---

# Video Wash Pipeline

## Goal

Turn a source video link or local video file into a production-ready washed script: extract the faithful transcript, rewrite it through the established ra-洗稿 stack, then queue the approved script into `01-内容生产/视频工作台/待制作/` as the binding production contract. Video production is a separate stage picked up from that queue (normally by the production host through `ra-video-production-director`); continue into production in the same session only when the user explicitly asks.

This skill is an orchestrator. Do not duplicate the detailed rules from `ra-逐字稿提取skill`, `ra-洗稿`, `ra-人话`, `dbs-*`, or `ra-video-production-director`; load and follow those skills at the step where they own the work.

## Source Privacy Boundary

When this skill is used for video washing, the source transcript is an internal working artifact, not a deliverable.

Hard rules:

- Do not print, quote, summarize, or return the source video's transcript in the conversation.
- Do not include the source video title, source URL, source transcript path, or source phrases in the final answer or handoff file unless the user explicitly asks for transcript extraction.
- If a transcript tool normally prints the full transcript, override it with its internal/private mode or capture the output without showing it.
- Store source transcripts only in a temporary/internal location when needed for rewriting. Delete the source transcript after the rewritten script and checks are produced, unless the user explicitly asks to keep it.
- Deliver only the new script, rewritten hook, quality checks, production brief, and source-free factual corrections.

## Route

Use this skill when the input is a video URL or local video file and the user wants a rewritten or newly produced video.

Do not use this skill for narrower tasks:

- transcript only -> use `ra-逐字稿提取skill`
- supplied transcript or rough text only -> use `ra-洗稿`
- finished script or storyboard only -> use `ra-video-production-director`
- fact research without video production -> use the relevant research or writing workflow

If the request says `视频洗稿`, `二创成新视频`, `洗稿并制作视频`, or similar, assume extract -> rewrite -> handoff queue. Continue into same-session production only when the user explicitly says `直接制作`, `直接出片`, or `一条龙`. Narrow the scope when the user explicitly asks for `只要逐字稿`, `只要脚本`, `先不要生成视频`, or `只分析`.

## Workflow

### 1. Intake

Capture the minimum decisions:

- source link or local file
- target platform and ratio; default to Douyin horizontal `16:9` landscape video when unspecified
- expected scope: script-only, 10-second sample, or full video
- visual direction; default to the white-first Xiaohei system in `ra-video-production-director`
- if the user mentions 小黑配图, Ian 小黑, or a specific illustration skill,
  preserve that as a required production constraint rather than a loose style
  preference
- narration; default to the user's cloned voice when full AI narration is needed and no source audio should be reused

Ask only when the answer changes the execution path. Otherwise choose the conservative default and proceed.

查重硬门：拿到源链接后、提取逐字稿前，先运行 `python3 automation/scripts/wash_ledger.py check "<url>"`。退出码 3 = 已洗过：停下，把台账记录（时间、选题卡、产出去向）报给用户，用户明确确认重洗才继续；退出码 4 = 曾标记不做或标题疑似：提示一句后继续。查重结果只在会话里说，不写进任何产物。

### 2. Extract Transcript

Invoke `ra-逐字稿提取skill` first, but use it as an internal dependency.

For Douyin/Xiaohongshu URLs, prefer:

```bash
python3 "$ZT_HOME/scripts/transcript.py" "<url>" --internal --output-dir "<temporary_internal_dir>"
```

Required outcomes:

- platform, duration, segment count, and estimated wait time after probe
- complete transcript text available to the agent for rewriting
- no source transcript, source title, source URL, source phrases, or source transcript path exposed to the user

If extraction fails because the platform blocks access or the link is private, stop and ask for a local file, public link, or exported captions. Do not continue from a guessed transcript.

### 3. Rewrite Script

Pass the complete transcript and user goal into `ra-洗稿`.

Require `ra-洗稿` to run its default stack:

1. `ra-人话` rewrite
2. `dbs-ai-check` diagnostic pass
3. `dbs-hook` first-five-seconds pass
4. `dbs-resonate` resonance pass
5. `ra-video-title` candidates pass: 8-12 candidates with a Top 3 recommendation into the handoff 标题候选 section (no final title — the user picks manually at publish time)
6. `dbs-xhs-title` only when Xiaohongshu 图文/笔记 titles are in scope

Expected rewrite output:

- new spoken script or逐字稿
- final hook and second line
- publish-title candidates with a Top 3 recommendation (`ra-video-title`)
- flow checks for AI flavor, opening, resonance, and Xiaohongshu title if relevant
- handoff contract content: frontmatter fields plus per-segment Xiaohei illustration intent, on-page info components, captions/motion notes, and archive slug

If the user asks for `只要脚本`, stop here and return the rewritten script and flow checks only. Do not return the source transcript path.

### 4. Queue The Handoff (default endpoint)

Require `ra-洗稿` to finish with its default endpoint: a handoff file in
`01-内容生产/视频工作台/待制作/YYYY-MM-DD-<主题slug>/交接稿.md` following `01-内容生产/视频工作台/_交接模板.md` (create the project folder first; the handoff lives inside).

Before stopping, verify:

- the handoff file exists and its frontmatter contract is complete
  (`status: 待制作`, platform, ratio defaulting to `16:9`, `duration_target_s`,
  `word_count`, `voice: pluvio-indextts2-calm-v1`,
  `voice_provider: indextts2-local`,
  `captions: asr-word-timestamps`, `caption_style: anchor-dark`, `visual`,
  `illustration_skill`)
- the 标题候选 section holds 8-12 candidates with a Top 3 recommendation from
  `ra-video-title`; no final title is picked — the user selects manually later
- the script body is split into segments with per-segment Xiaohei intent and
  on-page info components
- no source URL, source title, source transcript, or source transcript path
  appears anywhere in the file
- the wash ledger entry has been added（台账登记完成才算收尾）

台账登记（硬门）：交接稿与选题卡落地后，登记洗稿台账——优先 `python3 automation/scripts/wash_ledger.py add --status washed --from-source-json "<.internal/<日期>-<平台>-download/…source.json>" --card "<选题卡相对路径>" --handoff "<交接稿相对路径>"`（本流水线下载源视频时一定有这个文件）；未走下载、只有链接时用 `--url "<源URL>" --title "<源标题>"`；来自云端选题推荐时加 `--work-id <云端作品id>`。用户看完源决定不洗时，也要 `add --status skipped --url "<源URL>" --note "<原因>"`，防止之后重复推荐。

Then stop and return the handoff file path plus the script and flow checks.
Production is picked up from the queue as a separate stage.

### 5. Produce Video (only on explicit request)

Only when the user explicitly said `直接制作`, `直接出片`, or `一条龙`:
invoke `ra-video-production-director` with the handoff file as the binding
production contract, plus:

- source-free video metadata and private transcript context
- `ra-洗稿` flow-check results
- default Douyin horizontal `16:9` landscape canvas with the white-first Xiaohei visual system unless the user gave a different style
- required illustration skill: `ian-xiaohei-illustrations` whenever the user
  asked for 小黑配图 or the white-first Xiaohei default is selected

For a first run, changed style, or uncertain motion direction, render a 10-second sample first. Continue to the full video only after approval unless the user has explicitly asked to skip the sample gate.

### 6. QC And Archive (explicit production only)

Let `ra-video-production-director` run its normal QC and archive rules.

Minimum final checks:

- final MP4 exists in `01-内容生产/视频工作台/已制作/<月上旬|月下旬>/<日期-主题>/成片/`
- `automation/scripts/check_delivery.py` passes against the handoff file, project dir, and final MP4
- the handoff file's 制作端回执 is filled, `status: 已完成`, and `01-内容生产/视频工作台/已制作/<月上旬|月下旬>/<日期-主题>/` is assembled with the handoff file, the final MP4 copy under `成片/`, and key QC frames under `质检/`
- rewritten script path is recorded; source transcript path stays private or is deleted
- captions use safe zones and do not have unwanted UI frames
- production subtitles were generated from the exact final audio through
  `ra-audio-to-subtitles`; `caption-qc.json` passed; `skill-captions` applied
  the handoff `caption_style` (default `anchor-dark`) and produced a passing
  `caption-render-qc.json`; character-count timing was not used
- page base stays stable; motion happens on components
- Xiaohei illustrations are generated through `ian-xiaohei-illustrations`,
  saved as project assets, loaded directly by the render, and explain the
  current point instead of acting as decoration
- representative frames confirm progressive reveals and no text overlap

## Output

For the default handoff completion, return:

```text
交接文件：
[01-内容生产/视频工作台/待制作/YYYY-MM-DD-<slug>/交接稿.md]

标题候选：
[Top 3 推荐；完整候选见交接文件]

新逐字稿/脚本：
[script]

流程检查：
- AI 味：
- 开头：
- 共鸣：
- 小红书标题（如适用）：
```

For script-only completion (`只要脚本`), return the same block without the
交接文件 line and do not create a queue file.

For explicit in-session production completion, return:

```text
成片：
[final MP4 path]

质检：
[key QC path]

过程资产：
- 新脚本：

规格：
[ratio, resolution, duration, codecs]

限制：
[only if something remains]
```
