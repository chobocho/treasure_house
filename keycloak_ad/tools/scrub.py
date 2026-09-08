# -*- coding: utf-8 -*-
"""scrub.py — 캡처에서 '돌릴 때마다 달라지는 것' 만 고정값으로 바꾼다.

왜 필요한가: 이 덱의 약속은 "화면의 출력은 전부 진짜로 돌린 것" 이다. 그
약속을 지키는지 확인하는 방법은 하나뿐이다 — 두 번 돌려서 결과가 같은지 본다
(`make record` 를 두 번 하고 md5 를 견준다). 그런데 진짜 출력에는 시각·난수처럼
매번 달라지는 값이 섞여 있어서, 손대지 않으면 두 번 돌린 결과가 늘 다르다.
그러면 "달라진 것이 시계 때문인지, 코드가 깨져서인지" 를 구별할 수 없다.

그래서 **뜻이 없는 값만** 고정한다. 뜻이 있는 값(상태 번호, 헤더 이름,
Content-Length, 오류 문구)은 한 글자도 건드리지 않는다.

고정하는 것:
  · HTTP Date 헤더와 Go 로그의 시각
  · curl 이 보여 주는 내 쪽 포트, OpenSSL 오류 줄의 식별자
  · 세션 번호 같은 16진수 덩어리 (나온 순서대로 정해진 값을 준다)
  · 이 기계에서만 뜻이 있는 절대 경로와 프로세스 번호
  · 걸린 시간(0.123s 따위)

    python3 tools/scrub.py out/web02_login_ok.txt ...   # 제자리에서
"""
import io
import os
import re
import sys

# 이 시각으로 못 박는다. 실제로 언제 돌렸는지는 claims.md 에 적는다.
FIXED_HTTP_DATE = 'Mon, 08 Sep 2026 09:00:00 GMT'
FIXED_LOG_TIME = '2026/09/08 09:00:00'

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_RULES = [
    # HTTP Date 헤더 — curl 의 '< Date:' 와 서버가 낸 'Date:' 둘 다
    # HTTP/2 로 붙으면 curl 이 헤더 이름을 소문자로 보여 준다 — 둘 다 잡는다
    (re.compile(r'(?i)(date:\s*)[a-z]{3}, \d{2} [a-z]{3} \d{4}'
                r' \d{2}:\d{2}:\d{2} GMT'),
     lambda m: m.group(1) + FIXED_HTTP_DATE),
    # curl 쿠키 항아리의 만료 시각(1970년부터 센 초)
    (re.compile(r'(expire )\d{9,}'), lambda m: m.group(1) + '1788856500'),
    (re.compile(r'^(\S+\t(?:TRUE|FALSE)\t\S+\t(?:TRUE|FALSE)\t)\d{9,}',
                re.M),
     lambda m: m.group(1) + '1788856500'),
    # Go 표준 로그의 시각 접두사
    (re.compile(r'\b\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\b'),
     lambda m: FIXED_LOG_TIME),
    # 걸린 시간
    (re.compile(r'\b\d+\.\d{2,3}s\b'), lambda m: '0.00s'),
    (re.compile(r'\(\d+(\.\d+)? ?ms\)'), lambda m: '(0 ms)'),
    # 프로세스 번호
    (re.compile(r'\bpid[= ]\d+\b'), lambda m: 'pid=0'),
    # curl 이 알려 주는 내 쪽 포트. 운영체제가 그때그때 아무 번호나 준다.
    (re.compile(r'(from \S+ port )\d+'), lambda m: m.group(1) + '50000'),
    # 서버 로그에 찍힌 상대편 임시 포트. 리눅스는 32768~60999 에서 고른다 —
    # 그 아래(8081·8443 같은 우리 포트)는 뜻이 있으니 건드리지 않는다.
    (re.compile(r':(\d{5})\b'),
     lambda m: ':50000' if int(m.group(1)) >= 32768 else m.group(0)),
    # OpenSSL 오류 줄 앞의 16자리 식별자 — 프로세스마다 다르다
    (re.compile(r'^[0-9A-F]{16}:error:', re.M),
     lambda m: '0000000000000000:error:'),
]


def _fake_id(n, length):
    """n번째로 나온 16진수 덩어리에 줄 값. 무작위처럼 보이되 늘 같다."""
    out = []
    v = (n + 1) * 37
    while len(out) * 2 < length:
        v = (v * 1103515245 + 12345) & 0xFFFFFFFF
        out.append((v >> 16) & 0xFF)
    return ''.join('%02x' % b for b in out)[:length]


# 무작위 값이 실려 나오는 자리들. **이름을 아는 곳만** 바꾼다.
#
# 처음에는 "16진수 32글자 이상이면 전부 바꾼다" 로 두었는데, 그 규칙이
# sha256 출력까지 바꿔 버렸다. 해시는 매번 같은 값이 나오는, 뜻이 있는
# 값이다 — 그걸 가짜로 바꾸면 덱이 "sha256('minji') 는 이것이다" 라고
# 거짓말을 하게 된다. 실제로 한 번 그런 캡처가 나왔다.
# 그래서 값의 모양이 아니라 **자리**로 고른다.
RANDOM_KEYS = ['lunch_session', 'state', 'nonce', 'session_state',
               'sid', 'jti', 'kid', 'code_verifier', 'code_challenge']
_HEX = re.compile(r'(?<![\w-])(%s)(["\s]*[=:]["\s]*)([0-9a-zA-Z_-]{16,})'
                  % '|'.join(RANDOM_KEYS))


def scrub(text):
    for pat, rep in _RULES:
        text = pat.sub(rep, text)

    # 같은 값은 파일 안에서 같은 것으로 바뀌어야 한다. 안 그러면
    # "쿠키의 이 번호와 로그의 저 번호가 같다" 는 설명이 거짓이 된다.
    seen = {}

    def hexsub(m):
        key, sep, raw = m.group(1), m.group(2), m.group(3)
        if raw not in seen:
            seen[raw] = _fake_id(len(seen), len(raw))
        return key + sep + seen[raw]

    text = _HEX.sub(hexsub, text)

    # curl 의 쿠키 항아리는 이름과 값이 탭으로 갈려 있어 위 규칙에 안 걸린다.
    def jarsub(m):
        raw = m.group(2)
        if raw not in seen:
            seen[raw] = _fake_id(len(seen), len(raw))
        return m.group(1) + seen[raw]

    text = re.sub(r'(\tlunch_session\t)([0-9a-f]{16,})', jarsub, text)

    # 이 기계에서만 뜻이 있는 경로
    text = text.replace(REPO, '/…/keycloak_ad')
    text = text.replace(os.path.expanduser('~'), '~')
    return text


def main(paths):
    if not paths:
        sys.stderr.write(__doc__)
        return 2
    n = 0
    for p in paths:
        if not os.path.isfile(p):
            continue
        src = io.open(p, encoding='utf-8', errors='replace').read()
        out = scrub(src)
        if out != src:
            n += 1
        io.open(p, 'w', encoding='utf-8', newline='\n').write(out)
    print('  정리한 캡처 %d개 / 전체 %d개' % (n, len(paths)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
