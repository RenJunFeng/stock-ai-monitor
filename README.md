# 股票 AI 监控分析系统

这是一个面向大 A 自选池的 AI 监控系统，支持：

- 自选股管理
- 手动和定时 AI 分析
- 监控大屏
- 告警日志
- 邮件提醒

## Docker 部署约定

已经固定好的部署参数：

- 前端容器名：`stock-ai-monitor-web`
- 后端容器名：`stock-ai-monitor-api`
- 对外访问端口：`51998`
- 对外访问地址：`http://服务器IP:51998`

`docker-compose.yml` 已经加了：

```yaml
restart: unless-stopped
```

这表示只要 Docker 服务本身开机自启，容器就会自动恢复运行。

## CentOS 启动和关闭

进入项目目录后：

启动：

```bash
docker compose up -d --build
```

关闭：

```bash
docker compose down
```

查看状态：

```bash
docker compose ps
```

查看日志：

```bash
docker compose logs -f
```

## 行情源排查

部署后可以直接检查实时行情是否真正连通：

```bash
curl "http://127.0.0.1:51998/api/market/quote/600519?stock_name=贵州茅台"
```

正常情况下会返回 `current_price` 和 `source`。如果行情源不可用，接口会返回错误，不会静默返回模拟价格。

临时允许模拟行情兜底时，可以在 `backend/.env` 中设置：

```env
MARKET_ALLOW_MOCK_FALLBACK=true
```

生产环境建议保持：

```env
MARKET_ALLOW_MOCK_FALLBACK=false
```

也可以直接用脚本：

启动：

```bash
bash scripts/start-docker.sh
```

关闭：

```bash
bash scripts/stop-docker.sh
```

查看状态：

```bash
bash scripts/status-docker.sh
```

## CentOS 开机自启

推荐用 `systemd` 托管整个 Docker 编排。

项目里已经准备好了：

- 服务模板：[deploy/systemd/stock-ai-monitor.service](/C:/Users/Administrator/Documents/投资项目开发/deploy/systemd/stock-ai-monitor.service)
- 安装脚本：[scripts/install-centos-service.sh](/C:/Users/Administrator/Documents/投资项目开发/scripts/install-centos-service.sh)

在服务器项目目录执行：

```bash
chmod +x scripts/*.sh
bash scripts/install-centos-service.sh
```

这一步会自动做几件事：

- 启用 Docker 开机自启
- 把项目注册成 `systemd` 服务 `stock-ai-monitor`
- 立即启动服务
- 设置系统开机自动拉起这套系统

安装完成后，常用命令如下：

启动：

```bash
sudo systemctl start stock-ai-monitor
```

停止：

```bash
sudo systemctl stop stock-ai-monitor
```

重启：

```bash
sudo systemctl restart stock-ai-monitor
```

查看状态：

```bash
sudo systemctl status stock-ai-monitor
```

查看开机自启是否生效：

```bash
sudo systemctl is-enabled stock-ai-monitor
sudo systemctl is-enabled docker
```

## 首次部署建议

如果你的 CentOS 服务器还没准备好 Docker，先确保：

```bash
docker --version
docker compose version
```

然后把项目放到一个固定目录，比如：

```bash
/opt/stock-ai-monitor
```

再进入该目录执行上面的启动命令或安装自启动脚本。

## 本地 Windows 脚本

如果你仍然会在本机调试，也保留了 PowerShell 脚本：

- [scripts/start-local.ps1](/C:/Users/Administrator/Documents/投资项目开发/scripts/start-local.ps1)
- [scripts/stop-local.ps1](/C:/Users/Administrator/Documents/投资项目开发/scripts/stop-local.ps1)
- [scripts/start-docker.ps1](/C:/Users/Administrator/Documents/投资项目开发/scripts/start-docker.ps1)
- [scripts/stop-docker.ps1](/C:/Users/Administrator/Documents/投资项目开发/scripts/stop-docker.ps1)

## 配置提醒

- 真实配置文件在 [backend/.env](/C:/Users/Administrator/Documents/投资项目开发/backend/.env)
- 如果要改行情来源，可修改 `MARKET_PROVIDER`
- 如果要启用邮件，请补齐 SMTP 配置
