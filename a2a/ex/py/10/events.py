# 식사 에이전트에 SendStreamingMessage 한 번 — SDK 없이 urllib 으로
# SSE 를 읽고, 이벤트마다 한 줄씩 무엇이 왔는지 찍는다.
#   python 10/events.py 주소
import json
import sys
import urllib.request

URL = sys.argv[1]
ASK = {"nights": 1, "headcount": 30, "vegetarians": 2}


# region: open
def open_stream():
    msg = {"messageId": "m-1", "role": "ROLE_USER"}
    msg["parts"] = [{"text": "식단 부탁합니다"}, {"data": ASK}]
    body = {"jsonrpc": "2.0", "id": 1, "method": "SendStreamingMessage"}
    body["params"] = {"message": msg}
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    head["Accept"] = "text/event-stream"
    req = urllib.request.Request(URL, json.dumps(body).encode(), head)
    return urllib.request.urlopen(req)


def events(resp):
    """SSE 이벤트 하나 = (event 이름, data 를 푼 JSON)."""
    name, data = None, []
    for raw in resp:
        line = raw.decode().rstrip("\r\n")
        if line.startswith("event:"):
            name = line[6:].strip()
        elif line.startswith("data:"):
            data.append(line[5:].lstrip(" "))
        elif not line and data:
            yield name, json.loads("\n".join(data))
            name, data = None, []


# endregion


def flag(ev, key):
    """와이어에 실린 그대로 — 없으면 '없음'."""
    return json.dumps(ev[key]) if key in ev else "없음"


# region: show
def show(n, kind, ev):
    if kind == "task":
        state = ev["status"]["state"][11:]
        what = f"{state} history {len(ev.get('history', []))}"
        what += f" artifacts {len(ev.get('artifacts', []))}"
    elif kind == "statusUpdate":
        state = ev["status"]["state"][11:]
        parts = ev["status"].get("message", {}).get("parts", [])
        what = " ".join([state] + [p["text"] for p in parts])
    else:
        a = ev["artifact"]
        what = f"{a['artifactId']} append={flag(ev, 'append')}"
        what += f" lastChunk={flag(ev, 'lastChunk')}"
    print(f"{n:>2} {kind:<14} {what}")


with open_stream() as resp:
    print("Content-Type:", resp.headers["Content-Type"])
    n = 0
    for name, msg in events(resp):
        n += 1
        if name:
            print(f"   (event: {name})")
        ((kind, ev),) = msg["result"].items()
        show(n, kind, ev)
    print(f"스트림이 닫혔다 — 이벤트 {n}개")
# endregion
# @ norun
