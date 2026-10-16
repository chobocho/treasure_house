# -*- coding: utf-8 -*-
"""wiretap.py 시험 — 기록 형식(헤더 허용 목록·JSON 보기·SSE 사건)과, 진짜 소켓으로 중계해 보기.

   중계 시험은 이 프로세스 안에 위쪽 서버(가짜 에이전트)와 탭을 스레드로 띄운다.
   SSE 는 '흘려 보내는가' 가 핵심이라, 위쪽이 둘째 사건을 내기 전에 클라이언트가
   첫 사건을 이미 받았는지 — 그리고 기록에도 이미 적혔는지 — 를 본다.
"""
import http.client
import http.server
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import wiretap  # noqa: E402


class Format(unittest.TestCase):
    def test_request_block_with_json_body(self):
        lines = wiretap.format_head('→ POST / HTTP/1.1',
                                    [('Content-Type', 'application/json'),
                                     ('A2A-Version', '1.0')])
        lines += wiretap.format_body(b'{"jsonrpc":"2.0","id":1,"method":"SendMessage"}',
                                     'application/json')
        self.assertEqual('\n'.join(lines),
                         '→ POST / HTTP/1.1\n'
                         '  Content-Type: application/json\n'
                         '  A2A-Version: 1.0\n'
                         '  {\n'
                         '    "jsonrpc": "2.0",\n'
                         '    "id": 1,\n'
                         '    "method": "SendMessage"\n'
                         '  }')

    def test_only_allowed_headers_in_fixed_order_with_canonical_names(self):
        got = wiretap.format_head('← 401 Unauthorized', [
            ('location', '/x'), ('User-Agent', 'curl/8'), ('Host', '127.0.0.1:1'),
            ('www-authenticate', 'Bearer'), ('x-a2a-notification-token', 't'),
            ('Accept', '*/*'), ('authorization', 'Bearer abc'),
            ('A2a-Extensions', 'https://e/x'), ('a2a-version', '1.0'),
            ('content-type', 'application/json'), ('Date', 'Thu')])
        self.assertEqual(got, [
            '← 401 Unauthorized',
            '  Content-Type: application/json',
            '  A2A-Version: 1.0',
            '  A2A-Extensions: https://e/x',
            '  Authorization: Bearer abc',
            '  Accept: */*',
            '  X-A2A-Notification-Token: t',
            '  WWW-Authenticate: Bearer',
            '  Location: /x'])

    def test_json_keys_keep_their_order_and_korean_is_not_escaped(self):
        got = wiretap.format_body('{"b":1,"a":"숙소"}'.encode('utf-8'), 'application/json')
        self.assertEqual(got, ['  {', '    "b": 1,', '    "a": "숙소"', '  }'])

    def test_non_json_text_is_verbatim(self):
        got = wiretap.format_body(b'hello\nworld\n', 'text/plain')
        self.assertEqual(got, ['  hello', '  world'])

    def test_json_looking_text_that_does_not_parse_is_verbatim(self):
        got = wiretap.format_body(b'{not json', 'application/json')
        self.assertEqual(got, ['  {not json'])

    def test_binary_body_is_a_byte_count(self):
        self.assertEqual(wiretap.format_body(b'\xff\xfe\x00\x01', 'application/octet-stream'),
                         ['  <4 bytes>'])

    def test_empty_body_adds_nothing(self):
        self.assertEqual(wiretap.format_body(b'', 'application/json'), [])

    def test_sse_event_with_json_data(self):
        got = wiretap.format_event(['event: message', 'data: {"id":1,"result":{}}'])
        self.assertEqual(got, ['  event: message', '  data: {',
                               '    "id": 1,', '    "result": {}', '  }'])

    def test_sse_event_with_text_data_and_id(self):
        got = wiretap.format_event(['id: 7', 'data: plain words'])
        self.assertEqual(got, ['  id: 7', '  data: plain words'])

    def test_sse_multiline_data_is_joined_before_parsing(self):
        got = wiretap.format_event(['data: {"a":', 'data: 1}'])
        self.assertEqual(got, ['  data: {', '    "a": 1', '  }'])

    def test_sse_comment_is_kept(self):
        self.assertEqual(wiretap.format_event([': keepalive']), ['  : keepalive'])


