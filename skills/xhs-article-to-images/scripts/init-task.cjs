#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);

if (args.includes('--help') || args.includes('-h')) {
  console.log(`Usage:
  xhs-init <task-dir> [--force]

Creates a task folder with index.html, styles, and demo assets.`);
  process.exit(0);
}

const targetArg = args.find((arg) => !arg.startsWith('-'));
if (!targetArg) {
  console.error('请提供任务目录，例如：xhs-init ./work/my-article');
  process.exit(1);
}

const force = args.includes('--force');
const rootDir = path.resolve(__dirname, '..');
const targetDir = path.resolve(targetArg);

function copyFile(src, dest) {
  if (fs.existsSync(dest) && !force) {
    console.error(`文件已存在，跳过覆盖：${dest}`);
    console.error('如需覆盖，请加 --force');
    process.exit(1);
  }
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
}

fs.mkdirSync(path.join(targetDir, 'assets'), { recursive: true });
fs.mkdirSync(path.join(targetDir, 'output'), { recursive: true });

copyFile(path.join(rootDir, 'assets', 'template.html'), path.join(targetDir, 'index.html'));
copyFile(path.join(rootDir, 'assets', 'styles.css'), path.join(targetDir, 'styles.css'));
copyFile(path.join(rootDir, 'assets', 'styles-d.css'), path.join(targetDir, 'styles-d.css'));
copyFile(path.join(rootDir, 'assets', 'styles-e.css'), path.join(targetDir, 'styles-e.css'));
copyFile(path.join(rootDir, 'assets', 'styles-fem.css'), path.join(targetDir, 'styles-fem.css'));
copyFile(path.join(rootDir, 'assets', 'avatar.png'), path.join(targetDir, 'assets', 'avatar.png'));
copyFile(path.join(rootDir, 'assets', 'cover-hero.jpg'), path.join(targetDir, 'assets', 'cover-hero.jpg'));
copyFile(path.join(rootDir, 'assets', 'media-1.jpg'), path.join(targetDir, 'assets', 'media-1.jpg'));

console.log(`已初始化任务目录：${targetDir}`);
console.log('下一步：编辑 index.html，保留需要的卡片并填入文章内容。');
