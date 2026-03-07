"""指标查询工具"""

from typing import Any

from mcp.types import TextContent, Tool

from gangtise_client import GangtiseClient

INDICATOR_TOOL = Tool(
    name="gangtise_indicator",
    description=(
        "查询宏观经济指标和行业市场指标的结构化数据。\n"
        "✅ 支持：宏观指标（GDP、CPI、PMI、M2、利率）、行业指标（市场规模、产能、销量、价格指数）。\n"
        "❌ 不支持：A股个股财务数据（营收/净利润/毛利率等）——个股财务请改用 gangtise_knowledge_search 查研报/年报。\n"
        "示例：'中国半导体设备市场规模2022-2024'、'全球光模块出货量'、'中国GDP增速'"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "自然语言查询，描述你想查询的指标",
            }
        },
        "required": ["query"],
    },
)


async def handle_indicator(
    client: GangtiseClient, arguments: dict[str, Any]
) -> list[TextContent]:
    query = arguments["query"]
    result = await client.query_indicator(query)
    text = f"## 指标查询：{query}\n\n{result}"
    return [TextContent(type="text", text=text)]
