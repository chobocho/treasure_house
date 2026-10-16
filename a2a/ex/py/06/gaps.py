# 맨손 서버에 없는 것 두드리기 — 빠진 메서드 넷, 판을 알리는 다른 길.
# 같은 프로그램을 SDK 서버에도 보내 답을 견준다. urllib 만 쓴다.
#   python 06/gaps.py 주소
import json
import sys
import urllib.error
import urllib.request

URL = sys.argv[1]
N = iter(range(1, 100))  # messageId 와 JSON-RPC id 를 매기는 번호


# region: rpc
def call(method, params, version="1.0", query=""):
    """JSON-RPC 한 번 → 응답(스트림이면 첫 이벤트), HTTP 오류면 코드."""
    body = {"jsonrpc": "2.0", "id": next(N), "method": method}
    body["params"] = params
    head = {"Content-Type": "application/json"}
    head |= {"A2A-Version": version} if version else {}
    data = json.dumps(body).encode()
    req = urllib.request.Request(URL + query, data, head)
    try:
        with urllib.request.urlopen(req) as r:
            if r.headers.get_content_type() != "text/event-stream":
                return json.load(r)
            for raw in r:  # 첫 data 줄 하나만
                if raw.startswith(b"data:"):
                    return json.loads(raw[5:])
    except urllib.error.HTTPError as e:
        return {"http": e.code}


def line(resp):
    """응답 → 한 줄: 오류의 code·message, 또는 result 의 생김새."""
    if "http" in resp:
        return f"HTTP {resp['http']}"
    if "error" in resp:
        e = resp["error"]
        return f"{e['code']} {e['message']}"
    res = resp["result"]
    if "status" in res:
        return f"Task {res['status']['state'][11:]}"
    return "{" + ", ".join(sorted(res)) + "}"  # 키의 차례는 SDK 마다


def pad(label, width=21):
    """한글은 두 칸 — 화살표가 한 줄로 서게 칸 수로 채운다."""
    wide = sum(1 for c in label if "가" <= c <= "힣")
    return label + " " * (width - len(label) - wide)


# endregion


# region: probe
msg = {"messageId": "g-1", "role": "ROLE_USER"}
msg["parts"] = [{"text": "2026-10-30 1박 30명"}]
task = call("SendMessage", {"message": msg})["result"]["task"]
tid = task["id"]  # 끝난 작업 하나 — 아래 요청들의 재료
for step, method, params in (
    ("ListTasks", "ListTasks", {}),
    ("SubscribeToTask", "SubscribeToTask", {"id": tid}),
    (
        "푸시 설정 만들기",
        "CreateTaskPushNotificationConfig",
        {"taskId": tid, "url": "http://127.0.0.1:10699/"},
    ),
    ("확장 카드", "GetExtendedAgentCard", {}),
):
    print(f"{pad(step)} → {line(call(method, params))}")
for step, kw in (
    ("GetTask 판 1.0.1", {"version": "1.0.1"}),
    ("GetTask 판 1.5", {"version": "1.5"}),
    ("GetTask 판 없음", {"version": ""}),
    (
        "GetTask ?A2A-Version",
        {"version": "", "query": "?A2A-Version=1.0"},
    ),
):
    print(f"{pad(step)} → {line(call('GetTask', {'id': tid}, **kw))}")
# endregion
# @ norun
