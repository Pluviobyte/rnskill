#!/bin/bash
#
# 火山引擎录音文件识别 2.0（Seed ASR v3 异步模式）
#
# 用法:
#   ./volcengine_transcribe.sh <audio.mp3>
#   ./volcengine_transcribe.sh <https://example.com/audio.mp3>
#
# 输出:
#   volcengine_result.json
#   volcengine_asr_meta.json
#

set -euo pipefail

AUDIO_SOURCE="${1:-}"
VOLCENGINE_CONSOLE_URL="https://console.volcengine.com/speech/new/setting/activate?projectName=default"
SUBMIT_URL="https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit"
QUERY_URL="https://openspeech.bytedance.com/api/v3/auc/bigmodel/query"
RESOURCE_ID="${VOLCENGINE_ASR_RESOURCE_ID:-volc.seedasr.auc}"
MODEL_NAME="${VOLCENGINE_ASR_MODEL_NAME:-bigmodel}"

print_api_key_help() {
  echo "请先打开火山控制台注册 / 开通语音识别服务，并创建 API Key:"
  echo "$VOLCENGINE_CONSOLE_URL"
  echo ""
  echo "然后复制环境变量模板并填写:"
  echo "cp .env.example .env"
  echo "VOLCENGINE_API_KEY=你的火山语音识别 API Key"
}

open_volcengine_console_if_possible() {
  if command -v open >/dev/null 2>&1; then
    open "$VOLCENGINE_CONSOLE_URL" >/dev/null 2>&1 || true
  fi
}

if [ -z "$AUDIO_SOURCE" ]; then
  echo "❌ 用法: ./volcengine_transcribe.sh <audio.mp3|audio_url>"
  exit 1
fi

# 获取 API Key
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$(dirname "$(dirname "$SCRIPT_DIR")")/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ 找不到 $ENV_FILE"
  print_api_key_help
  open_volcengine_console_if_possible
  exit 1
fi

API_KEY=$(grep '^VOLCENGINE_API_KEY=' "$ENV_FILE" | tail -1 | cut -d'=' -f2- | tr -d '"' | tr -d "'")

if [ -z "$API_KEY" ] || [ "$API_KEY" = "your_volcengine_api_key_here" ]; then
  echo "❌ $ENV_FILE 里还没有有效的 VOLCENGINE_API_KEY"
  print_api_key_help
  open_volcengine_console_if_possible
  exit 1
fi

TMP_FILES=()
cleanup() {
  for file in "${TMP_FILES[@]}"; do
    [ -n "$file" ] && [ -e "$file" ] && rm -f "$file"
  done
}
trap cleanup EXIT

AUDIO_FILE="$AUDIO_SOURCE"
if [[ "$AUDIO_SOURCE" == file:* ]]; then
  AUDIO_FILE="${AUDIO_SOURCE#file:}"
