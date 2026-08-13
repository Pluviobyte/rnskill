---
name: grok-build-cli
description: Invoke the locally installed Grok Build CLI from Codex and return Grok's response. Use whenever the user asks Codex to call, consult, run, or delegate a prompt to Grok or Grok Build, including Grok web/X searches and agentic Grok tasks. This Skill covers only the invocation mechanism, process monitoring, and response capture; it does not prescribe the task itself.
---

# Call Grok Build

Call the local `grok` CLI from Codex. Do not add an unrelated research,
download, editing, or production workflow.

## Check availability

Before the first call in a task, run:

```bash
command -v grok
grok models
```

`grok models` must confirm that the user is logged in and show at least one
available model. If authentication is missing, report it and run `grok login`
only when the user wants to authenticate interactively.

## Choose the call form

For a direct single-turn answer that does not need Grok tools:

```bash
grok --single 'PROMPT' --output-format plain
```

For an agentic task that may use Grok's tools, including X or web search, put
the full prompt in a UTF-8 file and run:

```bash
grok --prompt-file '/absolute/path/prompt.md' \
  --max-turns 8 \
  --output-format plain
```

Use `--model MODEL` only when the user requests a particular available model.
Otherwise use Grok's configured default.

## Run from Codex

1. For a long prompt, create `prompt.md` with `apply_patch`; avoid fragile shell
   quoting.
2. Start Grok with `exec_command`, normally using `yield_time_ms: 1000`.
3. If the command returns a session ID, poll it with `write_stdin`, sending an
   empty string and waiting at most 30 seconds per poll.
4. Share a concise progress update when a call runs longer than 60 seconds.
5. Capture Grok's final stdout. Treat a nonzero exit code, `Max turns reached`,
   or empty final output as failure.
6. Return Grok's answer to the user, clearly identified as Grok's result when
   attribution matters.

## Isolation

When Grok should only execute the supplied prompt and must not inspect the
current repository's skills or instructions, give it an empty temporary
working directory:

```bash
GROK_CALL_DIR="$(mktemp -d)"
grok --cwd "$GROK_CALL_DIR" --no-memory --no-subagents \
  --prompt-file '/absolute/path/prompt.md' \
  --max-turns 8 \
  --output-format plain
```

Use this isolation by default for web/X research and independent second
opinions. Use the actual project directory only when Grok must read or modify
that project.

## Guardrails

- Do not claim Grok was called unless the CLI actually ran.
- Do not fabricate, paraphrase as successful, or silently replace an empty or
  failed Grok response.
- Do not pass secrets in prompts or command-line arguments.
- Do not use `--always-approve`, `bypassPermissions`, or broad write access
  unless the user explicitly authorizes the corresponding mutations.
- Do not resume an unrelated prior Grok session. Start a new call unless the
  user explicitly asks to continue a specific Grok session.
- Keep this Skill task-agnostic: the user's prompt determines what Grok does.
