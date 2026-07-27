---
name: ra-洗稿
description: 视频脚本洗稿和二创脚本工作流。Use when the user provides an existing transcript, oral draft, viral script, competitor video text, rough topic notes, or wants 洗稿, 二创改写, 爆款视频脚本重写, 逐字稿改成短视频脚本, rewrite with ra-人话, and queue the approved script into 01-内容生产/视频工作台/待制作/ as the handoff contract for video production. If the user provides a video URL or local video file and asks 视频洗稿、视频二创、洗稿并制作视频, use ra-video-wash-pipeline first.
---

# ra-洗稿

## Goal

Turn a supplied transcript into a human-sounding Chinese video script, then queue it into the `待制作` handoff queue for video production.

Treat `ra-洗稿` as lawful secondary creation and topic reconstruction, not sentence-level plagiarism. Keep the useful topic and audience tension; rebuild the angle, order, hook, wording, and video plan.

If the source is a video URL or local video file and the user wants a new rewritten video, route through `ra-video-wash-pipeline` so transcript extraction happens before this skill.

## Default Skill Stack

1. Apply the `ra-人话` skill to rewrite the script into direct Chinese public-writing style while preserving the creator's judgment.
2. Run `dbs-ai-check` after the rewrite as a diagnostic pass. Fix concrete AI fingerprints only; keep the user's topic, judgment, and preferred tone.
3. Run `dbs-hook` on the first 5 seconds. Use its diagnosis to strengthen the opening without breaking `ra-人话` bans on command-template openings and binary contrast shells.
4. Run `dbs-resonate` before final output or video handoff. If the draft is complete but does not hit a clear audience tension, revise the script before production.
5. Run `ra-video-title` after the script is final: derive the theme from the finished script, generate 8-12 two-part candidates with a Top 3 recommendation, and write them into the handoff 标题候选 section. Do not finalize a title — the user picks one manually at publish time. Production neither generates nor applies publish titles.
6. Run `dbs-xhs-title` only for 小红书图文/笔记 title needs; video publish titles always go through `ra-video-title`.
7. Write the finished script into the handoff queue `01-内容生产/视频工作台/待制作/YYYY-MM-DD-<主题slug>/交接稿.md` following `01-内容生产/视频工作台/_交接模板.md`, then stop. Invoke `ra-video-production-director` in the same session only when the user explicitly asks for immediate production (`直接制作`, `直接出片`, `一条龙`).

## Hard Rules

- Do not treat the user's example as a fixed template. Extract the reusable workflow only.
- Do not invent details that are not present in the source material unless the user explicitly asks for research or expansion.
- Rewrite the structure. Do not keep the original sentence order with swapped synonyms.
- Keep the final spoken script口语化, sharp, and usable for video. Avoid lecture tone, empty grand summaries, and AI-flavored shells.
- The first sentence must hook. The second sentence should raise emotion, pressure, curiosity, or self-identification.
- Treat `dbs-*` skills as quality gates. Use their findings to revise the script; do not dump long diagnostic reports unless the user asks for them.
- When the source came from a reference video URL, keep the source transcript private. Do not return source transcript text, source title, source URL, source transcript path, or source phrases. Quality checks must cite the rewritten draft, not the source transcript.

## Workflow

### 1. Intake

Identify:

- platform: 抖音, 小红书, 视频号, B站, YouTube Shorts, or unspecified
- goal: quick list, tutorial,观点, product explainer, course lead-in, or hot take
- intended length: default 60-120 seconds for short video; infer from the source if obvious
- audience: AI工具用户, SaaS创业者, 内容创作者, 跨境从业者, developer, or broader public
- production scope: script-only, video brief, or full AI video production

Ask only when the missing answer changes the output path. Otherwise choose a conservative default and continue.

洗稿前查重（硬门）：本次洗稿存在可追溯源（源 URL、云端爆款、选题卡带来源链接）时，先运行 `python3 automation/scripts/wash_ledger.py check "<源URL或post_id>" --title "<源标题>"`。退出码 3 = 这条已经洗过：停下，把台账记录（日期、选题卡、产出去向）报给用户，用户明确说重洗才继续；退出码 4 = 曾标记不做或标题疑似：向用户提示一句后继续。纯想法、自供文稿没有源，不查。查重结果只在会话里说，不写进任何产物。

