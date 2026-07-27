#!/bin/bash
#
# 根据删除列表剪辑视频（匹配码率重编码，帧级精确）
#
# 原理：每个保留片段用 -ss/-to 独立提取（避免 trim filter 灰帧问题）
# 分批并行处理，最后 concat demuxer 无损拼接
#
# 用法: ./cut_video.sh <input.mp4> <delete_segments.json> [output.mp4]
#

INPUT="$1"
DELETE_JSON="$2"
OUTPUT="${3:-output_cut.mp4}"
PARALLEL=4  # 同时编码的段数

if [ -z "$INPUT" ] || [ -z "$DELETE_JSON" ]; then
  echo "❌ 用法: ./cut_video.sh <input.mp4> <delete_segments.json> [output.mp4]"
  exit 1
fi

if [ ! -f "$INPUT" ]; then
  echo "❌ 找不到输入文件: $INPUT"
  exit 1
fi

if [ ! -f "$DELETE_JSON" ]; then
  echo "❌ 找不到删除列表: $DELETE_JSON"
  exit 1
fi

# 获取视频信息
DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "file:$INPUT")
BITRATE=$(ffprobe -v error -show_entries stream=bit_rate -select_streams v:0 -of csv=p=0 "file:$INPUT")
PROFILE=$(ffprobe -v error -show_entries stream=profile -select_streams v:0 -of csv=p=0 "file:$INPUT")
PIX_FMT=$(ffprobe -v error -show_entries stream=pix_fmt -select_streams v:0 -of csv=p=0 "file:$INPUT")

BITRATE_K=$((BITRATE/1000))
MAXRATE_K=$((BITRATE_K * 13 / 10))
BUFSIZE_K=$((BITRATE_K * 2))

echo "📹 视频时长: ${DURATION}s"
echo "📊 原片参数: ${BITRATE_K}kbps, profile=${PROFILE}, pix_fmt=${PIX_FMT}"
echo "⚙️ 匹配码率重编码（-ss/-to 逐段提取，无 trim filter）"

# 创建临时目录
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

# 映射 profile
PROFILE_LC=$(echo "$PROFILE" | tr '[:upper:]' '[:lower:]')
case "$PROFILE_LC" in
  "high") X264_PROFILE="high" ;;
  "main") X264_PROFILE="main" ;;
  "baseline") X264_PROFILE="baseline" ;;
  *) X264_PROFILE="high" ;;
esac

