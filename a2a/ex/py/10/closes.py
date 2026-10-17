# 종료 실험 에이전트에 일곱 가지 끝을 차례로 청하고, 스트림이 어떻게
# 끝났는지 — 서버가 닫았나, 2초 동안 열린 채였나 — 와 저장된 상태를
# 찍는다. SDK 없이 urllib 으로 읽는다.
#   python 10/closes.py 주소
import json
import sys
import time
import urllib.request

URL = sys.argv[1]
WORDS = ["COMPLETED", "INPUT_REQUIRED", "AUTH_REQUIRED", "WORKING"]
WORDS += ["LATE", "BOOM", "MESSAGE"]
N = iter(range(1, 100))  # messageId 와 JSON-RPC id 의 번호


def call(method, params, timeout=None):
    body = {"jsonrpc": "2.0", "id": next(N), "method": method}
    body["params"] = params
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    req = urllib.request.Request(URL, json.dumps(body).encode(), head)
    return urllib.request.urlopen(req, timeout=timeout)


# region: read
def read(word):
    """스트림 하나 → (이벤트 요약 목록, 끝난 모습, taskId)."""
    msg = {"messageId": f"m-{word}", "role": "ROLE_USER"}
    msg["parts"] = [{"text": word}]
    seen, task_id, data = [], None, []
    resp = call("SendStreamingMessage", {"message": msg}, timeout=2)
    if not resp.headers["Content-Type"].startswith("text/event-stream"):
        got = json.load(resp)  # 스트림이 아니라 JSON 하나
        return [f"JSON error {got['error']['code']}"], "JSON 응답", None
    try:
        for raw in resp:
            line = raw.decode().rstrip("\r\n")
            if line.startswith("data:"):
                data.append(line[5:].lstrip(" "))
                continue
            if line or not data:
                continue
            got = json.loads("\n".join(data))
            data = []
            if "error" in got:
                seen.append(f"error {got['error']['code']}")
                continue
            ((kind, ev),) = got["result"].items()
            task_id = task_id or ev.get("id") or ev.get("taskId")
            state = ev.get("status", {}).get("state", "")[11:]
            seen.append(f"{kind} {state}".rstrip())
        end = "서버가 닫았다"
    except TimeoutError:
        end = "2초 동안 열린 채 — 클라이언트가 끊었다"
    resp.close()
    return seen, end, task_id


# endregion


# region: main
for i, word in enumerate(WORDS):
    seen, end, task_id = read(word)
    print(f"{chr(0x2460 + i)} {word}: {' → '.join(seen)}")
    time.sleep(1)  # 늦게 실리는 상태(LATE)가 저장될 틈
    stored = "Task 없음"
    if task_id:
        with call("GetTask", {"id": task_id}) as r:
            got = json.load(r)
        if "error" in got:
            stored = f"error {got['error']['code']}"
        else:
            stored = got["result"]["status"]["state"][11:]
    print(f"   끝: {end} · GetTask → {stored}")
# endregion
# @ norun
