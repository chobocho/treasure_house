# 보안 요구의 AND 와 OR — 파이썬 SDK 의 AuthInterceptor 는 머리글을 몇
# 개 다나. 자격 증명은 둘(oauth 토큰, API 키) 다 쥐여 준다. 연결은
# 없다 — 가로채기의 before 만 불러 본다.
import asyncio

from a2a.client import ClientCallContext
from a2a.client.auth import (
    AuthInterceptor,
    InMemoryContextCredentialStore,
)
from a2a.client.card_resolver import parse_agent_card
from a2a.client.interceptors import BeforeArgs

SCHEMES = {
    "oauth": {
        "oauth2SecurityScheme": {"flows": {"clientCredentials": {}}}
    },
    "key": {
        "apiKeySecurityScheme": {
            "location": "header",
            "name": "X-Api-Key",
        }
    },
}
CASES = {
    "AND(요구 하나에 스킴 둘)": [{"schemes": {"oauth": {}, "key": {}}}],
    "OR(스킴 하나씩 요구 둘)": [
        {"schemes": {"oauth": {}}},
        {"schemes": {"key": {}}},
    ],
}


# region: main
async def main():
    store = InMemoryContextCredentialStore()
    await store.set_credentials("s1", "oauth", "tok-planner-1")
    await store.set_credentials("s1", "key", "key-123")
    auth = AuthInterceptor(store)
    for name, reqs in CASES.items():
        card = parse_agent_card(
            {"securitySchemes": SCHEMES, "securityRequirements": reqs}
        )
        ctx = ClientCallContext(state={"sessionId": "s1"})
        args = BeforeArgs(None, "SendMessage", card, ctx)
        await auth.before(args)
        got = sorted(args.context.service_parameters or {})
        # 맵(schemes)을 도는 차례는 프로세스마다 달라 AND 는 수만 찍는다
        shown = got if len(reqs) > 1 else "…"
        print(f"{name} → 머리글 {len(got)}개 {shown}")


# endregion

asyncio.run(main())
