# 종료 실험 에이전트에 끝나지 않는 세 가지 끝을 청한 뒤, 그 작업에
# SubscribeToTask 로 다시 붙는다. 실행기는 이미 돌아갔다 — 다시 붙은
# 스트림은 무엇을 주고, 언제 닫히나. SDK 없이 urllib 으로 읽는다.
#   python 10/paused.py 주소
import json
import sys
import urllib.request

URL = sys.argv[1]
WORDS = ["INPUT_REQUIRED", "AUTH_REQUIRED", "WORKING"]
N = iter(range(1, 100))  # messageId 와 JSON-RPC id 의 번호


def call(method, params):
    body = {"jsonrpc": "2.0", "id": next(N), "method": method}
    body["params"] = params
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    req = urllib.request.Request(URL, json.dumps(body).encode(), head)
    return urllib.request.urlopen(req, timeout=2)


# region: read
def read(resp):
    """스트림 하나 → (이벤트 요약들, 끝난 모습, taskId)."""
    seen, task_id, data = [], None, []
    try:
        for raw in resp:
            line = raw.decode().rstrip("\r\n")
            if line.startswith("data:"):
                data.append(line[5:].lstrip(" "))
            elif not line and data:
                got = json.loads("\n".join(data))
                data = []
                ((kind, ev),) = got["result"].items()
                task_id = task_id or ev.get("id") or ev.get("taskId")
                state = ev["status"]["state"][11:]
                seen.append(f"{kind} {state}")
        end = "서버가 닫았다"
    except TimeoutError:
        end = "2초 동안 열린 채"
    resp.close()
    return seen, end, task_id


# endregion

# region: main
for i, word in enumerate(WORDS):
    msg = {"messageId": f"m-{word}", "role": "ROLE_USER"}
    msg["parts"] = [{"text": word}]
    seen, end, task_id = read(
        call("SendStreamingMessage", {"message": msg})
    )
    print(f"{chr(0x2460 + i)} {word}: {' → '.join(seen)} · {end}")
    seen, end, _ = read(call("SubscribeToTask", {"id": task_id}))
    print(f"   다시 붙음: {' → '.join(seen)} · {end}")
# endregion
# @ norun
