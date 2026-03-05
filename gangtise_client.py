"""
Gangtise API 客户端
支持：知识库检索、批量检索、指标查询、深度研究 Agent（SSE）

认证说明：
  - 调用 /application/auth/oauth/open/loginV2 换取 accessToken（有效期 4 小时）
  - 返回的 accessToken 已含 "Bearer " 前缀，直接用于 Authorization 头
  - 客户端自动处理 token 刷新（到期前 5 分钟自动换取新 token）
"""

import asyncio
import json
import logging
import time
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

BASE_URL = "https://open.gangtise.com"
TOKEN_ENDPOINT = f"{BASE_URL}/application/auth/oauth/open/loginV2"
TOKEN_TTL_BUFFER = 300  # 到期前 5 分钟刷新
DEFAULT_KNOWLEDGE_NAMES = ["system_knowledge_doc"]  # 官方默认知识库
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 3, 5]  # 重试等待秒数

# 资源类型中文到编码的映射
RESOURCE_TYPE_MAP: dict[str, int] = {
    "券商研报": 10,
    "内部研究报告": 20,
    "分析师观点": 40,
    "公司公告": 50,
    "会议纪要": 60,
    "调研纪要": 70,
    "网络资源": 80,
    "产业公众号": 90,
}

# Agent 名称映射（支持中文别名）
AGENT_MAP: dict[str, str] = {
    "搜索": "searcher",
    "数据搜索": "searcher",
    "调研提纲": "investigation_outline",
    "产业链分析": "industry_expert",
    "产业链": "industry_expert",
    "主题晨报": "theme_daily_report",
    "每日报告": "theme_daily_report",
    "投资逻辑": "investment_logic",
    # 直接传英文也支持
    "searcher": "searcher",
    "investigation_outline": "investigation_outline",
    "industry_expert": "industry_expert",
    "theme_daily_report": "theme_daily_report",
    "investment_logic": "investment_logic",
}


def _resolve_resource_types(types: list[str]) -> list[int]:
    result = []
    for t in types:
        if t in RESOURCE_TYPE_MAP:
            result.append(RESOURCE_TYPE_MAP[t])
        elif t.isdigit():
            result.append(int(t))
    return result or None


def _days_to_timestamps(days: Optional[int]) -> tuple[Optional[int], Optional[int]]:
    if not days:
        return None, None
    end = int(time.time() * 1000)
    start = int((time.time() - days * 86400) * 1000)
    return start, end


