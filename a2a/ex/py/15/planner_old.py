# 고치기 전의 기획 에이전트 — agents/planner.py 를 2026-10-18 에
# 고치기 전 모습 그대로 옮겨 두었다(2장의 "전"). 15/old_at.py 로 띄운다.
"""기획 에이전트 — 총무팀의 한 문장을 받아 워크숍 전체를 꾸린다.

서버이면서 클라이언트다. 카드로 동료를 찾고(스킬 태그), 숙소·식사·
교통을 동시에 맡기고, 견적을 정산 에이전트에 넘겨 결재를 받는다.
정산이 결재를 요구하면 그 요구를 자기 사용자에게 넘긴다(§7.6.2 의
AUTH_REQUIRED 사슬).
"""

import asyncio
import json
import uuid

import httpx
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers.proto_helpers import (
    get_data_parts,
    get_message_text,
    new_data_part,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Message,
    Role,
    SendMessageRequest,
    TaskState,
)
from a2a.utils.signing import create_signature_verifier
from jwt import PyJWK

from agents.common import (
    PROVIDER,
    begin,
    jsonrpc_interface,
    parse_args,
    serve,
)
from workshop import domain
from workshop.fixtures import FIXTURES

# region: roles
# 맡길 일 → 그 일을 하는 에이전트의 스킬 태그
ROLES = {
    "lodging": "lodging",
    "meals": "meals",
    "bus": "transport",
    "settle": "budget",
}
# endregion
ASK = {
    "date": "날짜(예: 2026-10-30)",
    "nights": "박 수(예: 1박)",
    "headcount": "인원(예: 30명)",
    "budget": "예산(예: 예산 6,000,000원)",
}


def card(url):
    return AgentCard(
        name="보물상사 기획 에이전트",
        description=(
            "한 문장 요청으로 워크숍 숙소·식사·교통·정산을 꾸립니다."
        ),
        version="1.0.0",
        provider=PROVIDER,
        supported_interfaces=[jsonrpc_interface(url)],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text/plain"],
        default_output_modes=["text/markdown", "application/json"],
        skills=[
            AgentSkill(
                id="plan-workshop",
                name="워크숍 기획",
                description="동료 에이전트에게 일을 나눠 맡깁니다.",
                tags=["workshop", "orchestration"],
                examples=[
                    (
                        "2026-10-30부터 1박 2일, 30명(채식 2명), "
                        "예산 6,000,000원, 출발 강남역"
                    )
                ],
            )
        ],
    )


# region: discover
def pinned_verifier():
    """카드 서명은 미리 받아 둔 공개 키로만 검증한다.

    카드 안의 jku 를 따라가 키를 받으면, 카드를 위조한 쪽이 자기 키를
    가리키게 할 수 있다 — 그래서 jku 는 믿지 않는다.
    """
    jwks = json.loads((FIXTURES / "keys/jwks.json").read_text())
    keys = {k["kid"]: PyJWK(k) for k in jwks["keys"]}
    return create_signature_verifier(
        lambda kid, jku: keys[kid], algorithms=["EdDSA"]
    )


async def discover(urls):
    """카드를 읽어 역할별로 하나씩 고른다. 서명이 있으면 검증한다."""
    verify = pinned_verifier()
    found = {}
    async with httpx.AsyncClient() as http:
        for url in urls:
            c = await A2ACardResolver(http, url).get_agent_card()
            if c.signatures:
                verify(c)  # 틀리면 예외 — 위조 카드는 쓰지 않는다
            tags = {t for s in c.skills for t in s.tags}
            for role, tag in ROLES.items():
                if tag in tags and role not in found:
                    found[role] = c
    return found


# endregion


# region: delegate
def ask_message(parts, context_id, refs=()):
    m = Message(
        role=Role.ROLE_USER, parts=parts, message_id=str(uuid.uuid4())
    )
    m.context_id = context_id
    m.reference_task_ids.extend(refs)
    return m


