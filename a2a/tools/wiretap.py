#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wiretap — 요청을 그대로 넘겨 주며 오간 것을 적는 작은 역방향 프록시(표준 라이브러리만).

     python tools/wiretap.py 11101 11151 [--log FILE] [--whole]

   127.0.0.1:LISTEN 으로 들어온 요청을 127.0.0.1:TARGET 으로 바꾸지 않고 넘기고,
   응답을 그대로 돌려준다. 그 사이에 한 번의 주고받음(exchange)을 이렇게 적는다:

     → POST / HTTP/1.1
       Content-Type: application/json
       A2A-Version: 1.0
       {보기 좋게 편 JSON — 2칸 들여쓰기, 키 순서는 원래대로}
     ← 200 OK
       Content-Type: application/json
       {…}

   text/event-stream 응답은 모았다가 넘기지 않는다 — 사건(event) 하나가 끝날 때마다
   곧바로 클라이언트에 흘려 보내고(flush), 기록에도 그 사건을 바로 적는다. 스트리밍을
   가르치는 덱에서 탭이 스트림을 뭉쳐 버리면 보여 주려던 것이 사라진다.

   헤더는 HEADERS 의 허용 목록만, 그 순서로, 그 이름 꼴로 적는다. 같은 헤더라도 언어마다
   대소문자가 달라(Go 는 A2a-Version 으로 고친다) 캡처가 언어 따라 흔들리지 않게 하려는
   것이다. Authorization 값도 그대로 적는다 — 이 덱의 토큰은 전부 이 기계 안의 가짜다.

   --whole 이면 주고받음 하나를 다 모은 뒤 한 번에 적는다(동시에 오가는 요청을 a2arun 이
   통째로 정렬할 수 있게 — order=sorted). 기본은 SSE 사건이 지나가는 대로 적는다.
