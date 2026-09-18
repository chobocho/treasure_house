# -*- coding: utf-8 -*-
"""scrub.py — 캡처의 개인정보를 지우고, 남은 것을 빌드에서 막는다.

    python3 tools/scrub.py --fix FILE …    # 자리표시로 바꾼다
    python3 tools/scrub.py --check PATH …  # 남은 것이 있으면 1

이 덱의 캡처는 사용자가 날마다 쓰는 폰에서 뜬다(PLAN.md §0.8).
전화번호 하나가 공개 저장소에 올라가면 지워도 늦는다. 그래서 사람의
눈이 아니라 빌드가 막는다.

두 갈래로 나눈 까닭 — 바꿔도 그 장의 뜻이 그대로인 것(Wi-Fi 이름,
공인 IP, 집 아래 경로)은 fix() 가 자리표시로 바꾼다. 바꾸면 뜻이
사라지거나 애초에 캡처에 있으면 안 되는 것(전화번호·IMEI·MAC·위치·
전자우편·이름)은 problems() 가 잡아 빌드를 멈춘다 — 그런 캡처는
명령부터 다시 골라야 한다.

보고에는 값을 그대로 찍지 않는다. 앞 두 글자와 길이만 보인다.
로그인 이름은 소스에도 평문으로 두지 않고 SHA-256 앞 16자리로만 안다.

시간 O(글자 수), 공간 O(글자 수).
"""
import hashlib
import io
import ipaddress
import os
import re
import sys

HOME = '/data/data/com.termux/files/home'
KEEP_UNDER = ('github/treasure_house/', 'github/treasure_house')
SHARED = '/storage/emulated/0'

# 사용자 이름 — sha256(소문자)[:16]. 평문은 어디에도 적지 않는다.
NAME_HASHES = {'5fbf858b0ed750b0', 'eb4db9c3e5e0479d'}

# 공개된 주소라 캡처에 남아도 되는 전자우편 꼬리
MAIL_OK = ('@users.noreply.github.com', '@noreply.github.com',
           '@example.com', '@example.org', '@termux.dev')
# 안드로이드가 앱에 돌려주는 가짜 MAC — 진짜 주소가 아니다
MAC_OK = {'02:00:00:00:00:00', '00:00:00:00:00:00'}


def name_hash(word):
    return hashlib.sha256(word.lower().encode('utf-8')).hexdigest()[:16]


# ── fix: 자리표시로 바꾸기 ─────────────────────────────────────────
SSID_RE = re.compile(r'("ssid"\s*:\s*")(?!<ssid>")[^"]*(")', re.I)
SSID_TXT = re.compile(r'(\bSSID\s*[:=]\s*)(?!<ssid>)(\S[^\n]*)')
BSSID_RE = re.compile(r'("bssid"\s*:\s*")(?!<bssid>")[^"]*(")', re.I)
IP4_RE = re.compile(r'(?<![\w.])(\d{1,3}(?:\.\d{1,3}){3})(?![\w.])')
# IPv6 후보. 12:34:56 같은 시각도 걸리지만 ipaddress 가 걸러 낸다.
IP6_RE = re.compile(r'(?<![\w:])([0-9a-fA-F]{0,4}(?::[0-9a-fA-F]{0,4})'
                    r'{2,7})(?![\w:])')
# 경로는 낱말 머리에서만 본다 — "main/x11/root/TUR" 의 /root 는
# 경로가 아니다(data/repos_apt.tsv 에서 실제로 오탐이 났다).
HOME_RE = re.compile(r'(?<![\w/.-])(?:%s|/root)/([^\s\'"<>]*)'
                     % re.escape(HOME))
SHARED_RE = re.compile(r'%s/[^\s\'"<>]+' % re.escape(SHARED))


def _ip4_public(s):
    try:
        a = ipaddress.IPv4Address(s)
    except ValueError:
        return False
    return not (a.is_private or a.is_loopback or a.is_unspecified
                or a.is_link_local or a.is_multicast
                or s.startswith('255.'))


def _ip6_sensitive(s):
    if s.count(':') < 2:
        return False
    try:
        a = ipaddress.IPv6Address(s)
    except ValueError:
        return False
    return not (a.is_loopback or a.is_unspecified)


def _home_sub(m):
    rest = m.group(1)
    if rest == '' or rest.startswith(KEEP_UNDER):
        return m.group(0)
    return '<home>/…'


