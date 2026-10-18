"""고치기 전의 문지기로 띄운 정산 에이전트.

완성 정산 에이전트(agents/settlement.py)의 Bearer 검사는 처음에
아래 두 클래스였다 — 토큰이 발급 기록에 있는지만 보고, 카드가
요구하는 스코프(payment:read)는 보지 않았다. 고치기 전의 코드를
그대로 옮겨 두고, 카드·실행기·발급기는 완성 에이전트의 것을 쓴다.
    python 12/bearer_old.py --port P [--url U]
"""

from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    SimpleUser,
)
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route

from agents.common import parse_args, serve
from agents.settlement import (
    TOKENS,
    SettlementExecutor,
    card,
    jwks_endpoint,
    signed,
    token_endpoint,
)


# region: before
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

if __name__ == "__main__":
    args = parse_args("고치기 전의 정산 에이전트")
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
# @ norun
