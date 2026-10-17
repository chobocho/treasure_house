# 스트림의 끝을 HTTP 에서 본다 — 소켓으로 SendStreamingMessage 를
# 쓰고 청크를 손으로 푼 뒤, 본문이 끝나고 연결이 어떻게 되는지 본다.
# Connection: close 를 보내지 않는다(SDK 클라이언트처럼 다시 쓰려고).
#   python 10/frames.py 포트
import json
import socket
import sys

PORT = int(sys.argv[1])
SHOW = ("content-type", "transfer-encoding", "content-length")
SHOW += ("connection",)

msg = {"messageId": "m-1", "role": "ROLE_USER"}
msg["parts"] = [{"text": "COMPLETED"}]
rpc = {"jsonrpc": "2.0", "id": 1, "method": "SendStreamingMessage"}
rpc["params"] = {"message": msg}
body = json.dumps(rpc).encode()
head = f"POST / HTTP/1.1\r\nHost: 127.0.0.1:{PORT}\r\n"
head += "Content-Type: application/json\r\nA2A-Version: 1.0\r\n"
head += f"Content-Length: {len(body)}\r\n\r\n"


def inside(chunk):
    """청크 하나에 든 줄들 — data 는 result 의 첫 키, 그 밖은 필드 이름.

    끝에 줄 끝 꼴(LF 또는 CRLF)을 붙인다. SSE 는 둘 다 허락한다.
    """
    got = []
    for line in chunk.decode().splitlines():
        if line.startswith("data:"):
            got.append(next(iter(json.loads(line[5:])["result"])))
        elif line:
            got.append(line.partition(":")[0] + ":")
    ends = "CRLF" if b"\r\n" in chunk else "LF"
    return ", ".join(got) + f" ({ends})"


# region: frames
sock = socket.create_connection(("127.0.0.1", PORT), timeout=2)
sock.sendall(head.encode() + body)
f = sock.makefile("rb")
print(f.readline().decode().strip())  # 상태 줄
for line in iter(f.readline, b"\r\n"):
    name, _, value = line.decode().partition(":")
    if name.lower() in SHOW:
        print(f"  {name.lower()}: {value.strip()}")
while True:  # 청크: 16진수 길이 줄, 그만큼의 바이트, CRLF
    size = int(f.readline(), 16)
    if size == 0:
        f.readline()  # 길이 0 청크 뒤의 빈 줄
        print("  길이 0 청크 — 응답 본문이 끝났다")
        break
    chunk = f.read(size)
    f.readline()
    # 길이는 찍지 않는다 — 시각의 자릿수 따라 바이트 수가 흔들린다
    print(f"  청크: {inside(chunk)}")
try:
    more = f.read(1)
    print("연결: 서버가 닫았다" if not more else "연결: 무언가 더 왔다")
except TimeoutError:
    print("연결: 2초 동안 열린 채 — 같은 연결로 다음 요청을 쓸 수 있다")
# endregion
# @ norun
