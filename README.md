# Gangtise MCP Server

将 [Gangtise 开放平台](https://www.gangtise.com) 投研知识库接入 Claude Desktop，让 Claude 能直接检索研报、分析师观点、产业链数据，并调用 AI Agent 进行深度投研分析。

## 工具总览

| 工具 | 说明 | 响应时间 |
|------|------|---------|
| `gangtise_knowledge_search` | 单条知识库检索（研报、公告、纪要等） | 2-5s |
| `gangtise_knowledge_batch` | 批量检索，一次最多 5 个问题 | 2-5s |
| `gangtise_indicator` | 查询宏观/行业市场指标 | 10-45s |
| `gangtise_deep_research` | 调用 AI Agent 深度研究（5种Agent） | 47-251s |
| `gangtise_create_session` | 创建会话 ID，用于多轮对话 | <1s |
| `gangtise_daily_report` | 生成每日赛道追踪报告 | 30-60s |

---

## 安装与配置

### 环境要求

- Python 3.11+
- Gangtise 开放平台 API 凭证（`ACCESS_KEY` + `SECRET_KEY`）

### 安装

```bash
git clone https://github.com/chiak280/gangtise-mcp-server
cd gangtise-mcp-server
python3 -m venv .venv
.venv/bin/pip install -e .
```

### 配置凭证

在项目根目录创建 `.env` 文件：

```
GANGTISE_ACCESS_KEY=your_access_key
GANGTISE_SECRET_KEY=your_secret_key
```

### 接入 Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "gangtise": {
      "command": "/path/to/gangtise-mcp-server/.venv/bin/python",
      "args": ["/path/to/gangtise-mcp-server/server.py"]
    }
  }
}
```

保存后**重启 Claude Desktop** 生效。

---

## 工具详细说明

### gangtise_knowledge_search — 单条知识库检索

在 Gangtise 投研知识库中检索研报、公告、纪要等内容。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | ✅ | 查询问题 |
| `resource_types` | list | 否 | 资源类型过滤，见下表 |
| `top` | int | 否 | 返回条数，默认 20，最大 20 |
| `days` | int | 否 | 只查最近 N 天，不填则不限时间 |

**资源类型（resource_types）：**

| 类型名称 | 说明 |
|---------|------|
| `券商研究报告` | 证券公司发布的研究报告 |
| `内部研究报告` | 机构内部研究报告 |
| `首席分析师观点` | 首席分析师观点文章 |
| `公司公告` | 上市公司公告、年报、季报 |
| `会议平台纪要` | 电话会议纪要 |
| `调研纪要公告` | 机构调研纪要 |
| `网络资源纪要` | 网络整理纪要 |
| `产业公众号` | 产业相关公众号文章 |

**示例：**
```
# 查询长川科技近90天的券商研报
gangtise_knowledge_search(
    query="长川科技 深度报告 投资评级",
    resource_types=["券商研究报告"],
    days=90
)
```

---

### gangtise_knowledge_batch — 批量知识库检索

一次调用同时查询最多 5 个问题，效率是逐条查询的 5 倍。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `queries` | list | ✅ | 查询列表，最多 5 条 |
| `resource_types` | list | 否 | 资源类型过滤（同上） |
| `top` | int | 否 | 每个问题返回条数，默认 20，最大 20 |
| `days` | int | 否 | 只查最近 N 天 |

**示例：**
```
# 一次采集公司多维度信息
gangtise_knowledge_batch(
    queries=[
        "长川科技 主营业务 收入结构",
        "长川科技 行业地位 竞争对手",
        "长川科技 核心客户 下游应用",
        "长川科技 近期订单 2025",
        "长川科技 管理层 股权结构"
    ]
)
```

---

### gangtise_indicator — 宏观/行业指标查询

查询宏观经济和行业市场的结构化数据，底层为 AI 驱动的指标检索。

**⚠️ 重要限制：**
- ✅ **支持**：宏观指标（GDP、CPI、PMI、M2、利率）、行业市场数据（市场规模、产能、销量、价格指数）
- ❌ **不支持**：A 股个股财务数据（营收/净利润/毛利率等）。个股财务请改用 `gangtise_knowledge_search` 查年报/研报

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `query` | string | ✅ | 自然语言查询 |

**示例（✅ 有效）：**
```
gangtise_indicator(query="中国半导体设备市场规模 2022 2023 2024")
gangtise_indicator(query="全球光模块出货量趋势")
gangtise_indicator(query="中国GDP增速 2023 2024")
```

**示例（❌ 无效，返回"获取数据失败"）：**
```
gangtise_indicator(query="长川科技 2024年营收 净利润")  # 个股财务不支持
```

---

### gangtise_deep_research — 深度研究 Agent

调用 Gangtise AI Agent 进行深度研究分析，支持 5 种专用 Agent。

**⚠️ 响应时间说明：** 此工具需要 47-251 秒，是重型工具，轻量查询请优先使用 `gangtise_knowledge_batch`。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `question` | string | ✅ | 研究问题（格式见各Agent要求） |
| `agent` | string | 否 | Agent 类型，不填则自动选择 |
| `group_id` | int | 否 | 会话 ID，用于多轮对话 |
| `web_enable` | bool | 否 | 是否联网，默认 true |
| `include_types` | list | 否 | 限定信息来源类型 |

---

#### 5 种 Agent 详细说明

##### 1. `searcher` — 数据搜索

搜索公司最新订单、业绩、公告等实时数据，会主动检索公告库并联网查询。

| 项目 | 说明 |
|------|------|
| **实测耗时** | ~47 秒 |
| **问题格式** | `"公司名 + 简短查询关键词"`，总长度不超过 15 字 |
| **返回内容** | 最新订单数据、业绩数字、关键事件，附引用来源 |

```
# ✅ 正确
gangtise_deep_research(question="长川科技最新订单", agent="searcher")
gangtise_deep_research(question="中际旭创2025年业绩", agent="searcher")

