# SSE 응답을 HTTP 의 날 바이트로 본다 — 머리와, 본문이 어떻게
# 잘려(프레이밍) 오는지. 소켓을 직접 열고, 닫힐 때까지 다 읽는다.
#   python 06/frames.py 포트
import json
import socket
import sys

PORT = int(sys.argv[1])
MSG = {"messageId": "f-1", "role": "ROLE_USER"}
MSG["parts"] = [
    {"data": {"date": "2026-10-30", "nights": 1, "headcount": 30}}
]
BODY = json.dumps(
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "SendStreamingMessage",
        "params": {"message": MSG},
    }
).encode()


# region: send
def exchange():
    """요청을 쓰고, 서버가 연결을 닫을 때까지 받은 바이트 전부."""
    head = (
        "POST / HTTP/1.1\r\n"
        f"Host: 127.0.0.1:{PORT}\r\n"
        "Content-Type: application/json\r\n"
        "A2A-Version: 1.0\r\n"
        f"Content-Length: {len(BODY)}\r\n"
        "Connection: close\r\n\r\n"  # 다 보내면 닫아 달라
    )
    with socket.create_connection(("127.0.0.1", PORT)) as s:
        s.sendall(head.encode() + BODY)
        got = b""
        while chunk := s.recv(65536):
            got += chunk
    return got


# endregion


# region: frames
def kind(ev):
    """이벤트 하나(data 줄 + 빈 줄)에 실린 StreamResponse 의 종류."""
    resp = json.loads(ev.decode().removeprefix("data: "))
    return "data: … " + next(iter(resp["result"]))


head, _, body = exchange().partition(b"\r\n\r\n")
lines = head.decode().split("\r\n")
print(lines[0])  # 상태 줄 — HTTP 판이 여기 있다
for h in lines[1:]:
    if not h.startswith("Date:"):  # 날짜는 실행마다 다르다
        print(" ", h)
if "Transfer-Encoding: chunked" in lines:
    while True:  # 청크 = 16진 길이 줄 + 그만큼의 바이트 + CRLF
        size, _, body = body.partition(b"\r\n")
        n = int(size, 16)
        if n == 0:  # 길이 0 인 청크가 본문의 끝
            print(
                f"  청크 {size.decode():>4} = {n:>3}바이트  (본문 끝)"
            )
            break
        what = kind(body[:n])
        print(f"  청크 {size.decode():>4} = {n:>3}바이트  {what}")
        body = body[n + 2 :]
else:  # 길이도 청크도 없다 — 연결이 닫히는 곳이 본문의 끝
    for ev in body.split(b"\n\n")[:-1]:
        print(f"  {len(ev) + 2:>4}바이트  {kind(ev)}")
    print("  (연결이 닫힘)")
# endregion
# @ norun
