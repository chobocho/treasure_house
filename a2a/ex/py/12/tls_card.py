# HTTPS 로 카드를 두 번 읽는다 — 기본 신뢰 목록으로 한 번, 시험 CA 를
# 믿게 하고 한 번. 서버 인증서 검사는 SDK 가 아니라 httpx 의 일이다.
#   python 12/tls_card.py https://127.0.0.1:P/ CA파일
import asyncio
import ssl
import sys

import httpx
from a2a.client import A2ACardResolver, AgentCardResolutionError


# region: main
async def card(url, verify):
    async with httpx.AsyncClient(verify=verify) as http:
        return await A2ACardResolver(http, url).get_agent_card()


async def main(url, ca):
    try:
        await card(url, True)  # True = certifi 의 공인 CA 목록
    except AgentCardResolutionError as e:
        print(f"① 기본 신뢰 목록 → {type(e).__name__}")
        print(f"   원인: {e.__cause__}")
    # 시험 CA 하나만 믿는 TLS 설정. 인증서의 IP(127.0.0.1)도 맞춰 본다.
    tls = ssl.create_default_context(cafile=ca)
    c = await card(url, tls)
    flow = c.security_schemes["oauth"].oauth2_security_scheme.flows
    print(f"② 시험 CA 를 믿으면 → {c.name}")
    print(f"   인터페이스 {c.supported_interfaces[0].url}")
    print(f"   토큰 주소 {flow.client_credentials.token_url}")


# endregion

if __name__ == "__main__":
    asyncio.run(main(*sys.argv[1:3]))
# @ norun
