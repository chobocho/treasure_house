# JSON-RPC 2.0 클라이언트 — urllib 만으로. 요청마다 새 id 를 붙이고,
# 응답의 id 가 맞는지, result 인지 error 인지 가른다.
import argparse
import itertools
import json
import urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("--url", required=True)
args = ap.parse_args()


# region: client
class RpcError(Exception):
    pass


ids = itertools.count(1)


def call(url, method, params):
    rid = next(ids)
    body = {"jsonrpc": "2.0", "id": rid, "method": method}
    body["params"] = params
    r = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(r) as resp:
        reply = json.load(resp)
    if reply.get("id") != rid:  # 다른 요청의 답이면 받지 않는다
        raise RpcError(f"id 가 다르다: {reply.get('id')}")
    if "error" in reply:
        e = reply["error"]
        raise RpcError(f"{e['code']} {e['message']}")
    return reply["result"]


# endregion


# region: main
Q = {"date": "2026-10-30", "nights": 1, "headcount": 30}
q = call(args.url, "ChooseLodging", Q)
print(f"ChooseLodging → {q['venueName']} {q['rooms']}실 {q['total']}원")
try:
    call(args.url, "BookLodging", Q)
except RpcError as e:
    print(f"BookLodging → 오류 {e}")
# endregion
# @ norun
