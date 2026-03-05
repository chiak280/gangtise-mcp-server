"""指标查询工具"""

from typing import Any

from mcp.types import TextContent, Tool

from gangtise_client import GangtiseClient

INDICATOR_TOOL = Tool(
    name="gangtise_indicator",
    description=(
        "查询经济指标、行业指标、公司财务/销量等结构化数据。\n"
        "适合场景：查询宏观经济数据、行业市场规模、公司营收/利润/出货量等指标。\n"
        "示例：'2024年中国光模块出货量'、'比亚迪2024年销售数据'、'全球半导体设备市场规模趋势'"
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
