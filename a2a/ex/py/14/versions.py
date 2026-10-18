# 판 머리글을 바꿔 가며 없는 작업을 묻는다 — 서버가 그 판을 받으면
# 작업 조회까지 가서 "작업 없음", 아니면 VersionNotSupported.
#   python 14/versions.py RPC1 RPC2 RPC3 -- REST1 REST2 REST3
import sys

import httpx

GET = {"jsonrpc": "2.0", "id": 1, "method": "GetTask"}
GET["params"] = {"id": "t-nope"}
NO = "VERSION_NOT_SUPPORTED"
CASES = ["1.0", "1.0.1", "1.1", "1.5", "2.0", "0.3", "없음", "?인자"]


# region: ask
def ask(url, rest, case):
    """한 번 묻고 답을 통과(작업 없음)·거절(판)·그 밖의 코드로."""
    head = {} if case in ("없음", "?인자") else {"A2A-Version": case}
    q = {"A2A-Version": "1.0"} if case == "?인자" else {}
    if rest:
        r = httpx.get(url + "tasks/t-nope", headers=head, params=q)
        body = r.json() if "json" in r.headers["content-type"] else {}
        why = body.get("error", {}).get("details", [{}])[0]
        got = why.get("reason", str(r.status_code))
        return {"TASK_NOT_FOUND": "통과", NO: "거절"}.get(got, got)
    r = httpx.post(url, json=GET, headers=head, params=q)
    code = r.json()["error"]["code"]
    return {-32001: "통과", -32009: "거절"}.get(code, str(code))


# endregion

rpc = sys.argv[1:4]
rest = sys.argv[5:8]
print("JSON-RPC        HTTP+JSON")
print("py   ts   go    py   ts   go     A2A-Version")
for case in CASES:
    a = [ask(u, False, case) for u in rpc]
    b = [ask(u, True, case) for u in rest]
    print(" ".join(a), " ", " ".join(b), "  ", case)
# @ norun