# ❌ 错误（问题过长，返回"发生未知错误"）
gangtise_deep_research(question="请帮我搜索长川科技最新的订单情况和业绩数据", agent="searcher")
```

---

##### 2. `investment_logic` — 投资逻辑

生成公司完整投资逻辑报告，包含短期催化剂和长期成长驱动力。

| 项目 | 说明 |
|------|------|
| **实测耗时** | ~60 秒 |
| **问题格式** | **直接输入公司名**，不加任何其他描述 |
| **返回内容** | 短期逻辑（季度催化剂）+ 长期逻辑（成长主题），附参考资料引用 |

```
# ✅ 正确
gangtise_deep_research(question="长川科技", agent="investment_logic")
gangtise_deep_research(question="北方华创", agent="investment_logic")

# ❌ 错误（不要加任何描述）
gangtise_deep_research(question="长川科技投资逻辑分析", agent="investment_logic")
```

**返回示例结构：**
```
## 短期逻辑
### 1. 存储大厂扩产招标落地在即...
### 2. 日系设备断供带来转单窗口...

## 长期逻辑
### 1. 平台化布局打开成长天花板...
### 2. 国产替代浪潮持续深化...
```

---

##### 3. `investigation_outline` — 调研提纲

生成机构调研框架，聚焦当前市场最关心的热点问题，适合调研前准备。

| 项目 | 说明 |
|------|------|
| **实测耗时** | ~67 秒 |
| **问题格式** | **直接输入公司名**，不加任何其他描述 |
| **返回内容** | 按热门话题/公司经营/行业背景/财务质量/其他分类的调研问题清单，含背景说明 |

```
# ✅ 正确
gangtise_deep_research(question="长川科技", agent="investigation_outline")
gangtise_deep_research(question="中际旭创", agent="investigation_outline")

# ❌ 错误
gangtise_deep_research(question="请生成长川科技的调研提纲", agent="investigation_outline")
```

**返回示例结构：**
```
## 热门话题
### 季度订单环比变化及增长驱动因素
背景：...
问题：...

## 公司经营
### 内江基地二期产能爬坡进度...

## 财务质量
### 毛利率提升可持续性...
```

---

##### 4. `industry_expert` — 产业链分析

生成公司产业链全景报告，涵盖上游供应商、公司定位、下游客户及各环节具体公司名单。

| 项目 | 说明 |
|------|------|
| **实测耗时** | ~251 秒（最慢，约4分钟） |
| **问题格式** | **`"公司名" + "产业链"`**，如 `"长川科技产业链"` |
| **返回内容** | 一级子分类（6个）+ 二级子分类 + 各环节关联公司名单（实测约46家） |

```
# ✅ 正确
gangtise_deep_research(question="长川科技产业链", agent="industry_expert")
gangtise_deep_research(question="北方华创产业链", agent="industry_expert")