async def delegate(c, data, context_id, *, token=None, refs=()):
    """막는 호출 하나로 맡기고 끝(또는 멈춤) 상태의 Task 를 받는다."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    http = httpx.AsyncClient(headers=headers, timeout=30)
    client = await create_client(
        c, ClientConfig(streaming=False, httpx_client=http)
    )
    req = SendMessageRequest(
        message=ask_message([new_data_part(data)], context_id, refs)
    )
    async for ev in client.send_message(req):
        task = ev.task
    await client.close()
    return task


async def follow_up(c, task, text, token):
    """멈춘 작업에 같은 taskId·contextId 로 한마디 더 한다."""
    http = httpx.AsyncClient(
        headers={"Authorization": f"Bearer {token}"}, timeout=30
    )
    client = await create_client(
        c, ClientConfig(streaming=False, httpx_client=http)
    )
    m = ask_message([new_text_part(text)], task.context_id)
    m.task_id = task.id
    async for ev in client.send_message(SendMessageRequest(message=m)):
        done = ev.task
    await client.close()
    return done


# endregion


# region: token
async def get_token(c, scope, client_id, secret):
    """카드의 securitySchemes 에서 토큰 주소를 찾아 토큰을 받는다."""
    flow = c.security_schemes["oauth"].oauth2_security_scheme.flows
    async with httpx.AsyncClient() as http:
        r = await http.post(
            flow.client_credentials.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": secret,
                "scope": scope,
            },
        )
    r.raise_for_status()
    return r.json()["access_token"]


# endregion


def quote_of(task):
    """완료된 Task 의 첫 DataPart(견적)를 꺼낸다."""
    for a in task.artifacts:
        for d in get_data_parts(a.parts):
            return d
    return None


def plan_markdown(req, lodging, meals, bus, sheet):
    won = lambda n: f"{int(n):,}원"
    return "\n".join(
        [
            "# 보물상사 가을 워크숍 계획서",
            "",
            f"- 일정: {req['date']}부터 {req['nights']}박",
            (
                f"- 인원: {req['headcount']}명"
                f"(채식 {req['vegetarians']}명)"
            ),
            (
                f"- 숙소: {lodging['venueName']}"
                f" {int(lodging['rooms'])}실 — {won(lodging['total'])}"
            ),
            f"- 식사: {len(meals['slots'])}끼 — {won(meals['total'])}",
            f"- 교통: {int(bus['days'])}일 — {won(bus['total'])}",
            (
                f"- 합계: {won(sheet['total'])}"
                f" / 예산 {won(sheet['budget'])}"
                f" (남음 {won(sheet['remaining'])})"
            ),
            f"- 결재: {sheet['approvedBy']}",
            "",
        ]
    )


class PlannerExecutor(AgentExecutor):
    def __init__(self, urls, client_id, secret):
        self.urls = urls
        self.client_id, self.secret = client_id, secret
        # 결재를 기다리는 기획 작업 → 이어 가는 데 필요한 것들
        self.waiting = {}

    # region: say
    async def say(self, up, text, state=TaskState.TASK_STATE_WORKING):
        print(f"[기획] {text}", flush=True)
        await up.update_status(
            state, up.new_agent_message([new_text_part(text)])
        )

    # endregion

    # region: parse
    async def execute(self, ctx: RequestContext, queue: EventQueue):
        task, up = await begin(ctx, queue)
        if task.id in self.waiting:
            await self.resume(ctx, up, task)
            return
        heard = task.history  # begin() 이 이번 메시지까지 넣어 둔다
        text = " ".join(
            get_message_text(m)
            for m in heard
            if m.role == Role.ROLE_USER
        )
        req = domain.parse_request(text)
        missing = req.get("missing", [])
        if req["ok"] and req["budget"] is None:
            missing = ["budget"]
        if missing:
            ask = ", ".join(ASK[k] for k in missing)
            await up.requires_input(
                up.new_agent_message(
                    [
                        new_text_part(f"알려 주세요: {ask}"),
                        new_data_part({"missing": missing}),
                    ]
                )
            )
            return
        await self.plan(up, task, req)

    # endregion

    # region: plan
    async def plan(self, up, task, req):
        await self.say(up, "동료 에이전트를 찾는 중")
        cards = await discover(self.urls)
        await self.say(up, f"에이전트 {len(cards)}곳을 찾았습니다")
        ctx_id = task.context_id
        lodging, meals, bus = await asyncio.gather(
            delegate(cards["lodging"], req, ctx_id),
            delegate(cards["meals"], req, ctx_id),
            delegate(cards["bus"], req, ctx_id),
        )
        # 도착 순서는 매번 다를 수 있다 — 알릴 때는 정한 순서대로.
        for label, t in (
            ("숙소", lodging),
            ("식사", meals),
            ("교통", bus),
        ):
            if t.status.state != TaskState.TASK_STATE_COMPLETED:
                why = get_message_text(t.status.message)
                print(f"[기획] {label} 실패: {why}", flush=True)
                await up.reject(
                    up.new_agent_message(
                        [new_text_part(f"{label}: {why}")]
                    )
                )
                return
            total = int(quote_of(t)["total"])
            await self.say(up, f"{label} 견적 {total:,}원")
        quotes = [quote_of(t) for t in (lodging, meals, bus)]
        items = [
            {"name": n, "amount": int(q["total"])}
            for n, q in zip(
                ("숙소", "식사", "교통"), quotes, strict=True
            )
        ]
        # endregion
        # region: settle
        token = await get_token(
            cards["settle"], "payment:read", self.client_id, self.secret
        )
        settle = await delegate(
            cards["settle"],
            {"items": items, "budget": req["budget"]},
            ctx_id,
            token=token,
            refs=[lodging.id, meals.id, bus.id],
        )
        state = settle.status.state
        if state == TaskState.TASK_STATE_AUTH_REQUIRED:
            self.waiting[task.id] = (cards, req, quotes, settle)
            total = f"{sum(i['amount'] for i in items):,}원"
            await self.say(
                up,
                f"팀장 결재가 필요합니다(합계 {total}). "
                "'승인'이라고 답하면 결재를 진행합니다.",
                TaskState.TASK_STATE_AUTH_REQUIRED,
            )
            return
        await self.finish(up, req, quotes, settle)

    # endregion

    # region: resume
    async def resume(self, ctx, up, task):
        cards, req, quotes, settle = self.waiting.pop(task.id)
        if "승인" not in get_message_text(ctx.message):
            await self.say(
                up,
                "결재가 반려되어 멈춥니다",
                TaskState.TASK_STATE_REJECTED,
            )
            return
        # 결재 토큰도 문지기를 지나니 payment:read 도 받는다
        token = await get_token(
            cards["settle"],
            "payment:read payment:approve",
            self.client_id,
            self.secret,
        )
        settle = await follow_up(
            cards["settle"], settle, "결재합니다", token
        )
        await self.finish(up, req, quotes, settle)

    # endregion

    # region: finish
    async def finish(self, up, req, quotes, settle):
        if settle.status.state != TaskState.TASK_STATE_COMPLETED:
            why = get_message_text(settle.status.message)
            await up.reject(
                up.new_agent_message([new_text_part(f"정산: {why}")])
            )
            return
        sheet = quote_of(settle)
        doc = plan_markdown(req, *quotes, sheet)
        await up.add_artifact(
            [
                new_text_part(doc, media_type="text/markdown"),
                new_data_part({**req, "total": int(sheet["total"])}),
            ],
            artifact_id="workshop-plan",
            name="워크숍 계획서",
        )
        await self.say(up, "계획서를 완성했습니다")
        await up.complete()

    # endregion

    async def cancel(self, ctx: RequestContext, queue: EventQueue):
        task = ctx.current_task
        await TaskUpdater(queue, task.id, task.context_id).cancel()


if __name__ == "__main__":
    import argparse
    import sys

    extra = argparse.ArgumentParser(add_help=False)
    extra.add_argument(
        "--agents", required=True, help="쉼표로 구분한 URL"
    )
    extra.add_argument("--client-id", default="planner")
    extra.add_argument("--client-secret", default="planner-secret")
    mine, rest = extra.parse_known_args()
    sys.argv[1:] = rest
    args = parse_args("보물상사 기획 에이전트")
    executor = PlannerExecutor(
        mine.agents.split(","), mine.client_id, mine.client_secret
    )
    serve(card(args.url), executor, args.port)
# @ norun
