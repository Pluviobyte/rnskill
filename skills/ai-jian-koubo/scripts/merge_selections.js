#!/usr/bin/env node
/**
 * 合并 AI 口误分析结果到 auto_selected.json
 *
 * 用法: node merge_selections.js <sentence_map.json> <speech_errors.json> <auto_selected.json>
 *
 * speech_errors.json 格式:
 *   旧格式: [2, 3, 11]（句号数组，向后兼容）
 *   新格式: {"delete_sentences": [2, 3], "delete_idx": [22, 23, 45]}
 */

const fs = require('fs');

const mapFile = process.argv[2];
const errorsFile = process.argv[3];
const autoFile = process.argv[4];

if (!mapFile || !errorsFile || !autoFile) {
  console.error('用法: node merge_selections.js <sentence_map.json> <speech_errors.json> <auto_selected.json>');
  process.exit(1);
}

const sentenceMap = JSON.parse(fs.readFileSync(mapFile, 'utf8'));
const rawErrors = JSON.parse(fs.readFileSync(errorsFile, 'utf8'));
const autoSelected = JSON.parse(fs.readFileSync(autoFile, 'utf8'));

// 兼容旧格式（纯数组）和新格式（对象）
const deleteSentences = Array.isArray(rawErrors) ? rawErrors : (rawErrors.delete_sentences || []);
const deleteIdx = Array.isArray(rawErrors) ? [] : (rawErrors.delete_idx || []);

// 句号 → idx 展开
const sentenceIdx = [];
for (const sentNum of deleteSentences) {
  if (sentNum < 0 || sentNum >= sentenceMap.length) {
    console.warn('跳过无效句号: ' + sentNum);
    continue;
  }
  const { startIdx, endIdx } = sentenceMap[sentNum];
  for (let i = startIdx; i <= endIdx; i++) {
    sentenceIdx.push(i);
  }
}

// 合并：静音 idx + 句级 idx + 词级 idx → 去重排序
const merged = [...new Set([...autoSelected, ...sentenceIdx, ...deleteIdx])].sort((a, b) => a - b);

fs.writeFileSync(autoFile, JSON.stringify(merged, null, 2));

console.log('整句删: ' + deleteSentences.length + ' 句 (' + sentenceIdx.length + ' idx), 词级删: ' + deleteIdx.length + ' idx, 合并后总计: ' + merged.length + ' 个');
