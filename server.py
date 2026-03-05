"""
Gangtise MCP Server
让 Claude Desktop 能直接调用 Gangtise 投研知识库 API
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    ServerCapabilities,
    TextContent,
    Tool,
    ToolsCapability,
)

# 加载 .env（支持从项目目录 / 任意位置启动）
_env_path = Path(__file__).parent / ".env"
load_dotenv(_env_path)

from gangtise_client import GangtiseClient  # noqa: E402
from tools.knowledge import (  # noqa: E402
    KNOWLEDGE_SEARCH_TOOL,
    KNOWLEDGE_BATCH_TOOL,
    handle_knowledge_search,
    handle_knowledge_batch,
)
from tools.indicator import INDICATOR_TOOL, handle_indicator  # noqa: E402
from tools.agent import (  # noqa: E402
    CREATE_SESSION_TOOL,
    DEEP_RESEARCH_TOOL,
    handle_create_session,
    handle_deep_research,
)
from tools.report import DAILY_REPORT_TOOL, handle_daily_report  # noqa: E402

# 日志：写到 logs/ 目录（不输出到 stdout，避免干扰 MCP JSON-RPC）
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "server.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("gangtise_mcp")

ALL_TOOLS: list[Tool] = [
    KNOWLEDGE_SEARCH_TOOL,
    KNOWLEDGE_BATCH_TOOL,
    INDICATOR_TOOL,
    DEEP_RESEARCH_TOOL,
    CREATE_SESSION_TOOL,
    DAILY_REPORT_TOOL,
]

TOOL_HANDLERS = {
    "gangtise_knowledge_search": handle_knowledge_search,
    "gangtise_knowledge_batch": handle_knowledge_batch,
    "gangtise_indicator": handle_indicator,
    "gangtise_deep_research": handle_deep_research,
    "gangtise_create_session": handle_create_session,
    "gangtise_daily_report": handle_daily_report,
}


def get_client() -> GangtiseClient:
    access_key = os.environ.get("GANGTISE_ACCESS_KEY", "").strip()
    secret_key = os.environ.get("GANGTISE_SECRET_KEY", "").strip()
    if not access_key or not secret_key:
        logger.error("GANGTISE_ACCESS_KEY / GANGTISE_SECRET_KEY 未配置，请在 .env 中设置")
        sys.exit(1)
    return GangtiseClient(access_key=access_key, secret_key=secret_key)


async def main():
    server = Server("gangtise-mcp")
    client = get_client()

    logger.info("Gangtise MCP Server 启动，已加载 %d 个工具", len(ALL_TOOLS))

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return ALL_TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        logger.info("调用工具: %s, 参数: %s", name, arguments)
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            return [TextContent(type="text", text=f"未知工具: {name}")]
        try:
            result = await handler(client, arguments)
            logger.info("工具 %s 执行成功", name)
            return result
        except Exception as e:
            logger.error("工具 %s 执行失败: %s", name, e, exc_info=True)
            return [TextContent(type="text", text=f"工具执行失败（{name}）：{e}")]

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main_sync():
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
