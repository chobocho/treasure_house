#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""a2arun — 예제를 진짜로 돌려 그 화면(캡처)을 out/ 에 남긴다. 이 덱에서 코드를 돌리는 것은 이것 하나뿐이다.

     python3 tools/a2arun.py ex/py/02/hello_json.py     파일 하나 — out/02/hello_json.py.txt
     python3 tools/a2arun.py ex/go/02/hello_json        Go 패키지 디렉터리 하나
     python3 tools/a2arun.py ex/run/02/curl_card.run    여러 프로세스(서버·탭·클라이언트) 명세
     python3 tools/a2arun.py --all [--only ex/py/02]    전부(norun 빼고) / 그 아래만
     python3 tools/a2arun.py --check --all              다시 돌려 이미 있는 캡처와 글자까지 같은지
     python3 tools/a2arun.py --manifest-check           돌리지 않고 입력·캡처 해시만 장부와 대조
     python3 tools/a2arun.py --prune                    예제가 사라진 캡처·장부 줄을 지운다

   언어마다 뿌리가 있고, 프로세스는 그 뿌리에서 돈다(화면의 명령이 짧아지게):

     .py  ex/py   <a2a>/.venv/bin/python NN/x.py  (PYTHONPATH=ex/py)    $ python NN/x.py
     .ts  ex/ts   node NN/x.ts (Node 24 가 타입을 지운다)               $ node NN/x.ts
     Go   ex/go   go build -p 1 → scratch/bin/NN_name, 그 바이너리       $ go run ./NN/name
     sh:  ex      /bin/sh -c (curl 따위)                                $ <그 줄>

   파일 예제의 설정은 파일 **끝**의 지시자 줄 — `# @ key: value`(py; ruff format 이 '#@' 를
   이렇게 고친다, '#@' 도 받는다), `//@ key: value`(ts·go).
   끝에 두는 까닭: 오류 메시지의 줄 번호가 슬라이드의 줄 번호와 같아야 해서다.
   args · stdin(\\n 이스케이프) · exit · timeout(기본 20초) · norun(컴파일만) · env: K=V

   명세(.run)는 줄마다 동사 하나 — serve · tap · run · wait (parse_spec 참고).
   서버는 차례로 띄워 ready 를 기다리고, run 을 차례로 돌리고, 끝나면 성공이든 실패든
   모든 서버의 프로세스 그룹에 SIGTERM(3초 뒤 SIGKILL)을 보낸다. 고아는 남기지 않는다.

   캡처에 손대는 곳은 RULES 표의 다섯 가지뿐이다. 그 밖의 글자는 그대로 둔다.
   포트: NN부는 10000 + NN*100 + k (k = 0..99). 범위를 벗어난 포트는 거부한다.
