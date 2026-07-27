#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


def load_words(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    words = data.get("words", data) if isinstance(data, dict) else data
    if not isinstance(words, list):
        raise SystemExit("ASR JSON must contain a words array")
    return words


def is_gap(item: dict) -> bool:
    return bool(item.get("isGap")) or item.get("type") in {"spacing", "gap"}


def smart_join(tokens: list[str]) -> str:
    out = ""
    prev_ascii = False
    for token in tokens:
        token = str(token).strip()
        if not token:
            continue
        ascii_token = bool(re.fullmatch(r"[A-Za-z0-9.+\-/]+", token))
        if out and ascii_token and prev_ascii:
            out += " "
        out += token
        prev_ascii = ascii_token
    return out


def apply_glossary(text: str, entries: list[dict]) -> tuple[str, list[dict]]:
    corrected = text
    applied = []
    for entry in entries:
        pattern = re.escape(entry["from"])
        updated, count = re.subn(pattern, entry["to"], corrected, flags=re.IGNORECASE)
        if count:
            applied.append({**entry, "count": count})
            corrected = updated
    return corrected, applied


def srt_time(seconds: float) -> str:
    millis = max(0, round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("words_json", type=Path)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--glossary", type=Path, required=True)
    ap.add_argument("--phrase-gap", type=float, default=0.5)
    args = ap.parse_args()

    words = load_words(args.words_json)
    glossary = json.loads(args.glossary.read_text())
    phrases: list[dict] = []
    current: list[tuple[int, dict]] = []

    def flush() -> None:
        if not current:
            return
        tokens = [w.get("text", "") for _, w in current if not is_gap(w)]
        raw = smart_join(tokens)
        if not raw:
            current.clear()
            return
        caption_tokens = [token for token in tokens if str(token).strip() not in {"呃", "额"}]
        caption_raw = smart_join(caption_tokens)
        corrected, applied = apply_glossary(caption_raw, glossary.get("entries", []))
        phrases.append({
            "id": len(phrases),
            "start": float(current[0][1]["start"]),
            "end": float(current[-1][1]["end"]),
            "start_index": current[0][0],
            "end_index": current[-1][0],
            "raw": raw,
            "corrected": corrected,
            "glossary_applied": applied,
        })
        current.clear()

    for idx, word in enumerate(words):
        if is_gap(word) and float(word["end"]) - float(word["start"]) >= args.phrase_gap:
            flush()
            continue
        if not is_gap(word):
            current.append((idx, word))
    flush()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "phrase-map.json").write_text(
        json.dumps(phrases, ensure_ascii=False, indent=2) + "\n"
    )

    review = [
        "# Transcript review",
        "",
        "| Phrase | Source time | Raw ASR | Corrected for meaning/captions |",
        "|---:|---:|---|---|",
    ]
    for phrase in phrases:
        review.append(
            f"| {phrase['id']} | {phrase['start']:.2f}-{phrase['end']:.2f} | "
            f"{phrase['raw'].replace('|', '\\|')} | "
            f"{(phrase['corrected'] or '（计划删除口癖）').replace('|', '\\|')} |"
        )
    (args.out_dir / "review.md").write_text("\n".join(review) + "\n")

    script = ["# Corrected spoken script", ""]
    script.extend(f"- 口播：{p['corrected']}" for p in phrases if p["corrected"])
    (args.out_dir / "corrected-script.md").write_text("\n".join(script) + "\n")

    srt_blocks = []
    srt_index = 1
    for phrase in phrases:
        if not phrase["corrected"]:
            continue
        srt_blocks.append(
            f"{srt_index}\n{srt_time(phrase['start'])} --> {srt_time(phrase['end'])}\n"
            f"{phrase['corrected']}"
        )
        srt_index += 1
    (args.out_dir / "precut-review.srt").write_text("\n\n".join(srt_blocks) + "\n")

    uncertainties = []
    for phrase in phrases:
        for item in glossary.get("uncertain_patterns", []):
            if re.search(re.escape(item["pattern"]), phrase["corrected"], re.IGNORECASE):
                uncertainties.append({
                    "phrase": phrase["id"],
                    "time": f"{phrase['start']:.2f}-{phrase['end']:.2f}",
                    "text": phrase["corrected"],
                    **item,
                })
    uncertain_md = [
        "# Uncertain terms",
        "",
        "Resolve every row before production captions. Do not guess from phonetics alone.",
        "",
    ]
    if uncertainties:
        uncertain_md += ["| Phrase | Time | Pattern | Context | Reason |", "|---:|---:|---|---|---|"]
        for item in uncertainties:
            uncertain_md.append(
                f"| {item['phrase']} | {item['time']} | {item['pattern']} | "
                f"{item['text'].replace('|', '\\|')} | {item['reason']} |"
            )
    else:
        uncertain_md.append("No unresolved glossary terms detected.")
    (args.out_dir / "uncertain-terms.md").write_text("\n".join(uncertain_md) + "\n")

    fingerprint = hashlib.sha256(
        args.words_json.read_bytes() + b"\0" + args.glossary.read_bytes()
    ).hexdigest()
    approval_path = args.out_dir / "subtitle-approval.json"
    approval = {
        "approved": False,
        "approved_by": None,
        "approved_at": None,
        "transcript_fingerprint": fingerprint,
        "unresolved_terms": [
            {
                "phrase": item["phrase"],
                "time": item["time"],
                "pattern": item["pattern"],
                "reason": item["reason"],
            }
            for item in uncertainties
        ],
        "notes": ["Review precut-review.srt and corrected-script.md before approving."],
    }
    approval_path.write_text(json.dumps(approval, ensure_ascii=False, indent=2) + "\n")
    print(f"phrases={len(phrases)} glossary_fixes={sum(len(p['glossary_applied']) for p in phrases)} uncertainties={len(uncertainties)}")


if __name__ == "__main__":
    main()
