# HTTP 를 소켓으로 직접 — 요청도 응답도 글자 몇 줄이라는 것을 본다.
# 줄 끝의 CR LF 를 눈에 보이게 \r\n 으로 찍는다.
import argparse
import json
import socket

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, required=True)
args = ap.parse_args()

# region: request
body = json.dumps({"date": "2026-10-30", "nights": 1, "headcount": 30})
head = (
    "POST /quote HTTP/1.1\r\n"  # 요청 줄: 메서드 경로 판
    f"Host: 127.0.0.1:{args.port}\r\n"
    "Content-Type: application/json\r\n"
    f"Content-Length: {len(body.encode())}\r\n"
    "Connection: close\r\n"  # 다 보내면 서버가 끊게 한다
    "\r\n"  # 빈 줄 — 머리글 끝, 여기부터 본문
)
request = (head + body).encode("utf-8")
# endregion


def show(raw):
    text = raw.decode("utf-8").replace("\r\n", "\\r\\n\n")
    print(text if text.endswith("\n") else text + "\n", end="")


with socket.create_connection(("127.0.0.1", args.port)) as s:
    s.sendall(request)
    chunks = []
    while chunk := s.recv(4096):  # 서버가 닫을 때까지 읽는다
        chunks.append(chunk)

print("[보낸 것]")
show(request)
print("[받은 것]")
show(b"".join(chunks))
# @ norun
