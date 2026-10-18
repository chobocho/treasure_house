# 카드를 받아 스킬의 id 와 태그를 늘어놓는다 — 기획 에이전트가
# 역할을 고를 때 보는 것이 이 둘이다.
#   python 15/skills.py 포트…
import asyncio
import sys

import httpx
from a2a.client import A2ACardResolver


async def main():
    async with httpx.AsyncClient() as http:
        for port in sys.argv[1:]:
            url = f"http://127.0.0.1:{port}/"
            c = await A2ACardResolver(http, url).get_agent_card()
            for s in c.skills:
                print(f"{port} {c.name}: {s.id} {list(s.tags)}")


asyncio.run(main())
# @ norun