class GangtiseClient:
    def __init__(self, access_key: str, secret_key: str):
        self.access_key = access_key
        self.secret_key = secret_key
        # 初始时先把 secret_key 当长期 token 尝试；loginV2 成功后会覆盖
        self._token: Optional[str] = f"Bearer {secret_key}"
        self._token_expires_at: float = 0.0     # 0 = 需要通过 loginV2 刷新
        self._session: Optional[aiohttp.ClientSession] = None
        self._token_lock = asyncio.Lock()
        self._use_long_term_token: bool = False  # loginV2 失败时回落到长期 token

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=120)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def _refresh_token(self) -> str:
        """
        换取新 accessToken。
        优先走 loginV2（4h 短期 token）；
        若账号信息匹配失败（8000014），回落到把 secretAccessKey 直接当长期 Bearer token。
        """
        session = await self._get_session()
        payload = {"accessKey": self.access_key, "secretAccessKey": self.secret_key}
        try:
            async with session.post(
                TOKEN_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                if data.get("code") == "000000" and data.get("status"):
                    token_data = data["data"]
                    token = token_data["accessToken"]       # 已含 "Bearer " 前缀
                    expires_in = token_data.get("expiresIn", 14400)
                    self._token = token
                    self._token_expires_at = time.time() + expires_in - TOKEN_TTL_BUFFER
                    self._use_long_term_token = False
                    logger.info("loginV2 成功，token 有效 %ds", expires_in)
                    return token
                # loginV2 失败：回落到长期 token
                logger.warning("loginV2 失败（%s），回落到长期 secretAccessKey 模式", data.get("msg"))
        except Exception as e:
            logger.warning("loginV2 请求异常（%s），回落到长期 secretAccessKey 模式", e)

        # 长期 token 模式：直接用 secretAccessKey 作为 Bearer token
        self._use_long_term_token = True
        self._token = f"Bearer {self.secret_key}"
        self._token_expires_at = time.time() + 86400 * 365  # 假设长期有效，1 年后再检查
        return self._token

    async def _get_token(self) -> str:
        """获取有效 token（过期则自动刷新）"""
        async with self._token_lock:
            if time.time() >= self._token_expires_at:
                await self._refresh_token()
            return self._token

    async def _auth_headers(self) -> dict:
        token = await self._get_token()
        return {
            "Authorization": token,   # token 已含 "Bearer " 前缀
            "Content-Type": "application/json",
        }

    async def _post_with_retry(self, url: str, payload: dict) -> dict:
        """POST 请求，遇到 429 自动重试"""
        session = await self._get_session()
        for attempt in range(MAX_RETRIES):
            async with session.post(url, headers=await self._auth_headers(), json=payload) as resp:
                if resp.status == 429:
                    wait = RETRY_BACKOFF[attempt] if attempt < len(RETRY_BACKOFF) else 5
                    logger.warning("429 限流，%ds 后重试（%d/%d）", wait, attempt + 1, MAX_RETRIES)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                return await resp.json()
        raise RuntimeError(f"请求 {url} 连续 {MAX_RETRIES} 次 429 限流")

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def create_group(self) -> int:
        """创建会话，返回 groupId"""
        session = await self._get_session()
        url = f"{BASE_URL}/application/open-ai/ai/chat/createGroup"
        async with session.get(url, headers=await self._auth_headers()) as resp:
            resp.raise_for_status()
            data = await resp.json()
            if data.get("code") != "000000":
                raise RuntimeError(f"创建会话失败: {data.get('msg')}")
            return data["data"]

    async def search_knowledge(
        self,
        query: str,
        top: int = 10,
        resource_types: Optional[list[str]] = None,
        days: Optional[int] = None,
    ) -> list[dict]:
        """单条知识库检索"""
        url = f"{BASE_URL}/application/open-data/ai/search/knowledge_base"

        start_time, end_time = _days_to_timestamps(days)
        payload: dict = {
            "query": query,
            "top": min(top, 20),
            "knowledgeNames": DEFAULT_KNOWLEDGE_NAMES,
        }
        if resource_types:
            rt = _resolve_resource_types(resource_types)
            if rt:
                payload["resourceTypes"] = rt
        if start_time:
            payload["startTime"] = start_time
        if end_time:
            payload["endTime"] = end_time

        data = await self._post_with_retry(url, payload)
        if data.get("code") != "000000":
            raise RuntimeError(f"知识库查询失败: {data.get('msg')}")
        return data.get("data") or []

    async def search_knowledge_batch(
        self,
        queries: list[str],
        top: int = 10,
        resource_types: Optional[list[str]] = None,
        days: Optional[int] = None,
    ) -> list[dict]:
        """
        批量知识库检索（最多5条）
        返回: [{query: "...", data: [...]}, ...]
        """
        if len(queries) > 5:
            raise ValueError("批量查询最多5条")
        url = f"{BASE_URL}/application/open-data/ai/search/knowledge/batch"

        start_time, end_time = _days_to_timestamps(days)
        payload: dict = {
            "queries": queries,
            "top": min(top, 20),
            "knowledgeNames": DEFAULT_KNOWLEDGE_NAMES,
        }
        if resource_types:
            rt = _resolve_resource_types(resource_types)
            if rt:
                payload["resourceTypes"] = rt
        if start_time:
            payload["startTime"] = start_time
        if end_time:
            payload["endTime"] = end_time

        data = await self._post_with_retry(url, payload)
        if data.get("code") != "000000":
            raise RuntimeError(f"批量知识库查询失败: {data.get('msg')}")
        return data.get("data") or []

    async def query_indicator(self, text: str) -> str:
        """指标查询 Agent（非流式，等待完整返回）"""
        url = f"{BASE_URL}/application/open-ai/ai/search/indicator"
        payload = {"text": text, "stream": False}

        data = await self._post_with_retry(url, payload)
        # 兼容 OpenAI 格式返回
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        # 直接业务格式
        if data.get("code") == "000000":
            return data.get("data", "")
        raise RuntimeError(f"指标查询失败: {data}")

    async def deep_research(
        self,
        question: str,
        agent: Optional[str] = None,
        group_id: Optional[int] = None,
        web_enable: bool = True,
        include_types: Optional[list[str]] = None,
    ) -> tuple[str, str]:
        """
        深度研究 Agent（SSE 流式，收集后返回）
        返回: (思考过程, 最终回答)
        """
        session = await self._get_session()
        url = f"{BASE_URL}/application/open-ai/ai/chat/sse"

        # 解析 agent 名称
        forced_agent = None
        if agent:
            forced_agent = AGENT_MAP.get(agent, agent)

        # 解析资源类型
        include_search_types = None
        if include_types:
            include_search_types = _resolve_resource_types(include_types)

        payload: dict = {
            "text": question,
            "mode": "deep_research",
            "askChatParam": {
                "webEnable": web_enable,
                "traceId": f"mcp_{int(time.time() * 1000)}",
            },
        }
        if group_id:
            payload["groupId"] = group_id
        if forced_agent:
            payload["askChatParam"]["forcedAgent"] = forced_agent
        if include_search_types:
            payload["askChatParam"]["includeSearchTypes"] = include_search_types

        think_parts: list[str] = []
        answer_parts: list[str] = []

        async with session.post(url, headers=await self._auth_headers(), json=payload) as resp:
            resp.raise_for_status()
            async for raw_line in resp.content:
                line = raw_line.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                json_str = line[5:].strip()
                if not json_str or json_str == "[DONE]":
                    continue
                try:
                    event = json.loads(json_str)
                except json.JSONDecodeError:
                    continue

                phase = event.get("phase", "")
                delta = ""
                result = event.get("result", {})
                if isinstance(result, dict):
                    delta = result.get("delta", "")

                if phase == "think" and delta:
                    think_parts.append(delta)
                elif phase == "answer" and delta:
                    answer_parts.append(delta)

        think_text = "".join(think_parts)
        answer_text = "".join(answer_parts)
        return think_text, answer_text
