---
name: yolo-detection-notes
description: YOLO检测关键设计决策 — 95类LifeWatch体系，结构张量法84.7% mAP50，形状结构为主
metadata: 
  node_type: memory
  type: project
  originSessionId: 95c26e9c-64d7-43aa-a412-2c2dc963faa7
---

V1.0 已从 6 类升级为 95 类 LifeWatch 标准体系，mAP50 **84.7%**（YOLOv8s）。结构张量偏振模拟是唯一有效方案（HSV 法 mAP50 仅 37.9%，已放弃）。

检测仍以形状结构特征（灰度）为主。95 类场景下，蓝藻 vs 硅藻 vs 甲藻的颜色差异（蓝绿 vs 金棕 vs 褐）可能成为未来区分依据，但当前数据集仅 293 张，颜色通道增益被数据量瓶颈压制。

**Why:** 6类→95类的跃迁改变了决策逻辑——95类下形态相似但颜色不同的藻种（如金棕硅藻 Nitzschia vs 蓝绿微囊藻群体）需要更多区分维度。但当前瓶颈仍是数据量（FMPD 293 张），不是特征工程。

**How to apply:** 后续扩充数据集时优先收集颜色差异大的藻种。训练时保持 gray-first 策略，但可实验性加入 RGB/HSV 通道看 mAP50-95 是否提升。
