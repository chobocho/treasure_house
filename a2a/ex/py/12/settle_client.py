# 정산 에이전트를 SDK 클라이언트로 부른다 — 토큰 없이 한 번, 카드의
# tokenUrl 에서 토큰을 받아 AuthInterceptor 로 한 번.
#   python 12/settle_client.py 에이전트주소 client_id client_secret
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
from a2a.helpers import get_data_parts, new_data_part
from a2a.types import Message, Role, SendMessageRequest, TaskState

SMALL = {
    "items": [{"name": "숙소", "amount": 2100000}],
    "budget": 6000000,
}


def request(mid):
    parts = [new_data_part(SMALL)]
    msg = Message(message_id=mid, role=Role.ROLE_USER, parts=parts)
    return SendMessageRequest(message=msg)


# region: token
async def get_token(card, client_id, secret):
    """카드가 알려 준 tokenUrl 에 client_credentials 로 묻는다."""
    flows = card.security_schemes["oauth"].oauth2_security_scheme.flows
    form = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": secret,
    }
    async with httpx.AsyncClient() as http:
        r = await http.post(
            flows.client_credentials.token_url, data=form
        )
    r.raise_for_status()
    return r.json()["access_token"]


# endregion


# region: main
async def main(url, client_id, secret):
    async with httpx.AsyncClient() as http:
        card = await A2ACardResolver(http, url).get_agent_card()
    store = InMemoryContextCredentialStore()  # 처음엔 비었다
    client = await create_client(
        card,
        ClientConfig(streaming=False),
        interceptors=[AuthInterceptor(store)],
    )
    try:
        async for _ in client.send_message(request("py-1")):
            pass
    except Exception as e:  # noqa: BLE001 — 무엇이 오는지 보려고
        print(f"① 토큰 없이 → {type(e).__name__}: {e}")
    token = await get_token(card, client_id, secret)
    print(f"② 받은 토큰 {token}")
    await store.set_credentials("s1", "oauth", token)
    ctx = ClientCallContext(state={"sessionId": "s1"})
    async for ev in client.send_message(request("py-2"), context=ctx):
        task = ev.task
    sheet = get_data_parts(task.artifacts[0].parts)[0]
    state = TaskState.Name(task.status.state)
    print(f"③ 토큰 달고 → {state}, approvedBy {sheet['approvedBy']}")
    await client.close()


# endregion

if __name__ == "__main__":
    asyncio.run(main(*sys.argv[1:4]))
# @ norun
