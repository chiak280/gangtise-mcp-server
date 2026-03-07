"""每日赛道追踪报告工具（组合调用 Agent + 知识库）"""

import asyncio
from datetime import datetime
from typing import Any

from mcp.types import TextContent, Tool

from gangtise_client import GangtiseClient

DAILY_REPORT_TOOL = Tool(
    name="gangtise_daily_report",
    description=(
        "对指定的投资赛道生成每日追踪报告，包含：券商最新观点、行业动态、投资机会与风险。\n"
        "适合每天早上追踪多个赛道的最新进展。\n"
        "支持赛道：半导体设备、半导体材料、先进封装、光通信、AI算力、新能源等。"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "sectors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "赛道列表，例如：['半导体设备', '光通信', '先进封装']",
            },
            "focus_points": {
                "type": "array",
                "items": {"type": "string"},
                "description": "重点关注方向，例如：['国产替代进展', '美国出口管制影响']。不填则生成综合报告。",
            },
            "days": {
                "type": "integer",
                "description": "拉取最近N天的新闻/报告，默认3天",
                "default": 3,
            },
        },
        "required": ["sectors"],
    },
)


async def _generate_sector_report(
    client: GangtiseClient,
    sector: str,
    focus_points: list[str],
    days: int,
) -> str:
    """为单个赛道生成报告（并发调用 Agent + 知识库）"""

    focus_str = "，".join(focus_points) if focus_points else ""
    question = f"{sector}赛道今日最新动态，包括：券商观点、行业新闻、投资机会与风险"
    if focus_str:
        question += f"，重点关注：{focus_str}"

    # 并发执行：Agent 主题晨报 + 知识库券商观点
    broker_query = f"{sector} 券商研究报告 最新观点"

    async def run_agent():
        try:
            _, answer = await client.deep_research(
                question=question,
                agent="theme_daily_report",
                web_enable=True,
            )
            return answer
        except Exception as e:
            return f"（Agent 调用失败：{e}）"

    async def run_knowledge():
        try:
            results = await client.search_knowledge(
                query=broker_query,
                top=20,
                resource_types=["券商研究报告", "首席分析师观点"],
                days=days,
            )
            if not results:
                return "（暂无近期券商报告）"
            lines = []
            for item in results:
                title = item.get("title", "")
                content = item.get("content", "")[:300]
                doc_time = item.get("time", "")
                lines.append(f"- **{title}** ({doc_time})\n  {content}...")
            return "\n\n".join(lines)
        except Exception as e:
            return f"（知识库查询失败：{e}）"

    agent_result, broker_result = await asyncio.gather(run_agent(), run_knowledge())

    return (
        f"### {sector}\n\n"
        f"**主题晨报**\n\n{agent_result}\n\n"
        f"---\n\n"
        f"**近期券商观点**\n\n{broker_result}"
    )


async def handle_daily_report(
    client: GangtiseClient, arguments: dict[str, Any]
) -> list[TextContent]:
    sectors = arguments["sectors"]
    focus_points = arguments.get("focus_points", [])
    days = arguments.get("days", 3)

    today = datetime.now().strftime("%Y年%m月%d日")
    parts = [
        f"# 投研每日追踪报告 — {today}",
        f"**追踪赛道**：{'、'.join(sectors)}",
    ]
    if focus_points:
        parts.append(f"**重点关注**：{'、'.join(focus_points)}")
    parts.append("\n---\n")

    # 并发生成所有赛道报告
    tasks = [
        _generate_sector_report(client, sector, focus_points, days)
        for sector in sectors
    ]
    sector_reports = await asyncio.gather(*tasks)
    parts.extend(sector_reports)

    parts.append("\n---\n*报告由 Gangtise 知识库 + AI Agent 生成，仅供参考，不构成投资建议。*")

    return [TextContent(type="text", text="\n\n".join(parts))]
