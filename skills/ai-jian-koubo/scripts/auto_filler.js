#!/usr/bin/env node
/**
 * 自动识别并删除口癖（单字语气词 + 句首/句尾废词 + 任意位置的"然后"）
 *
 * 用法: node auto_filler.js <sentence_map.json> <subtitles_words.json> <speech_errors.json>
 *
 * 行为:
 *   - 读取 speech_errors.json 中已有的 delete_sentences（整句删除句号）
 *   - 对剩余句子按规则扫描口癖，得到 idx 列表
 *   - 与 speech_errors.json 中已有的 delete_idx 合并去重后写回
 *
 * 删除规则:
 *   1) 任意位置：呃、嗯、额(排除"额外/金额"等真词)、诶、欸、唉、噢
 *   2) 句首：然后/那么/好的（两字）、啊/哦/哎/呀/对/呢/那（单字，"那"需排除"那个/那么/那里"等）
 *   3) 任意位置：然后（用户偏好：宁可手动加回）
 *   4) 句尾：对、呢、啊、哦
 *   规则 2/4 仅在删除后剩余 > 3-4 字时执行，避免句子被掏空
 */

const fs = require('fs');

const [, , mapFile, wordsFile, errorsFile] = process.argv;
if (!mapFile || !wordsFile || !errorsFile) {
  console.error('用法: node auto_filler.js <sentence_map.json> <subtitles_words.json> <speech_errors.json>');
  process.exit(1);
}

const map = JSON.parse(fs.readFileSync(mapFile, 'utf8'));
const words = JSON.parse(fs.readFileSync(wordsFile, 'utf8'));
const errors = JSON.parse(fs.readFileSync(errorsFile, 'utf8'));

const deletedSentences = new Set(errors.delete_sentences || []);
const existingIdx = new Set(errors.delete_idx || []);

const ALWAYS = new Set(['呃', '嗯', '额', '诶', '欸', '唉', '噢']);
const EDGE_HEAD = new Set(['啊', '哦', '哎', '呀', '对', '呢']);
const EDGE_TAIL = new Set(['对', '呢', '啊', '哦']);
const NA_FOLLOW = new Set(['个', '么', '里', '种', '时', '样', '边', '些', '位', '段', '次', '天', '年', '场']);
const E_AFTER = new Set(['外', '度', '头']);
const E_BEFORE = new Set(['金', '余', '差', '份', '配', '名', '限']);

const addedIdx = new Set();
const log = [];

for (let s = 0; s < map.length; s++) {
  if (deletedSentences.has(s)) continue;
  const { startIdx, endIdx } = map[s];
  const seq = [];
  for (let i = startIdx; i <= endIdx; i++) {
    if (!words[i].isGap) seq.push({ idx: i, c: words[i].text });
  }
  if (seq.length === 0) continue;

  const toDelete = new Set();

  // 1) 单字语气词（任意位置）
  for (let i = 0; i < seq.length; i++) {
    const c = seq[i].c;
    if (!ALWAYS.has(c)) continue;
    if (c === '额') {
      const nxt = seq[i + 1]?.c;
      const prv = seq[i - 1]?.c;
      if (E_AFTER.has(nxt)) continue;
      if (E_BEFORE.has(prv)) continue;
    }
    toDelete.add(i);
  }

  const remainLen = () => seq.length - toDelete.size;
  const firstReal = () => {
    let f = 0;
    while (f < seq.length && toDelete.has(f)) f++;
    return f;
  };

  // 2) 句首过渡词（反复推进）
  let changed = true;
  while (changed) {
    changed = false;
    const f = firstReal();
    if (f >= seq.length) break;
    const c = seq[f].c;
    const c2 = seq[f + 1]?.c;
    if (remainLen() > 4) {
      if ((c === '然' && c2 === '后') ||
          (c === '那' && c2 === '么') ||
          (c === '好' && c2 === '的')) {
        toDelete.add(f); toDelete.add(f + 1); changed = true; continue;
      }
    }
    if (remainLen() > 3) {
      if (EDGE_HEAD.has(c)) { toDelete.add(f); changed = true; continue; }
      if (c === '那' && !NA_FOLLOW.has(c2)) { toDelete.add(f); changed = true; continue; }
    }
  }

  // 3) 任意位置的"然后"（用户偏好：全删）
  for (let i = 0; i + 1 < seq.length; i++) {
    if (toDelete.has(i) || toDelete.has(i + 1)) continue;
    if (seq[i].c === '然' && seq[i + 1].c === '后') {
      toDelete.add(i); toDelete.add(i + 1);
    }
  }

  // 4) 句尾废词（反复回退）
  changed = true;
  while (changed) {
    changed = false;
    let l = seq.length - 1;
    while (l >= 0 && toDelete.has(l)) l--;
    if (l < 0 || remainLen() <= 3) break;
    if (EDGE_TAIL.has(seq[l].c)) { toDelete.add(l); changed = true; }
  }

  if (toDelete.size === 0) continue;
  const list = [...toDelete].sort((a, b) => a - b);
  const idxs = list.map(i => seq[i].idx);
  const chars = list.map(i => seq[i].c).join('');
  for (const id of idxs) addedIdx.add(id);
  log.push(`句${s}: 删[${chars}] idx=[${idxs.join(',')}]`);
}

const merged = [...new Set([...existingIdx, ...addedIdx])].sort((a, b) => a - b);
errors.delete_idx = merged;
fs.writeFileSync(errorsFile, JSON.stringify(errors, null, 2));

console.log(log.join('\n'));
console.log(`\n自动口癖: ${log.length} 句, 新增 idx ${addedIdx.size} 个`);
console.log(`speech_errors.delete_idx 合并后总计 ${merged.length} 个`);
