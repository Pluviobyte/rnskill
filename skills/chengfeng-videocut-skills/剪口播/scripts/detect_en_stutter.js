#!/usr/bin/env node
/**
 * 英文/拼音 部分词卡壳 确定性检测
 *
 * 模式：相邻两个英文 token(中间仅隔短停顿)，前一个是后一个的开头子串、或两者完全相同、
 *       或共享前缀≥2 —— 即「词头卡壳/重启」(ben benchmark、Mindverse Mindverse、ada adapter)。
 * 删前保后：删【前一个】(较早的卡壳) + 中间停顿，保留后一个完整词。
 *
 * 用法: node detect_en_stutter.js <subtitles_words.json>
 * 输出: stdout = 要删的 idx JSON 数组；stderr = 人类可读清单
 *
 * 接入点(两道关，每次自动跑)：
 *   1. 剪口播 步骤5.4：扫原片 subtitles_words.json，结果并入 auto_selected
 *   2. 剪后字幕 QC：剪完重转录成片后再扫一遍，抓漏网/剪辑残留
 */
const fs = require('fs');
const file = process.argv[2] || 'subtitles_words.json';
const W = JSON.parse(fs.readFileSync(file, 'utf8'));

const isEn = t => /^[A-Za-z][A-Za-z0-9\-]*$/.test((t || '').trim());
const MAX_GAP = 0.6;   // 卡壳重启的停顿一般很短
const MIN_PREFIX = 2;  // 共享前缀至少2字母，排除 a/I 这类

const flagged = [];
const report = [];
for (let i = 0; i < W.length; i++) {
  if (W[i].isGap || !isEn(W[i].text)) continue;
  // 找下一个实义 token，累计中间停顿
  let j = i + 1, gap = 0;
  while (j < W.length) {
    if (W[j].isGap) { gap += W[j].end - W[j].start; j++; continue; }
    if (!(W[j].text || '').trim()) { j++; continue; }
    break;
  }
  if (j >= W.length || !isEn(W[j].text)) continue;
  if (gap > MAX_GAP) continue;
  const a = W[i].text.trim().toLowerCase(), b = W[j].text.trim().toLowerCase();
  let p = 0; while (p < a.length && p < b.length && a[p] === b[p]) p++;
  const isPrefix = b.startsWith(a) || a.startsWith(b);
  if (p < MIN_PREFIX && !isPrefix) continue;
  // 命中：删 i..(j-1)（前片段 + 中间停顿），保留 j
  for (let k = i; k < j; k++) flagged.push(k);
  report.push(`[${W[i].start.toFixed(2)}s] 删「${W[i].text}」保「${W[j].text}」` +
    `${a === b ? '(完全重复)' : isPrefix ? '(词头卡壳)' : '(共享' + p + '字母)'} gap=${gap.toFixed(2)}s`);
}
const uniq = [...new Set(flagged)].sort((x, y) => x - y);
console.error(`英文卡壳: ${report.length} 处，${uniq.length} 个待删 idx`);
report.forEach(r => console.error('  ' + r));
console.log(JSON.stringify(uniq));
