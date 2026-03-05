"""
快速验证 Gangtise API 认证状态
用法：python scripts/test_auth.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import os
from gangtise_client import GangtiseClient


async def main():
    access_key = os.environ.get("GANGTISE_ACCESS_KEY", "")
    secret_key = os.environ.get("GANGTISE_SECRET_KEY", "")

    print(f"Access Key: {access_key}")
    print(f"Secret Key: {secret_key[:8]}...{secret_key[-4:]}")
    print()

    client = GangtiseClient(access_key=access_key, secret_key=secret_key)

    # 1. 测试 loginV2
    import aiohttp
    print("【1】测试 loginV2 换取 token...")
    session = await client._get_session()
    async with session.post(
        "https://open.gangtise.com/application/auth/oauth/open/loginV2",
        json={"accessKey": access_key, "secretAccessKey": secret_key},
        headers={"Content-Type": "application/json"},
    ) as resp:
        data = await resp.json()
        if data.get("code") == "000000":
            print(f"  ✓ loginV2 成功，token: {data['data']['accessToken'][:40]}...")
        else:
            print(f"  ✗ loginV2 失败：{data.get('msg')} (code={data.get('code')})")

    # 2. 测试长期 token 直接访问
    print("\n【2】测试 secretAccessKey 作为长期 Bearer token...")
    async with session.get(
        "https://open.gangtise.com/application/open-ai/ai/chat/createGroup",
        headers={"Authorization": f"Bearer {secret_key}"},
    ) as resp:
        data = await resp.json()
        if data.get("code") == "000000":
            print(f"  ✓ 长期 token 有效，groupId = {data['data']}")
        else:
            print(f"  ✗ 长期 token 无效：{data.get('msg')} (code={data.get('code')})")

    # 3. 用 client 自动获取 token 并测试知识库
    print("\n【3】测试知识库查询（自动选择最佳认证方式）...")
    try:
        results = await client.search_knowledge(query="光模块市场规模", top=2)
        if results:
            print(f"  ✓ 知识库查询成功，返回 {len(results)} 条")
            print(f"     第1条标题：{results[0].get('title', 'N/A')}")
        else:
            print("  ! 查询成功但无结果")
    except Exception as e:
        print(f"  ✗ 知识库查询失败：{e}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
