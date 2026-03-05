# Gangtise MCP Server

将 [Gangtise 开放平台](https://www.gangtise.com) 投研知识库接入 Claude Desktop，让 Claude 能直接检索研报、分析师观点、产业链数据，并调用 AI Agent 进行深度投研分析。

## 功能

提供 6 个工具：

| 工具 | 说明 |
|------|------|
| `gangtise_knowledge_search` | 单条知识库检索（研报、公告、纪要等） |
| `gangtise_knowledge_batch` | 批量检索，一次最多 5 个问题 |
| `gangtise_indicator` | 查询经济指标、行业数据、公司财务/销量 |
| `gangtise_deep_research` | 调用 AI Agent 进行深度研究（产业链/投资逻辑/调研提纲等） |
| `gangtise_create_session` | 创建会话 ID，用于多轮对话保持上下文 |
| `gangtise_daily_report` | 生成每日赛道追踪报告（含券商观点、公司动态） |

## 环境要求

- Python 3.10+
- Gangtise 开放平台 API 凭证（`ACCESS_KEY` + `SECRET_KEY`）

## 安装

```bash
# 克隆项目
git clone <repo-url>
cd gangtise-mcp-server

# 创建虚拟环境并安装依赖
python3 -m venv .venv
.venv/bin/pip install -e .
```

## 配置

在项目根目录创建 `.env` 文件：

```bash
GANGTISE_ACCESS_KEY=your_access_key
GANGTISE_SECRET_KEY=your_secret_key
```

## 接入 Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`，添加以下配置：

```json
{
  "mcpServers": {
    "gangtise": {
      "command": "/path/to/gangtise-mcp-server/.venv/bin/python",
      "args": ["/path/to/gangtise-mcp-server/server.py"],
      "env": {
        "GANGTISE_ACCESS_KEY": "your_access_key",
        "GANGTISE_SECRET_KEY": "your_secret_key"
      }
    }
  }
}
```

> 将 `/path/to/gangtise-mcp-server` 替换为实际路径，也可通过 `.env` 文件管理凭证而不在配置中明文填写。

保存后**重启 Claude Desktop** 即可生效。

## 工具使用示例

### 知识库检索

```
查询最近 7 天光通信行业的券商研报
```

```
同时查询：1) 英伟达 GPU 集群网络架构  2) 800G 光模块主要厂商  3) 光通信国产替代进度
```

### 深度研究 Agent

支持以下 Agent 类型：

| Agent | 中文别名 | 适用场景 |
|-------|----------|----------|
| `searcher` | 数据搜索 | 搜索特定数据和信息 |
| `industry_expert` | 产业链分析 | 深度产业链研究 |
| `investment_logic` | 投资逻辑 | 分析公司或行业投资逻辑 |
| `investigation_outline` | 调研提纲 | 生成调研框架 |
| `theme_daily_report` | 主题晨报 | 生成主题赛道每日报告 |

多轮对话示例：

```
# 第一步：创建会话
调用 gangtise_create_session → 获得 group_id

# 第二步：基于同一会话连续提问
用 group_id 调用 gangtise_deep_research，追问上下文相关问题
```

### 每日赛道报告

```
生成今日半导体设备、光通信、先进封装的每日追踪报告，重点关注券商最新观点和投资机会
```

## 项目结构

```
gangtise-mcp-server/
├── server.py              # MCP Server 入口
├── gangtise_client.py     # Gangtise API 客户端（认证、请求、SSE 流处理）
├── tools/
│   ├── knowledge.py       # 知识库检索工具
│   ├── indicator.py       # 经济指标工具
│   ├── agent.py           # 深度研究 Agent 工具
│   └── report.py          # 每日报告工具
├── scripts/
│   ├── test_auth.py       # 鉴权测试脚本
│   └── daily_report.sh    # 每日报告定时脚本（配合 cron）
├── pyproject.toml
└── .env                   # API 凭证（不提交到 git）
```

## 日志

运行日志写入 `logs/server.log`，不输出到 stdout（避免干扰 MCP JSON-RPC 通信）。

## 定时报告（可选）

配置 crontab，每个工作日早上 8:30 自动生成每日报告：

```bash
crontab -e
# 添加以下行：
30 8 * * 1-5 /path/to/gangtise-mcp-server/scripts/daily_report.sh
```
