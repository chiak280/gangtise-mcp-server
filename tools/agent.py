"""深度研究 Agent 工具 + 会话创建工具"""

from typing import Any

from mcp.types import TextContent, Tool

from gangtise_client import GangtiseClient, AGENT_MAP, RESOURCE_TYPE_MAP

_AGENT_TYPES_HINT = "\n".join([
    "- searcher / 数据搜索：搜索相关数据和信息",
    "- industry_expert / 产业链分析：深度产业链研究",
    "- investment_logic / 投资逻辑：分析公司或行业投资逻辑",
    "- investigation_outline / 调研提纲：生成调研框架",
    "- theme_daily_report / 主题晨报：生成主题赛道每日报告",
])

_RESOURCE_TYPES_HINT = "、".join(RESOURCE_TYPE_MAP.keys())

CREATE_SESSION_TOOL = Tool(
    name="gangtise_create_session",
    description=(
        "创建 Gangtise 会话 ID（groupId），用于深度研究的多轮对话。"
        "如需在多次 gangtise_deep_research 调用之间保持上下文，先调用此工具获取 group_id，再传入研究工具。"
    ),
    inputSchema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)

DEEP_RESEARCH_TOOL = Tool(
    name="gangtise_deep_research",
    description=(
        "调用 Gangtise Agent 进行深度研究分析。\n"
        "支持以下 Agent 类型：\n"
        f"{_AGENT_TYPES_HINT}\n\n"
        "适合场景：研究行业产业链（如光通信）、分析公司投资逻辑、生成调研提纲、每日主题报告。"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "研究问题，例如：'英伟达GPU集群的网络架构，各层使用的交换机和光模块规格是什么？'"
            },
            "agent": {
                "type": "string",
                "description": (
                    "指定 Agent 类型。可选：searcher、industry_expert、investment_logic、"
                    "investigation_outline、theme_daily_report。"
                    "也支持中文别名：数据搜索、产业链分析、投资逻辑、调研提纲、主题晨报。"
                    "不填则由平台自动选择最合适的 Agent。"
                ),
            },
            "group_id": {
                "type": "integer",
                "description": "会话 ID，由 gangtise_create_session 获取。填入后可实现多轮对话，保持上下文。",
            },
            "web_enable": {
                "type": "boolean",
                "description": "是否允许联网搜索补充信息，默认 true",
                "default": True,
            },
            "include_types": {
                "type": "array",
                "items": {"type": "string"},
                "description": f"限定信息来源类型，可选：{_RESOURCE_TYPES_HINT}。不填则使用所有来源。",
            },
        },
        "required": ["question"],
    },
)


async def handle_create_session(
    client: GangtiseClient, arguments: dict[str, Any]
) -> list[TextContent]:
    group_id = await client.create_group()
    text = (
        f"已创建新会话，group_id = **{group_id}**\n\n"
        "在后续的 `gangtise_deep_research` 调用中传入此 group_id，可实现多轮对话。"
    )
    return [TextContent(type="text", text=text)]


async def handle_deep_research(
    client: GangtiseClient, arguments: dict[str, Any]
) -> list[TextContent]:
    question = arguments["question"]
    agent = arguments.get("agent")
    group_id = arguments.get("group_id")
    web_enable = arguments.get("web_enable", True)
    include_types = arguments.get("include_types")

    think_text, answer_text = await client.deep_research(
        question=question,
        agent=agent,
        group_id=group_id,
        web_enable=web_enable,
        include_types=include_types,
    )

    # 解析 agent 显示名
    agent_display = "自动"
    if agent:
        resolved = AGENT_MAP.get(agent, agent)
        agent_display_map = {
            "searcher": "数据搜索",
            "industry_expert": "产业链分析",
            "investment_logic": "投资逻辑",
            "investigation_outline": "调研提纲",
            "theme_daily_report": "主题晨报",
        }
        agent_display = agent_display_map.get(resolved, agent)

    parts = [f"## 深度研究：{question}", f"**Agent**: {agent_display}"]
    if group_id:
        parts.append(f"**会话 ID**: {group_id}")

    parts.append("\n---\n")

    if think_text:
        parts.append("### 思考过程")
        parts.append(think_text[:1000] + ("..." if len(think_text) > 1000 else ""))
        parts.append("\n---\n")

    parts.append("### 研究结论")
    parts.append(answer_text or "（无返回内容，请检查 API 状态）")

    return [TextContent(type="text", text="\n\n".join(parts))]
