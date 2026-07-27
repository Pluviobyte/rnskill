const fs = require('fs');
const path = require('path');

const inputFile = process.argv[2];
const outDir = process.argv[3];

if (!inputFile || !outDir) {
  console.error('用法: node gen_analysis.js <subtitles_words.json> <输出目录>');
  process.exit(1);
}

if (!fs.existsSync(inputFile)) {
  console.error('文件不存在: ' + inputFile);
  process.exit(1);
}

// 确保输出目录存在（recursive: true 本身幂等，无需 existsSync）
fs.mkdirSync(outDir, { recursive: true });

const data = JSON.parse(fs.readFileSync(inputFile, 'utf8'));

// 分句（按 ≥0.2s 静音分界），同时收集静音 idx — 一次遍历完成
const sentences = [];
const silenceIdx = [];
let curr = { text: '', startIdx: -1, endIdx: -1 };

data.forEach((w, i) => {
  if (w.isGap && (w.end - w.start) >= 0.2) {
    silenceIdx.push(i);
    if (curr.text.length > 0) {
      sentences.push({ ...curr });
      curr = { text: '', startIdx: -1, endIdx: -1 };
    }
  } else if (!w.isGap) {
    if (curr.startIdx === -1) curr.startIdx = i;
    curr.text += w.text;
    curr.endIdx = i;
  }
});
if (curr.text.length > 0) sentences.push(curr);

fs.writeFileSync(path.join(outDir, 'auto_selected.json'), JSON.stringify(silenceIdx, null, 2));

// analysis.txt: 序号: 文本
const analysisLines = sentences.map((s, i) => i + ': ' + s.text).join('\n');
fs.writeFileSync(path.join(outDir, 'analysis.txt'), analysisLines);

// sentence_map.json: [{startIdx, endIdx}, ...]
const sentenceMap = sentences.map(s => ({ startIdx: s.startIdx, endIdx: s.endIdx }));
fs.writeFileSync(path.join(outDir, 'sentence_map.json'), JSON.stringify(sentenceMap, null, 2));

console.log('analysis: ' + sentences.length + ' 句, ' + silenceIdx.length + ' 静音');
