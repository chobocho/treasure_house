# JSON-RPC 서버 시험 — 본문 여덟 가지를 차례로 보낸다(urllib 만).
# 무엇이 오갔는지는 와이어 탭이 적는다. 여기서는 HTTP 상태만 찍는다.
import argparse
import json
import urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("--url", required=True)
args = ap.parse_args()

# region: cases
Q = {"date": "2026-10-30", "nights": 1, "headcount": 30}


def req(rid, method="ChooseLodging", params=Q):
    return {
        "jsonrpc": "2.0",
        "id": rid,
        "method": method,
        "params": params,
    }


def note():  # 알림: id 가 아예 없다
    return {
        "jsonrpc": "2.0",
        "method": "ChooseLodging",
        "params": Q,
    }


CASES = [
    ("성공", req(1)),
    ("없는 메서드", req(2, "BookLodging")),
    ("params 모자람", req(3, params={"date": "2026-10-30"})),
    ("깨진 JSON", '{"jsonrpc": "2.0", "id": 4, '),
    ("요청 아님", {"jsonrpc": "2.0", "method": 1}),
    ("알림", note()),
    (
        "배치",
        [
            req(5),
            note(),
            {"jsonrpc": "2.0", "id": 6, "method": "BookLodging"},
        ],
    ),
    ("빈 배치", []),
]
# endregion

for name, body in CASES:
    text = body if isinstance(body, str) else json.dumps(body)
    r = urllib.request.Request(
        args.url,
        data=text.encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(r) as resp:
        print(f"[{name}] HTTP {resp.status}")
# @ norun
