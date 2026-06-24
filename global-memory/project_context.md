---
name: ""
description: 藻影卫士偏振显微监测 — 当前状态与目标，2026-05-29 更新
metadata: 
  node_type: memory
  type: project
  originSessionId: 89f35391-5e74-49c5-9461-0323ab8e473e
---

## 项目定位

藻类显微图像偏振检测的研究到产品管线。

| 目录 | 状态 | 说明 |
|------|------|------|
| `code/algae_image_v2/` | **当前产品主线** | V2.0，5类FMPD，HSV偏振，已封装exe |
| `code/algae_image_v1/` | 稳定备份 | V1.0，95类LifeWatch，结构张量+RDN，论文答辩版 |
| `code/algae_guardian/` | 研究参考 | 训练/评估/实验 |
| `code/Polar_sim_0520/` | 算法来源 | 结构张量管线，mAP50 84.7% |
| `code/Polar_sim_0522/` | 已废弃 | HSV 管线实验，含 Docker 训练环境 |
| `code/RDN_HSV_0526/` | 实验对照 | HSV+RDN 对照实验，为V2跳过RDN提供实验依据 |

**当前分支**: `HSV`。`algae_image_v1/` 和 `algae_image_v2/` 均未 git 提交。

## 近期目标

- V2 exe 封装已完成（PyInstaller onedir，dist-release/）
- 云部署已完成
- 后续：采集更多数据扩充 FMPD（当前仅293张是瓶颈）

## 环境

- 本地: Windows 11, conda `ican` (Python 3.11, A:\Anaconda_envs\envs\ican)
- 本地 GPU: RTX 4050 Laptop 6GB
- 云 GPU: RTX 5060 Ti 16GB (训练用)
- 模型后端: DeepSeek v4-pro[1m]
