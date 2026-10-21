# 느린 클라이언트 하나가 서버 전체를 세우는가 — 연결 하나를 열어
# 요청의 머리글을 반만 보내 두고, 그동안 다른 요청을 보낸다.
#   python 06/stall.py 포트
import json
import socket
import sys
import urllib.request

PORT = int(sys.argv[1])

# region: stall
slow = socket.create_connection(("127.0.0.1", PORT))
slow.sendall(b"POST / HTTP/1.1\r\nHost: x\r\n")  # 빈 줄을 안 보낸다
body = {"jsonrpc": "2.0", "id": 1, "method": "GetTask"}
body["params"] = {"id": "nope"}
head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
req = urllib.request.Request(
    f"http://127.0.0.1:{PORT}/", json.dumps(body).encode(), head
)
try:
    with urllib.request.urlopen(req, timeout=2) as r:
        print("다른 요청 → 답:", json.load(r)["error"]["message"])
except TimeoutError:
    print("다른 요청 → 2초 안에 답이 없다")
slow.close()
# endregion
# @ norun