### 2. Rewrite With 人话

Use the `ra-人话` skill rules during rewriting:

- preserve important source details and exact technical names
- keep first-person judgment when the creator is sharing selection or testing
- replace vague statements with concrete categories, tradeoffs, or examples when the source supports them
- remove AI-writing shells, lecture colon, slogan endings, and empty transitions
- write for spoken delivery, not article paragraphs

Default script shape:

1. hook: one sentence, direct and tension-driven
2. emotional second line: make the viewer feel early, late, called out, or suddenly responsible
3. premise: why this matters now
4. body: 3-6 rebuilt points, each with one concrete use, warning, or scene
5. synthesis: how the pieces combine into a workflow, if the source supports it
6. CTA: ask one specific question tied to the viewer's real work

### 3. AI Fingerprint Pass

Use `dbs-ai-check` after the `ra-人话` rewrite:

- identify exact sentences or patterns that still feel AI-written
- fix only concrete issues it catches, especially command-template openings, high-density binary contrast, fake insight markers, lecture colon, and overly smooth transitions
- keep the pass diagnostic by default; revise the script only after the issue is clear
- if no material issue appears, note that the script has no major AI fingerprint and continue

### 4. Hook Pass

Use `dbs-hook` on the first 5 seconds:

- make the opening work without relying on title or cover
- check whether the opening includes topic, hook, and credibility when the source supports them
- prefer imageable failure, result gap, number, contrast, or concrete scene
- avoid self-question-and-answer openings, written-language openings, and openings that reveal the full answer too early
- produce multiple options only when the current hook is weak or the user asks for options; otherwise keep one recommended hook

### 5. Resonance Pass

Use `dbs-resonate` before final script output or video handoff:

- extract the script's core mechanism in one sentence
- check whether the draft hits a real audience tension instead of listing many correct points
- if the core is diluted, revise the premise, hook, or body order before production
- proceed only after the script has a clear target audience, position, and emotional reason to keep watching

### 6. Xiaohongshu Title Pass

Use `dbs-xhs-title` only for 小红书图文/笔记 titles when 小红书 is in scope (video publish titles are owned by `ra-video-title` in the default stack):

- generate title candidates after the final script direction is stable
- keep 小红书标题 separate from the spoken 抖音 hook
- preserve the formula number or formula type when returning title options
- do not let a title formula rewrite the口播 script

### 7. Local Hook Guardrails

News override: when the video reports a new event (a new paper, model, product, or announcement), the first sentence must state the event directly — who + did what + a tension-carrying result. Do not open with metaphor or personification; metaphors and analogies belong in the body as explanation aids. News titles follow the same rule inside `ra-video-title`.

Good news opening:

> Anthropic 发了篇论文，说他们造出了一个能偷看 AI 心里话的工具，还真看到了不该看的东西。

Bad news opening:

> AI 是有心里话的。嘴上答应你，心里想的可能是另一套。

For non-news content, the first sentence should create one of these effects:

- result gap: someone gets an outcome while the viewer is still doing it manually
- missed advantage: the viewer may already be late to a workflow shift
- counterintuitive correction: the popular tool list is not the real value; the combination is
- risk reversal: the dangerous part is not AI replacing people, but people using AI like a search box
- concrete payoff: one night, one report, one prototype, one content pipeline, one launch asset

Good first lines are specific and a little uncomfortable. Avoid vague openings like `今天给大家分享几个工具` or `AI时代来了`.

### 8. Emotional Second-Line Bank

Choose or adapt one line. Do not reuse the same line mechanically.

