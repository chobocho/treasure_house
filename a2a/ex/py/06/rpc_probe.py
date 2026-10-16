# 맨손 서버 하나에 틀린 요청 열 가지를 보내고, 답의 오류만 한 줄씩.
# urllib 만 쓴다 — 어느 SDK 의 손도 타지 않은 바이트를 보내려고.
#   python 06/rpc_probe.py 주소
import json
import sys
import urllib.request

URL = sys.argv[1]
MSG = {"messageId": "probe-1", "role": "ROLE_USER"}
MSG["parts"] = [{"text": "숙소 부탁합니다"}]


def env(method, params):
    """JSON-RPC 봉투 — id 는 늘 1."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }


# region: cases
V1, V03, PATCH = (
    {"A2A-Version": "1.0"},
    {"A2A-Version": "0.3"},
    {"A2A-Version": "1.0.1"},
)
SEND = env("SendMessage", {"message": MSG})
CASES = [  # (이름, 판 헤더, 본문)
    ("판 헤더 없음", {}, SEND),
    ("판 0.3", V03, SEND),
    ("판 0.3 + 옛 이름", V03, env("message/send", {"message": MSG})),
    ("판 1.0.1, 없는 작업", PATCH, env("GetTask", {"id": "nope"})),
    ("깨진 JSON", V1, '{"jsonrpc": "2.0",'),
    ("배치(배열)", V1, [SEND]),
    ("id 없음(알림)", V1, {k: v for k, v in SEND.items() if k != "id"}),
    ("v1.0 에 옛 이름", V1, env("message/send", {"message": MSG})),
    ("params 가 배열", V1, env("GetTask", ["nope"])),
    (
        "parts 가 빈 배열",
        V1,
        env("SendMessage", {"message": MSG | {"parts": []}}),
    ),
]
# endregion


# region: probe
def post(headers, body):
    """본문을 그대로 보내고 (HTTP 상태, 응답 JSON) 을 돌려준다."""
    data = body if isinstance(body, str) else json.dumps(body)
    head = {"Content-Type": "application/json"} | headers
    req = urllib.request.Request(URL, data.encode(), head)
    with urllib.request.urlopen(req) as r:
        return r.status, json.load(r)


for name, headers, body in CASES:
    status, resp = post(headers, body)
    err = resp.get("error", {})
    detail = err.get("data", [{}])[0]
    # ErrorInfo 는 reason, BadRequest 는 틀린 필드를 찍는다
    why = detail.get("reason") or ",".join(
        v["field"] for v in detail.get("fieldViolations", [])
    )
    msg = err.get("message", "")
    print(f"{status} {err.get('code')} {msg:<32} {why:<21} ← {name}")
# endregion
# @ norun
