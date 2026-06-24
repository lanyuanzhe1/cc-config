---
name: windows-dev
description: 用户在 Windows 上开发，部署到 Linux 机器人
metadata:
  type: user
---

用户在 Windows 上进行所有编码工作。代码通过 SSH 上传到机器人的 Ubuntu 22.04 系统执行。本地开发使用 Mock SDK 模拟硬件，不需要 Linux 环境。Python 跨平台，路径处理统一用 pathlib。

**Why:** 避免建议需要 macOS/Linux 的命令或工具。

**How to apply:** 所有开发命令和示例代码应该能在 Windows 上运行。部署相关的 Linux 命令标记清楚（仅机器人端执行）。不要建议 brew 或 macOS 专有工具。
