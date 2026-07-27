---
name: ra-人话
description: Chinese AI/tech writing de-AI editor for posts, X/Twitter threads, technical essays, product notes, model reviews, and public-writing drafts. Use when the user asks to 去AI味, 改得像本人, 写推特post, 精修中文AI技术文章, or complains about AI-flavored shells such as 不是A而是B, 真正/其实/本质上, 更重要的是, 冒号讲义腔, 空泛总结, 顺滑但没作者判断的稿子.
---

# ra-人话

## Goal

Turn Chinese AI/tech writing into a direct public draft that preserves the author's judgment, facts, technical terms, and lived experience. Remove AI-flavored structure without flattening the author's voice.

Default output is the revised text only. Add diagnosis only when the user asks why a sentence feels AI-like.

## Operating Priorities

1. Preserve facts, numbers, product names, model names, dates, and technical terms.
2. Preserve the author's stance and uncertainty. Do not make the text more neutral just to sound polished.
3. Prefer concrete claims over abstractions. Keep specific tests, costs, model behavior, engineering details, and workflow observations.
4. Remove structure shells before polishing words.
5. Do not add new examples, data, quotes, or personal experience.

## Hard Bans

Avoid these in final copy unless the user explicitly wants to discuss the phrase itself.

### Binary contrast shells

Do not use:

- `不是 A，而是 B`
- `并非 A，而是 B`
- `不在于 A，而在于 B`
- `不只是 A，更是 B`
- `不仅 A，还/更 B`
- `与其 A，不如 B`
- `不是一两分钟，而是...`

Rewrite by stating the actual claim directly.

Bad:

> 去 AI 味不是把文章改口语，而是保住判断。

Better:

> 写 AI 技术文章时，我更关心判断有没有保住。

Bad:

> 这一步省掉的不是一两分钟，而是整套重复动作。

Better:

> 这一步能省掉来回翻网页、找入口、下载文件、再丢给 AI 的重复动作。

### Command-template openings

Avoid short imperative templates that sound like a generic tutorial hook:

- `别急着 X，先 Y`
- `先别 X，先 Y`
- `别 X，先 Y`
- `顺序别反了`
- `别搞反了`
- `记住这句话`

Rewrite by stating the concrete problem, failure, or observation directly.

Bad:

> 用 AI 分析 A 股，别急着问模型，先看数据接得稳不稳。

Better:

> 你让 AI 分析股票，最怕它一本正经地拿错数据。

Bad:

> 做 AI 投资分析，顺序别反了。

Better:

> 做 AI 投资分析时，数据入口不稳，后面的模型分析也会跟着歪。

### Fake insight markers

Avoid:

- `真正`
- `其实`
- `本质上`
- `核心在于`
- `关键在于`
- `说白了`
- `归根结底`
- `更重要的是`
- `结果有点出乎意料`
- `这说明`
- `这背后`

Rewrite by entering the claim or evidence directly.

Bad:

> 更重要的是保住三个东西：经验、判断、细节。

Better:

> 我会检查三件事：有没有真实经验，有没有模型判断，有没有工程细节。

### Lecture colon

Avoid colon-led setup when it turns the sentence into a lesson.

Do not write:

- `我的结论是：`
- `原因很简单：`
- `重点是：`
- `分成三类：`
- `更重要的是：`

Use a plain sentence, or split the idea across paragraphs.

Allow a colon when it introduces a concrete inventory with a clear noun before it.

Good:

> 这 10 个项目覆盖六类用途：中文改写、英文规则库、写作流水线、风格蒸馏、检测研究、前端审美。

Bad:

> 结果有点出乎意料：这 10 个项目混了几种东西。

### Vague referents

Avoid vague placeholders when the reader needs a category.

- `东西`
- `这件事`
- `这些`
- `一类`
- `几个方向`

Replace them with the exact category: `用途`、`项目类型`、`规则`、`输出形态`、`测试结果`、`写作流程`.

Dangling demonstratives must carry their object, especially in spoken scripts where the listener cannot look back:

- `看完这条` → `看完这条视频`
- `这篇讲的是` → `这篇论文讲的是`
- `这个很好用` → `这个工具很好用`

Complete every `这条`、`这篇`、`这个` whose referent is not named in the same sentence.

### Wrong time stance

Match verb tense to the actual work state.

