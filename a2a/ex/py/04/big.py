# 큰 raw 파트를 맨손 JSON-RPC 로 보낸다(SDK 없이 urllib). 파일 크기를
# 둘로 바꿔 가며, 주소마다 HTTP 상태와 에이전트의 답을 한 줄씩 찍는다.
#   python 04/big.py 주소…
import base64
import json
import sys
import urllib.error
import urllib.request


# region: body
def body(size):
    raw = base64.b64encode(bytes(size)).decode()  # 0 바이트 size 개
    part = {"raw": raw, "filename": "map.png", "mediaType": "image/png"}
    msg = {
        "messageId": f"big-{size}",
        "role": "ROLE_USER",
        "parts": [part],
    }
    req = {"jsonrpc": "2.0", "id": 1, "method": "SendMessage"}
    req["params"] = {"message": msg}
    return json.dumps(req).encode()


# endregion


def send(url, data):
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, data, head)
        ) as r:
            res = json.load(r)["result"]["message"]
            return f"{r.status} {res['parts'][0]['text']}"
    except urllib.error.HTTPError as e:
        return f"{e.code} {e.reason}"


for size in (70_000, 80_000):
    data = body(size)
    print(f"파일 {size:,}바이트 → 요청 본문 {len(data):,}바이트")
    for url in sys.argv[1:]:
        print(f"  {url} → {send(url, data)}")
# @ norun
