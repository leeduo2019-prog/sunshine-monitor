# 阳光平台监控系统

自动爬取青岛阳光采购平台招标公告，按关键词筛选后发送钉钉通知。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入真实值：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```ini
# 钉钉机器人配置
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
DINGTALK_SECRET=SECxxxxxxxxxxxxxxxxxxxxxxxx

# 筛选关键词
FILTER_KEYWORDS=造价,审计,决算,财务,预算
```

> ⚠️ **不要将 `.env` 文件提交到版本控制！**

### 3. 运行

```bash
python src/main.py
```

## 配置说明

所有配置通过 `.env` 文件管理，主要参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `DINGTALK_WEBHOOK_URL` | 钉钉机器人 Webhook | - |
| `DINGTALK_SECRET` | 钉钉加签密钥 | - |
| `MAX_PAGES` | 最大爬取页数 | 10 |
| `MAX_RETRIES` | 爬虫重试次数 | 3 |
| `FILTER_KEYWORDS` | 筛选关键词（逗号分隔） | 造价,审计,决算,财务,预算 |

完整配置项见 `.env.example`。

## 功能特性

- ✅ 自动爬取多页公告
- ✅ 关键词筛选
- ✅ 项目去重（避免重复通知）
- ✅ 失败重试机制
- ✅ 钉钉通知（成功/失败/无匹配）
- ✅ 智能等待页面加载

## GitHub Actions 定时监控

无需本地运行，可通过 GitHub Actions 自动定时执行。

### 部署步骤

#### 1. 创建 GitHub 仓库并推送代码

```bash
git init
git add .
git commit -m "feat: 阳光平台监控初始版本"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

#### 2. 创建 `gh-pages` 分支（用于持久化去重数据）

```bash
git checkout --orphan gh-pages
mkdir -p data
echo '{}' > data/project_history.json
git add data/project_history.json
git commit -m "初始化去重数据"
git push origin gh-pages
git checkout main
```

#### 3. 配置 Repository Secrets

进入仓库 **Settings → Secrets and variables → Actions**，添加：

| Secret | 说明 |
|--------|------|
| `DINGTALK_WEBHOOK_URL` | 钉钉机器人 Webhook 完整地址 |
| `DINGTALK_SECRET` | 钉钉加签密钥 |

可选：添加 **Variables**：

| Variable | 说明 | 默认值 |
|----------|------|--------|
| `FILTER_KEYWORDS` | 筛选关键词 | `造价,审计,决算,财务,预算` |

### 运行时间

| Cron | UTC | 北京时间 |
|------|-----|----------|
| `0 0 * * *` | 00:00 | 08:00 |
| `0 8 * * *` | 08:00 | 16:00 |

### 数据持久化

去重数据 `data/project_history.json` 存储在 `gh-pages` 分支。每次工作流执行时：
1. 从 `main` 拉取代码
2. 从 `gh-pages` 恢复去重数据
3. 执行爬取和去重
4. 将更新后的数据提交回 `gh-pages`

### 手动触发

在仓库 **Actions → 阳光平台监控 → Run workflow** 可手动触发一次运行。

## Windows 定时任务

以管理员身份运行 `deploy_schedule.bat`，会创建两个每日任务（09:30 / 21:30）。

- 入口脚本：`run_monitor.bat`（自动定位项目根，日志写到 `logs/`）
- 不再使用 `setup_task.py`（已移除）

## 目录结构

```
wlpc-c1/
├── .env.example        # 环境变量模板
├── .gitignore
├── requirements.txt
├── deploy_schedule.bat # Windows 计划任务部署脚本
├── run_monitor.bat     # Windows 批处理入口（自适配路径）
├── README.md
├── CLAUDE.md
├── data/               # 运行数据（本地；GitHub Actions 用 gh-pages 分支持久化）
│   └── project_history.json  # 项目去重历史
├── logs/               # 运行日志（monitor.log、monitor_YYYY-MM-DD.log）
└── src/
    ├── config.py           # 配置管理 + 日志初始化
    ├── main.py             # 主入口
    ├── crawler.py          # 爬虫模块（Selenium）
    ├── parser.py           # 解析模块（BS4 选择器）
    ├── dedup.py            # 去重模块
    └── dingtalk_notifier.py # 钉钉通知模块
```

## 部署到 GitHub 的前置准备

1. 推送代码到 GitHub 仓库（默认分支 `main`）
2. 创建 `gh-pages` 分支并提交一份空的 `data/project_history.json`（用于首次去重数据）
3. 在 **Settings → Secrets and variables → Actions** 添加：
   - `DINGTALK_WEBHOOK_URL`
   - `DINGTALK_SECRET`
4. 工作流会在每个 cron 触发时拉取 `gh-pages` 数据、执行爬虫、回写 `gh-pages`

> ⚠️ 如果 `gh-pages` 分支不存在或权限被撤销，去重历史会丢失，钉钉可能收到重复推送。
