#!/bin/bash
#
# Generate raw transcript files from a finished/cut video.
#
# Usage:
#   generate_srt_for_video.sh <video.mp4> <subtitle_output_dir>
#
# Output:
#   <subtitle_output_dir>/1_转录/audio.mp3
#   <subtitle_output_dir>/1_转录/volcengine_result.json
#   <subtitle_output_dir>/subtitles_with_time.json
#   <subtitle_output_dir>/3_输出/video.raw.srt
#

set -euo pipefail

VIDEO_PATH="${1:-}"
OUTPUT_DIR="${2:-}"

if [ -z "$VIDEO_PATH" ] || [ -z "$OUTPUT_DIR" ]; then
  echo "用法: generate_srt_for_video.sh <video.mp4> <subtitle_output_dir>" >&2
  exit 1
fi

if [ ! -f "$VIDEO_PATH" ]; then
  echo "找不到视频文件: $VIDEO_PATH" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TRANSCRIBE_SCRIPT="$SCRIPT_DIR/volcengine_transcribe.sh"

mkdir -p "$OUTPUT_DIR/1_转录" "$OUTPUT_DIR/3_输出"

cd "$OUTPUT_DIR/1_转录"

echo "🎧 提取剪后视频音频..."
ffmpeg -y -v error -i "file:$VIDEO_PATH" -vn -acodec libmp3lame audio.mp3

echo "🎤 调用火山引擎录音文件识别 2.0..."
bash "$TRANSCRIBE_SCRIPT" audio.mp3

node - <<'NODE'
const fs = require('fs');
const result = JSON.parse(fs.readFileSync('volcengine_result.json', 'utf8'));
const utterances = result.utterances || result.result?.utterances || [];

const subtitles = utterances.map((u, i) => ({
  id: i + 1,
  text: u.text || '',
  start: (u.start_time ?? u.start ?? 0) / 1000,
  end: (u.end_time ?? u.end ?? 0) / 1000
}));

fs.writeFileSync('../subtitles_with_time.json', JSON.stringify(subtitles, null, 2));

function toSRT(sec) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = Math.floor(sec % 60);
  const ms = Math.round((sec % 1) * 1000);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')},${String(ms).padStart(3, '0')}`;
}

const srt = subtitles.map((item, i) => {
  const text = item.text.replace(/[。！？]+$/g, '');
  return `${i + 1}\n${toSRT(item.start)} --> ${toSRT(item.end)}\n${text}`;
}).join('\n\n');

fs.writeFileSync('../3_输出/video.raw.srt', srt.trim() + '\n');
console.log(`✅ 已生成 ${subtitles.length} 条转写初稿: ../3_输出/video.raw.srt`);
NODE

echo "✅ Raw SRT: $OUTPUT_DIR/3_输出/video.raw.srt"
echo "下一步：Agent 读取转写初稿，对照原稿/正文做 AI 校对后，再写入 $OUTPUT_DIR/3_输出/video.srt"
