#!/usr/bin/env node
/**
 * 从火山引擎结果生成字级别字幕
 *
 * 用法: node generate_subtitles.js <volcengine_v3_result.json> [delete_segments.json]
 * 输出: subtitles_words.json
 */

const fs = require('fs');
const path = require('path');

const resultFile = process.argv[2] || 'volcengine_v3_result.json';
const deleteFile = process.argv[3];
const outDir = process.argv[4] || '.';

if (!fs.existsSync(resultFile)) {
  console.error('❌ 找不到文件:', resultFile);
  process.exit(1);
}

const result = JSON.parse(fs.readFileSync(resultFile, 'utf8'));

// 兼容 v1（顶层 utterances）和 v3（result.utterances）两种格式
const utterances = result.result ? result.result.utterances : result.utterances;

if (!utterances || utterances.length === 0) {
  console.error('❌ 未找到 utterances，响应格式可能不符合预期');
  console.error('响应顶层字段:', Object.keys(result));
  process.exit(1);
}

// 提取所有字
// 注意：火山 flash 引擎会在中英文边界塞入 text=' ' 且 start_time/end_time=-1 的"分隔符词"，
// 必须过滤掉，否则 lastEnd 会被污染成负数，导致 gap 计算出几十秒的假静音段
const allWords = [];
for (const utterance of utterances) {
  if (utterance.words) {
    for (const word of utterance.words) {
      if (word.start_time < 0 || word.end_time < 0) continue;
      if (!word.text || !word.text.trim()) continue;
      allWords.push({
        text: word.text,
        start: word.start_time / 1000,
        end: word.end_time / 1000
      });
    }
  }
}

console.log('原始字数:', allWords.length);

// 如果有删除片段，映射时间
let outputWords = allWords;

if (deleteFile && fs.existsSync(deleteFile)) {
  const deleteSegments = JSON.parse(fs.readFileSync(deleteFile, 'utf8'));
  console.log('删除片段数:', deleteSegments.length);

  function getDeletedTimeBefore(time) {
    let deleted = 0;
    for (const seg of deleteSegments) {
      if (seg.end <= time) {
        deleted += seg.end - seg.start;
      } else if (seg.start < time) {
        deleted += time - seg.start;
      }
    }
    return deleted;
  }

  function isDeleted(start, end) {
    for (const seg of deleteSegments) {
      if (start < seg.end && end > seg.start) return true;
    }
    return false;
  }

  outputWords = [];
  for (const word of allWords) {
    if (!isDeleted(word.start, word.end)) {
      const deletedBefore = getDeletedTimeBefore(word.start);
      outputWords.push({
        text: word.text,
        start: Math.round((word.start - deletedBefore) * 100) / 100,
        end: Math.round((word.end - deletedBefore) * 100) / 100
      });
    }
  }
  console.log('映射后字数:', outputWords.length);
}

// 添加空白标记（≥0.2秒才生成，与 gen_analysis.js 阈值一致）
const wordsWithGaps = [];
let lastEnd = 0;

for (const word of outputWords) {
  const gapDuration = word.start - lastEnd;

  if (gapDuration >= 0.2) {
    wordsWithGaps.push({
      text: '',
      start: Math.round(lastEnd * 100) / 100,
      end: Math.round(word.start * 100) / 100,
      isGap: true
    });
  }

  wordsWithGaps.push({
    text: word.text,
    start: word.start,
    end: word.end,
    isGap: false
  });
  lastEnd = word.end;
}

const gaps = wordsWithGaps.filter(w => w.isGap);
console.log('总元素数:', wordsWithGaps.length);
console.log('空白段数:', gaps.length);

fs.writeFileSync(path.join(outDir, 'subtitles_words.json'), JSON.stringify(wordsWithGaps, null, 2));
console.log(`✅ 已保存 ${path.join(outDir, 'subtitles_words.json')}`);