def fix(text):
    """(바꾼 글, 바꾼 개수). 두 번 불러도 결과가 같다."""
    n = [0]

    def count(repl):
        def f(m):
            out = repl(m) if callable(repl) else m.expand(repl)
            if out != m.group(0):
                n[0] += 1
            return out
        return f

    text = SSID_RE.sub(count(r'\1<ssid>\2'), text)
    text = SSID_TXT.sub(count(r'\1<ssid>'), text)
    text = BSSID_RE.sub(count(r'\1<bssid>\2'), text)
    text = IP4_RE.sub(count(lambda m: '<ip>' if _ip4_public(m.group(1))
                            else m.group(0)), text)
    text = IP6_RE.sub(count(lambda m: '<ip>'
                            if _ip6_sensitive(m.group(1))
                            else m.group(0)), text)
    text = HOME_RE.sub(count(_home_sub), text)
    text = SHARED_RE.sub(count(lambda m: SHARED + '/<…>'
                               if m.group(0) != SHARED + '/<…>'
                               else m.group(0)), text)
    return text, n[0]


# ── problems: 남으면 안 되는 것 ────────────────────────────────────
CHECKS = [
    ('phone', re.compile(r'(?<![\d.])01[016789][-. ]?\d{3,4}[-. ]?\d{4}'
                         r'(?![\d.])')),
    ('phone', re.compile(r'\+\d{1,3}[- ]?\d{1,4}[- ]?\d{3,4}[- ]?\d{4}'
                         r'(?!\d)')),
    ('imei', re.compile(r'(?<![\d.])\d{15}(?![\d.])')),
    ('serial', re.compile(r'serial(?:no|_?number)?\s*[:=]\s*(?!<)'
                          r'[A-Za-z0-9]{6,}', re.I)),
    ('mac', re.compile(r'(?<![\w:])(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}'
                       r'(?![\w:])')),
    ('gps', re.compile(r'-?\d{1,3}\.\d{5,}\s*,\s*-?\d{1,3}\.\d{5,}')),
    ('gps', re.compile(r'"(?:latitude|longitude)"\s*:\s*-?\d', re.I)),
    ('email', re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+')),
    ('ssid', SSID_RE),
    ('ssid', SSID_TXT),
]
WORD_RE = re.compile(r'[A-Za-z][A-Za-z0-9._-]{2,}')


def _mask(s):
    return '%s…(%d자)' % (s[:2], len(s))


def problems(text):
    """[(줄 번호, 종류, 가린 값)]. 없으면 빈 목록."""
    out = []
    for no, line in enumerate(text.split('\n'), 1):
        for kind, rx in CHECKS:
            for m in rx.finditer(line):
                v = m.group(0)
                if kind == 'mac' and v.lower() in MAC_OK:
                    continue
                if kind == 'email' and v.lower().endswith(MAIL_OK):
                    continue
                out.append((no, kind, _mask(v)))
        for m in IP4_RE.finditer(line):
            if _ip4_public(m.group(1)):
                out.append((no, 'ip', _mask(m.group(1))))
        for m in IP6_RE.finditer(line):
            if _ip6_sensitive(m.group(1)):
                out.append((no, 'ip', _mask(m.group(1))))
        for m in HOME_RE.finditer(line):
            if _home_sub(m) != m.group(0):
                out.append((no, 'home', _mask(m.group(1))))
        for m in WORD_RE.finditer(line):
            parts = [m.group(0)] + re.split(r'[._-]', m.group(0))
            if any(name_hash(p) in NAME_HASHES for p in parts if p):
                out.append((no, 'name', _mask(m.group(0))))
    return out


# ── 명령줄 ─────────────────────────────────────────────────────────
def files_under(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = sorted(d for d in dirs
                                 if not d.startswith('.'))
                for n in sorted(names):
                    yield os.path.join(root, n)
        else:
            yield p


def main(argv):
    if len(argv) < 2 or argv[0] not in ('--fix', '--check'):
        print('사용법: scrub.py --fix FILE … | --check PATH …')
        return 2
    missing = [p for p in argv[1:] if not os.path.exists(p)]
    if missing:
        print('없는 경로: %s' % ', '.join(missing))
        return 2
    bad = total = 0
    for f in files_under(argv[1:]):
        try:
            text = io.open(f, encoding='utf-8').read()
        except UnicodeDecodeError:
            continue                    # 바이너리 — 캡처가 아니다
        total += 1
        if argv[0] == '--fix':
            new, n = fix(text)
            if n:
                io.open(f, 'w', encoding='utf-8',
                        newline='\n').write(new)
                print('  %s: %d곳 바꿈' % (f, n))
            continue
        for no, kind, shown in problems(text):
            bad += 1
            print('  ✗ %s:%d %s %s' % (f, no, kind, shown))
    if argv[0] == '--check':
        print('개인정보 검사 %d개 파일 — 걸린 것 %d건' % (total, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
