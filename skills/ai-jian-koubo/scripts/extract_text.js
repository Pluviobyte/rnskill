#!/usr/bin/env node
/**
 * 从 subtitles_words.json 提取纯文本
 *
 * 用法: node extract_text.js <subtitles_words.json> [输出目录]
 * 输出: raw_text.txt（每句一行，gap 处换行）
 */

const fs = require('fs');
const path = require('path');

const inputFile = process.argv[2];
const outDir = process.argv[3] || '.';

if (!inputFile || !fs.existsSync(inputFile)) {
  console.error('❌ 用法: node extract_text.js <subtitles_words.json> [输出目录]');
  process.exit(1);
}

const words = JSON.parse(fs.readFileSync(inputFile, 'utf8'));

const lines = [];
let current = '';

for (const w of words) {
  if (w.isGap) {
    if (current.trim()) {
      lines.push(current.trim());
    }
    current = '';
  } else {
    current += w.text;
  }
}
if (current.trim()) {
  lines.push(current.trim());
}

const output = lines.join('\n');
const outFile = path.join(outDir, 'raw_text.txt');
fs.writeFileSync(outFile, output);
console.log(`✅ 已提取 ${lines.length} 句，保存到 ${outFile}`);
