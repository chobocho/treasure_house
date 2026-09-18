#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사실 검사 — 덱이 적은 소스 줄과 연도가 근거를 갖고 있는가.

    python3 deck/check_claims.py

이 덱이 가장 쉽게 틀릴 자리는 코드가 아니라 문장이다. "2015년 시작",
"0.101 에서 멈췄다", "Android 12 부터 32개" — 전부 기억으로 적으면
반드시 어딘가 어긋나고, 어긋나도 아무 시험이 빨개지지 않는다.
(트랜스포머 덱의 논문 절 검사를 upstream 소스 줄 검사로 바꾼 것이다 —
PLAN.md §1·§3.2.)

세 가지를 본다.

  1. **소스 줄** — 조립기가 남긴 deck/src_used.txt 의 (저장소·커밋·
     경로·줄) 이 그 커밋에 진짜 있는가. `git show <sha>:<path>` 로 읽으니
     sources/ 의 작업 트리가 움직여도 답이 같다. sources/ 는 커밋하지
     않는 캐시라 비어 있으면 `make sources` 로 받는다.
  2. **연도** — 조각 파일의 산문에 적힌 네 자리 연도가 deck/claims.md 나
     data/*.tsv 에 근거와 함께 적혀 있는가. 없으면 그 연도는 기억에서
     나온 것이다.
  3. **2025년 이후** — 지식 마감 뒤의 일이라 같은 장에 "2026-09 기준"
     도장이 있어야 한다(PLAN.md §0.4).

연도처럼 보이지만 연도가 아닌 수(8022 포트, 2048 바이트)는
단위를 보고 걸러 내고, 그래도 남는 것은 deck/years_ok.txt 에 적는다.

시간 O(조각 크기 + 인용한 파일 크기).
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SECTIONS = os.path.join(HERE, 'sections')
DATA = os.path.join(BASE, 'data')
sys.path.insert(0, HERE)
import srcpin                                                  # noqa: E402

# 지식 마감 뒤의 해. 이 해부터는 도장 없이 적지 않는다.
STAMP_FROM = 2025
STAMP = '2026-09 기준'

YEAR = re.compile(r'(?<![\d.\-])(1[89]\d\d|20\d\d)(?![\d.\-])')
# 연도가 아닌 것들 — 뒤에 이런 단위가 붙으면 수치다.
NOT_YEAR_AFTER = re.compile(
    r'\s*(개|장|줄|칸|바이트|비트|글자|번|초|쪽|명'
    r'|MB|KB|GB|M\b|K\b|B\b|ms|MiB|KiB)')
# 문맥이 연도임을 못 박는 표시 — 이게 붙으면 반드시 근거가 있어야 한다.
TAG = re.compile(r'<[^>]+>')
PRE = re.compile(r'<pre.*?</pre>|<!--.*?-->|<code.*?</code>', re.S)


def read(p):
    return io.open(p, encoding='utf-8').read()


def evidence_text():
    """근거로 인정하는 글 뭉치 — claims.md 와 data/*.tsv 전부."""
    parts = []
    p = os.path.join(HERE, 'claims.md')
    if os.path.exists(p):
        parts.append(read(p))
    if os.path.isdir(DATA):
        for name in sorted(os.listdir(DATA)):
            if name.endswith('.tsv'):
                parts.append(read(os.path.join(DATA, name)))
    return '\n'.join(parts)


def allowed_years():
    p = os.path.join(HERE, 'years_ok.txt')
    if not os.path.exists(p):
        return set()
    return set(l.split('#')[0].strip() for l in read(p).split('\n')
               if l.split('#')[0].strip())


def check_srcs(pins=None):
    """src_used.txt 의 줄이 핀 커밋의 그 파일에 있는가."""
    pins = pins or srcpin.Pins(BASE)
    p = os.path.join(HERE, 'src_used.txt')
    if not os.path.exists(p):
        return [], 0
    bad, n = [], 0
    for line in read(p).split('\n'):
        if not line.strip() or line.startswith('#'):
            continue
        cols = line.split('\t')
        if len(cols) < 4:
            continue
        repo, sha, path, ln = cols[:4]
        n += 1
        why = pins.check(repo, sha)
        if why:
            bad.append(why)
            continue
        got = pins.lines('sources/%s/%s' % (repo, path))
        if got is None:
            bad.append('%s@%s:%s — 그 커밋에 그 파일이 없다 (make sources?)'
                       % (repo, sha[:7], path))
            continue
        if ln:
            a, _, b = ln.partition('-')
            a, b = int(a), int(b or a)
            if not 1 <= a <= b <= len(got):
                bad.append('%s@%s:%s:%s — 파일은 %d줄이다'
                           % (repo, sha[:7], path, ln, len(got)))
    return bad, n


def check_years():
    """조각 산문의 연도가 근거를 갖고 있는가. 2025년 이후는 도장까지.

    장(<article>) 단위로 본다 — 도장은 그 연도와 같은 화면에 있어야
    독자가 본다. 부록의 참고문헌처럼 날짜가 많은 장도 도장 하나면 된다.
    """
    ev = evidence_text()
    ok = allowed_years()
    bad, n = [], 0
    if not os.path.isdir(SECTIONS):
        return bad, n
    for name in sorted(os.listdir(SECTIONS)):
        if not name.endswith('.html'):
            continue
        for art in re.split(r'(?=<article)', read(os.path.join(SECTIONS, name))):
            prose = TAG.sub(' ', PRE.sub(' ', art))
            for m in YEAR.finditer(prose):
                after = prose[m.end():m.end() + 12]
                if NOT_YEAR_AFTER.match(after):
                    continue
                y = m.group(1)
                if y in ok:
                    continue
                n += 1
                a = max(0, m.start() - 18)
                near = prose[a:m.end() + 12].strip()
                if y not in ev:
                    bad.append('%s: %s — 근거가 없다 (앞뒤: …%s…)'
                               % (name, y, near))
                elif int(y) >= STAMP_FROM and STAMP not in prose:
                    bad.append('%s: %s — 같은 장에 "%s" 도장이 없다 '
                               '(앞뒤: …%s…)' % (name, y, STAMP, near))
    return bad, n


def main():
    sbad, sn = check_srcs()
    ybad, yn = check_years()
    for line in sbad + ybad:
        print('  ✗ ' + line)
    print('소스 줄 인용 %d건 · 연도 %d건 — 근거 없음 %d건'
          % (sn, yn, len(sbad) + len(ybad)))
    return 1 if (sbad or ybad) else 0


if __name__ == '__main__':
    sys.exit(main())
