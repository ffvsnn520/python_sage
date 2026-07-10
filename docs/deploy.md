# PHP-Sage 部署说明

## Day13 当前必学

- 环境变量：API Key、模型地址、MySQL 密码不能写死在代码里。
- 镜像构建：用 Dockerfile 固化 Python 运行环境和启动命令。
- 服务编排：用 docker-compose 同时启动 API 服务和 MySQL。
- 数据初始化：上线前先运行离线摄入脚本，生成 Qdrant 本地索引。
- 健康检查：用 `/health` 判断服务是否真的加载完知识库。

## 本地部署流程

1. 准备配置：

```bash
cp .env.example .env
```

然后把 `.env` 里的 `API_KEY`、`MYSQL_PASSWORD`、`MYSQL_ROOT_PASSWORD` 改成真实值。

2. 构建镜像：

```bash
docker compose build
```

3. 初始化知识库：

```bash
docker compose run --rm php-sage python scripts/ingest.py
```

4. 启动服务：

```bash
docker compose up -d
```

5. 验证健康检查：

```bash
curl http://localhost:8000/health
```

`ready=true` 表示 FastAPI 已启动，Qdrant 索引已加载，服务可以接收问答请求。

## 最小上线检查

```bash
python scripts/check_day13_deploy.py
```

这一步只检查部署文件、配置安全和健康检查配置，不会真正启动 Docker。

## 暂缓进阶

- Nginx 反向代理、HTTPS 证书和域名解析。
- CI/CD 自动构建、自动测试和自动发布。
- 多副本部署、滚动发布、蓝绿发布。
- 线上密钥管理服务，例如云厂商 Secret Manager。
- Qdrant Server 模式、独立向量数据库和备份恢复。

## 建议补学时机

- Day14：结合日志、trace、latency 和 feedback 建立线上观测。
- 中级可靠性阶段：补 Nginx、HTTPS、熔断、重试和容量规划。
- 中级数据库阶段：补 MySQL 连接池、迁移、备份恢复和权限收敛。
