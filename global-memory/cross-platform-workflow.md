---
name: cross-platform-workflow
description: User switches between macOS and Windows for this project
metadata: 
  node_type: memory
  type: user
  originSessionId: a2807aa9-74c7-466e-ac86-21a9fa87579f
---

The user works on this project from both macOS and Windows machines. The conda environment `lnn_env` is consistent across platforms, but absolute paths differ (macOS: `/opt/homebrew/...`, Windows: `A:\Software\Anaconda\...`). When suggesting commands or file paths, prefer relative paths from the project root or `conda run -n lnn_env python ...` over hardcoded absolute interpreter paths. Verify which platform is current before assuming tool locations.
