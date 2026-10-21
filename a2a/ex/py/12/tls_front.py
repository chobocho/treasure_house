"""TLS 앞단 — HTTPS 를 받아 풀고, 뒤의 http 에이전트에 그대로 넘긴다.

    python 12/tls_front.py --port P --to http://127.0.0.1:Q/ \
        --cert 인증서 --key 개인키

운영에서는 보통 리버스 프록시(nginx 따위)가 맡는 자리다. 표준
라이브러리만 쓴다. 스트림(SSE)은 넘기지 않는다 — 몸통을 다 읽는다.
"""

import argparse
import http.client
import ssl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

# 홉마다 다시 정하는 머리글(RFC 9110 7.6.1)은 넘기지 않는다
HOP = {
    "connection",
    "keep-alive",
    "transfer-encoding",
    "content-length",
}


# region: relay
class Front(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    target = urlsplit("http://127.0.0.1/")

    def relay(self):
        size = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(size)
        up = http.client.HTTPConnection(self.target.netloc, timeout=30)
        heads = {k: v for k, v in self.headers.items()}
        up.request(self.command, self.path, body, heads)
        resp = up.getresponse()
        data = resp.read()
        self.send_response(resp.status)
        for k, v in resp.getheaders():
            if k.lower() not in HOP:
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        up.close()

    do_GET = do_POST = relay

    def log_message(self, fmt, *args):
        print(f"[앞단] {self.command} {self.path}", flush=True)


# endregion


# region: tls
def main():
    p = argparse.ArgumentParser()
    for name in ("--port", "--to", "--cert", "--key"):
        p.add_argument(name, required=True)
    a = p.parse_args()
    Front.target = urlsplit(a.to)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.minimum_version = ssl.TLSVersion.TLSv1_3  # §7.1 권고
    tls.load_cert_chain(a.cert, a.key)
    srv = ThreadingHTTPServer(("127.0.0.1", int(a.port)), Front)
    srv.socket = tls.wrap_socket(srv.socket, server_side=True)
    print(f"[앞단] https://127.0.0.1:{a.port}/ → {a.to}", flush=True)
    srv.serve_forever()


# endregion

if __name__ == "__main__":
    main()
# @ norun