# ❌ 错误（宽泛行业词会触发过多检索，必然失败）
gangtise_deep_research(question="半导体", agent="industry_expert")
gangtise_deep_research(question="半导体设备产业链", agent="industry_expert")
gangtise_deep_research(question="光通信", agent="industry_expert")
```

**失败原因：** `industry_expert` 以公司名为锚点检索资料，精确公司名约检索 35 条（可处理），宽泛行业词检索 49+ 条，超出内部处理上限导致失败。

**返回示例结构（以长川科技为例）：**
```
# 长川科技产业链全景分析

## 上游：电子元器件
- 被动元器件：江苏芯声微电子（供应基础元器件）
- 半导体石英制品：浙江泓芯新材料（供应高纯石英材料）
- 精密陶瓷基板：景德镇奈创陶瓷（供应绝缘基材）
- 流体控制部件：深圳蓝动精密（供应气液控制组件）

## 上游：机械加工
...

## 中游：长川科技（集成电路装备制造）
公司在产业链的定位、话语权分析...

## 下游：封装测试
...

## 下游：晶圆制造
...
```

---

##### 5. `theme_daily_report` — 主题晨报

生成赛道最新动态报告，包含宏观政策、行业新闻、公司动态等。

| 项目 | 说明 |
|------|------|
| **实测耗时** | ~64 秒 |
| **问题格式** | **赛道名称**，如 `"光通信"`、`"AI算力"`、`"半导体设备"` |
| **返回内容** | 宏观政策动态 + 行业新闻 + 公司公告 + 市场展望 |

```
# ✅ 正确
gangtise_deep_research(question="光通信", agent="theme_daily_report")
gangtise_deep_research(question="半导体设备", agent="theme_daily_report")
gangtise_deep_research(question="AI算力", agent="theme_daily_report")
gangtise_deep_research(question="先进封装", agent="theme_daily_report")
```

---

#### Agent 选用速查

| 需求 | 推荐 Agent | 问题格式 |
|------|-----------|---------|
| 公司最新订单/业绩/公告 | `searcher` | `"公司名+关键词"` |
| 公司投资逻辑 | `investment_logic` | `"公司名"` |
| 调研前准备问题清单 | `investigation_outline` | `"公司名"` |
| 产业链上下游全景+公司名单 | `industry_expert` | `"公司名产业链"` |
| 赛道每日动态 | `theme_daily_report` | `"赛道名"` |
| 综合深度研究 | 不指定（自动） | 详细问题均可 |

---

### gangtise_create_session — 创建多轮对话会话

创建 `groupId`，传入后续 `gangtise_deep_research` 调用可保持对话上下文。

```
# 创建会话
session = gangtise_create_session()  → 返回 group_id = 123

# 基于同一会话连续提问
gangtise_deep_research(question="长川科技", agent="investment_logic", group_id=123)
gangtise_deep_research(question="和北方华创相比有哪些优劣势？", group_id=123)
```

---

### gangtise_daily_report — 每日赛道追踪报告

对指定赛道生成每日追踪报告，并发调用 Agent 晨报 + 知识库券商观点。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `sectors` | list | ✅ | 赛道列表 |
| `focus_points` | list | 否 | 重点关注方向 |
| `days` | int | 否 | 拉取最近 N 天，默认 3 天 |

```
gangtise_daily_report(
    sectors=["半导体设备", "光通信", "先进封装"],
    focus_points=["国产替代进展", "美国出口管制影响"]
)
```

---

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
├── prompts/
│   └── TMT个股深度研究_prompt模板.md   # TMT 个股研究 Prompt 模板
├── logs/
│   └── server.log         # 运行日志（不输出到 stdout）
├── pyproject.toml
└── .env                   # API 凭证（不提交 git）
```

## 日志

运行日志写入 `logs/server.log`，不输出到 stdout（避免干扰 MCP JSON-RPC 通信）。
