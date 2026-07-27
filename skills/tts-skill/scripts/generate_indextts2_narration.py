#!/usr/bin/env python3
"""Generate lossless local narration with the canonical IndexTTS2 voice."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def find_workspace() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "CLAUDE.md").is_file() and (parent / "automation").is_dir():
            return parent
    raise SystemExit("Unable to locate workspace root")


WORKSPACE = find_workspace()
DEFAULT_CONFIG = WORKSPACE / "automation" / "config" / "tts-routing.json"
DEFAULT_PRONUNCIATION_LEXICON = (
    Path(__file__).resolve().parents[1] / "references" / "pronunciation-lexicon.json"
)


def run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True)


def capture(command: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.check_output(command, cwd=cwd, text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def probe(path: Path) -> dict[str, Any]:
    output = capture(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_name,sample_rate,channels,bits_per_sample",
            "-show_entries",
            "format=duration,size,bit_rate",
            "-of",
            "json",
            str(path),
        ]
    )
    return json.loads(output)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSONL line {line_number}: {exc}") from exc
        if not isinstance(item, dict) or not str(item.get("text", "")).strip():
            raise SystemExit(f"JSONL line {line_number} must contain non-empty text")
        tasks.append(item)
    if not tasks:
        raise SystemExit("Batch contract is empty")
    return tasks


def load_pronunciation_lexicon(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"Pronunciation lexicon does not exist: {path}")
    try:
        lexicon = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid pronunciation lexicon: {exc}") from exc
    if not isinstance(lexicon, dict) or not isinstance(lexicon.get("terms"), dict):
        raise SystemExit("Pronunciation lexicon must contain an object named 'terms'")
    return lexicon


def validate_pronunciations(
    tasks: list[dict[str, Any]], lexicon: dict[str, Any]
) -> list[str]:
    violations: list[str] = []
    matched_terms: set[str] = set()
    for task_index, task in enumerate(tasks, 1):
        text = str(task["text"])
        for term, contract in lexicon["terms"].items():
            if not isinstance(contract, dict):
                raise SystemExit(f"Pronunciation contract for {term!r} must be an object")
            approved_tts = str(contract.get("tts", term))
            if approved_tts and approved_tts in text:
                matched_terms.add(str(term))
            forbidden_forms = contract.get("forbidden_tts", [])
            if not isinstance(forbidden_forms, list):
                raise SystemExit(f"forbidden_tts for {term!r} must be a list")
            for forbidden in forbidden_forms:
                forbidden_text = str(forbidden)
                if forbidden_text and forbidden_text in text:
                    violations.append(
                        f"task {task_index}: {forbidden_text!r} is forbidden for "
                        f"{term!r}; use {approved_tts!r}"
                    )
    if violations:
        raise SystemExit(
            "Pronunciation contract violation:\n- " + "\n- ".join(violations)
        )
    return sorted(matched_terms)


def ensure_local_contract(config: dict[str, Any], reference: Path) -> dict[str, Any]:
    if not reference.is_file():
        raise SystemExit(f"Canonical lossless reference is missing: {reference}")
    if reference.suffix.lower() != ".wav":
        raise SystemExit(f"Canonical reference must be WAV, got: {reference.suffix}")
    actual_sha = sha256(reference)
    expected_sha = str(config["reference_sha256"])
    if actual_sha != expected_sha:
        raise SystemExit(
            "Canonical reference SHA-256 mismatch: "
            f"expected {expected_sha}, got {actual_sha}"
        )
    metadata = probe(reference)
    streams = metadata.get("streams") or []
    if not streams or not str(streams[0].get("codec_name", "")).startswith("pcm_"):
        raise SystemExit("Canonical reference must use a lossless PCM codec")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-file", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--pronunciation-lexicon",
        type=Path,
        default=DEFAULT_PRONUNCIATION_LEXICON,
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.output.suffix.lower() != ".wav":
        raise SystemExit("Local production output must be a lossless .wav file")
    if not args.batch_file.is_file():
        raise SystemExit(f"Batch contract does not exist: {args.batch_file}")
    if not args.config.is_file():
        raise SystemExit(f"TTS routing config does not exist: {args.config}")
    if args.output.exists() and not args.force and not args.dry_run:
        raise SystemExit(f"Output already exists (use --force): {args.output}")

    routing = json.loads(args.config.read_text(encoding="utf-8"))
    local = routing["local_video"]
    if local.get("provider") != "indextts2-local":
        raise SystemExit("Local video provider must be indextts2-local")

    repository = Path(local["repository"])
    model_dir = Path(local["model_dir"])
    reference = Path(local["reference_wav"])
    if not repository.is_dir() or not model_dir.is_dir():
        raise SystemExit("IndexTTS2 repository or model directory is missing")

    tasks = read_jsonl(args.batch_file)
    pronunciation_lexicon = load_pronunciation_lexicon(args.pronunciation_lexicon)
    matched_pronunciation_terms = validate_pronunciations(tasks, pronunciation_lexicon)
    defaults = local["default_delivery"]
    if "playback_speed" not in defaults:
        raise SystemExit("default_delivery.playback_speed is required")
    try:
        playback_speed = float(defaults["playback_speed"])
    except (TypeError, ValueError) as exc:
        raise SystemExit(
            "default_delivery.playback_speed must be a number"
        ) from exc
    if not 0.5 <= playback_speed <= 2.0:
        raise SystemExit(
            "default_delivery.playback_speed must be between 0.5 and 2.0 "
            "for ffmpeg atempo"
        )
    effective_tasks: list[dict[str, Any]] = []
    for task in tasks:
        effective = dict(task)
        has_emotion_source = any(
            key in effective for key in ("emotion_vector", "emotion_audio", "emotion_text")
        )
        if not has_emotion_source:
            effective["emotion_vector"] = defaults["emotion_vector"]
            effective["emotion_weight"] = defaults["emotion_weight"]
        effective_tasks.append(effective)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    effective_batch = args.output.with_name(f"{args.output.stem}-effective.jsonl")
    effective_batch.write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in effective_tasks) + "\n",
        encoding="utf-8",
    )
    reference_probe = ensure_local_contract(local, reference)
    uv = shutil.which("uv")
    if not uv:
        raise SystemExit("uv is required for the official IndexTTS2 environment")

    raw_output = args.output.with_name(f"{args.output.stem}-raw.wav")
    command = [
        uv,
        "run",
        "indextts2",
        "batch",
        "--batch-file",
        str(effective_batch.resolve()),
        "--voice",
        str(reference),
        "--concat",
        "--output",
        str(raw_output.resolve()),
        "--model-dir",
        str(model_dir),
        "--device",
        str(local.get("device", "mps")),
        "--no-fp16",
        "--no-deepspeed",
        "--no-cuda-kernel",
    ]
    if args.dry_run:
        command.append("--dry-run")
    if args.force or args.dry_run:
        command.append("--force")

    environment = os.environ.copy()
    environment.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    run(command, cwd=repository, env=environment)
    if args.dry_run:
        print(
            "Pronunciation contract: PASS"
            + (
                f" ({', '.join(matched_pronunciation_terms)})"
                if matched_pronunciation_terms
                else ""
            )
        )
        print("IndexTTS2 local narration contract: PASS")
        return 0

    run(
        [
            "ffmpeg",
            "-y" if args.force else "-n",
            "-loglevel",
            "error",
            "-i",
            str(raw_output),
            "-af",
            (
                f"atempo={playback_speed},"
                f"loudnorm=I={defaults['integrated_loudness_lufs']}:TP=-1.5:LRA=11"
            ),
            "-ar",
            str(local["default_delivery"]["output_sample_rate"]),
            "-ac",
            str(local["default_delivery"]["output_channels"]),
            "-c:a",
            str(local["default_delivery"]["output_codec"]),
            str(args.output),
        ]
    )

    output_probe = probe(args.output)
    manifest_path = args.manifest or args.output.with_name("voice_manifest.json")
    manifest = {
        "provider": "IndexTTS2",
        "provider_route": "indextts2-local",
        "voice_id": local["voice_id"],
        "model": local["model"],
        "device": local.get("device", "mps"),
        "repository_commit": capture(["git", "rev-parse", "HEAD"], cwd=repository),
        "reference": {
            "path": str(reference),
            "sha256": local["reference_sha256"],
            "probe": reference_probe,
            "lossless": True,
        },
        "batch_file": str(args.batch_file.resolve()),
        "effective_batch_file": str(effective_batch.resolve()),
        "pronunciation_contract": {
            "lexicon_path": str(args.pronunciation_lexicon.resolve()),
            "lexicon_sha256": sha256(args.pronunciation_lexicon),
            "validated": True,
            "matched_terms": matched_pronunciation_terms,
        },
        "segments": [
            {
                "index": index,
                "text": item["text"],
                "emotion_vector": item.get("emotion_vector"),
                "emotion_weight": item.get("emotion_weight"),
                "silence_after_ms": item.get("silence_after_ms", 0),
                "provider": "IndexTTS2",
                "voice_id": local["voice_id"],
                "used_fallback": False,
            }
            for index, item in enumerate(effective_tasks, 1)
        ],
        "raw_output": str(raw_output.resolve()),
        "playback_speed": playback_speed,
        "speed_filter": f"atempo={playback_speed}",
        "output": str(args.output.resolve()),
        "output_probe": output_probe,
        "used_fallback": False,
        "minimax_used": False,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"narration: {args.output.resolve()}")
    print(f"manifest: {manifest_path.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