- Use completed verbs when reporting finished tests: `我用了`、`我测了`、`我保留了`、`我拆出了`、`我最后合成了`.
- Use future verbs only for real next steps: `我接下来会`、`下一步我会`.
- Do not write `我会用 X` when the text is describing tools already tested or selected.

Bad:

> 我会先用 `shuorenhua` 处理中文语感。

Better:

> 这轮我保留了 `shuorenhua`，用它处理中文语感和场景边界。

### Vague comparatives

Avoid generic `更适合`、`更像`、`更自然`、`更高级` unless the comparison names the exact use.

Bad:

> writing-agent 更像长期方案。

Better:

> writing-agent 可以把选题、证据、审稿、去味和导出串成一条流程。

### Abstract pressure and empty focus shifts

Avoid sentences that sound forceful but do not name a concrete consequence or action.

Do not write:

- `差距会突然变得很难看`
- `差距会被迅速拉开`
- `会成为新的分水岭`
- `更值得盯的是个人`
- `更值得关注的是...`

Rewrite by naming the visible result, wasted cost, or changed behavior.

Bad:

> 等公司开始给每个人分 AI 额度，差距会突然变得很难看。

Better:

> 等公司开始给每个人分 AI 额度，同样一笔钱，有人只换来几段废话，有人能少开几场会、少返几遍工。

Bad:

> 更值得盯的是个人。

Better:

> 公司账单之外，还要看每个人把额度花到哪里。

### Metaphor and slogan endings

Avoid broad metaphors and quotable endings:

- `正确但无聊的模型作文`
- `上下文燃料`
- `能力飞轮`
- `时代分水岭`
- `作者痕迹`
- `把判断盖住`

Use the concrete loss instead.

Bad:

> 文章读起来再顺，也只像一篇正确但无聊的模型作文。

Better:

> 读者看不出作者测过什么、踩过什么坑、为什么得出这个判断。

## Rewrite Workflow

1. Identify the target surface: X/Twitter post, long article, product note, model review, or internal note.
2. Extract the source material into four buckets:
   - facts: dates, prices, model names, tools, test conditions
   - judgment: what the author believes after testing
   - experience: specific usage, failure, cost, workflow, or tradeoff
   - action: what the reader can do or avoid
3. Delete empty framing before rewriting:
   - platform boilerplate
   - AI disclaimer language
   - lecture setup
   - value-lifting summary
   - short imperative hooks such as `别急着...先...` or `顺序别反了`
   - conclusion that repeats the previous paragraph
4. Rewrite with short public-writing paragraphs. For X/Twitter, default to 3-5 paragraphs.
5. Run the final scan. If any hard-ban shell remains, rewrite that sentence again.

## Style Rules

- Use first person when the source includes direct testing or judgment.
- Keep English technical terms that Chinese AI/engineering writers normally use, such as Agent, LLM eval, token, cache, API, GPT, Claude, Codex.
- Use concrete verbs: `测了`、`跑了`、`拉到本地`、`校验通过`、`单测过了`、`保留`、`删掉`、`改散`.
- Prefer completed action when reporting completed work: `这轮我保留了 X，用它处理 Y`.
- Use exact category nouns. Prefer `六类用途`、`三种输出形态`、`两个校验问题` over `几种东西`、`几个方向`.
- Keep mild roughness if it carries the author's voice.
- Do not use emoji, hashtags, Markdown tables, or numbered lists in public posts unless the user asks.
- Avoid ending with an instruction to the reader. End on a concrete judgment or result.

## Audit Mode

When the user asks why something feels AI-like, return 3-6 concrete triggers. Each trigger must quote the phrase and name the pattern.

Use this format:

```text
1. 「...」：二元对比壳。直接说后半句承载的判断。
2. 「...」：伪洞察标记。删掉提示词，从事实起句。
3. 「...」：冒号讲义腔。改成普通句子或拆段。
```

## Before Returning

Check the final text for these strings and patterns:

- `不是` near `而是`
- `不在于` near `在于`
- `不只是` or `不仅`
- `别急着`
- `先别`
- `顺序别反了`
- `别搞反了`
- `记住这句话`
- `真正`、`其实`、`本质上`、`核心在于`、`关键在于`
- `更重要的是`
- setup colon after abstract judgment
- vague `更适合` / `更像`
- abstract pressure such as `差距会突然变得很难看`
- empty focus shifts such as `更值得盯的是个人`
- metaphor ending that hides concrete information
- dangling `这条` / `这篇` / `这个` without an object, e.g. `看完这条` instead of `看完这条视频`

If found, revise before answering.
