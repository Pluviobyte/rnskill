#!/usr/bin/env node
/**
 * Wait for review_server.js to finish a manual cut.
 *
 * Usage:
 *   node watch_cut_done.js <review_dir> [timeout_seconds]
 *
 * Output:
 *   Prints cut_done.json after the cut video exists and its size is stable.
 */

const fs = require('fs');
const path = require('path');

const reviewDir = path.resolve(process.argv[2] || process.cwd());
const timeoutSeconds = Number(process.argv[3] || 3600);
const cutDonePath = path.join(reviewDir, 'cut_done.json');
const startAt = Date.now();

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function readCutDone() {
  const raw = fs.readFileSync(cutDonePath, 'utf8');
  return JSON.parse(raw);
}

async function waitForStableFile(filePath) {
  let previous = -1;
  let stableCount = 0;

  while (true) {
    if (!fs.existsSync(filePath)) {
      stableCount = 0;
      previous = -1;
    } else {
      const size = fs.statSync(filePath).size;
      if (size > 0 && size === previous) {
        stableCount += 1;
      } else {
        stableCount = 0;
        previous = size;
      }

      if (stableCount >= 2) {
        return size;
      }
    }

    if ((Date.now() - startAt) / 1000 > timeoutSeconds) {
      throw new Error(`等待剪后视频稳定超时: ${filePath}`);
    }
    await sleep(1000);
  }
}

(async () => {
  if (!fs.existsSync(reviewDir)) {
    throw new Error(`找不到审核目录: ${reviewDir}`);
  }

  while (!fs.existsSync(cutDonePath)) {
    if ((Date.now() - startAt) / 1000 > timeoutSeconds) {
      throw new Error(`等待 cut_done.json 超时: ${cutDonePath}`);
    }
    await sleep(1000);
  }

  const cutDone = readCutDone();
  if (!cutDone.output) {
    throw new Error(`cut_done.json 缺少 output 字段: ${cutDonePath}`);
  }

  const size = await waitForStableFile(cutDone.output);
  const result = {
    ...cutDone,
    outputSize: size,
    detectedAt: new Date().toISOString()
  };

  console.log(JSON.stringify(result, null, 2));
})().catch(error => {
  console.error(error.message);
  process.exit(1);
});
