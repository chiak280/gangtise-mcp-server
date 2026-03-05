# Gangtise 开放平台 - 人工智能服务完整开发文档指南

# gangtise开放平台 - 人工智能服务 完整开发文档指南

本文档整合**全部已提供接口**，形成一套可直接用于对接开发的完整指南，包含鉴权、会话创建、知识库查询、指标Agent、智能助手全能力。

---

## 1. 文档概述

本文档适用于对接 gangtise 开放平台**人工智能服务**，包含：

- 会话创建（用于多轮对话上下文）

- 知识库单条/批量检索

- 经济/行业指标智能查询

- 深度研究Agent多轮对话

所有接口均需先获取 `accessToken` 完成鉴权。

---

## 2. 接入前置通用规范

### 2.1 通用请求头

所有接口必须携带：

|请求头名称|类型|说明|
|---|---|---|
|Authorization|String|格式：`Bearer {accessToken}`<br>accessToken 通过开放平台账号授权接口获取|
### 2.2 公共枚举（全局复用）

#### 2.2.1 知识库资源类型 resourceTypes

|数值|含义|
|---|---|
|10|券商研究报告|
|20|内部研究报告|
|40|首席分析师观点|
|50|公司公告|
|60|会议平台纪要|
|70|调研纪要公告|
|80|网络资源纪要|
|90|产业公众号|
#### 2.2.2 知识库类型 knowledgeNames

- `system_knowledge_doc`：系统库（默认）

- `tenant_knowledge_doc`：租户库

---

## 3. 接口总览

|接口名称|请求方式|接口地址|功能|
|---|---|---|---|
|创建新会话|GET|/application/open-ai/ai/chat/createGroup|创建会话ID，用于Agent接口多轮对话|
|知识库查询|POST|/application/open-data/ai/search/knowledge_base|单条问题知识库检索|
|知识库查询（批量）|POST|/application/open-data/ai/search/knowledge/batch|一次多条问题批量检索|
|指标查询Agent|POST/SSE|/application/open-ai/ai/search/indicator|经济/行业/公司指标查询，兼容OpenAI格式|
|Agent助手（深度研究）|POST(SSE)|/application/open-ai/ai/chat/sse|深度研究、产业链、投资逻辑、调研提纲等智能体|
---

# 4. 接口详细说明

## 4.1 人工智能服务 - 创建新会话

**作用**：生成 `groupId`，供 Agent 接口读取历史对话，实现多轮问答。

### 基本信息

