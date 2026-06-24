---
name: architecture-pragmatism
description: User priorities when doing architecture refactoring
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 96897d22-35a9-4b12-bed2-ca4407ce8daf
---

## 架构改进优先级

用户在 2026-06-09 架构审查中明确了以下立场：

### 做
- **消除代码重复**（如 shared/schemas.py 单一来源）— 一处修改、多处同步
- **拆分路由按依赖分层**（如 routes_data.py 零 ML 依赖，可独立 import）— 降低耦合
- **明确模块边界**（如加 docstring 说明 config 职责）— 低成本、高清晰度

### 不做
- **为测试而分离** — 用户明确说"现在没有测试需求"，因此不要为了可测试性而拆分模块（如 PipelineRunner 可视化分离被拒绝）

**Why:** 用户重视即时的维护收益（少改一处、不会改错），不追求尚未需要的测试基础设施。项目仍处于竞赛展示阶段，不是长期维护的 production 系统。

**How to apply:** 提议架构改动前，先回答："改完立刻能省多少维护？" 如果不能量化即时收益（比如 "一处修改 vs 两处修改"），搁置。
