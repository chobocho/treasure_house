"""정산 에이전트 — 견적을 모아 예산과 대 보고, 결재를 받는다.

보여 주는 것: securitySchemes(OAuth2 client-credentials), Bearer
토큰 검사와 401, 스코프에 따른 권한, 확장 Agent Card, 서명된 카드
(JWS EdDSA + JCS), 작업 중 권한 요청(AUTH_REQUIRED).
같은 서버가 시험용 OAuth2 토큰 발급기(/oauth/token)도 겸한다.
"""

import json
from urllib.parse import parse_qs

from a2a.helpers.proto_helpers import (
    new_data_part,
    new_task_from_user_message,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    ClientCredentialsOAuthFlow,
    OAuth2SecurityScheme,
    OAuthFlows,
    SecurityRequirement,
    SecurityScheme,
    StringList,
)
from a2a.utils.signing import create_agent_card_signer
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    SimpleUser,
)
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

from agents.common import (
    PROVIDER,
    as_ints,
    data_of,
    jsonrpc_interface,
    parse_args,
    serve,
)
from workshop import domain
from workshop.fixtures import FIXTURES, clients

KEYS = FIXTURES / "keys"
APPROVE = "payment:approve"
SCOPES = {"payment:read": "정산 조회", APPROVE: "결재 승인"}

# region: tokens
# 발급한 토큰 → (클라이언트, 스코프). 시험용이라 메모리에만 둔다.
TOKENS: dict[str, tuple[str, list[str]]] = {}
ISSUED: dict[str, int] = {}


async def token_endpoint(request):
    """OAuth2 client-credentials 토큰 발급(RFC 6749 4.4절)."""
    # 몸통은 application/x-www-form-urlencoded. 표준 라이브러리로 푼다.
    raw = parse_qs((await request.body()).decode())
    form = {k: v[0] for k, v in raw.items()}
    if form.get("grant_type") != "client_credentials":
        return JSONResponse({"error": "unsupported_grant_type"}, 400)
    who = next(
        (
            c
            for c in clients()
            if c["clientId"] == form.get("client_id")
            and c["clientSecret"] == form.get("client_secret")
        ),
        None,
    )
    if who is None:
        return JSONResponse({"error": "invalid_client"}, 401)
    asked = str(form.get("scope", "")).split() or who["scopes"]
    if not set(asked) <= set(who["scopes"]):
        return JSONResponse({"error": "invalid_scope"}, 400)
    cid = who["clientId"]
    ISSUED[cid] = ISSUED.get(cid, 0) + 1
    # 진짜 토큰은 추측할 수 없는 난수여야 한다. 여기서는 캡처가
    # 매번 같도록 일부러 '클라이언트-순번'으로 만든다.
    token = f"tok-{cid}-{ISSUED[cid]}"
    TOKENS[token] = (cid, asked)
    print(f"[정산] 토큰 발급: {cid} {' '.join(asked)}", flush=True)
    return JSONResponse(
        {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": " ".join(asked),
        }
    )


# endregion


