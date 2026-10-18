# 정산 에이전트의 공개 카드와 확장 카드를 SDK 클라이언트로 견준다 —
# intern 토큰으로 GetExtendedAgentCard 를 부르고, 클라이언트가 들고
# 있는 카드가 바뀌는지 본다.
#   python 12/xcard.py 에이전트주소
import asyncio
import sys

import httpx
from a2a.client import (
    A2ACardResolver,
    ClientCallContext,
    ClientConfig,
    create_client,
)
from a2a.client.auth import (
    AuthInterceptor,
    InMemoryContextCredentialStore,
)
from a2a.types import GetExtendedAgentCardRequest


def show(label, card):
    skills = ", ".join(s.id for s in card.skills)
    print(f"{label}: 스킬 [{skills}] · 서명 {len(card.signatures)}개")


async def token(card, cid, secret):
    flows = card.security_schemes["oauth"].oauth2_security_scheme.flows
    form = {"grant_type": "client_credentials", "client_id": cid}
    form["client_secret"] = secret
    async with httpx.AsyncClient() as http:
        url = flows.client_credentials.token_url
        r = await http.post(url, data=form)
    return r.json()["access_token"]


# region: main
async def main(url):
    async with httpx.AsyncClient() as http:
        card = await A2ACardResolver(http, url).get_agent_card()
    show("① 공개 카드", card)
    store = InMemoryContextCredentialStore()
    await store.set_credentials(
        "s1", "oauth", await token(card, "intern", "intern-secret")
    )
    client = await create_client(
        card, ClientConfig(), interceptors=[AuthInterceptor(store)]
    )
    ctx = ClientCallContext(state={"sessionId": "s1"})
    extended = await client.get_extended_agent_card(
        GetExtendedAgentCardRequest(), context=ctx
    )
    show("② 확장 카드", extended)
    # 비공개 필드지만, 클라이언트가 이제 어느 카드를 쓰는지 보려고
    show("③ 클라이언트의 카드", client._card)
    await client.close()


# endregion

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
# @ norun
