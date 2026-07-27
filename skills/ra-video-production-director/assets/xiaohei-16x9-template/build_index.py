#!/usr/bin/env python3
import html
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if (SCRIPT_DIR / "narration_segments.json").exists():
    ROOT = SCRIPT_DIR
elif (SCRIPT_DIR.parent / "narration_segments.json").exists():
    ROOT = SCRIPT_DIR.parent
else:
    ROOT = SCRIPT_DIR
SEGMENTS = ROOT / "narration_segments.json"
MANIFEST = ROOT / "media" / "voice_manifest.json"
CAPTIONS = ROOT / "media" / "captions" / "captions.json"
CAPTION_QC = ROOT / "media" / "captions" / "caption-qc.json"
OVERRIDES = ROOT / "layout_overrides.json"
OUT = ROOT / "index.html"


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def load_overrides() -> dict:
    if not OVERRIDES.exists():
        return {}
    return json.loads(OVERRIDES.read_text(encoding="utf-8"))


def load_captions() -> list[dict]:
    if not CAPTIONS.exists() or not CAPTION_QC.exists():
        raise RuntimeError(
            "Missing real-timestamp captions. Run ra-audio-to-subtitles against "
            "the final voiceover before building the composition."
        )
    qc = json.loads(CAPTION_QC.read_text(encoding="utf-8"))
    if qc.get("status") != "pass" or qc.get("timing_source") != "volcengine-word-timestamps":
        raise RuntimeError(f"Caption QC did not pass: {CAPTION_QC}")
    captions = json.loads(CAPTIONS.read_text(encoding="utf-8"))
    if not isinstance(captions, list) or not captions:
        raise RuntimeError(f"No captions found in {CAPTIONS}")
    for index, caption in enumerate(captions, 1):
        if not isinstance(caption, dict) or not all(key in caption for key in ("start", "end", "text")):
            raise RuntimeError(f"Invalid caption #{index} in {CAPTIONS}")
        if float(caption["end"]) <= float(caption["start"]):
            raise RuntimeError(f"Caption #{index} has non-positive duration")
    return captions


def lines_html(value: list[str] | str) -> str:
    if isinstance(value, str):
        value = [value]
    return "".join(f'<span class="text-line">{esc(line)}</span>' for line in value)


def note_html(scene: dict) -> str:
    rows = []
    for label, text in scene["notes"]:
        rows.append(f"<li><b>{esc(label)}</b><span>{esc(text)}</span></li>")
    return f"""
      <aside class="left-note">
        <div class="note-kicker">{esc(scene["kicker"])}</div>
        <ul>{"".join(rows)}</ul>
      </aside>
    """


def scene_html(scene: dict, item: dict, index: int, timed: list[dict], total: float, overrides: dict) -> str:
    start = item["start"]
    next_start = timed[index + 1]["audio"]["start"] if index + 1 < len(timed) else total
    duration = max(1.0, next_start - start - 0.02)
    layout = overrides.get(scene["id"], {})
    title = lines_html(layout.get("title_lines", scene["title"]))
    subtitle = lines_html(layout.get("subtitle_lines", scene["subtitle"]))
    variant = layout.get("variant", "standard")
    visual = f'assets/xiaohei-illustrations/{scene["visual"]}'
    return f"""
      <section id="scene-{esc(scene['id'])}" class="scene scene-{esc(scene['id'])} variant-{esc(variant)} clip" data-start="{start:.3f}" data-duration="{duration:.3f}" data-track-index="1">
        <div class="ghost" data-layout-allow-occlusion>{esc(scene['progress'])}</div>
        <div class="topbar"><span><i></i>{esc(scene['chapter'])} / {esc(scene['label'])}</span><span class="mono">{start:05.1f}s</span></div>
        <div class="copy">
          <h1>{title}</h1>
          <p>{subtitle}</p>
          <div class="accent-line"></div>
        </div>
        {note_html(scene)}
        <div class="visual">
          <img class="xiaohei-art" src="{esc(visual)}" alt="" />
        </div>
      </section>
    """


def captions_html(captions: list[dict]) -> str:
    blocks = []
    for cap_index, caption in enumerate(captions, 1):
        start = float(caption["start"])
        duration = float(caption["end"]) - start
        blocks.append(
            f'<div id="caption-{cap_index:02d}" class="caption clip" data-start="{start:.3f}" data-duration="{duration:.3f}" data-track-index="6">{esc(str(caption["text"]))}</div>'
        )
    return "\n".join(blocks)