# region: bearer
class BearerBackend(AuthenticationBackend):
    """Authorization: Bearer <토큰> 을 읽어 사용자와 스코프를 붙인다."""

    async def authenticate(self, conn):
        header = conn.headers.get("authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or token not in TOKENS:
            return None  # 익명 — 막을지는 RequireBearer 가 정한다
        cid, scopes = TOKENS[token]
        return AuthCredentials(scopes), SimpleUser(cid)


class RequireBearer:
    """JSON-RPC 경로(POST /)는 토큰 없이는 401 로 돌려보낸다.

    카드·JWKS·토큰 발급 경로는 누구나 읽어야 하므로 열어 둔다.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        rpc = scope["type"] == "http" and scope["path"] == "/"
        if rpc and not scope["user"].is_authenticated:
            sent = any(
                k == b"authorization" for k, _ in scope["headers"]
            )
            # RFC 6750: 토큰이 아예 없으면 error 를 붙이지 않는다.
            challenge = 'Bearer realm="settlement"'
            if sent:
                challenge += ', error="invalid_token"'
            body = {
                "error": "invalid_token" if sent else "unauthorized"
            }
            resp = JSONResponse(
                body, 401, headers={"WWW-Authenticate": challenge}
            )
            await resp(scope, receive, send)
            return
        await self.app(scope, receive, send)


# endregion


# region: card
def skill(sid, name, desc):
    return AgentSkill(
        id=sid, name=name, description=desc, tags=["budget", "workshop"]
    )


def card(url, extended=False):
    oauth = SecurityScheme(
        oauth2_security_scheme=OAuth2SecurityScheme(
            flows=OAuthFlows(
                client_credentials=ClientCredentialsOAuthFlow(
                    token_url=url + "oauth/token", scopes=SCOPES
                )
            )
        )
    )
    skills = [
        skill(
            "check-budget", "예산 검토", "견적 합계를 예산과 대 봅니다."
        )
    ]
    if extended:  # 로그인한 클라이언트에게만 보이는 기술
        skills.append(
            skill(
                "settle-budget",
                "정산·결재",
                "결재를 받아 정산서를 냅니다.",
            )
        )
    return AgentCard(
        name="보물상사 정산 에이전트",
        description="견적을 모아 예산과 대 보고 결재를 받습니다.",
        version="1.0.0",
        provider=PROVIDER,
        supported_interfaces=[jsonrpc_interface(url)],
        capabilities=AgentCapabilities(
            streaming=True, extended_agent_card=True
        ),
        security_schemes={"oauth": oauth},
        security_requirements=[
            SecurityRequirement(
                schemes={"oauth": StringList(list=["payment:read"])}
            )
        ],
        default_input_modes=["application/json"],
        default_output_modes=["application/json"],
        skills=skills,
    )


def signed(c, url):
    """공개 카드에 서명을 단다. EdDSA 는 결정적이라 매번 같은 값."""
    sign = create_agent_card_signer(
        signing_key=(KEYS / "settlement-ed25519.pem").read_bytes(),
        protected_header={
            "alg": "EdDSA",
            "kid": "settlement-2026",
            "jku": url + ".well-known/jwks.json",
            "typ": "JOSE",
        },
    )
    return sign(c)


async def jwks_endpoint(request):
    keys = json.loads((KEYS / "jwks.json").read_text(encoding="utf-8"))
    return JSONResponse(keys)


# endregion


# region: executor
class SettlementExecutor(AgentExecutor):
    async def execute(self, ctx: RequestContext, queue: EventQueue):
        task = ctx.current_task or new_task_from_user_message(
            ctx.message
        )
        if ctx.current_task is None:
            await queue.enqueue_event(task)
        up = TaskUpdater(queue, task.id, task.context_id)
        auth = ctx.call_context.state.get("auth")
        who = ctx.call_context.user.user_name
        scopes = set(auth.scopes) if auth else set()
        req = data_of(*task.history, ctx.message)
        items = [as_ints(i, "amount") for i in req.get("items", [])]
        result = domain.settle(
            {
                "items": items,
                "budget": int(req.get("budget", 0)),
                "approved": APPROVE in scopes,
            }
        )
        if not result["ok"]:
            over = f"{result['reason']} ({result['over']:,}원)"
            print(f"[정산] 거절: {over}", flush=True)
            await up.reject(up.new_agent_message([new_text_part(over)]))
            return
        if result["status"] == "auth-required":
            note = (
                f"합계 {result['total']:,}원은 결재가 필요합니다. "
                f"{APPROVE} 스코프 토큰으로 다시 보내 주세요."
            )
            print(f"[정산] 결재 요청: {who}", flush=True)
            await up.requires_auth(
                up.new_agent_message(
                    [new_text_part(note), new_data_part(result)]
                )
            )
            return
        sheet = {**result, "items": items, "approvedBy": who}
        print(f"[정산] 완료: {result['total']:,}원 ({who})", flush=True)
        await up.add_artifact(
            [new_data_part(sheet)],
            artifact_id="settlement",
            name="정산서",
        )
        await up.complete()

    async def cancel(self, ctx: RequestContext, queue: EventQueue):
        task = ctx.current_task
        await TaskUpdater(queue, task.id, task.context_id).cancel()


# endregion


if __name__ == "__main__":
    args = parse_args("보물상사 정산 에이전트")
    serve(
        signed(card(args.url), args.url),
        SettlementExecutor(),
        args.port,
        routes=[
            Route("/oauth/token", token_endpoint, methods=["POST"]),
            Route("/.well-known/jwks.json", jwks_endpoint),
        ],
        middleware=[
            Middleware(
                AuthenticationMiddleware, backend=BearerBackend()
            ),
            Middleware(RequireBearer),
        ],
        extended_agent_card=card(args.url, extended=True),
    )
