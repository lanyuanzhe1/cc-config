---
name: memory
description: Manage Claude Code persistent memory. Use when user wants to list, clean, save, or review memories — or mentions /memory, "管理记忆", "更新memory", "清理记忆", "保存到记忆", "查看记忆"
user_invocable: true
---

# Memory Manager

管理 Claude Code 的持久化记忆系统。记忆存放在 `~/.claude/projects/<project>/memory/` 下，分为四种类型。

## Usage

```
/memory              → 列出全部记忆，标记过期风险
/memory clean        → 逐条审查：保留/删除/重写
/memory save <内容>  → 自动识别类型，写入新记忆
/memory types        → 显示四种类型的数量占比
/memory help         → 显示此帮助
```

## Standard Operation

**列出记忆**：读取 MEMORY.md 索引 + 每条记忆文件的 frontmatter。计算每条记忆的"新鲜度"——超过 7 天的 project 类型标记为 `⚠ stale`，超过 14 天的标记为 `🔴 likely rotten`。

**审查清理**：逐条展示记忆内容摘要（前 3 行），让用户选择 `[K]eep / [D]elete / [R]ewrite`。删除时先备份内容再删除文件。重写时询问新内容。最后更新 MEMORY.md 索引。

**保存记忆**：先判断内容属于哪种类型（feedback/project/reference/user），在 frontmatter 中设置正确的 type。自动生成 name slug（kebab-case）。写入后追加 MEMORY.md 索引行。

**类型占比**：统计 MEMORY.md 中每条记忆的 type，计算百分比，与推荐比例对比（50% feedback / 20% user / 20% reference / 10% project），标出偏差。

## Advanced: Quick Commands

用户可以直接说自然语言而不用 `/memory` 前缀，例如：
- "记住：xxx" → 等同于 `/memory save`
- "忘记关于 xxx 的记忆" → 等同于 `/memory clean` 单条
- "我的记忆健康吗" → 等同于 `/memory types`