"""
import argparse
import fcntl
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # a2a/
REPO = os.path.dirname(ROOT)                                           # treasure_house/
PYTHON = os.environ.get('A2ARUN_PYTHON', os.path.join(ROOT, '.venv', 'bin', 'python'))
WIRETAP = os.path.join(ROOT, 'tools', 'wiretap.py')

# 언어 → (뿌리, 확장자, 지시자 줄의 머리). 파이썬은 '#@' 와 '# @' 둘 다 받는다 —
# ruff format 이 '#@' 를 '# @' 로 고치기 때문이다(그래서 정식 꼴은 '# @ key: value').
LANGS = {'py': ('ex/py', '.py', r'#\s?@'), 'ts': ('ex/ts', '.ts', '//@'), 'go': ('ex/go', '', '//@')}
# 언어 뿌리 안에서 예제도 공유 소스도 아닌 것 — 입력 해시에서 뺀다.
NOT_SHARED = ('gate', 'node_modules', '__pycache__', '.ruff_cache')
KEYS = ('args', 'stdin', 'exit', 'timeout', 'norun', 'env')
DEFAULT_TIMEOUT = 20
READY_TIMEOUT = 15
BUILD_TIMEOUT = 600          # 이 기계에서 첫 go build 는 몇 분 걸리기도 한다
TERM_GRACE = 3
PART = re.compile(r'^\d\d$')


class RunError(Exception):
    pass


def _read(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()


def _write(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


# ── 지시자 ─────────────────────────────────────────────────────────
def parse_directives(text, lang):
    """(본문 줄 수, 설정). 지시자는 파일 끝에만 — 그 앞의 빈 줄도 본문이 아니다."""
    mark = re.compile('^' + LANGS[lang][2])
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    tail = []
    while lines and mark.match(lines[-1]):
        tail.append(lines.pop())
    while tail and lines and lines[-1].strip() == '':
        lines.pop()
    if not lines:
        raise RunError('소스가 비었다')
    for i, ln in enumerate(lines, 1):
        if mark.match(ln):
            raise RunError('%d번 줄: 지시자는 파일 끝에만 둔다' % i)
    d = {'args': '', 'stdin': None, 'exit': 0, 'timeout': DEFAULT_TIMEOUT,
         'norun': False, 'env': []}
    pat = re.compile(r'^%s\s*([a-z]+)\s*(?::\s*(.*?))?\s*$' % LANGS[lang][2])
    for ln in reversed(tail):
        m = pat.match(ln)
        if not m or m.group(1) not in KEYS:
            raise RunError('모르는 지시자: %s' % ln)
        key, val = m.group(1), m.group(2) or ''
        if key in ('exit', 'timeout'):
            if not val.isdigit():
                raise RunError('%s 에는 숫자를 적는다: %s' % (key, ln))
            d[key] = int(val)
        elif key == 'norun':
            d[key] = True
        elif key == 'env':
            k, eq, v = val.partition('=')
            if not eq or not re.match(r'^[A-Z_][A-Z0-9_]*$', k):
                raise RunError('env 는 K=V 꼴이다: %s' % ln)
            d['env'].append((k, v))
        elif key == 'stdin':
            if "'" in val or '%' in val:
                raise RunError("stdin 에 ' 와 %% 는 못 쓴다 (printf 로 보이기 때문)")
            d[key] = val.replace('\\n', '\n')
        else:
            d[key] = val
    return len(lines), d


def shown_command(kind, rel, d):
    """화면에 보일 명령. rel 은 언어 뿌리 기준(02/x.py, 02/hello)."""
    prog = {'py': 'python ' + rel, 'ts': 'node ' + rel, 'go': 'go run ./' + rel}[kind]
    cmd = ' '.join(['%s=%s' % kv for kv in d['env']] + [prog] + ([d['args']] if d['args'] else []))
    if d['stdin'] is not None:
        cmd = "printf '%s' | %s" % (d['stdin'].replace('\n', '\\n'), cmd)
    return cmd


# ── 정규화 — 선언한 다섯 가지뿐 ───────────────────────────────────
_UUID = re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b')
# 우리 포트는 10000–11899. 루프백 위의 그 밖의 포트는 운영체제가 고른 임시 포트다.
_EPHEMERAL_FROM = 12000


def _port(m):
    return m.group(1) + ('<port>' if int(m.group(2)) >= _EPHEMERAL_FROM else m.group(2))


RULES = [
    # (이름, 무엇을, 왜)
    ('path', '저장소의 절대 경로 → 상대 경로', '기계마다 다르다'),
    ('timestamp', 'RFC 3339 / ISO 8601 시각 → <시각>', '실행마다 다르다'),
    ('duration', '우리 코드가 찍는 12.3ms 꼴 걸린 시간 → <ms>', '실행마다 다르다'),
    ('port', '루프백의 임시 포트(12000 이상) → <port>', '운영체제가 고른다'),
    ('uuid', 'UUID → <id1>, <id2>… (파일 안에서 처음 나온 차례)', '실행마다 새로 만든다'),
]
_SUBS = {
    'timestamp': (re.compile(r'\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?'),
                  '<시각>'),
    'duration': (re.compile(r'\b\d+\.\d+ms\b'), '<ms>'),
    'port': (re.compile(r'((?:127\.0\.0\.1|localhost|\[::1\]):)(\d+)'), _port),
}


def normalize(text, root):
    """RULES 의 차례대로. 캡처 파일 하나를 통째로 넣어야 <idN> 번호가 파일 안에서 일관된다."""
    text = text.replace(root + '/', '').replace(root, '.')
    for name in ('timestamp', 'duration', 'port'):
        rx, rep = _SUBS[name]
        text = rx.sub(rep, text)
    seen = {}

    def label(m):
        k = m.group(0).lower()
        if k not in seen:
            seen[k] = '<id%d>' % (len(seen) + 1)
        return seen[k]
    return _UUID.sub(label, text)


# ── 경로 ───────────────────────────────────────────────────────────
def example_of(rel):
    """파일·디렉터리 경로 → 그 예제의 뿌리. 예제가 아니면(workshop·fixtures) None."""
    parts = rel.strip('/').split('/')
    if len(parts) < 4 or parts[0] != 'ex' or not PART.match(parts[2]):
        return None
    if parts[1] == 'go':
        return '/'.join(parts[:4])
    if parts[1] in ('py', 'ts', 'run') and len(parts) == 4:
        return '/'.join(parts)
    return None


def kind_of(rel):
    return {'py': 'py', 'ts': 'ts', 'go': 'go', 'run': 'run'}[rel.split('/')[1]]


def part_of(rel):
    return int(rel.split('/')[2])


def port_range(part):
    lo = 10000 + part * 100
    return lo, lo + 99


def capture_path(rel):
    """ex/py/02/x.py → out/02/x.py.txt · ex/go/02/h → out/02/h.go.txt · ex/run/11/p.run → out/11/p.txt

       세 언어가 한 부 안에서 같은 이름을 쓰므로(hello_json.py/.ts/Go) 파일 예제는 언어를 이름에 남긴다.
    """
    rel = rel.rstrip('/')
    _, lang, nn, name = rel.split('/')[:4]
    if lang == 'run':
        return 'out/%s/%s.txt' % (nn, name[:-4])
    if lang == 'go':
        return 'out/%s/%s.go.txt' % (nn, name)
    return 'out/%s/%s.txt' % (nn, name)


def source_of(cap):
    _, nn, name = cap.split('/')
    for suf, lang in (('.py.txt', 'py'), ('.ts.txt', 'ts')):
        if name.endswith(suf):
            return 'ex/%s/%s/%s' % (lang, nn, name[:-4])
    if name.endswith('.go.txt'):
        return 'ex/go/%s/%s' % (nn, name[:-7])
    return 'ex/run/%s/%s.run' % (nn, name[:-4])


def _main_file(root, rel):
    """예제의 지시자가 사는 파일 — Go 는 디렉터리 안의 main.go."""
    p = os.path.join(root, rel)
    return os.path.join(p, 'main.go') if kind_of(rel) == 'go' else p


def _norun(root, rel):
    if kind_of(rel) == 'run':
        return False
    p = _main_file(root, rel)
    try:
        return parse_directives(_read(p), kind_of(rel))[1]['norun']
    except (RunError, OSError):
        return False


def sources(root):
    """ex/ 아래의 예제 전부(norun 포함) — 조립기가 '어느 슬라이드도 싣지 않는 예제' 를 셀 때 쓴다."""
    found = []
    ex = os.path.join(root, 'ex')
    for lang, suffix in (('go', None), ('py', '.py'), ('run', '.run'), ('ts', '.ts')):
        base = os.path.join(ex, lang)
        if not os.path.isdir(base):
            continue
        for nn in sorted(os.listdir(base)):          # gate·workshop·node_modules 는 NN 이 아니다
            pdir = os.path.join(base, nn)
            if not PART.match(nn) or not os.path.isdir(pdir):
                continue
            for n in sorted(os.listdir(pdir)):
                p = os.path.join(pdir, n)
                if suffix is None:
                    if os.path.isfile(os.path.join(p, 'main.go')):
                        found.append('ex/go/%s/%s' % (nn, n))
                elif n.endswith(suffix) and os.path.isfile(p):
                    found.append('ex/%s/%s/%s' % (lang, nn, n))
    return found


def examples(root):
    """돌려서 캡처를 남기는 예제 — norun 은 뺀다."""
    return [rel for rel in sources(root) if not _norun(root, rel)]


# ── 명세 ───────────────────────────────────────────────────────────
VERBS = {'serve': (('name', 'cmd', 'ready'), ()),
         'tap': (('name', 'listen', 'target'), ('order',)),
         'run': (('cmd',), ('exit', 'timeout')),
         'wait': (('ms',), ())}
_INTS = ('listen', 'target', 'exit', 'timeout', 'ms')


def parse_spec(text):
    """명세 → 단계 dict 의 목록. 줄 끝의 # 은 주석(따옴표 안은 빼고).

       serve name=N cmd="LANG:..." ready=http://127.0.0.1:P/… | tcp:P
       tap   name=N listen=P target=P [order=sorted]
       run   cmd="LANG:..." [exit=N] [timeout=S]
       wait  ms=N
       LANG = py | ts | go | sh      — 긴 줄은 끝에 \\ 를 달아 다음 줄과 잇는다.
    """
    steps, names = [], set()
    logical, buf, first = [], '', 0
    for no, ln in enumerate(text.split('\n'), 1):
        # 줄 끝의 \ 는 다음 줄과 잇는다(슬라이드 72칸). 이은 자리는 빈칸 하나 —
        # 따옴표 안에서 이어도 화면의 명령에 들여쓰기가 끼지 않는다.
        if not buf:
            first = no
        else:
            ln = ln.lstrip()
        if ln.rstrip().endswith('\\') and not ln.lstrip().startswith('#'):
            buf += ln.rstrip()[:-1].rstrip() + ' '
            continue
        logical.append((first, buf + ln))
        buf = ''
    if buf:
        logical.append((first, buf))
    for no, ln in logical:
        lex = shlex.shlex(ln, posix=True)
        lex.whitespace_split, lex.commenters = True, '#'
        try:
            toks = list(lex)
        except ValueError as e:
            raise RunError('%d번 줄: %s' % (no, e))
        if not toks:
            continue
        verb = toks[0]
        if verb not in VERBS:
            raise RunError('%d번 줄: 모르는 동사 %s (serve·tap·run·wait)' % (no, verb))
        need, opt = VERBS[verb]
        s = {'verb': verb, 'line': no}
        for t in toks[1:]:
            k, eq, v = t.partition('=')
            if not eq or k not in need + opt:
                raise RunError('%d번 줄: %s 에 쓸 수 없는 것: %s' % (no, verb, t))
            if k in _INTS:
                if not v.isdigit():
                    raise RunError('%d번 줄: %s 는 숫자: %s' % (no, k, v))
                v = int(v)
            s[k] = v
        miss = [k for k in need if k not in s]
        if miss:
            raise RunError('%d번 줄: %s 에 %s 가 없다' % (no, verb, ', '.join(miss)))
        if 'cmd' in s and s['cmd'].split(':', 1)[0] not in ('py', 'ts', 'go', 'sh'):
            raise RunError('%d번 줄: cmd 는 py: ts: go: sh: 로 시작한다: %s' % (no, s['cmd']))
        if s.get('order', 'sorted') != 'sorted':
            raise RunError('%d번 줄: order 는 sorted 만 받는다' % no)
        if 'name' in s:
            if s['name'] in names:
                raise RunError('%d번 줄: 이름이 겹친다: %s' % (no, s['name']))
            names.add(s['name'])
        if verb == 'serve' and not re.match(r'^(?:tcp:\d+|http://127\.0\.0\.1:\d+/\S*)$', s['ready']):
            raise RunError('%d번 줄: ready 는 tcp:PORT 나 http://127.0.0.1:PORT/… 다' % no)
        steps.append(s)
    if not any(s['verb'] == 'run' for s in steps):
        raise RunError('run 이 하나도 없다')
    taps = {s['listen'] for s in steps if s['verb'] == 'tap'}
    for s in steps:
        if s['verb'] == 'serve' and _ready_port(s['ready']) in taps:
            # 준비 확인 요청이 와이어 기록에 섞인다 — 서버 자기 포트로 확인한다.
            raise RunError('%d번 줄: ready 가 탭(%d)을 거친다 — 서버 자기 포트로 확인한다'
                           % (s['line'], _ready_port(s['ready'])))
    return steps


def _ready_port(ready):
    return int(re.search(r'(?:tcp:|:)(\d+)', ready.replace('http://127.0.0.1', '')).group(1))


_PORTS = re.compile(r'(?:127\.0\.0\.1|localhost|\[::1\]):(\d+)|--port[= ](\d+)|tcp:(\d+)'
                    r'|listen=(\d+)|target=(\d+)')


def ports_in(text):
    return sorted({int(next(g for g in m.groups() if g)) for m in _PORTS.finditer(text)})


def check_ports(part, ports):
    lo, hi = port_range(part)
    bad = [p for p in ports if not lo <= p <= hi]
    if bad:
        raise RunError('%d부의 포트는 %d–%d 다 — 범위 밖: %s'
                       % (part, lo, hi, ', '.join(map(str, bad))))


def _busy(port):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(('127.0.0.1', port))
        return False
    except OSError:
        return True
    finally:
        s.close()


def sort_exchanges(log):
    """와이어 기록을 주고받음(→ 로 시작하는 덩어리) 단위로 정렬한다 — 동시에 오간 요청의 순서는
       실행마다 다르기 때문이다. 열쇠는 요청 줄+요청 본문, UUID 는 번호 없이 지운 꼴로 비교한다."""
    blocks, cur = [], None
    for ln in log.rstrip('\n').split('\n') if log else []:
        if ln.startswith('→ ') or cur is None:
            cur = []
            blocks.append(cur)
        cur.append(ln)

    def key(b):
        req = []
        for ln in b:
            if ln.startswith('← '):
                break
            req.append(ln)
        k = _UUID.sub('<id>', '\n'.join(req))
        k = _SUBS['timestamp'][0].sub('<시각>', k)
        return (k, _UUID.sub('<id>', '\n'.join(b)))
    return ''.join(ln + '\n' for b in sorted(blocks, key=key) for ln in b)


# ── 입력 · 해시 · 장부 ─────────────────────────────────────────────
def _sha_tree(p):
    if not os.path.exists(p):
        return '-'
    if os.path.isfile(p):
        with open(p, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    h = hashlib.sha256()
    for base, dirs, files in os.walk(p):
        dirs[:] = sorted(x for x in dirs if x not in ('__pycache__', 'node_modules'))
        for n in sorted(files):
            if n.endswith('.pyc'):
                continue
            fp = os.path.join(base, n)
            h.update(os.path.relpath(fp, p).encode('utf-8') + b'\0')
            with open(fp, 'rb') as f:
                h.update(f.read() + b'\0')
    return h.hexdigest()


def shared(root, lang):
    """언어 뿌리의 공유 소스 디렉터리들 — workshop 은 늘(없어도), 그 밖에 NN·gate·캐시가 아닌 것."""
    base = LANGS[lang][0]
    names = {'workshop'}
    d = os.path.join(root, base)
    if os.path.isdir(d):
        names.update(n for n in os.listdir(d) if os.path.isdir(os.path.join(d, n))
                     and not PART.match(n) and n not in NOT_SHARED)
    return ['%s/%s' % (base, n) for n in sorted(names)]


def _cmd_example(cmd):
    """명세의 cmd → 그것이 돌리는 예제(ex/…) 또는 None(sh:)."""
    lang, _, rest = cmd.partition(':')
    if lang == 'sh':
        return None
    first = shlex.split(rest)[0] if rest.strip() else ''
    return '%s/%s' % (LANGS[lang][0], first.rstrip('/'))


def inputs(root, rel):
    """캡처를 만든 입력의 목록 [(경로, sha256)] — 하나라도 바뀌면 캡처가 낡았다."""
    langs, items = [], [rel]
    if kind_of(rel) == 'run':
        steps = parse_spec(_read(os.path.join(root, rel)))
        for s in steps:
            ex = _cmd_example(s['cmd']) if 'cmd' in s else None
            if ex:
                if ex not in items:
                    items.append(ex)
                lang = s['cmd'].split(':', 1)[0]
                if lang not in langs:
                    langs.append(lang)
        tap = any(s['verb'] == 'tap' for s in steps)
    else:
        langs, tap = [kind_of(rel)], False
    for lang in ('py', 'ts', 'go'):
        if lang in langs:
            items += shared(root, lang)
    items.append('ex/fixtures')
    out = [(i, _sha_tree(os.path.join(root, i))) for i in items]
    if tap:
        out.append(('tools/wiretap.py', _sha_tree(WIRETAP)))
    return out


def _manifest_path(root):
    return os.path.join(root, 'out', 'MANIFEST.tsv')


MANIFEST_HEAD = 'capture\tsource\tinputs\tcapture_sha256\ttoolchain\n'


def manifest_load(root):
    """{캡처 경로: (예제, {입력: sha}, 캡처 sha, 도구 판)}"""
    rows = {}
    p = _manifest_path(root)
    if os.path.isfile(p):
        for ln in _read(p).split('\n'):
            f = ln.split('\t')
            if len(f) == 5 and f[0].startswith('out/'):
                ins = dict(x.split('=', 1) for x in f[2].split(' ') if '=' in x)
                rows[f[0]] = (f[1], ins, f[3], f[4])
    return rows


def _manifest_write(root, rows):
    p = _manifest_path(root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p + '.tmp', 'w', encoding='utf-8', newline='') as f:
        f.write(MANIFEST_HEAD)
        for cap in sorted(rows):
            src, ins, csha, tool = rows[cap]
            f.write('\t'.join((cap, src, ' '.join('%s=%s' % kv for kv in ins.items()),
                               csha, tool)) + '\n')
    os.replace(p + '.tmp', p)


def manifest_update(root, rel, toolchain):
    rows = manifest_load(root)
    cap = capture_path(rel)
    rows[cap] = (rel, dict(inputs(root, rel)), _sha_tree(os.path.join(root, cap)), toolchain)
    _manifest_write(root, rows)


def stale(root, rel, rows=None):
    """캡처가 없거나, 입력·캡처가 장부와 다르면 까닭. 멀쩡하면 ''."""
    rows = manifest_load(root) if rows is None else rows
    cap = capture_path(rel)
    if not os.path.isfile(os.path.join(root, cap)):
        return '캡처가 없다'
    if cap not in rows:
        return '장부에 없다'
    try:
        now = inputs(root, rel)
    except (RunError, OSError) as e:
        return '입력을 읽지 못했다: %s' % e
    old = rows[cap][1]
    changed = [p for p, sha in now if old.get(p) != sha]
    if changed or set(old) != set(p for p, _ in now):
        return '입력이 캡처 뒤에 바뀌었다: %s' % ', '.join(changed or sorted(set(old) ^ set(p for p, _ in now)))
    if rows[cap][2] != _sha_tree(os.path.join(root, cap)):
        return '캡처가 손으로 고쳐졌다'
    return ''


def orphans(root):
    have = set(capture_path(e) for e in examples(root))
    found = []
    out = os.path.join(root, 'out')
    for base, _, files in os.walk(out):
        for n in sorted(files):
            rel = os.path.relpath(os.path.join(base, n), root)
            if n.endswith('.txt') and rel not in have:
                found.append(rel)
    return sorted(found)


def prune(root):
    for rel in orphans(root):
        os.remove(os.path.join(root, rel))
    have = set(capture_path(e) for e in examples(root))
    rows = {k: v for k, v in manifest_load(root).items() if k in have}
    _manifest_write(root, rows)


_TOOLS = {}


def _tool_version(root, lang):
    """장부에 남길 도구 판. 한 번 물어 본 것은 기억한다."""
    key = (root, lang)
    if key in _TOOLS:
        return _TOOLS[key]

    def out(cmd):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return '?'
    if lang == 'py':
        v = out([PYTHON, '-c', 'import sys, importlib.metadata as m\ntry: s = m.version("a2a-sdk")\n'
                 'except Exception: s = "?"\nprint("python %s a2a-sdk %s" % (sys.version.split()[0], s))'])
    elif lang == 'ts':
        try:
            sdk = json.loads(_read(os.path.join(root, 'ex/ts/node_modules/@a2a-js/sdk/package.json')))['version']
        except (OSError, ValueError, KeyError):
            sdk = '?'
        v = 'node %s @a2a-js/sdk %s' % (out(['node', '-v']), sdk)
    elif lang == 'go':
        try:
            m = re.search(r'github\.com/a2aproject/a2a-go/v2 (\S+)', _read(os.path.join(root, 'ex/go/go.mod')))
            sdk = m.group(1) if m else '?'
        except OSError:
            sdk = '?'
        v = '%s a2a-go %s' % (out(['go', 'env', 'GOVERSION']), sdk)
    else:
        v = ' '.join(out(['curl', '--version']).split(' ')[:2])
    _TOOLS[key] = v
    return v


def toolchain(root, rel):
    if kind_of(rel) != 'run':
        langs = [kind_of(rel)]
    else:
        langs = []
        for s in parse_spec(_read(os.path.join(root, rel))):
            lang = s.get('cmd', '').split(':', 1)[0]
            if lang and lang not in langs:
                langs.append(lang)
        if any(s['verb'] == 'tap' for s in parse_spec(_read(os.path.join(root, rel)))) and 'py' not in langs:
            langs.append('py')
    return '; '.join(_tool_version(root, lang) for lang in sorted(langs))


# ── 실행 ───────────────────────────────────────────────────────────
def _shim(scratch):
    """PATH 맨 앞의 python — 화면의 'python' 이 곧 a2a/.venv 의 파이썬이다(sh: 줄에서도)."""
    d = os.path.join(scratch, 'shim')
    p = os.path.join(d, 'python')
    want = '#!/bin/sh\nexec %s "$@"\n' % PYTHON
    if not os.path.isfile(p) or _read(p) != want:
        _write(p, want)
        os.chmod(p, 0o755)
    return d


def _env(root, scratch, extra=()):
    # 바깥 설정이 예제의 동작을 바꾸지 않게 — 파이썬·node 설정과 GOFLAGS 는 떼어 낸다.
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('PYTHON', 'NODE_')) and k not in ('GOFLAGS', 'GOOS', 'GOARCH')}
    env.update({
        'PATH': _shim(scratch) + os.pathsep + env.get('PATH', '/usr/bin:/bin'),
        'PYTHONPATH': os.path.join(root, 'ex', 'py'),
        'PYTHONUNBUFFERED': '1', 'PYTHONDONTWRITEBYTECODE': '1',
        'LANG': 'C.UTF-8', 'TERM': 'dumb', 'NO_COLOR': '1',
        'GOTOOLCHAIN': 'local', 'GOWORK': 'off', 'CGO_ENABLED': '0',
        'TMPDIR': os.path.join(scratch, 'tmp'),
    })
    env.update(dict(extra))
    os.makedirs(env['TMPDIR'], exist_ok=True)
    return env


def _kill(p):
    """프로세스 그룹째 SIGTERM, TERM_GRACE 초 뒤에도 살아 있으면 SIGKILL."""
    try:
        os.killpg(p.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        p.wait(TERM_GRACE)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(p.pid, signal.SIGKILL)       # 그룹의 손자까지
    except ProcessLookupError:
        pass
    try:
        p.wait(TERM_GRACE)
    except subprocess.TimeoutExpired:
        pass


def _call(argv, cwd, env, timeout, stdin=None):
    """끝날 때까지 돌리고 (stdout+stderr, 종료 코드). 시간을 넘기면 그룹째 죽이고 RunError."""
    p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE if stdin is not None
                         else subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, start_new_session=True)
    try:
        raw, _ = p.communicate(stdin.encode('utf-8') if stdin is not None else None, timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill(p)
        p.communicate()
        raise RunError('%d초 안에 끝나지 않았다: %s' % (timeout, ' '.join(argv)))
    finally:
        if p.poll() is None:
            _kill(p)
    return raw.decode('utf-8', 'replace'), p.returncode


def _go_build(root, scratch, rel, env):
    """ex/go/NN/name → scratch/bin/NN_name. 입력 해시가 같으면 다시 짓지 않는다."""
    nn, name = rel.split('/')[2:4]
    out = os.path.join(scratch, 'bin', '%s_%s' % (nn, name))
    key = ' '.join('%s=%s' % kv for kv in
                   [(i, _sha_tree(os.path.join(root, i))) for i in
                    [rel] + shared(root, 'go') + ['ex/go/go.mod', 'ex/go/go.sum']])
    stamp = out + '.sha'
    if os.path.isfile(out) and os.path.isfile(stamp) and _read(stamp) == key:
        return out
    os.makedirs(os.path.dirname(out), exist_ok=True)
    text, rc = _call(['go', 'build', '-p', '1', '-o', out, './%s/%s' % (nn, name)],
                     os.path.join(root, 'ex', 'go'), env, BUILD_TIMEOUT)
    if rc != 0:
        raise RunError('go build 실패: %s\n%s' % (rel, normalize(text, root)))
    _write(stamp, key)
    return out


def _check_compiles(root, scratch, rel, env):
    """norun — 파이썬은 compile(), Go 는 build. TypeScript 는 make ts-check(tsc)가 본다."""
    kind = kind_of(rel)
    if kind == 'py':
        text, rc = _call([PYTHON, '-c', 'import sys; compile(open(sys.argv[1], encoding="utf-8").read(), '
                          'sys.argv[1], "exec")', rel.split('/', 2)[2]],
                         os.path.join(root, 'ex', 'py'), env, DEFAULT_TIMEOUT)
        if rc != 0:
            raise RunError('컴파일 실패: %s\n%s' % (rel, normalize(text, root)))
    elif kind == 'go':
        _go_build(root, scratch, rel, env)
    return None


def run_single(root, rel, scratch):
    kind = kind_of(rel)
    lroot = LANGS[kind][0]
    _, d = parse_directives(_read(_main_file(root, rel)), kind)
    check_ports(part_of(rel), ports_in(d['args']))
    env = _env(root, scratch, d['env'])
    if d['norun']:
        return _check_compiles(root, scratch, rel, env)
    short = rel[len(lroot) + 1:]
    args = shlex.split(d['args'])
    if kind == 'py':
        argv = [PYTHON, short] + args
    elif kind == 'ts':
        argv = ['node', short] + args
    else:
        argv = [_go_build(root, scratch, rel, env)] + args
    text, rc = _call(argv, os.path.join(root, lroot), env, d['timeout'], d['stdin'])
    if rc != d['exit']:
        raise RunError('종료 코드 %d (기대 %d — 일부러라면 지시자 exit: 를 단다)\n%s'
                       % (rc, d['exit'], normalize(text, root)))
    cap = '$ ' + shown_command(kind, short, d) + '\n'
    if text:
        cap += text if text.endswith('\n') else text + '\n'
    if rc:
        cap += '[종료 코드 %d]\n' % rc
    return normalize(cap, root)


def _resolve(root, scratch, cmd, env):
    """명세의 cmd → (argv, cwd, 화면의 명령)."""
    lang, _, rest = cmd.partition(':')
    if lang == 'sh':
        return ['/bin/sh', '-c', rest], os.path.join(root, 'ex'), rest
    toks = shlex.split(rest)
    if not toks:
        raise RunError('cmd 에 프로그램이 없다: %s' % cmd)
    lroot = os.path.join(root, LANGS[lang][0])
    target = toks[0].rstrip('/')
    if not os.path.exists(os.path.join(lroot, target)):
        raise RunError('없는 예제: %s/%s' % (LANGS[lang][0], target))
    if lang == 'py':
        return [PYTHON] + toks, lroot, 'python ' + rest
    if lang == 'ts':
        return ['node'] + toks, lroot, 'node ' + rest
    binp = _go_build(root, scratch, '%s/%s' % (LANGS['go'][0], target), env)
    return [binp] + toks[1:], lroot, 'go run ./' + rest


def _wait_ready(step, proc, timeout, outfile):
    ready = step['ready']
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RunError('%s 가 준비되기 전에 끝났다 (종료 코드 %d)\n%s'
                           % (step['name'], proc.returncode, _read(outfile)))
        try:
            if ready.startswith('tcp:'):
                socket.create_connection(('127.0.0.1', int(ready[4:])), 0.5).close()
                return
            with urllib.request.urlopen(ready, timeout=1) as r:
                if r.status == 200:
                    return
        except OSError:
            pass
        time.sleep(0.1)
    raise RunError('%s 가 %d초 안에 준비되지 않았다 (%s)\n%s'
                   % (step['name'], timeout, ready, _read(outfile)))


def run_spec(root, rel, scratch, ready_timeout=READY_TIMEOUT):
    steps = parse_spec(_read(os.path.join(root, rel)))
    part = part_of(rel)
    check_ports(part, ports_in(_read(os.path.join(root, rel))))
    for s in steps:                          # 쓰는 포트 — 서버·탭이 들을 자리
        for p in ([_ready_port(s['ready'])] if s['verb'] == 'serve' else
                  [s['listen']] if s['verb'] == 'tap' else []):
            if _busy(p):
                raise RunError('포트 %d 를 이미 누가 쓰고 있다 — 남은 프로세스를 먼저 내린다' % p)
    work = os.path.join(scratch, 'run', rel.replace('/', '_'))
    shutil.rmtree(work, True)
    os.makedirs(work)
    env = _env(root, scratch)
    plan = []                                # 띄우기 전에 전부 푼다(go build 포함)
    for s in steps:
        if s['verb'] in ('serve', 'run'):
            plan.append((s, _resolve(root, scratch, s['cmd'], env)))
        elif s['verb'] == 'tap':
            argv = [PYTHON, WIRETAP, str(s['listen']), str(s['target']),
                    '--log', os.path.join(work, s['name'] + '.wire')]
            if s.get('order') == 'sorted':
                argv.append('--whole')
            plan.append((s, (argv, root, 'python tools/wiretap.py %d %d' % (s['listen'], s['target']))))
        else:
            plan.append((s, None))
    procs = []                               # (step, Popen, 출력 파일)
    head, client, term = [], [], 0
    try:
        for s, r in plan:
            if s['verb'] in ('serve', 'tap'):
                term += 1
                argv, cwd, shown = r
                s['term'] = term
                outfile = os.path.join(work, s['name'] + '.out')
                with open(outfile, 'wb') as f:
                    p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                         stdout=f, stderr=subprocess.STDOUT, start_new_session=True)
                procs.append((s, p, outfile))
                head.append('[터미널 %d] $ %s' % (term, shown))
                _wait_ready(s if s['verb'] == 'serve' else dict(s, ready='tcp:%d' % s['listen']),
                            p, ready_timeout, outfile)
        cterm = term + 1
        for s, r in plan:
            if s['verb'] == 'wait':
                time.sleep(s['ms'] / 1000.0)
            elif s['verb'] == 'run':
                argv, cwd, shown = r
                text, rc = _call(argv, cwd, env, s.get('timeout', DEFAULT_TIMEOUT))
                client.append('[터미널 %d] $ %s' % (cterm, shown))
                if text:
                    client.append(text[:-1] if text.endswith('\n') else text)
                if rc:
                    client.append('[종료 코드 %d]' % rc)
                if rc != s.get('exit', 0):
                    raise RunError('`%s` 의 종료 코드가 %d (기대 %d)\n%s'
                                   % (shown, rc, s.get('exit', 0), normalize(text, root)))
        for s, p, outfile in procs:
            if p.poll() is not None:
                raise RunError('%s 가 먼저 끝났다 (종료 코드 %d)\n%s'
                               % (s['name'], p.returncode, normalize(_read(outfile), root)))
    finally:
        for s, p, _ in reversed(procs):
            _kill(p)
    tail = []
    for s, p, outfile in procs:
        out = _read(outfile)
        if s['verb'] == 'serve':
            tail.append('── 터미널 %d (%s) 출력 ──' % (s['term'], s['name']))
            if out:
                tail.append(out[:-1] if out.endswith('\n') else out)
        else:
            if out:
                raise RunError('탭 %s 가 오류를 냈다\n%s' % (s['name'], out))
            wf = os.path.join(work, s['name'] + '.wire')
            wire = _read(wf) if os.path.isfile(wf) else ''
            if s.get('order') == 'sorted':
                wire = sort_exchanges(wire)
            tail.append('── 와이어 (%s)%s ──' % (s['name'], ' (정렬됨)' if s.get('order') else ''))
            if wire:
                tail.append(wire[:-1] if wire.endswith('\n') else wire)
    shutil.rmtree(work, True)
    return normalize('\n'.join(head + client + tail) + '\n', root)


def run_example(root, rel, scratch=None, ready_timeout=READY_TIMEOUT):
    """예제 하나를 돌려 캡처 글을 돌려준다(norun 이면 None). 기대와 다르면 RunError.

       scratch/run.lock 을 잡는다 — 러너는 한 번에 하나(PLAN.md §0.9).
    """
    scratch = os.path.abspath(scratch or os.path.join(root, 'scratch'))
    os.makedirs(scratch, exist_ok=True)
    ex = example_of(rel)
    if ex is None:
        raise RunError('예제가 아니다(ex/{py,ts,go,run}/NN/… 만): %s' % rel)
    with open(os.path.join(scratch, 'run.lock'), 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if kind_of(ex) == 'run':
            return run_spec(root, ex, scratch, ready_timeout)
        return run_single(root, ex, scratch)


# ── 명령 줄 ────────────────────────────────────────────────────────
def _targets(root, args):
    if args.all:
        found = examples(root)
    else:
        found = []
        for a in args.paths:
            rel = os.path.relpath(os.path.abspath(a), root).rstrip('/')
            ex = example_of(rel)
            if ex:
                found.append(ex)
            else:
                found += [e for e in sources(root) if e.startswith(rel + '/')]
    if args.only:
        only = args.only.rstrip('/')
        found = [e for e in found if e == only or e.startswith(only + '/')]
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description='예제를 돌려 캡처를 남긴다')
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--all', action='store_true', help='ex/ 의 예제 전부 (norun 빼고)')
    ap.add_argument('--only', help='이 경로 아래의 것만')
    ap.add_argument('--stale', action='store_true', help='캡처가 없거나 낡은 것만')
    ap.add_argument('--check', action='store_true', help='다시 돌려 캡처와 같은지만 본다')
    ap.add_argument('--manifest-check', action='store_true', help='돌리지 않고 해시만 본다')
    ap.add_argument('--prune', action='store_true', help='예제가 사라진 캡처·장부 줄을 지운다')
    ap.add_argument('-q', '--quiet', action='store_true', help='캡처를 화면에 찍지 않는다')
    args = ap.parse_args(argv)
    root = ROOT

    if args.prune:
        for o in orphans(root):
            print('  - ' + o)
        prune(root)
        return 0

    if args.manifest_check:
        rows = manifest_load(root)
        exs = examples(root)
        bad = [(e, stale(root, e, rows)) for e in exs]
        bad = [(e, why) for e, why in bad if why]
        for e, why in bad:
            print('  ✗ %s — %s (python3 tools/a2arun.py %s)' % (e, why, e))
        lost = orphans(root)
        for o in lost:
            print('  ✗ %s — 예제가 없는 캡처 (python3 tools/a2arun.py --prune)' % o)
        print('  예제 %d개 — 낡은 캡처 %d개, 주인 없는 캡처 %d개' % (len(exs), len(bad), len(lost)))
        return 1 if bad or lost else 0

    targets = _targets(root, args)
    if not targets:
        ap.error('돌릴 예제가 없다 (경로를 주거나 --all)')
    failed = 0
    for rel in targets:
        if args.stale and not stale(root, rel):
            continue
        try:
            cap = run_example(root, rel)
        except RunError as e:
            print('  ✗ %s\n%s' % (rel, e))
            failed += 1
            continue
        if cap is None:
            print('  · %s — norun: 컴파일만 확인했다' % rel)
            continue
        out = os.path.join(root, capture_path(rel))
        if args.check:
            old = _read(out) if os.path.isfile(out) else None
            if old != cap:
                print('  ✗ %s — 다시 돌리니 캡처와 다르다\n%s' % (rel, cap))
                failed += 1
            else:
                print('  ✓ %s' % rel)
            continue
        _write(out, cap)
        manifest_update(root, rel, toolchain(root, rel))
        print('  ✓ %s → %s' % (rel, capture_path(rel)))
        if not args.quiet:
            sys.stdout.write(cap)
    if failed:
        print('  실패 %d개' % failed)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
