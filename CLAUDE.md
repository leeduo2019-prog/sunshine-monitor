# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

阳光平台监控系统 — 自动爬取青岛阳光采购平台（`www.qdygcg.com`）招标公告，按关键词筛选后通过钉钉机器人推送通知。

## 技术栈

- **Python 3** + Selenium (headless Chrome) 进行 SPA 页面爬取
- **BeautifulSoup4 + lxml** 解析 HTML
- **requests** 发送钉钉 Webhook 请求
- **python-dotenv** 管理环境变量
- **Windows 计划任务** (`schtasks`) 实现定时调度

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行主程序
python src/main.py

# 测试钉钉通知模块（需 .env 已配置）
python src/dingtalk_notifier.py

# 测试解析模块（需存在 page_saved.html）
python src/parser.py

# 测试爬虫模块
python src/crawler.py

# 创建 Windows 定时任务（需管理员权限）
deploy_schedule.bat

# 手动运行监控（批处理入口，带日志）
run_monitor.bat
```

> `run_monitor.bat` 使用 `%~dp0` 自适应路径，日志写入 `logs/monitor_YYYY-MM-DD.log`，可在任意目录部署。

## 架构与目录结构

项目采用**线性编排模式**，主入口 `src/main.py` 依次调用各模块：

```
src/
├── main.py              # 主入口：配置检查 → 爬虫 → 解析 → 筛选 → 去重 → 通知
├── config.py            # 集中配置管理，从 .env 读取所有参数
├── crawler.py           # Selenium 爬虫：访问 SPA 页面、点击筛选条件、分页遍历
├── parser.py            # HTML 解析：提取项目名称/招标人/发布时间、关键词过滤
├── dedup.py             # 项目去重：基于 JSON 持久化，30 天过期清理
└── dingtalk_notifier.py # 钉钉通知：加签验证、Markdown 格式、三类消息模板
```

### 数据流

1. **crawler.py** → `get_all_pages_html()` 返回合并后的 HTML 字符串
2. **parser.py** → `parse_projects()` 提取项目列表 → `filter_projects()` 关键词筛选
3. **dedup.py** → `filter_new_projects()` 对比 `data/project_history.json` 去重
4. **dingtalk_notifier.py** → `send_project_notifications()` 推送钉钉消息

### 关键设计细节

- **SPA 爬取**：目标站点为 Vue SPA，需等待 `li.number` 分页组件出现后才算就绪
- **筛选顺序**：`采购公告 → 全部(领域) → 全部(方式) → 今天`，时间筛选放最后避免被覆盖
- **分页策略**：不受 `MAX_PAGES` 限制，会一直爬到最后一页
- **去重存储**：`data/project_history.json`（GitHub Actions 用 `gh-pages` 分支持久化）
- **钉钉加签**：使用 HMAC-SHA256 + Base64 + URL-encode 生成签名参数
- **日志**：同时输出到控制台与 `logs/monitor.log`

## 配置

所有配置通过 `.env` 文件管理（复制 `.env.example` → `.env`）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DINGTALK_WEBHOOK_URL` | 钉钉机器人 Webhook | 必填 |
| `DINGTALK_SECRET` | 钉钉加签密钥 | 必填 |
| `FILTER_KEYWORDS` | 筛选关键词（逗号分隔） | 造价,审计,决算,财务,预算 |
| `MAX_PAGES` | 最大爬取页数 | 10 |
| `MAX_RETRIES` | 爬虫重试次数 | 3 |
| `PAGE_LOAD_TIMEOUT` | 页面加载超时(秒) | 120 |
| `ELEMENT_WAIT_TIMEOUT` | 元素等待超时(秒) | 30 |

`.env` 文件已在 `.gitignore` 中，**不要提交到版本控制**。

## 开发进展（2026-06-11 Cowork 会话）

本轮在 Cowork 沙箱端完成代码审查 + 修复，对应 commit `11a1533`。

### 已完成的修复

| 模块 | 改动 |
|------|------|
| `parser.py` | BS4 选择器替代字符串切分；新增 url 提取；日期支持 mm-dd 短格式；_is_valid_name 加严 |
| `crawler.py` | 点击顺序修正（时间筛选放最后）；点击失败降级不中断 |
| `config.py` | 新增 log_to_file 选项，写入 `logs/monitor.log` |
| `run_monitor.bat` | `%~dp0` 自适应路径；日志按日分文件 |
| `.env` / `.env.example` | 删除未使用的 SMTP 配置 |
| `README.md` | 修正目录名、补充 gh-pages 和 Actions 部署说明 |

### 当前 Git 状态

```
main 分支领先 origin/main 1 commit（11a1533），尚未 push
未暂存修改：CLAUDE.md、README.md、run_monitor.bat（本轮后续微调）
```

### CLI 接手后的待办

1. **推送代码**：先 commit 未暂存修改，然后 `git push origin main`
2. **验证 gh-pages**：`git fetch origin gh-pages && git ls-tree origin/gh-pages data/`，确认 `project_history.json` 存在
3. **触发 Actions**：push 后自动触发，用 `gh run list --workflow=<name>` 查看，`gh run view <id> --log` 看日志
4. **端到端验证**：确认钉钉收到通知、`data/project_history.json` 有新记录写入
