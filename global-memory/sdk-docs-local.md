---
name: sdk-docs-local
description: 松延动力 Noetix Hobbs SDK 文档已下载到本地
metadata:
  type: reference
---

SDK 技术文档已从飞书抓取并保存为本地 Markdown 文件：

- `公司资料/文档/01-SDK必读-通用篇.md` — SDK 概述、舵机映射表（29 舵机完整表）、配置格式、Blendshape 标准（51 种 ARKit）、音频格式要求（PCM 16kHz 单声道）
- `公司资料/文档/04-PythonSDK-API参考-v2.0.0.md` — 完整 Python API：HobbsLog、RobotConfigLoader、MotorController 的所有方法签名和参数表
- `公司资料/文档/02-SDK-Demo资源下载.md` — 版本信息（Python v0.2.0 最新、C++ 未开放、Android v2.3）
- `公司资料/文档/03-镜像烧录和示例程序.md` — 刷机步骤（RKDevTool）、CAN/USB 配置命令、demo 运行参数

SDK 核心 API：`motor.setFaceAngles([29个角度], time_ms)` 控制面部，`motor.setNeckRadiosPositionDuration([3个归一化值], duration_sec)` 控制颈部。

SDK 安装方式：`pip install noetix_hobbs_sdk-xxxxx.whl`，导入 `import noetix_hobbs_sdk as nhs`。

飞书文档链接：https://noetixrobotics.feishu.cn/wiki/B9oCwy2i9i6H6KkCYf2cpeSNnWe