elif [[ "$AUDIO_SOURCE" =~ ^https?:// ]]; then
  AUDIO_FILE="$(mktemp "${TMPDIR:-/tmp}/volc-seedasr-audio.XXXXXX")"
  TMP_FILES+=("$AUDIO_FILE")
  echo "☁️ 下载音频 URL 到本地临时文件..."
  curl -sS -L -o "$AUDIO_FILE" "$AUDIO_SOURCE"
fi

if [ ! -f "$AUDIO_FILE" ]; then
  echo "❌ 找不到音频文件: $AUDIO_FILE"
  exit 1
fi

REQUEST_ID=$(uuidgen 2>/dev/null | tr -d '-' | tr '[:upper:]' '[:lower:]' || true)
if [ -z "$REQUEST_ID" ]; then
  REQUEST_ID="$(date +%s)$$"
fi

REQUEST_BODY_FILE="$(mktemp "${TMPDIR:-/tmp}/volc-seedasr-body.XXXXXX.json")"
SUBMIT_BODY_FILE="$(mktemp "${TMPDIR:-/tmp}/volc-seedasr-submit.XXXXXX.json")"
SUBMIT_HEADER_FILE="$(mktemp "${TMPDIR:-/tmp}/volc-seedasr-submit-header.XXXXXX")"
QUERY_BODY_FILE="$(mktemp "${TMPDIR:-/tmp}/volc-seedasr-query.XXXXXX.json")"
QUERY_HEADER_FILE="$(mktemp "${TMPDIR:-/tmp}/volc-seedasr-query-header.XXXXXX")"
TMP_FILES+=("$REQUEST_BODY_FILE" "$SUBMIT_BODY_FILE" "$SUBMIT_HEADER_FILE" "$QUERY_BODY_FILE" "$QUERY_HEADER_FILE")

node - "$AUDIO_FILE" "$REQUEST_BODY_FILE" "$MODEL_NAME" <<'NODE'
const fs = require('fs');
const path = require('path');

const audioFile = process.argv[2];
const outputFile = process.argv[3];
const modelName = process.argv[4] || 'bigmodel';
const ext = path.extname(audioFile).replace('.', '').toLowerCase();
const format = ['mp3', 'wav', 'm4a', 'aac', 'ogg', 'opus'].includes(ext) ? ext : 'mp3';

const body = {
  user: { uid: 'chengfeng-videocut-skills' },
  audio: {
    data: fs.readFileSync(audioFile).toString('base64'),
    format,
    codec: 'raw',
    rate: 16000,
    bits: 16,
    channel: 1,
    language: 'zh-CN'
  },
  request: {
    model_name: modelName,
    enable_itn: true,
    enable_punc: true,
    show_utterances: true
  }
};

fs.writeFileSync(outputFile, JSON.stringify(body));
NODE

header_value() {
  awk -v key="$1" 'BEGIN{IGNORECASE=1} $0 ~ "^" key ":" {sub("^[^:]*:[[:space:]]*", ""); gsub("\r", ""); print; exit}' "$2"
}

echo "🎤 提交火山引擎录音文件识别 2.0..."
echo "模型资源: $RESOURCE_ID"
echo "请求 ID: $REQUEST_ID"

curl -sS -L -D "$SUBMIT_HEADER_FILE" -o "$SUBMIT_BODY_FILE" -X POST "$SUBMIT_URL" \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: $API_KEY" \
  -H "X-Api-Resource-Id: $RESOURCE_ID" \
  -H "X-Api-Request-Id: $REQUEST_ID" \
  -H "X-Api-Sequence: -1" \
  --data-binary "@$REQUEST_BODY_FILE"

SUBMIT_STATUS=$(header_value "x-api-status-code" "$SUBMIT_HEADER_FILE")
if [ -n "$SUBMIT_STATUS" ] && [ "$SUBMIT_STATUS" != "20000000" ]; then
  echo "❌ 提交失败，x-api-status-code=$SUBMIT_STATUS"
  cat "$SUBMIT_BODY_FILE"
  exit 1
fi

echo "✅ 任务已提交"
echo "⏳ 等待转录完成..."

START_MS=$(node -e "console.log(Date.now())")
MAX_ATTEMPTS=180
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  sleep 2
  ATTEMPT=$((ATTEMPT + 1))

  curl -sS -L -D "$QUERY_HEADER_FILE" -o "$QUERY_BODY_FILE" -X POST "$QUERY_URL" \
    -H "Content-Type: application/json" \
    -H "X-Api-Key: $API_KEY" \
    -H "X-Api-Resource-Id: $RESOURCE_ID" \
    -H "X-Api-Request-Id: $REQUEST_ID" \
    -H "X-Api-Sequence: -1" \
    -d '{}'

  QUERY_STATUS=$(header_value "x-api-status-code" "$QUERY_HEADER_FILE")

  if node - "$QUERY_BODY_FILE" <<'NODE'
const fs = require('fs');
const file = process.argv[2];
let data;
try {
  data = JSON.parse(fs.readFileSync(file, 'utf8'));
} catch {
  process.exit(1);
}
process.exit(data?.result?.utterances && Array.isArray(data.result.utterances) ? 0 : 1);
NODE
  then
    cp "$QUERY_BODY_FILE" volcengine_result.json
    END_MS=$(node -e "console.log(Date.now())")
    node - "$REQUEST_ID" "$RESOURCE_ID" "$MODEL_NAME" "$START_MS" "$END_MS" "$ATTEMPT" <<'NODE'
const fs = require('fs');
const result = JSON.parse(fs.readFileSync('volcengine_result.json', 'utf8'));
const [requestId, resourceId, modelName, startMs, endMs, attempts] = process.argv.slice(2);
fs.writeFileSync('volcengine_asr_meta.json', JSON.stringify({
  provider: 'volcengine',
  api: 'api/v3/auc/bigmodel',
  model: 'Seed ASR 2.0',
  model_name: modelName,
  resource_id: resourceId,
  request_id: requestId,
  attempts: Number(attempts),
  elapsed_ms: Number(endMs) - Number(startMs),
  utterances: result.result.utterances.length,
  generated_at: new Date().toISOString()
}, null, 2));
NODE
    UTTERANCES=$(node -e "const r=require('./volcengine_result.json'); console.log(r.result.utterances.length)")
    echo "✅ 转录完成，已保存 volcengine_result.json"
    echo "📝 识别到 $UTTERANCES 段语音"
    exit 0
  fi

  if [ -z "$QUERY_STATUS" ] || [ "$QUERY_STATUS" = "20000001" ] || [ "$QUERY_STATUS" = "20000002" ]; then
    echo -n "."
    continue
  fi

  echo ""
  echo "❌ 转录失败，x-api-status-code=$QUERY_STATUS"
  cat "$QUERY_BODY_FILE"
  exit 1
done

echo ""
echo "❌ 超时，任务未完成"
exit 1
