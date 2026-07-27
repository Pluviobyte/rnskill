#!/usr/bin/env node
/**
 * 查看指定句子的词级详情（含 idx）
 *
 * 用法: node gen_word_detail.js <sentence_map.json> <subtitles_words.json> <句号1> [句号2] ...
 * 输出: stdout 打印词级详情，供 AI 判断局部删除
 */

const fs = require('fs');

const mapFile = process.argv[2];
const wordsFile = process.argv[3];
const sentenceNums = process.argv.slice(4).map(Number);

if (!mapFile || !wordsFile || sentenceNums.length === 0) {
  console.error('用法: node gen_word_detail.js <sentence_map.json> <subtitles_words.json> <句号1> [句号2] ...');
  process.exit(1);
}

const sentenceMap = JSON.parse(fs.readFileSync(mapFile, 'utf8'));
const words = JSON.parse(fs.readFileSync(wordsFile, 'utf8'));

for (const num of sentenceNums) {
  if (num < 0 || num >= sentenceMap.length) {
    console.error('跳过无效句号: ' + num);
    continue;
  }

  const { startIdx, endIdx } = sentenceMap[num];
  console.log('句' + num + ' [idx ' + startIdx + '-' + endIdx + ']:');

  for (let i = startIdx; i <= endIdx; i++) {
    const w = words[i];
    if (w.isGap) continue;
    console.log('  [' + i + '] ' + w.text);
  }
  console.log('');
}
