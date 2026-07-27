<!--
input: subtitles_words.json
output: 连续语气词索引列表
pos: 规则，建议删优先级

架构守护者：一旦我被修改，请同步更新：
1. 所属文件夹的 README.md
-->

# 连续语气词

## 模式

两个语气词连在一起：

```
嗯啊、啊呃、哦嗯、呃啊
```

## 检测

```javascript
const fillerWords = ['嗯', '啊', '哎', '诶', '呃', '额', '唉', '哦', '噢', '呀', '欸'];

if (fillerWords.includes(curr) && fillerWords.includes(next)) {
  markAsError(curr, next);
}
```

## 删除策略

全部删除。