|项|内容|
|---|---|
|请求URL|[https://open.gangtise.com/application/open-ai/ai/chat/createGroup](https://open.gangtise.com/application/open-ai/ai/chat/createGroup)|
|请求方式|GET|
### 返回示例

```JSON

{
    "code": "000000",
    "msg": "操作成功",
    "status": true,
    "data": 15
}
```

### 返回参数

|参数名|类型|说明|
|---|---|---|
|data|Long|会话ID（groupId）|
---

## 4.2 人工智能服务 - 知识库查询

**作用**：单个问题查询研报、公告、纪要等知识库内容。

### 基本信息

|项|内容|
|---|---|
|请求URL|[https://open.gangtise.com/application/open-data/ai/search/knowledge_base](https://open.gangtise.com/application/open-data/ai/search/knowledge_base)|
|请求方式|POST|
### 请求参数

|参数名|必选|类型|说明|
|---|---|---|---|
|query|是|String|查询问题|
|top|否|Integer|返回条数，默认10，最大20|
|resourceTypes|否|List<Integer>|资源类型（见2.2.1）|
|knowledgeNames|否|List<String>|知识库类型（见2.2.2）|
|startTime|否|Long|开始时间（13位时间戳）|
|endTime|否|Long|结束时间（13位时间戳）|
### 请求示例

```JSON

{
    "query":"介绍一下比亚迪",
    "resourceTypes":[10,40],
    "startTime":1715616000000,
    "endTime":1741920835000,
    "top":1
}
```

### 返回参数（核心）

|字段|说明|
|---|---|
|content|文本内容|
|resourceType|资源类型|
|title|文档标题|
|time|文档时间|
|sourceId|溯源ID|
|extraInfo.position|页码/总页数|
---

## 4.3 人工智能服务 - 知识库查询（批量）

**作用**：一次接口调用，同时查询 **最多5个问题**。

### 基本信息

|项|内容|
|---|---|
|请求URL|[https://open.gangtise.com/application/open-data/ai/search/knowledge/batch](https://open.gangtise.com/application/open-data/ai/search/knowledge/batch)|
|请求方式|POST|
### 请求参数

|参数名|必选|类型|说明|
|---|---|---|---|
|queries|是|List<String>|查询列表，最多5条|
|top / resourceTypes / knowledgeNames / startTime / endTime|否|-|同单条查询|
### 请求示例

```JSON

{
    "queries":["介绍一下比亚迪","最近热门的概念"],
    "resourceTypes":[10,40],
    "top":1
}
```

---

## 4.4 人工智能服务 - 指标查询Agent

**作用**：经济、行业、公司销量/财务等指标查询，**支持流式/非流式**，兼容 OpenAI Chat 格式。

### 基本信息

|项|内容|
|---|---|
|请求URL|[https://open.gangtise.com/application/open-ai/ai/search/indicator](https://open.gangtise.com/application/open-ai/ai/search/indicator)|
|请求方式|POST + SSE协议|
### 请求参数

|参数名|必选|类型|说明|
|---|---|---|---|
|text|是|String|查询内容|
|stream|否|Boolean|是否流式返回，默认false（非流式约等待10s）|
### 流式返回（stream=true）

以 `data: {...}` 逐帧返回。

### 非流式返回（stream=false）

结构同 OpenAI `chat.completion`，返回完整回答与推理过程。

---

## 4.5 人工智能服务 - Agent助手（深度研究模式）

**作用**：深度研究、产业链分析、投资逻辑、调研提纲、主题晨报等高级Agent能力，**SSE流式输出思考过程**。

### 基本信息

|项|内容|
|---|---|
|请求URL|[https://open.gangtise.com/application/open-ai/ai/chat/sse](https://open.gangtise.com/application/open-ai/ai/chat/sse)|
|请求方式|POST（SSE协议）|
### 主参数

|参数名|必选|类型|说明|
|---|---|---|---|
|text|是|String|问题|
|mode|是|String|固定：`deep_research`|
|groupId|否|Long|会话ID（有值则读取历史对话）|
|askChatParam|是|Object|深度研究参数|
### askChatParam 关键参数

- `message`：历史对话列表（user/assistant/system/tool）

- `includeSearchTypes`：信息来源（同2.2.1）

- `webEnable`：是否联网

- `traceId`：请求追踪ID

- `forcedAgent`：强制指定Agent

### 支持的Agent列表

|Agent|功能|
|---|---|
|searcher|数据搜索|
|investigation_outline|生成调研提纲|
|industry_expert|产业链分析|
|theme_daily_report|主题晨报|
|investment_logic|公司投资逻辑|
### 返回结构说明

|字段|说明|
|---|---|
|phase|think=思考阶段 / answer=回答阶段|
|round|思考轮次|
|title|步骤标题|
|result.delta|流式内容增量|
---

# 5. 公共状态码

## 5.1 HTTP状态码

|码|说明|
|---|---|
|200|成功|
|429|接口繁忙，请稍后重试|
## 5.2 业务错误码

更多错误码请以开放平台首页错误码文档为准。

---

# 6. 开发建议

1. 先调用 **创建新会话** 获取 groupId，再调用 Agent 接口可实现多轮对话。

2. 研报/公告类检索优先使用 **知识库接口**，数据指标类使用 **指标Agent**。

3. 前端展示推荐使用 **SSE流式**，体验更流畅。

4. 时间参数统一使用 **13位时间戳**。

需要我再把这份文档导出成 **Markdown 文件版** 或 **可直接贴进项目的 Wiki 格式** 吗？
> （注：文档部分内容可能由 AI 生成）