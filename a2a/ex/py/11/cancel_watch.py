# 달리는 배차를 취소하면 구독자와 웹훅은 무엇을 보나. SDK 없이 urllib.
# (1) 푸시 설정을 실어 returnImmediately 로 맡기고 (2) SubscribeToTask
# 스트림을 연다. (3) 스트림에 첫 WORKING 이 오면 CancelTask — 시간이
# 아니라 이벤트에 맞춰 취소한다. (4) 스트림이 닫히기를, 중계기에 끝
# 알림이 지나가기를 기다려 셋이 본 것을 찍는다.
#   python 11/cancel_watch.py 탭 에이전트 웹훅 중계기 [N]
# 탭은 에이전트 앞의 탭(구독만 에이전트에 곧장), N 은 기다릴 끝 알림의
# 수(기본 1) — TS 서버는 CANCELED 를 두 번 보낸다.
import json
import sys
import threading
import time
import urllib.request

TAP, DIRECT, HOOK, RELAY = sys.argv[1:5]
ENDS = sys.argv[5] if len(sys.argv) > 5 else "1"
BUS = {"headcount": 30, "nights": 1, "depart": "강남역"}
HEAD = {"Content-Type": "application/json", "A2A-Version": "1.0"}


def body(method, params):
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }
    return json.dumps(req).encode()


def rpc(method, params):
    req = urllib.request.Request(TAP, body(method, params), HEAD)
    return json.loads(urllib.request.urlopen(req).read())["result"]


def line(ev):
    """StreamResponse 하나 → '종류 상태 글'."""
    ((kind, e),) = ev.items()
    st = e.get("status", {})
    text = [p["text"] for p in st.get("message", {}).get("parts", [])]
    return f"{kind} {st.get('state', '')[11:]} {' '.join(text)}".strip()


# region: watch
def watch(tid, seen, working):
    """구독 스트림을 읽어 seen 에 적는다. 첫 WORKING 이면 알린다."""
    head = {**HEAD, "Accept": "text/event-stream"}
    req = urllib.request.Request(
        DIRECT, body("SubscribeToTask", {"id": tid}), head
    )
    try:  # 닫히지 않는 스트림에 대비한 마지막 안전판
        with urllib.request.urlopen(req, timeout=8) as resp:
            for raw in resp:
                if raw.startswith(b"data:"):
                    ev = json.loads(raw[5:])["result"]
                    seen.append(line(ev))
                    if "WORKING" in seen[-1]:
                        working.set()
        seen.append("(스트림이 닫혔다)")
    except TimeoutError:
        seen.append("(8초 동안 아무것도 오지 않았다)")


# endregion


def hooked(tid):
    """첫 WORKING 푸시가 중계기에 닿을 때까지 — 서버 출력의 줄 차례가
    실행마다 같게(TS 서버는 푸시를 보낸 뒤 한 줄을 찍는다)."""
    for _ in range(400):
        got = json.loads(urllib.request.urlopen(f"{RELAY}seen").read())
        if any("WORKING" in r["what"] for r in got.get(tid, [])):
            return
        time.sleep(0.05)


# region: main
def main():
    msg = {"messageId": "cancel-1", "role": "ROLE_USER"}
    msg["parts"] = [{"data": BUS}]
    conf = {"returnImmediately": True}
    conf["taskPushNotificationConfig"] = {"url": HOOK, "token": "tok-c"}
    sent = rpc("SendMessage", {"message": msg, "configuration": conf})
    tid = sent["task"]["id"]
    seen, working = [], threading.Event()
    reader = threading.Thread(target=watch, args=(tid, seen, working))
    reader.start()
    working.wait(20)  # 첫 단계가 스트림에 왔다
    hooked(tid)  # 그 단계의 푸시도 웹훅에 닿았다
    task = rpc("CancelTask", {"id": tid})
    print("CancelTask →", line({"task": task}))
    reader.join()
    print("구독 스트림:", *seen, sep="\n  ")
    url = f"{RELAY}wait?task={tid}&n={ENDS}"  # 끝 알림 N건이 지나가면
    pushed = json.loads(urllib.request.urlopen(url).read())
    print("웹훅:", *[r["what"] for r in pushed], sep="\n  ")
    task = rpc("GetTask", {"id": tid, "historyLength": 0})
    print("GetTask →", line({"task": task}))


# endregion

main()
# @ norun
