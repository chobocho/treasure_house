# 식사 에이전트에 스트림을 열고, 첫 조각을 받은 뒤 SubscribeToTask
# 구독자 둘을 붙이고 원래 스트림을 끊는다. 구독 하나는 두 이벤트 뒤에
# 끊고, 다른 하나는 끝까지 읽는다. 끝난 작업과 없는 작업에도 구독해
# 본다. SDK 없이 urllib 으로 읽는다.
#   python 10/resub.py 주소
import json
import sys
import urllib.error
import urllib.request

URL = sys.argv[1]
ASK = {"nights": 1, "headcount": 30, "vegetarians": 2}
N = iter(range(1, 100))  # JSON-RPC id


def call(method, params):
    body = {"jsonrpc": "2.0", "id": next(N), "method": method}
    body["params"] = params
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    req = urllib.request.Request(URL, json.dumps(body).encode(), head)
    return urllib.request.urlopen(req, timeout=10)


def events(resp):
    """SSE 이벤트 하나 = data 를 푼 JSON-RPC 응답 하나."""
    data = []
    for raw in resp:
        line = raw.decode().rstrip("\r\n")
        if line.startswith("data:"):
            data.append(line[5:].lstrip(" "))
        elif not line and data:
            yield json.loads("\n".join(data))
            data = []


# region: show
def show(got):
    """이벤트 하나 → 한 줄. 첫 Task 는 아티팩트마다 파트 수를 붙인다."""
    if "error" in got:
        e = got["error"]
        return f"error {e['code']} {e['message']}"
    ((kind, ev),) = got["result"].items()
    state = ev.get("status", {}).get("state", "")[11:]
    if kind == "task":
        arts = [
            f"{a['artifactId']}×{len(a['parts'])}"
            for a in ev.get("artifacts", [])
        ]
        return f"task {state} [{' '.join(arts)}]"
    if kind == "statusUpdate":
        msg = ev["status"].get("message", {}).get("parts", [{}])
        return f"statusUpdate {state} {msg[0].get('text', '')}".rstrip()
    a = ev["artifact"]["artifactId"]
    return f"artifactUpdate {a}{' +' if ev.get('append') else ''}"


# endregion


def answer(method, params):
    """스트림이면 이벤트 줄들, JSON 하나면 그 오류 한 줄."""
    try:
        resp = call(method, params)
    except urllib.error.HTTPError as e:
        resp = e
    if resp.headers["Content-Type"].startswith("text/event-stream"):
        with resp:
            return [show(got) for got in events(resp)]
    return [show(json.load(resp))]


# region: main
msg = {"messageId": "m-1", "role": "ROLE_USER"}
msg["parts"] = [{"text": "식단 부탁합니다"}, {"data": ASK}]
s0 = call("SendStreamingMessage", {"message": msg})
it0 = events(s0)
print("원래 스트림:")
for got in it0:
    print("  " + show(got))
    ((kind, ev),) = got["result"].items()
    task_id = ev.get("id") or ev.get("taskId")
    if kind == "artifactUpdate":
        break  # 첫 조각까지 받았다
# 구독자 둘을 붙인 다음, 원래 스트림을 끊는다
s1 = call("SubscribeToTask", {"id": task_id})
s2 = call("SubscribeToTask", {"id": task_id})
s0.close()
print("  (끊음)")
print("구독 1:")
for i, got in enumerate(events(s1)):
    print("  " + show(got))
    if i == 2:
        break
s1.close()
print("  (끊음)")
print("구독 2:")
for got in events(s2):
    print("  " + show(got))
print("  (서버가 닫음)")
# endregion

# region: after
with call("GetTask", {"id": task_id}) as r:
    t = json.load(r)["result"]
print("GetTask:", show({"result": {"task": t}}))
print("끝난 작업에 구독:")
for line in answer("SubscribeToTask", {"id": task_id}):
    print("  " + line)
print("없는 작업에 구독:")
for line in answer("SubscribeToTask", {"id": "no-such-task"}):
    print("  " + line)
# endregion
# @ norun
