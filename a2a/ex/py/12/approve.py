# 큰 정산을 조회 토큰으로 맡겨 AUTH_REQUIRED 를 받고, 결재 스코프가
# 든 새 토큰으로 같은 작업에 이어 말해 끝낸다. SDK 클라이언트 하나,
# 자격 증명 저장소의 토큰만 바꾼다.
#   python 12/approve.py 에이전트주소
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
from a2a.helpers import (
    get_data_parts,
    get_message_text,
    new_data_part,
    new_text_part,
)
from a2a.types import Message, Role, SendMessageRequest, TaskState

BIG = {
    "items": [
        {"name": "숙소", "amount": 2100000},
        {"name": "식사", "amount": 1542000},
        {"name": "교통", "amount": 1200000},
    ],
    "budget": 6000000,
}


async def token(card, scope):
    flows = card.security_schemes["oauth"].oauth2_security_scheme.flows
    form = {"grant_type": "client_credentials", "client_id": "planner"}
    form |= {"client_secret": "planner-secret", "scope": scope}
    async with httpx.AsyncClient() as http:
        url = flows.client_credentials.token_url
        r = await http.post(url, data=form)
    return r.json()["access_token"]


async def send(client, msg):
    ctx = ClientCallContext(state={"sessionId": "s1"})
    req = SendMessageRequest(message=msg)
    async for ev in client.send_message(req, context=ctx):
        task = ev.task
    return task


# region: main
async def main(url):
    async with httpx.AsyncClient() as http:
        card = await A2ACardResolver(http, url).get_agent_card()
    store = InMemoryContextCredentialStore()
    client = await create_client(
        card,
        ClientConfig(streaming=False),
        interceptors=[AuthInterceptor(store)],
    )
    read = await token(card, "payment:read")
    await store.set_credentials("s1", "oauth", read)
    msg = Message(message_id="a-1", role=Role.ROLE_USER)
    msg.parts.append(new_data_part(BIG))
    task = await send(client, msg)
    state = TaskState.Name(task.status.state)
    print(f"① {read} → {state}")
    print(f"   {get_message_text(task.status.message)}")
    both = await token(card, "payment:read payment:approve")
    await store.set_credentials("s1", "oauth", both)  # 토큰만 바꾼다
    msg = Message(message_id="a-2", role=Role.ROLE_USER)
    msg.task_id, msg.context_id = task.id, task.context_id
    msg.parts.append(new_text_part("결재합니다"))
    task = await send(client, msg)
    sheet = get_data_parts(task.artifacts[0].parts)[0]
    state = TaskState.Name(task.status.state)
    print(f"② {both} → {state}, approvedBy {sheet['approvedBy']}")
    await client.close()


# endregion

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
# @ norun
