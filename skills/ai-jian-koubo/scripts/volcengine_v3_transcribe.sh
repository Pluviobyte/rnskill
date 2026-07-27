#!/bin/bash
#
# 火山引擎 大模型录音文件标准版（auc 接口，异步 submit → query 轮询）
#
# 用法:
#   ./volcengine_v3_transcribe.sh <local_file.mp3> [output_dir]   ← 推荐，base64 直传
#   ./volcengine_v3_transcribe.sh <audio_url>      [output_dir]   ← URL 模式
#
# 输出: <output_dir>/volcengine_v3_result.json
#
# 关键（与极速版的差异）:
#   - 异步：先 submit 提交任务，再 query 轮询，直到完成
#   - 任务状态在响应头 X-Api-Status-Code，不在 body
#     （20000000 成功 / 20000001 处理中 / 20000002 排队 / 20000003 静音）
#     —— 处理中阶段 body 会是 {"result":{"text":""}} 空结果，别误判为失败
#   - query 必须带回 submit 返回的 X-Tt-Logid，否则可能查不到任务
#   - 标准版 API: https://www.volcengine.com/docs/6561/1354868
#
# 请求体构建 / 状态头解析 / 字数统计与极速版共用 lib/volc_common.sh + lib/build_request.py。

AUDIO_INPUT="$1"
OUT_DIR="${2:-.}"

if [ -z "$AUDIO_INPUT" ]; then
  echo "❌ 用法: $0 <local_file_or_url> [output_dir]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/lib/load_api_key.sh"
. "$SCRIPT_DIR/lib/volc_common.sh"

if [[ ! "$AUDIO_INPUT" =~ ^https?:// ]] && [ ! -f "$AUDIO_INPUT" ]; then
  echo "❌ 文件不存在: $AUDIO_INPUT"
  exit 1
fi
mkdir -p "$OUT_DIR"

REQ=$(mktemp /tmp/v3_req_XXXXX.json)
SUB_HDR=$(mktemp /tmp/v3_subhdr_XXXXX.txt)
SUB_BODY=$(mktemp /tmp/v3_subbody_XXXXX.json)
Q_HDR=$(mktemp /tmp/v3_qhdr_XXXXX.txt)
Q_BODY=$(mktemp /tmp/v3_qbody_XXXXX.json)
trap 'rm -f "$REQ" "$SUB_HDR" "$SUB_BODY" "$Q_HDR" "$Q_BODY"' EXIT

REQUEST_ID=$(volc_gen_request_id)

# ── 步骤 1: 提交任务 ────────────────────────────────────────
echo "🎤 提交火山引擎 标准版 转录任务..."
echo "   输入: $AUDIO_INPUT"
volc_build_request "$AUDIO_INPUT" "$REQ"

HTTP_CODE=$(curl -s -L -D "$SUB_HDR" -o "$SUB_BODY" -w "%{http_code}" \
  -X POST "https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit" \
  -H "X-Api-Key: $API_KEY" \
  -H "X-Api-Resource-Id: volc.bigasr.auc" \
  -H "X-Api-Request-Id: $REQUEST_ID" \
  -H "X-Api-Sequence: -1" \
  -H "Content-Type: application/json" \
  --data-binary "@$REQ")

SUBMIT_STATUS=$(volc_status "$SUB_HDR")
LOG_ID=$(volc_header "$SUB_HDR" x-tt-logid)
echo "提交状态: ${SUBMIT_STATUS:-未返回} $(volc_header "$SUB_HDR" x-api-message)"

if [ "$SUBMIT_STATUS" != "20000000" ]; then
  echo "❌ 提交失败 (HTTP $HTTP_CODE, 状态码 ${SUBMIT_STATUS:-未返回})"
  cat "$SUB_BODY"
  echo ""
  exit 1
fi

echo "✅ 任务已提交"
echo "⏳ 等待转录完成..."

# query 时带回 submit 的 logid（用数组拼接，避免可选 header 的引号陷阱）
QUERY_LOGID=()
[ -n "$LOG_ID" ] && QUERY_LOGID=(-H "X-Tt-Logid: $LOG_ID")

# ── 步骤 2: 轮询结果 ────────────────────────────────────────
MAX_ATTEMPTS=120  # 最多等 10 分钟（每 5 秒一次）
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  sleep 5
  ATTEMPT=$((ATTEMPT + 1))

  curl -s -L -D "$Q_HDR" -o "$Q_BODY" \
    -X POST "https://openspeech.bytedance.com/api/v3/auc/bigmodel/query" \
    -H "X-Api-Key: $API_KEY" \
    -H "X-Api-Resource-Id: volc.bigasr.auc" \
    -H "X-Api-Request-Id: $REQUEST_ID" \
    "${QUERY_LOGID[@]}" \
    -H "Content-Type: application/json" \
    -d "{}"

  STATUS=$(volc_status "$Q_HDR")
  case "$STATUS" in
    20000000)
      cp "$Q_BODY" "$OUT_DIR/volcengine_v3_result.json"
      echo ""
      echo "✅ 转录完成，已保存 $OUT_DIR/volcengine_v3_result.json"
      echo "📝 识别结果: $(volc_word_count "$OUT_DIR/volcengine_v3_result.json")"
      exit 0
      ;;
    20000001|20000002)  # 处理中 / 排队 —— 空 body 正常，继续轮询
      echo -n "."
      ;;
    20000003)
      echo ""
      echo "⚠️  音频为静音，无法识别"
      exit 1
      ;;
    "")  # 头部暂未拿到状态码，继续
      echo -n "."
      ;;
    *)
      echo ""
      echo "❌ 转录失败（状态码: $STATUS）"
      echo "   消息: $(volc_header "$Q_HDR" x-api-message)"
      cat "$Q_BODY"
      echo ""
      exit 1
      ;;
  esac
done

echo ""
echo "❌ 超时，任务未完成"
exit 1
