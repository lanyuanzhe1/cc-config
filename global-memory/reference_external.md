---
name: reference-external
description: 外部资源指针 — 代码仓库、云服务器、竞赛文书、关键文档位置
metadata: 
  node_type: memory
  type: reference
  originSessionId: 95c26e9c-64d7-43aa-a412-2c2dc963faa7
---

## 代码仓库

- GitHub: `https://github.com/lanyuanzhe1/algaeimage.git`
- 知识笔记: `E:\code\learn\` (claude-code-knowledge.md, 网络学习.md)

## 云 GPU 服务器

训练用 RTX 5060 Ti，SSH 信息运行时从 `.claude/settings.json` 定时任务中获取（不在 memory 中硬编码密码）。

## 关键设计文档

- CLAUDE.md: `E:\code\codex\CLAUDE.md`
- code/README.md: 完整目录地图和权重清单
- docs/handoff-20260524-algae-guardian-v1.md: V1 构建交接文档
- docs/v1_product_build_0524.md: V1 产品构建日志

## 竞赛文书 (2026 光电设计竞赛)

- 旧策划书: `项目文书/策划书——藻影知微队.pdf`
- 旧PPT: `项目文书/藻影知微——水下偏振原位智能成像系统.pptx`
- 新技术方案: `项目文书/技术方案——藻影知微.md` + `.docx`
- 技术文书智能体: `.claude/agents/algae_technical_writer.agent.md`

## 模型权重位置

- RDN: `algae_image_v1/weights/rdn_polarization.pth` (PSNR 62.46dB)
- YOLO: `algae_image_v1/weights/best.pt` (YOLOv8s, mAP50 84.7%)
- 权重不在 git 中，由 Git LFS 追踪
