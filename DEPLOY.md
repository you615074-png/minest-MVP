# minest-MVP 云服务器部署指南

## 前置条件

- Linux 服务器（Ubuntu 20.04+ / CentOS 7+）
- 已安装 Docker 和 Docker Compose
- 已配置 `.env` 文件（填写 API Keys）
- 域名（可选，HTTPS 需要）

## 快速部署（5 分钟）

```bash
# 1. 克隆仓库
git clone https://github.com/you615074-png/minest-MVP.git
cd minest-MVP
git checkout master

# 2. 配置环境变量
cp .env.example .env
nano .env  # 填入 DeepSeek/Kimi/MiniMax API Key

# 3. 启动服务
docker compose up -d

# 4. 访问 http://your-server-ip:8501
```

## HTTPS 配置（可选）

```bash
# 1. 申请 SSL 证书（使用 certbot）
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com

# 2. 挂载证书
mkdir -p nginx-certs
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx-certs/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx-certs/

# 3. 修改 docker-compose.yml 中 nginx 的 volumes:
# - ./nginx-certs:/etc/nginx/certs:ro

# 4. 更新 nginx.conf 中的 server_name 为你的域名

# 5. 重启
docker compose down && docker compose up -d
```

## 仅 Streamlit 部署（无 Nginx/HTTPS）

```bash
docker run -d --name minest-sdr --restart unless-stopped \
  -p 8501:8501 \
  -v $(pwd)/.env:/app/.env:ro \
  minest-sdr
```

## 常用运维命令

```bash
# 查看日志
docker compose logs -f minest

# 重启
docker compose restart

# 停止
docker compose down

# 更新代码后重新构建
git pull origin master
docker compose build --no-cache
docker compose up -d

# 查看运行状态
docker compose ps
```

## 性能调优

在 `.env` 中调整：

```
RATE_LIMIT_RPM=30       # 批量模式每分钟调用数，根据 API 配额调整
```

在 `docker-compose.yml` 中可设置资源限制：

```yaml
services:
  minest:
    deploy:
      resources:
        limits:
          memory: 1G
```

## 数据持久化

- `app_data.db` 存储在 `./data/` 目录（Volume 挂载）
- `minest.log` 存储在容器内 `/app/minest.log`
- 备份：`docker compose cp minest:/app/data/app_data.db ./backup/`
