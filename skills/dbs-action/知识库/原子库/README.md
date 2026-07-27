# 原子库说明

## 数据来源

- 推文总量：12,307 条
- 筛选后实质性内容：4,201 条
- 最终知识原子：4176 个
- 时间范围：2024-10-20 ~ 2026-03-20

## 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 格式：{季度}_{序号}，如 2024Q4_001 |
| knowledge | string | 提炼后的知识点陈述句 |
| original | string | 推文原文（最多200字） |
| url | string | 推文链接 |
| date | string | 发布日期 |
| topics | string[] | 主题分类（10类） |
| skills | string[] | 关联 Skill |
| type | string | principle/method/case/anti-pattern/insight/tool |
| confidence | string | high/medium/low |

## 文件结构

- `atoms.jsonl` — 全量合并（4,176 条）
- `atoms_{季度}.jsonl` — 按季度拆分
- `atoms_{季度}_draft.jsonl` — 中间文件（可删除）

## 统计

- 2024Q4: 740 条
- 2025Q1: 586 条
- 2025Q2: 742 条
- 2025Q3: 689 条
- 2025Q4: 665 条
- 2026Q1: 754 条