"""
import argparse
import http.client
import http.server
import io
import json
import sys
import threading

# 적는 헤더 — 이 순서, 이 이름 꼴로. 나머지(Host·User-Agent·Date …)는 적지 않는다.
HEADERS = ('Content-Type', 'A2A-Version', 'A2A-Extensions', 'Authorization', 'Accept',
           'X-A2A-Notification-Token', 'WWW-Authenticate', 'Location')
_CANON = {h.lower(): h for h in HEADERS}
# 다음 홉에 넘기지 않는 헤더(RFC 9110 §7.6.1). 본문 길이는 탭이 다시 단다.
HOP = {'connection', 'keep-alive', 'proxy-connection', 'te', 'trailer',
       'transfer-encoding', 'upgrade', 'content-length'}
SSE_FIELDS = ('event', 'id', 'retry', 'data')


# ── 기록 형식 ─────────────────────────────────────────────────────
def format_head(line, headers):
    """'→ POST / HTTP/1.1' 같은 첫 줄 + 허용된 헤더만 정해진 순서로."""
    got = {}
    for k, v in headers:
        c = _CANON.get(k.lower())
        if c and c not in got:
            got[c] = v
    return [line] + ['  %s: %s' % (h, got[h]) for h in HEADERS if h in got]


def _pretty(text):
    """JSON 이면 2칸 들여 편 줄들, 아니면 None. 키 순서는 dict 가 지킨다."""
    s = text.strip()
    if not s or s[0] not in '{[':
        return None
    try:
        obj = json.loads(s)
    except ValueError:
        return None
    return json.dumps(obj, indent=2, ensure_ascii=False).split('\n')


def format_body(body, ctype):
    """본문 → 2칸 들여 쓴 줄들. JSON 은 펴고, 글은 그대로, 이진은 바이트 수만."""
    if not body:
        return []
    try:
        text = body.decode('utf-8')
    except UnicodeDecodeError:
        return ['  <%d bytes>' % len(body)]
    if '\x00' in text:
        return ['  <%d bytes>' % len(body)]
    lines = _pretty(text)
    if lines is None:
        lines = text.rstrip('\n').split('\n')
    return ['  ' + ln for ln in lines]


def format_event(lines):
    """SSE 사건 하나(빈 줄 앞까지의 줄들) → 기록 줄들. data 가 JSON 이면 편다."""
    out, data = [], []
    for ln in lines:
        if ln.startswith(':'):
            out.append('  ' + ln)
            continue
        name, _, value = ln.partition(':')
        value = value[1:] if value.startswith(' ') else value
        if name == 'data':
            data.append(value)
        else:
            out.append('  %s: %s' % (name, value))
    if data:
        joined = '\n'.join(data)
        pretty = _pretty(joined)
        if pretty is None:
            out += ['  data: ' + d for d in data]
        else:
            out.append('  data: ' + pretty[0])
            out += ['  ' + p for p in pretty[1:]]
    return out


# ── 중계 ──────────────────────────────────────────────────────────
class Log(object):
    """기록 파일. 여러 스레드가 함께 쓰므로 한 덩어리씩 잠그고 쓴다."""

    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()

    def write(self, lines):
        if not lines:
            return
        with self.lock:
            if self.path:
                with io.open(self.path, 'a', encoding='utf-8', newline='') as f:
                    f.write('\n'.join(lines) + '\n')
            else:
                sys.stdout.write('\n'.join(lines) + '\n')
                sys.stdout.flush()


class Tap(http.server.BaseHTTPRequestHandler):
    # 응답마다 연결을 닫는다 — SSE 는 길이 없이 닫힘으로 끝을 알린다(HTTP/1.1 에서 허용).
    protocol_version = 'HTTP/1.1'
    target = 0
    log = None
    whole = False

    def log_message(self, *a):       # 접속 기록은 와이어 기록과 섞지 않는다
        pass

    def _body(self):
        if self.headers.get('Transfer-Encoding', '').lower() == 'chunked':
            parts = []
            while True:
                size = int(self.rfile.readline().split(b';')[0].strip() or b'0', 16)
                if size == 0:
                    while self.rfile.readline() not in (b'\r\n', b'\n', b''):
                        pass
                    return b''.join(parts)
                parts.append(self.rfile.read(size))
                self.rfile.readline()
        n = int(self.headers.get('Content-Length') or 0)
        return self.rfile.read(n) if n else b''

    def _relay(self):
        self.close_connection = True
        body = self._body()
        req = format_head('→ ' + self.requestline, self.headers.items())
        req += format_body(body, self.headers.get('Content-Type', ''))
        up = http.client.HTTPConnection('127.0.0.1', self.target, timeout=120)
        try:
            up.putrequest(self.command, self.path, skip_host=True, skip_accept_encoding=True)
            for k, v in self.headers.items():
                if k.lower() not in HOP:
                    up.putheader(k, v)
            if body or self.command in ('POST', 'PUT', 'PATCH'):
                up.putheader('Content-Length', str(len(body)))
            up.endheaders(body)
            resp = up.getresponse()
        except OSError as e:
            msg = b'wiretap: upstream unreachable\n'
            self.send_response_only(502, 'Bad Gateway')
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(msg)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(msg)
            self.log.write(req + ['← 502 Bad Gateway',
                                  '  (탭: 127.0.0.1:%d 에 닿지 못했다 — %s)'
                                  % (self.target, e.__class__.__name__)])
            up.close()
            return
        try:
            head = format_head('← %d %s' % (resp.status, resp.reason), resp.getheaders())
            ctype = resp.getheader('Content-Type', '') or ''
            self.send_response_only(resp.status, resp.reason)
            for k, v in resp.getheaders():
                if k.lower() not in HOP:
                    self.send_header(k, v)
            if ctype.lower().startswith('text/event-stream'):
                self.send_header('Connection', 'close')
                self.end_headers()
                self._stream(resp, req + head)
            else:
                data = resp.read()
                # 기록을 먼저 — 클라이언트가 응답을 받았을 때는 기록도 이미 끝나 있어야
                # a2arun 이 클라이언트가 끝나자마자 탭을 내려도 빠진 줄이 없다.
                self.log.write(req + head + format_body(data, ctype))
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Connection', 'close')
                self.end_headers()
                if self.command != 'HEAD':
                    self.wfile.write(data)
        finally:
            up.close()

    def _stream(self, resp, first):
        """SSE — 사건 하나(빈 줄까지)를 모아, 적고 나서 곧바로 넘기고 flush 한다.

           적는 것이 먼저인 까닭은 _relay 의 JSON 쪽과 같다. 사건 사이에서는 아무것도
           붙들지 않으므로 클라이언트는 위쪽이 낸 사건을 그때그때 받는다.
        """
        pending = list(first)
        if not self.whole:
            self.log.write(pending)
            pending = []
        event, raw_event = [], []
        try:
            while True:
                raw = resp.readline()
                if not raw:
                    break
                raw_event.append(raw)
                line = raw.decode('utf-8', 'replace').rstrip('\r\n')
                if line:
                    event.append(line)
                    continue
                lines = format_event(event)
                if self.whole:
                    pending += lines
                else:
                    self.log.write(lines)
                self.wfile.write(b''.join(raw_event))
                self.wfile.flush()
                event, raw_event = [], []
            if event:
                pending += format_event(event)
            if raw_event:
                self.wfile.write(b''.join(raw_event))
        except (BrokenPipeError, ConnectionResetError):
            pending.append('  (클라이언트가 연결을 끊었다)')
        self.log.write(pending)


for _m in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'):
    setattr(Tap, 'do_' + _m, Tap._relay)


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_server(listen, target, log_path, whole=False):
    """127.0.0.1:listen 에 묶인 탭 서버(아직 돌지 않는다). listen=0 이면 빈 포트."""
    handler = type('BoundTap', (Tap,), {'target': target, 'log': Log(log_path),
                                        'whole': whole})
    return Server(('127.0.0.1', listen), handler)


def main(argv=None):
    ap = argparse.ArgumentParser(description='A2A 와이어 탭 — 기록하는 역방향 프록시')
    ap.add_argument('listen', type=int)
    ap.add_argument('target', type=int)
    ap.add_argument('--log', help='기록 파일 (없으면 표준 출력)')
    ap.add_argument('--whole', action='store_true', help='주고받음을 다 모아 한 번에 적는다')
    a = ap.parse_args(argv)
    srv = make_server(a.listen, a.target, a.log, a.whole)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