CSS = r"""
      :root {
        --bg: #fff;
        --ink: #111;
        --soft: #5f5f5f;
        --red: #c9281f;
        --orange: #f08a22;
        --blue: #2467d6;
      }
      * { box-sizing: border-box; }
      html, body {
        margin: 0;
        width: 1920px;
        height: 1080px;
        overflow: hidden;
        background: var(--bg);
        color: var(--ink);
        font-family: sans-serif;
        letter-spacing: 0;
      }
      .mono { font-family: monospace; }
      #main {
        position: relative;
        width: 1920px;
        height: 1080px;
        overflow: hidden;
        background:
          linear-gradient(90deg, rgba(17,17,17,.032) 2px, transparent 2px),
          linear-gradient(rgba(17,17,17,.032) 2px, transparent 2px),
          var(--bg);
        background-size: 96px 96px;
      }
      .scene { position: absolute; inset: 0; padding: 64px 104px 52px; overflow: hidden; }
      .ghost {
        position: absolute;
        right: 110px;
        top: 124px;
        color: rgba(17,17,17,.055);
        font-size: 196px;
        line-height: .86;
        font-weight: 900;
        pointer-events: none;
      }
      .topbar {
        position: absolute;
        left: 104px;
        right: 104px;
        top: 96px;
        display: flex;
        justify-content: space-between;
        color: var(--soft);
        font-size: 25px;
        font-weight: 800;
      }
      .topbar i {
        display: inline-block;
        width: 13px;
        height: 13px;
        margin-right: 12px;
        border-radius: 50%;
        background: var(--blue);
      }
      .copy { position: absolute; left: 104px; top: 140px; width: 780px; }
      h1 { margin: 0; font-size: 72px; line-height: 1.06; font-weight: 950; }
      .text-line { display: block; }
      .copy p {
        margin: 20px 0 0;
        width: 740px;
        color: var(--soft);
        font-size: 32px;
        line-height: 1.34;
        font-weight: 820;
      }
      .accent-line {
        width: 440px;
        height: 8px;
        margin-top: 22px;
        border-radius: 999px;
        background: var(--orange);
      }
      .left-note {
        position: absolute;
        left: 104px;
        top: 424px;
        width: 730px;
        min-height: 238px;
        padding: 24px 30px 22px;
        border: 4px solid var(--ink);
        background: rgba(255,255,255,.96);
        box-shadow: 14px 14px 0 rgba(226,59,46,.18);
      }
      .note-kicker {
        color: var(--red);
        font-size: 23px;
        line-height: 1;
        font-weight: 950;
        margin-bottom: 16px;
      }
      .left-note ul {
        list-style: none;
        margin: 0;
        padding: 0;
        display: grid;
        gap: 14px;
      }
      .left-note li {
        display: grid;
        grid-template-columns: 116px 1fr;
        align-items: baseline;
        gap: 17px;
        font-size: 30px;
        line-height: 1.16;
        font-weight: 850;
      }
      .left-note b { color: var(--blue); font-size: 23px; }
      .left-note span { color: var(--ink); }
      .visual {
        position: absolute;
        right: 72px;
        top: 264px;
        width: 972px;
        height: 547px;
        display: grid;
        place-items: center;
      }
      .xiaohei-art { width: 100%; height: 100%; object-fit: contain; display: block; }
      .caption {
        position: absolute;
        left: 50%;
        bottom: 96px;
        z-index: 30;
        transform: translateX(-50%);
        width: max-content;
        max-width: 1500px;
        padding: 22px;
        box-sizing: border-box;
        border: 0;
        border-radius: 16px;
        background: rgba(45, 51, 50, 0.8353);
        box-shadow: none;
        text-align: center;
        color: rgb(252, 252, 249);
        font-family: "STHeiti Medium", "PingFang SC", sans-serif;
        font-size: 56px;
        line-height: 1.15;
        font-weight: 500;
        text-shadow: none;
        -webkit-text-stroke: 0;
        text-wrap: balance;
        white-space: normal;
      }
"""


JS_HEAD = r"""
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      function enter(selector, start) {
        tl.from(`${selector} .topbar`, { opacity: 0, y: -18, duration: 0.34, ease: "power3.out" }, start + 0.08);
        tl.from(`${selector} .ghost`, { opacity: 0, x: 44, duration: 0.56, ease: "power2.out" }, start + 0.18);
        tl.from(`${selector} h1`, { opacity: 0, y: 34, scale: 0.985, duration: 0.54, ease: "power3.out" }, start + 0.22);
        tl.from(`${selector} .copy p`, { opacity: 0, y: 22, duration: 0.42, ease: "power3.out" }, start + 0.55);
        tl.from(`${selector} .accent-line`, { scaleX: 0, transformOrigin: "left center", duration: 0.38, ease: "power2.out" }, start + 0.78);
        tl.from(`${selector} .xiaohei-art`, { opacity: 0, y: 32, scale: 0.965, rotation: -0.5, duration: 0.64, ease: "power3.out" }, start + 0.86);
        tl.from(`${selector} .left-note`, { opacity: 0, y: 22, duration: 0.44, ease: "power3.out" }, start + 1.06);
        tl.from(`${selector} .left-note li`, { opacity: 0, x: -16, duration: 0.34, stagger: 0.07, ease: "power2.out" }, start + 1.22);
      }
"""


def main() -> None:
    scene_sources = json.loads(SEGMENTS.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    captions = load_captions()
    overrides = load_overrides()
    audio_output = Path(manifest.get("output", "media/voiceover.mp3"))
    audio_src = f"media/{audio_output.name}" if audio_output.is_absolute() else str(audio_output)
    audio_by_id = {item["id"]: item for item in manifest["segments"]}
    timed = [{"source": scene, "audio": audio_by_id[scene["id"]]} for scene in scene_sources]
    total = max(float(manifest["duration"]), timed[-1]["audio"]["end"]) + 0.7
    scene_blocks = "\n".join(scene_html(s["source"], s["audio"], idx, timed, total, overrides) for idx, s in enumerate(timed))
    caption_blocks = captions_html(captions)
    js = JS_HEAD
    for scene in timed:
        js += f'\n      enter("#scene-{scene["source"]["id"]}", {scene["audio"]["start"]:.3f});'
    js += '\n      window.__timelines["main"] = tl;\n'
    html_doc = f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>Xiaohei 16:9 Explainer</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>{CSS}</style>
  </head>
  <body>
    <div id="main" data-composition-id="main" data-start="0" data-duration="{total:.3f}" data-width="1920" data-height="1080">
      <audio id="narration" data-start="0" data-duration="{manifest['duration']:.3f}" data-track-index="9" src="{esc(audio_src)}" data-volume="1"></audio>
      {scene_blocks}
      {caption_blocks}
    </div>
    <script>{js}</script>
  </body>
</html>
"""
    OUT.write_text(html_doc, encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"duration {total:.3f}s")


if __name__ == "__main__":
    main()
