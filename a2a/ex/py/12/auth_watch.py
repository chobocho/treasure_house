# AUTH_REQUIRED 를 스트림으로 받고, 그 작업을 구독해 둔 채 결재 토큰
# 으로 이어 말한다. 첫 스트림·구독이 무엇을 보고 어떻게 끝났는지
# 찍는다. SDK 없이 urllib 으로 읽는다.
#   python 12/auth_watch.py 에이전트주소
import json
import sys
import threading
import urllib.parse
import urllib.request

URL = sys.argv[1]
BIG = {
    "budget": 6000000,
    "items": [{"name": "합계", "amount": 4842000}],
}
N = iter(range(1, 100))


def token(scope):
    form = {"grant_type": "client_credentials", "client_id": "planner"}
    form |= {"client_secret": "planner-secret", "scope": scope}
    body = urllib.parse.urlencode(form).encode()
    with urllib.request.urlopen(URL + "oauth/token", body) as r:
        return json.load(r)["access_token"]


def call(method, params, tok, timeout=None):
    body = {"jsonrpc": "2.0", "id": next(N), "method": method}
    body["params"] = params
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    head["Authorization"] = f"Bearer {tok}"
    req = urllib.request.Request(URL, json.dumps(body).encode(), head)
    return urllib.request.urlopen(req, timeout=timeout)


# region: read
def read(resp, seen, task, first):
    """SSE 를 끝까지 읽어 이벤트 요약을 seen 에 담고, 끝을 준다."""
    if not resp.headers["Content-Type"].startswith("text/event-stream"):
        seen.append(f"JSON error {json.load(resp)['error']['code']}")
        first.set()
        return "스트림이 아니다"
    data = []
    try:
        for raw in resp:
            line = raw.decode().rstrip("\r\n")
            if line.startswith("data:"):
                data.append(line[5:].lstrip(" "))
                continue
            if line or not data:
                continue
            got, data = json.loads("\n".join(data)), []
            ((kind, ev),) = got["result"].items()
            task.setdefault("id", ev.get("id") or ev.get("taskId"))
            task.setdefault("contextId", ev.get("contextId"))
            state = ev.get("status", {}).get("state", "")[11:]
            seen.append(f"{kind} {state}".rstrip())
            first.set()  # 이벤트 하나를 받았다
        return "서버가 닫았다"
    except TimeoutError:
        return "3초 동안 더 없음 — 클라이언트가 끊었다"
    finally:
        first.set()


# endregion


def watch(method, params, tok):
    """스트림을 따로 읽기 시작하고, 첫 이벤트를 받으면 돌아온다."""
    seen, task, first, end = [], {}, threading.Event(), []
    resp = call(method, params, tok, timeout=3)
    th = threading.Thread(
        target=lambda: end.append(read(resp, seen, task, first))
    )
    th.start()
    first.wait(10)
    return seen, task, th, end


# region: main
read_tok = token("payment:read")
both = token("payment:read payment:approve")
msg = {
    "messageId": "w-1",
    "role": "ROLE_USER",
    "parts": [{"data": BIG}],
}
seen, task, th, end = watch(
    "SendStreamingMessage", {"message": msg}, read_tok
)
th.join()
print(f"① 스트림: {' → '.join(seen)} · {end[0]}")
sub, _, th, subend = watch(
    "SubscribeToTask", {"id": task["id"]}, read_tok
)
reply = {"messageId": "w-2", "role": "ROLE_USER", "taskId": task["id"]}
reply |= {"contextId": task["contextId"]}
reply["parts"] = [{"text": "결재합니다"}]
with call("SendMessage", {"message": reply}, both) as r:
    done = json.load(r)["result"]["task"]["status"]["state"][11:]
print(f"② 결재 토큰으로 이어 말하기 → {done}")
th.join()
print(f"③ 구독: {' → '.join(sub)} · {subend[0]}")
# endregion
# @ norun
