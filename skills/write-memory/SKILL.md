---
name: write-memory
description: Extract key learnings from the current session and persist them to the Memory system. Use when user says /write_memory, "保存记忆", "写记忆", "记录这次对话", or when a session is ending and significant learnings occurred. Also triggered automatically via Stop hook.
user_invocable: true
---

# Write Memory

从当前会话中提取值得持久化的信息，写入 `~/.claude/projects/<project>/memory/`。

## 执行流程

### 1. 扫描当前会话

回顾对话历史，找出以下信号：

**Feedback（最重要，应占50%）**：
- 用户纠正了你的做法："不要 X"、"下次 Y"、"别用 Z"
- 用户明确认可了一个非显而易见的做法："对，就是这样"
- 用户表达了强烈的偏好

**User（占20%）**：
- 用户提到了新的角色/职责/知识背景
- 用户在某个领域表现出深度或缺乏经验

**Reference（占20%）**：
- 用户分享了新的外部链接、SSH地址、仪表盘URL
- 注意：不存密码/token，只存指针

**Project（占10%）**：
- 新的目标、截止日期、状态变更
- 注意：代码能推导的信息不存

### 2. 过滤

跳过以下内容：
- 已在 CLAUDE.md 中的信息
- 代码本身能推导的（文件路径、函数名、git历史）
- 临时的、一次性的任务细节
- 通用编程建议（不是针对这个项目的）

### 3. 写入

对每条要保存的信息：
1. 确定类型（feedback/user/reference/project）
2. 生成 kebab-case 文件名
3. 写入 frontmatter（name, description, type）
4. body 格式：feedback/project 类必须包含 **Why** 和 **How to apply**
5. 追加 MEMORY.md 索引行（不超过150字符）

如果更新已有记忆：先读原文件，合并内容，保留原有价值部分。

### 4. 报告

输出简短报告：
```
本次写入: N 条
  新建: [文件名] (类型)
  更新: [文件名] (类型)
  跳过: [原因]
当前记忆总数: N，类型占比: feedback X% user X% reference X% project X%
```

## 关键约束

- 宁可少存，不存垃圾。不确定是否该存的内容，跳过。
- 每条 feedback 必须有具体的 Why 和 How to apply。
- 发现记忆腐烂（过时的project信息）时主动更新或标记。
- 不要重复存储 CLAUDE.md 中已有的规则。
