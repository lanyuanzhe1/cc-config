---
name: aliyun-ecs-deployment
description: Alibaba Cloud ECS server connection and deployed services
metadata: 
  node_type: memory
  type: reference
  originSessionId: 96897d22-35a9-4b12-bed2-ca4407ce8daf
---

## 服务器

| 项目 | 值 |
|------|-----|
| 公网 IP | `120.27.15.235` |
| 内网 IP | `172.19.136.155` |
| SSH 别名 | `ssh aliyun-ecs` |
| SSH 密钥 | `~/.ssh/id_ed25519_aliyun` |
| 用户 | `root` |

## 部署架构

```
nginx (:80) → /            → Vue3 SPA (/www/wwwroot/algae_image/)
            → /api/v1/*    → FastAPI (:8000) 反向代理
            → /static/*    → FastAPI 静态文件
```

## 服务

- **藻影知微前端**: `http://120.27.15.235` — Vue3 SPA，nginx 托管
- **轻量 API**: systemd `algae-image.service`，代码在 `/opt/algae_image/server_light.py`
- **shared schemas**: `/opt/algae_image/shared/schemas.py`
- **宝塔面板**: `https://120.27.15.235:8888`

## 管理

```bash
ssh aliyun-ecs
systemctl status algae-image
systemctl restart algae-image
journalctl -u algae-image -f
```

## 部署命令

```bash
# 更新前端
scp -r code/algae_image_v2/frontend/dist/* aliyun-ecs:/www/wwwroot/algae_image/

# 更新后端
scp code/algae_image_v2/deploy/server_light.py aliyun-ecs:/opt/algae_image/
scp code/algae_image_v2/shared/schemas.py aliyun-ecs:/opt/algae_image/shared/
ssh aliyun-ecs "systemctl restart algae-image"
```

## 服务器规格

- 2 核 CPU / 1.6GB 内存 / 40GB 磁盘
- 无 GPU
- Ubuntu 26.04 LTS
- Python 3.14.4
