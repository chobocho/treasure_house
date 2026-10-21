# 정산 에이전트의 토큰 발급기(/oauth/token)에 여러 가지로 묻는다 —
# 맞는 요청 둘과 틀린 요청 다섯. 받은 HTTP 상태와 몸통을 그대로 찍는다.
#   python 12/token_try.py 발급기주소 [발급기주소 …]
import base64
import sys
import urllib.error
import urllib.parse
import urllib.request

PLANNER = {"client_id": "planner", "client_secret": "planner-secret"}
CC = {"grant_type": "client_credentials"}
BASIC = base64.b64encode(b"planner:planner-secret").decode()

# (표시, 폼, 머리글) — 머리글은 HTTP Basic 으로 클라이언트를 밝힐 때만
CASES = [
    ("① 스코프 없이", {**CC, **PLANNER}, {}),
    ("② 조회만", {**CC, **PLANNER, "scope": "payment:read"}, {}),
    (
        "③ intern 이 결재를",
        {**CC, "client_id": "intern", "client_secret": "intern-secret"}
        | {"scope": "payment:approve"},
        {},
    ),
    ("④ 틀린 비밀", {**CC, **PLANNER, "client_secret": "guess"}, {}),
    ("⑤ password 흐름", {**PLANNER, "grant_type": "password"}, {}),
    ("⑥ grant_type 없음", PLANNER, {}),
    ("⑦ HTTP Basic", CC, {"Authorization": f"Basic {BASIC}"}),
]


# region: ask
def ask(url, form, heads):
    body = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(url, body, heads)  # POST, 폼 몸통
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode(), r.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), e.headers


for url in sys.argv[1:]:
    print(f"== {url}")
    for mark, form, heads in CASES:
        status, body, h = ask(url, form, heads)
        print(f"{mark}: {status} {body}")
        if mark.startswith("①"):  # 토큰이 든 응답의 캐시 머리글
            cache = h.get("Cache-Control", "(없음)")
    print(f"   ① 의 Cache-Control: {cache}")
# endregion
# @ norun
