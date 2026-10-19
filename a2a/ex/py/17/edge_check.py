# 배포 점검 둘 — 카드의 캐시 머리글과 조건부 GET, 큰 요청 본문.
#   python 17/edge_check.py 이름=주소 …
# SDK 없이 httpx 로 묻는다(머리글과 상태 코드를 그대로 보려고).
import json
import sys

import httpx

CARD = ".well-known/agent-card.json"
MEMO = "x" * 150_000  # 본문이 150KB 를 조금 넘는다


def big_message():
    data = {"headcount": 30, "nights": 1, "depart": "강남역"}
    msg = {
        "messageId": "m-big",
        "role": "ROLE_USER",
        "parts": [{"data": data | {"memo": MEMO}}],
    }
    params = {"message": msg, "configuration": {}}
    req = {"jsonrpc": "2.0", "id": 1, "method": "SendMessage"}
    return json.dumps(req | {"params": params}).encode()


def outcome(r):  # 상태 코드와, JSON-RPC 면 그 결과·오류
    if "json" not in r.headers.get("content-type", ""):
        return f"{r.status_code} {r.headers.get('content-type')}"
    j = r.json()
    if "error" in j:
        e = j["error"]
        return f"{r.status_code} error {e['code']} {e['message']}"
    return f"{r.status_code} {j['result']['task']['status']['state']}"


# region: check
body = big_message()
print(f"큰 요청 본문: {len(body):,}바이트\n")
for arg in sys.argv[1:]:
    name, url = arg.split("=", 1)
    r = httpx.get(url + CARD)
    tag, cc = r.headers.get("etag"), r.headers.get("cache-control")
    again = "묻지 못함(ETag 없음)"
    if tag:
        r2 = httpx.get(url + CARD, headers={"If-None-Match": tag})
        again = f"{r2.status_code}"
    print(f"{name}  카드 {r.status_code}  ETag {tag or '-'}")
    print(f"{'':8}Cache-Control {cc or '-'}  다시 묻기 {again}")
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    r3 = httpx.post(url, content=body, headers=head, timeout=30)
    print(f"{'':8}큰 요청 → {outcome(r3)}")
    # 같은 본문을 길이를 밝히지 않고(Transfer-Encoding: chunked)
    r4 = httpx.post(url, content=iter([body]), headers=head, timeout=30)
    print(f"{'':8}같은 본문, chunked → {outcome(r4)}")
# endregion
# @ norun
