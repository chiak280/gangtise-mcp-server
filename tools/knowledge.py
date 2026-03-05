"""知识库查询工具（单条 + 批量）"""

from typing import Any, Optional

from mcp.types import TextContent, Tool

from gangtise_client import GangtiseClient, RESOURCE_TYPE_MAP

_RESOURCE_TYPES_HINT = "、".join(RESOURCE_TYPE_MAP.keys())

KNOWLEDGE_SEARCH_TOOL = Tool(
    name="gangtise_knowledge_search",
    description=(
        "在 Gangtise 投研知识库中检索研报、分析师观点、公司公告、纪要等内容。"
        "适合查询特定行业/公司的研究内容、券商观点、最新动态。"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "查询问题，例如：'英伟达GPU集群网络架构' 或 '光模块市场规模'"
            },
            "resource_types": {
                "type": "array",
                "items": {"type": "string"},
                "description": f"资源类型过滤，可选：{_RESOURCE_TYPES_HINT}。不填则查询所有类型。",
            },
            "top": {
                "type": "integer",
                "description": "返回条数，默认10，最大20",
                "default": 10,
            },
            "days": {
                "type": "integer",
                "description": "只查询最近N天的内容，不填则不限时间",
            },
        },
        "required": ["query"],
    },
)

KNOWLEDGE_BATCH_TOOL = Tool(
    name="gangtise_knowledge_batch",
    description=(
        "在 Gangtise 知识库中批量检索，一次最多5个问题。"
        "适合同时研究多个子话题，例如同时查询'光模块规格'和'相关上市公司'。"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "queries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "查询列表，最多5条",
            },
            "resource_types": {
                "type": "array",
                "items": {"type": "string"},
                "description": f"资源类型过滤，可选：{_RESOURCE_TYPES_HINT}",
            },
            "top": {
                "type": "integer",
                "description": "每个问题返回条数，默认5，最大20",
                "default": 5,
            },
            "days": {
                "type": "integer",
                "description": "只查询最近N天的内容",
            },
        },
        "required": ["queries"],
    },
)


def _format_knowledge_results(results: list[dict]) -> str:
    if not results:
        return "未找到相关内容。"

    parts = []
    for i, item in enumerate(results, 1):
        title = item.get("title", "无标题")
        content = item.get("content", "")
        doc_time = item.get("time", "")
        rtype = item.get("resourceType", "")
        extra = item.get("extraInfo", {}) or {}
        page = extra.get("position", "")

        # 资源类型名称
        rtype_name = {v: k for k, v in RESOURCE_TYPE_MAP.items()}.get(rtype, str(rtype))

        lines = [f"【{i}】{title}"]
        if doc_time:
            lines.append(f"  时间：{doc_time}  类型：{rtype_name}")
        if page:
            lines.append(f"  页码：{page}")
        if content:
            # 截取前500字
            snippet = content[:500].replace("\n", " ")
            if len(content) > 500:
                snippet += "..."
            lines.append(f"  内容：{snippet}")
        parts.append("\n".join(lines))

    return "\n\n".join(parts)


async def handle_knowledge_search(
    client: GangtiseClient, arguments: dict[str, Any]
) -> list[TextContent]:
    query = arguments["query"]
    top = min(arguments.get("top", 10), 20)
    resource_types = arguments.get("resource_types")
    days = arguments.get("days")

    results = await client.search_knowledge(
        query=query, top=top, resource_types=resource_types, days=days
    )
    text = f"## 知识库查询：{query}\n\n共找到 {len(results)} 条结果：\n\n"
    text += _format_knowledge_results(results)
    return [TextContent(type="text", text=text)]


async def handle_knowledge_batch(
    client: GangtiseClient, arguments: dict[str, Any]
) -> list[TextContent]:
    queries = arguments["queries"]
    if len(queries) > 5:
        queries = queries[:5]

    top = min(arguments.get("top", 5), 20)
    resource_types = arguments.get("resource_types")
    days = arguments.get("days")

    batch_result = await client.search_knowledge_batch(
        queries=queries, top=top, resource_types=resource_types, days=days
    )

    # batch 返回格式: [{query: "...", data: [...]}, ...]
    result_map: dict[str, list] = {}
    for item in batch_result:
        if isinstance(item, dict):
            result_map[item.get("query", "")] = item.get("data") or []

    parts = [f"## 批量知识库查询（{len(queries)} 个问题）\n"]
    for q in queries:
        results = result_map.get(q) or []
        parts.append(f"### 问题：{q}")
        parts.append(_format_knowledge_results(results))

    return [TextContent(type="text", text="\n\n".join(parts))]