# 用 node 计算保留片段，生成提取脚本和 concat 列表
TOTAL_SEGS=$(node -e "
const fs = require('fs');
const deleteSegs = JSON.parse(fs.readFileSync('$DELETE_JSON', 'utf8'));
const duration = $DURATION;

deleteSegs.sort((a, b) => a.start - b.start);

const MERGE_GAP = 0.2;
const mergedSegs = [];
for (const seg of deleteSegs) {
  if (mergedSegs.length === 0 || seg.start > mergedSegs[mergedSegs.length - 1].end + MERGE_GAP) {
    mergedSegs.push({ ...seg });
  } else {
    mergedSegs[mergedSegs.length - 1].end = Math.max(mergedSegs[mergedSegs.length - 1].end, seg.end);
  }
}

const keepSegs = [];
let cursor = 0;
for (const del of mergedSegs) {
  if (del.start > cursor) keepSegs.push({ start: cursor, end: del.start });
  cursor = del.end;
}
if (cursor < duration) keepSegs.push({ start: cursor, end: duration });

let deletedTime = 0;
for (const seg of mergedSegs) deletedTime += seg.end - seg.start;

console.error('保留片段数:', keepSegs.length);
console.error('删除片段数:', mergedSegs.length);
console.error('删除总时长:', deletedTime.toFixed(2) + 's');
console.error('预计输出时长:', (duration - deletedTime).toFixed(2) + 's');

// 生成 concat 列表和片段信息
const concatLines = [];
const segInfos = [];
keepSegs.forEach((seg, i) => {
  const padded = String(i).padStart(5, '0');
  const outFile = '$TMP_DIR/seg_' + padded + '.mp4';
  concatLines.push(\"file '\" + outFile + \"'\");
  segInfos.push({ i, start: seg.start, end: seg.end, out: outFile });
});

fs.writeFileSync('$TMP_DIR/concat.txt', concatLines.join('\n'));
fs.writeFileSync('$TMP_DIR/segments.json', JSON.stringify(segInfos));
console.log(keepSegs.length);
")

if [ -z "$TOTAL_SEGS" ] || [ "$TOTAL_SEGS" -eq 0 ]; then
  echo "❌ 计算保留片段失败"
  exit 1
fi

echo "✂️ 提取 $TOTAL_SEGS 个片段（并行度 $PARALLEL）..."
echo "   编码: libx264 -profile:v $X264_PROFILE -b:v ${BITRATE_K}k -pix_fmt $PIX_FMT"

# node 生成每段独立的 shell 脚本
node -e "
const fs = require('fs');
const segs = JSON.parse(fs.readFileSync('$TMP_DIR/segments.json', 'utf8'));
segs.forEach((s, i) => {
  const script = '#!/bin/bash\nffmpeg -y -v error' +
    ' -ss ' + s.start.toFixed(3) + ' -to ' + s.end.toFixed(3) +
    ' -accurate_seek -i \"file:' + process.argv[1] + '\"' +
    ' -c:v libx264 -profile:v ' + process.argv[2] +
    ' -b:v ' + process.argv[3] + 'k -maxrate ' + process.argv[4] + 'k -bufsize ' + process.argv[5] + 'k' +
    ' -pix_fmt ' + process.argv[6] +
    ' -c:a aac -b:a 128k' +
    ' -avoid_negative_ts make_zero' +
    ' \"file:' + s.out + '\"\n';
  const padded = String(i).padStart(5, '0');
  fs.writeFileSync('$TMP_DIR/cmd_' + padded + '.sh', script);
});
" "$INPUT" "$X264_PROFILE" "$BITRATE_K" "$MAXRATE_K" "$BUFSIZE_K" "$PIX_FMT"

# 逐段提取（控制并行度）
RUNNING=0
DONE=0

for CMD_FILE in "$TMP_DIR"/cmd_*.sh; do
  (
    bash "$CMD_FILE" || touch "$TMP_DIR/failed"
  ) &

  RUNNING=$((RUNNING + 1))
  if [ "$RUNNING" -ge "$PARALLEL" ]; then
    wait -n 2>/dev/null || wait
    RUNNING=$((RUNNING - 1))
    DONE=$((DONE + 1))
    printf "\r   进度: %d/%d" "$DONE" "$TOTAL_SEGS"
  fi
done

# 等待剩余任务
wait
echo ""

if [ -f "$TMP_DIR/failed" ]; then
  echo "❌ 部分片段编码失败"
  exit 1
fi

echo "   ✅ 全部 $TOTAL_SEGS 个片段提取完成"

# 拼接
echo "🔗 拼接..."
ffmpeg -y -v error -stats \
  -f concat -safe 0 -i "$TMP_DIR/concat.txt" \
  -c copy \
  -movflags +faststart \
  "file:$OUTPUT"

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ 已保存: $OUTPUT"
  NEW_DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "file:$OUTPUT")
  NEW_BR=$(ffprobe -v error -show_entries stream=bit_rate -select_streams v:0 -of csv=p=0 "file:$OUTPUT")
  NEW_BR_K=$((NEW_BR/1000))
  echo "📹 新时长: ${NEW_DURATION}s"
  echo "📊 原始码率: ${BITRATE_K}kbps → 输出码率: ${NEW_BR_K}kbps"
else
  echo "❌ 拼接失败"
  exit 1
fi
