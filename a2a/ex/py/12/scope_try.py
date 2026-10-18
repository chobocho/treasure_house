# 정산 에이전트에 스코프가 다른 토큰 다섯 가지로 정산을 맡긴다 —
# 누가, 어떤 스코프로, 얼마를. 받은 HTTP 상태와 작업 상태를 찍는다.
#   python 12/scope_try.py 에이전트주소 [에이전트주소 …]
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

SECRET = {"planner": "planner-secret", "intern": "intern-secret"}
SMALL = [{"name": "숙소", "amount": 2100000}]
BIG = SMALL + [
    {"name": "식사", "amount": 1542000},
    {"name": "교통", "amount": 1200000},
]
READ, BOTH = "payment:read", "payment:read payment:approve"
# (표시, 클라이언트, 달라는 스코프, 견적)
CASES = [
    ("①", "intern", READ, SMALL),
    ("②", "intern", READ, BIG),
    ("③", "planner", READ, BIG),
    ("④", "planner", BOTH, BIG),
    ("⑤", "planner", "payment:approve", BIG),
]


def post(url, body, heads):
    req = urllib.request.Request(url, body, heads)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r), r.headers
    except urllib.error.HTTPError as e:
        return e.code, json.load(e), e.headers


def token(base, cid, scope):
    form = {"grant_type": "client_credentials", "client_id": cid}
    form |= {"client_secret": SECRET[cid], "scope": scope}
    body = urllib.parse.urlencode(form).encode()
    return post(base + "oauth/token", body, {})[1]["access_token"]


# region: main
def settle(base, tok, items, n):
    msg = {"messageId": f"s-{n}", "role": "ROLE_USER"}
    msg["parts"] = [{"data": {"items": items, "budget": 6000000}}]
    rpc = {"jsonrpc": "2.0", "id": n, "method": "SendMessage"}
    rpc["params"] = {"message": msg}
    heads = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    heads["Authorization"] = f"Bearer {tok}"
    status, got, h = post(base, json.dumps(rpc).encode(), heads)
    if status != 200:
        return f"{status}\n   WWW-Authenticate: {h['WWW-Authenticate']}"
    task = got["result"]["task"]
    line = f"200 {task['status']['state'][11:]}"
    for art in task.get("artifacts", []):
        line += f" approvedBy={art['parts'][0]['data']['approvedBy']}"
    return line


for base in sys.argv[1:]:
    print(f"== {base}")
    for n, (mark, cid, scope, items) in enumerate(CASES, 1):
        total = sum(i["amount"] for i in items)
        got = settle(base, token(base, cid, scope), items, n)
        print(f"{mark} {cid} [{scope}] {total:,}원 → {got}")
# endregion
# @ norun
