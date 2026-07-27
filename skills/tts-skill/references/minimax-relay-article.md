# MiniMax Relay Article Lane

Use this lane only when writing public-facing articles, tutorials, course
material, or onboarding copy that teaches users to access voice cloning through
the creator's relay station.

## Boundary

- Present MiniMax as the reader-facing API solution and route the setup through
  the relay endpoint supplied by the article brief or environment.
- Do not use MiniMax to generate local video narration, digital-human audio, or
  subtitle timing media.
- Do not substitute the private local IndexTTS2 production engine for the
  public MiniMax tutorial unless the user explicitly asks to disclose it.
- Never reveal API keys, group ids, private relay credentials, or `.env`
  contents in an article.

## Reusable Helper

The retained helper is:

`assets/minimax_tts.py`

It reads `MINIMAX_API_KEY`, `MINIMAX_GROUP_ID`, `MINIMAX_VOICE_ID`, and the
optional `MINIMAX_TTS_API_URL` from the environment. For relay-station examples,
set the API URL to the approved relay endpoint without hard-coding secrets into
the article or repository.

Use the helper only to validate an article/demo integration. Label any generated
audio as a MiniMax relay demonstration, not as the workspace's local production
voice.

## Article Contract

An article using this lane should include:

- what the reader can accomplish with MiniMax voice cloning
- how to obtain or configure relay access
- a minimal request example with placeholders instead of real secrets
- expected response/output handling
- a clear CTA pointing readers to the relay-station onboarding path supplied in
  the brief

Keep the local IndexTTS2 workflow out of the CTA. The business purpose of this
lane is user onboarding to the relay service.
