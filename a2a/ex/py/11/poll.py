# 교통 에이전트에 returnImmediately 로 배차를 맡기고 GetTask 로 본다.
# SDK 없이 urllib 으로 — 물을 때마다 무엇이 왔는지 한 줄씩 찍는다.
#   python 11/poll.py 주소 [--every MS] [--hl N]
import argparse
import json
import re
import time
import urllib.request

BUS = {"headcount": 30, "nights": 1, "depart": "강남역"}
END = ("COMPLETED", "FAILED", "CANCELED", "REJECTED")
# 첫 물음은 받은 뒤 1초, 그다음은 every(2초의 배수)마다. 단계 경계
# (4초마다)와 늘 1초 떨어져, 어느 물음이 어느 단계를 보는지가
# 이 기계가 잠깐 느려져도 실행마다 같다.
PHASE = 1.0


def rpc(url, method, params):
    body = {"jsonrpc": "2.0", "id": 1, "method": method}
    body["params"] = params
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    req = urllib.request.Request(url, json.dumps(body).encode(), head)
    raw = urllib.request.urlopen(req).read().decode()
    # 시각 문자열은 순간마다 길이가 달라(끝의 0 을 줄인다) 빼고 센다
    size = len(re.sub(r'"timestamp": ?"[^"]*"', "", raw).encode())
    return json.loads(raw)["result"], size


def send(url, mid, data, now):
    msg = {"messageId": mid, "role": "ROLE_USER"}
    msg["parts"] = [{"data": data}]
    conf = {"returnImmediately": now}
    task, _ = rpc(
        url, "SendMessage", {"message": msg, "configuration": conf}
    )
    return task["task"]


# region: poll
def poll(url, tid, every, hl):
    t0, n, total, seen = time.monotonic(), 0, 0, None
    while True:
        # n 번째 물음은 t0 + PHASE + n×every — 시계를 재지 않고 계획표로
        time.sleep(max(0, t0 + PHASE + n * every - time.monotonic()))
        params = {"id": tid}
        if hl is not None:
            params["historyLength"] = hl
        task, size = rpc(url, "GetTask", params)
        n, total = n + 1, total + size
        st = task["status"]
        parts = st.get("message", {}).get("parts", [])
        now = " ".join([st["state"][11:]] + [p["text"] for p in parts])
        hist = len(task.get("history", []))
        new = "새 소식" if now != seen else "그대로"
        print(f"{n:>2} {size:>5}B history {hist} {new} {now}")
        seen = now
        if st["state"][11:] in END:
            return n, total


# endregion


def main():
    p = argparse.ArgumentParser()
    p.add_argument("url")
    p.add_argument("--every", type=int, default=2000)
    p.add_argument("--hl", type=int)
    a = p.parse_args()
    # 서버의 첫 작업은 답이 늦다(처음 쓰는 길을 데우는 중) — 계획표가
    # 밀리지 않게, 곧장 거절될 0명 요청 하나로 먼저 데운다
    send(a.url, "warm-up", {"headcount": 0, "nights": 1}, False)
    task = send(a.url, "poll-1", BUS, True)
    print("SendMessage →", task["status"]["state"][11:])
    n, total = poll(a.url, task["id"], a.every / 1000, a.hl)
    print(f"GetTask {n}번, 몸통 합계 {total}B(시각 빼고)")


main()
# @ norun
