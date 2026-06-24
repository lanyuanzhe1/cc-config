---
name: write_log
description: Use when the user wants to write a work log, session report, or work summary documenting what was accomplished. Triggers on phrases like "写工作报告", "写日志", "记录一下", "session log", "work report", or when wrapping up a significant session. Also use when the user says /write_log or mentions logging the session.
---

# Write Log

## Overview

Write a factual work log based on actual session activity. Technical details must be accurate — only record what really happened, never fabricate.

## File Naming

Format: `{name}_{MMDD}.{ext}`

- `name` = `session_log` (general) or descriptive phrase like `hsv_rdn_training`, `yolo_debug`
- `MMDD` = month + day from today's date (e.g., `0522` for May 22)

**MUST ask user to confirm the file name before writing.** Present the proposed name and wait for approval or revision.

## Output Formats

| User says | Format | Tool |
|-----------|--------|------|
| "写报告", "写日志" (default) | Markdown `.md` | Write |
| "写Word报告", "输出docx" | Word `.docx` | Use **docx** skill |

## Workflow

1. **Review the session** — scan what was actually done: files edited, commands run, decisions made, bugs found/fixed, results
2. **Propose file name** — ask user to confirm, suggest a name based on the work content
3. **Draft the log** with these sections (keep each concise):

```
# {title}

**日期:** YYYY-MM-DD
**分支:** {branch name}

## 完成事项
- bullet list of actual accomplishments

## 技术细节
- key technical decisions, parameters, file paths, commands (real values only)

## 遇到的问题
- bugs encountered and how they were resolved (if any)

## 结果/产出
- concrete outputs: model weights, metrics, config changes, new files

## 下一步
- next steps discussed (if any)
```

4. **Write the file** to the location agreed with user (default: project root or user-specified path)

## Rules

- **Details must be real** — copy actual file paths, git SHAs, command outputs, metrics from the session. Do not approximate.
- **No fabrication** — if something wasn't discussed, don't invent it. Sections can be omitted.
- **No commentary** — state facts, not opinions about the work.
- **Confirm name first** — never write before user approves the file name.
