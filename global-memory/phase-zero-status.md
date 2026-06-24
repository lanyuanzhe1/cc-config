---
name: phase-zero-status
description: 当前项目状态 — 方案已确定，等待下载 SDK wheel
metadata:
  type: project
---

项目处于阶段 0.5：方案设计完成，等待从飞书下载 Python SDK wheel 文件。

已完成：
- 完整技术方案文档：`docs/我的方案/仿生机器人面部表情控制-整体方案.md`
- SDK 文档已下载到本地（4 份 Markdown）
- CLAUDE.md 已更新 SDK 详情

待执行（拿到 .whl 后）：
1. 解包验证 API 签名
2. 编写代码（Mock SDK + 五表情模板 + 安全层 + 控制器）
3. 上真机验证

技术决策：
- 中间参数映射法（ARKit blendshape → motor）
- 先手工规则基线，后 MLP 升级
- Blendshape 优先表达
- 完整安全层（5 层）
- Windows 开发 → Linux 部署

**Why:** 避免后续对话重新讨论方案，确保方向一致。

**How to apply:** 新对话中如果用户问"下一步做什么"，直接指向方案文档并推进阶段 0.5。