# ── 진짜 소켓 ─────────────────────────────────────────────────────
class Upstream(http.server.BaseHTTPRequestHandler):
    """가짜 에이전트. /sse 는 사건 하나를 내고, 시험이 신호를 줄 때까지 기다렸다가 둘째를 낸다."""
    protocol_version = 'HTTP/1.1'
    gate = None
    seen = []

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == '/sse':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Transfer-Encoding', 'chunked')
            self.end_headers()

            def chunk(b):
                self.wfile.write(b'%x\r\n%s\r\n' % (len(b), b))
                self.wfile.flush()
            chunk(b'data: {"n":1}\n\n')
            Upstream.gate.wait(10)
            chunk(b'event: last\ndata: {"n":2}\n\n')
            chunk(b'')
            return
        body = b'{"name":"x"}'
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get('Content-Length', '0'))
        req = self.rfile.read(n)
        Upstream.seen.append((self.headers.get('A2A-Version'), req))
        body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'result': {'ok': True}}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(srv):
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return t


class Live(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='wiretap-test-')
        self.addCleanup(shutil.rmtree, self.tmp, True)
        Upstream.gate = threading.Event()
        Upstream.seen = []
        self.up = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
        self.addCleanup(self.up.server_close)
        self.addCleanup(self.up.shutdown)
        serve(self.up)
        self.log = os.path.join(self.tmp, 'wire.log')

    def tap(self, target=None, whole=False):
        target = target or self.up.server_address[1]
        srv = wiretap.make_server(0, target, self.log, whole=whole)
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        serve(srv)
        return srv.server_address[1]

    def logtext(self):
        with open(self.log, encoding='utf-8') as f:
            return f.read()

    def test_json_exchange_is_forwarded_unchanged_and_logged(self):
        port = self.tap()
        c = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
        c.request('POST', '/', body=b'{"jsonrpc":"2.0","id":1,"method":"SendMessage"}',
                  headers={'Content-Type': 'application/json', 'A2A-Version': '1.0',
                           'User-Agent': 'test'})
        r = c.getresponse()
        self.assertEqual(r.status, 200)
        self.assertEqual(json.loads(r.read()), {'jsonrpc': '2.0', 'id': 1, 'result': {'ok': True}})
        c.close()
        self.assertEqual(Upstream.seen, [('1.0', b'{"jsonrpc":"2.0","id":1,"method":"SendMessage"}')])
        self.assertEqual(self.logtext(),
                         '→ POST / HTTP/1.1\n'
                         '  Content-Type: application/json\n'
                         '  A2A-Version: 1.0\n'
                         '  {\n    "jsonrpc": "2.0",\n    "id": 1,\n    "method": "SendMessage"\n  }\n'
                         '← 200 OK\n'
                         '  Content-Type: application/json\n'
                         '  {\n    "jsonrpc": "2.0",\n    "id": 1,\n'
                         '    "result": {\n      "ok": true\n    }\n  }\n')

    def test_sse_is_streamed_and_logged_event_by_event(self):
        port = self.tap()
        c = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
        c.request('GET', '/sse', headers={'Accept': 'text/event-stream'})
        r = c.getresponse()
        self.assertEqual(r.getheader('Content-Type'), 'text/event-stream')
        # 위쪽은 아직 둘째 사건을 내지 않았다 — 첫 사건이 벌써 와 있어야 흘려 보낸 것이다.
        self.assertEqual(r.readline(), b'data: {"n":1}\n')
        self.assertEqual(r.readline(), b'\n')
        self.assertIn('  data: {\n    "n": 1\n  }\n', self.logtext())
        self.assertNotIn('"n": 2', self.logtext())
        Upstream.gate.set()
        rest = r.read()
        self.assertEqual(rest, b'event: last\ndata: {"n":2}\n\n')
        c.close()
        self.assertEqual(self.logtext(),
                         '→ GET /sse HTTP/1.1\n'
                         '  Accept: text/event-stream\n'
                         '← 200 OK\n'
                         '  Content-Type: text/event-stream\n'
                         '  data: {\n    "n": 1\n  }\n'
                         '  event: last\n'
                         '  data: {\n    "n": 2\n  }\n')

    def test_whole_mode_writes_each_exchange_at_once(self):
        port = self.tap(whole=True)
        c = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
        c.request('GET', '/sse')
        r = c.getresponse()
        r.readline()
        r.readline()
        self.assertEqual(self.logtext() if os.path.exists(self.log) else '', '')
        Upstream.gate.set()
        r.read()
        c.close()
        self.assertTrue(self.logtext().startswith('→ GET /sse HTTP/1.1\n'))
        self.assertIn('"n": 2', self.logtext())

    def test_upstream_down_gives_502(self):
        dead = http.server.HTTPServer(('127.0.0.1', 0), Upstream)
        free = dead.server_address[1]
        dead.server_close()
        port = self.tap(target=free)
        c = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
        c.request('GET', '/.well-known/agent-card.json')
        r = c.getresponse()
        self.assertEqual(r.status, 502)
        r.read()
        c.close()
        self.assertIn('← 502 Bad Gateway\n', self.logtext())


if __name__ == '__main__':
    unittest.main()