- `这条视频会让很多还在堆工具的人不舒服。`
- `你刷到这里，说明你已经撞上了效率差距。`
- `后面这一步，可能会直接改掉你的工作流。`
- `如果你还把 AI 当聊天框用，这条视频会有点扎心。`
- `很多人看完会删掉一半工具。`
- `这条视频只留给还想把副业、SaaS 或内容工作往前推的人。`
- `恭喜你刷到这条视频，但该紧张的是，你可能终于要换工作流了。`
- `后面每一步我都尽量讲人话。`
- `如果你最近总觉得 AI 没帮上忙，可能是你的流程太散。`
- `这条视频看完不一定让你变强，但至少能让你少走一段弯路。`

Revise any line that conflicts with the target platform, source material, or creator tone.

### 9. Handoff To The 待制作 Queue

After the script passes the quality gates, write a handoff file instead of starting production. This is the default endpoint.

- path: `01-内容生产/视频工作台/待制作/YYYY-MM-DD-<主题slug>/交接稿.md`（先建项目文件夹，交接稿住在文件夹里）
- structure: follow `01-内容生产/视频工作台/_交接模板.md`
- frontmatter is the binding production contract: `status: 待制作`, platform, ratio (default `16:9` horizontal unless the user chose otherwise), `duration_target_s`, `word_count` (spoken Chinese runs 4-5 chars/second; keep the script inside this budget at wash time), `voice: pluvio-indextts2-calm-v1`, `voice_provider: indextts2-local`, `captions: asr-word-timestamps`, `caption_style: anchor-dark`, `visual`, `illustration_skill`
- body: final hook and emotional second line; the spoken script split into segments where one segment = one page/scene, each with its Xiaohei illustration intent and on-page info components; the `dbs-*` check results; the 标题候选 section (8-12 candidates with a Top 3 recommendation from `ra-video-title`, final pick left to the user); keep the template's 制作要求 hard-constraint summary
- never write the source URL, source title, source transcript, or source transcript path into the handoff file
- the segments in the handoff file are the scene units; production must not re-split the script

After the handoff file lands, close the household register: find the topic card in `01-内容生产/00-选题池/`; if none exists, create one from `_选题卡模板.md` first. Append `- 视频 → [[交接稿文件名]]（日期 进待制作）` under the card's 已立项 section and set the card frontmatter 状态 to 已立项（卡留在原位，不移动文件）. Source links stay only in the card's `来源:` field, never in the handoff file. 卡有可解析的源链接时同步填 `源ID:`（`<platform>:<post_id>`）。

台账登记（硬门）：户口本收尾后立即登记洗稿台账——`python3 automation/scripts/wash_ledger.py add --status washed --url "<源URL>" --title "<源标题>" --author "<源作者>" --card "<选题卡相对路径>" --handoff "<交接稿相对路径>"`；本次下载过源视频时改用 `--from-source-json "<.internal 下载目录里的 *.source.json>"` 自动带出平台/ID/标题；来自云端选题推荐时加 `--work-id <云端作品id>`。无可追溯源不登记。台账住 `.internal/`，源信息只进台账和选题卡，仍然不得进交接稿。

Then stop and return the handoff file path plus the script.

Continue into `ra-video-production-director` in the same session only when the user explicitly asks for immediate production (`直接制作`, `直接出片`, `一条龙`). In that case still write the handoff file first and treat its frontmatter as the production contract. If the user says `只要脚本`, `先不要动工`, or `只分析`, return the script in conversation without creating a queue file.

## Output Format

For the default handoff completion, return:

```text
交接文件：
[01-内容生产/视频工作台/待制作/YYYY-MM-DD-<slug>/交接稿.md]

标题候选：
[Top 3 推荐；完整候选见交接文件]

改写脚本
[hook]
[second line]
[spoken script]

流程检查
- AI 味：
- 开头：
- 共鸣：
- 小红书标题（如适用）：
```

For script-only work (`只要脚本`), return the same block without the 交接文件 line and do not create a queue file.

Do not add `原视频逐字稿`, `原逐字稿路径`, source URL, source title, or quoted source lines to this output unless the user explicitly asks for transcript extraction instead of washing.

For explicit in-session production (`直接制作`, `直接出片`, `一条龙`), also return the final MP4 path, QC artifact path, confirmed specs, and any remaining limitation after `ra-video-production-director` finishes.
