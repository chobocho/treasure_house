#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사실 검사 — 덱이 적은 규격 조항과 연도가 근거를 갖고 있는가.

    python3 deck/check_claims.py

이 덱이 가장 쉽게 틀릴 자리는 코드가 아니라 문장이다. "1973년 4월 3일",
"TS 38.211 4.2절", "IS-95 는 1.2288 Mcps" — 전부 기억으로 적으면 반드시
어딘가 어긋나고, 어긋나도 아무 시험이 빨개지지 않는다. 그래서 규칙으로 옮겼다.

두 가지를 본다.

  1. **규격 조항** — 조립기가 남긴 deck/spec_used.txt 의 (기관·번호·조항) 이
     specs/ 에 내려받아 뽑아 둔 본문에 진짜 조항 제목으로 있는가.
     specs/ 가 비어 있으면 그 규격은 `make specs` 로 먼저 받아야 한다.
  2. **연도** — 조각 파일의 산문에 적힌 네 자리 연도가 deck/claims.md 나
     data/*.tsv 에 근거와 함께 적혀 있는가. 없으면 그 연도는 기억에서
     나온 것이다.

연도처럼 보이지만 연도가 아닌 수(1800 MHz 대역, 2048-포인트 FFT)는
단위를 보고 걸러 내고, 그래도 남는 것은 deck/years_ok.txt 에 적는다.

시간 O(조각 크기 + 규격 본문 크기).
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SECTIONS = os.path.join(HERE, 'sections')
DATA = os.path.join(BASE, 'data')
SPECS = os.path.join(BASE, 'specs')

YEAR = re.compile(r'(?<![\d.\-])(1[89]\d\d|20\d\d)(?![\d.\-])')
# 연도가 아닌 것들 — 뒤에 이런 단위가 붙으면 수치다.
NOT_YEAR_AFTER = re.compile(
    r'\s*(MHz|kHz|GHz|Hz|㎒|Mcps|kcps|ksps|kbps|Mbps|Gbps|bps|dB|dBm|dBi'
    r'|ms|μs|us|ns|km|m\b|비트|바이트|칩|슬롯|샘플|점|칸|줄|장|개|명|기)')
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


def check_specs():
    """spec_used.txt 의 조항이 specs/ 의 본문에 있는가."""
    p = os.path.join(HERE, 'spec_used.txt')
    if not os.path.exists(p):
        return [], 0
    bad, n = [], 0
    for line in read(p).split('\n'):
        if not line.strip() or line.startswith('#'):
            continue
        cols = line.split('\t')
        if len(cols) < 3:
            continue
        org, num, clause = cols[0], cols[1], cols[2]
        if not clause:
            # 번호만 인용한 것 — 볼 조항이 없다
            continue
        n += 1
        f = os.path.join(SPECS, '%s.txt' % num)
        if not os.path.exists(f):
            bad.append('%s %s — specs/%s.txt 가 없다'
                       % (org.upper(), num, num))
            continue
        # 조항 제목은 "4.2\t제목" 꼴로 한 줄을 연다.
        pat = re.compile(r'^\s*%s[\s\t]' % re.escape(clause), re.M)
        if not pat.search(read(f)):
            bad.append('%s %s §%s — 그런 조항이 본문에 없다'
                       % (org.upper(), num, clause))
    return bad, n


def check_years():
    """조각 산문의 연도가 근거를 갖고 있는가."""
    ev = evidence_text()
    ok = allowed_years()
    bad, n = [], 0
    if not os.path.isdir(SECTIONS):
        return bad, n
    for name in sorted(os.listdir(SECTIONS)):
        if not name.endswith('.html'):
            continue
        text = PRE.sub(' ', read(os.path.join(SECTIONS, name)))
        prose = TAG.sub(' ', text)
        for m in YEAR.finditer(prose):
            after = prose[m.end():m.end() + 12]
            if NOT_YEAR_AFTER.match(after):
                continue
            y = m.group(1)
            if y in ok:
                continue
            n += 1
            if y not in ev:
                a = max(0, m.start() - 18)
                near = prose[a:m.end() + 12].strip()
                bad.append('%s: %s — 근거가 없다 (앞뒤: …%s…)'
                           % (name, y, near))
    return bad, n


def main():
    sbad, sn = check_specs()
    ybad, yn = check_years()
    for line in sbad + ybad:
        print('  ✗ ' + line)
    print('규격 조항 인용 %d건 · 연도 %d건 — 근거 없음 %d건'
          % (sn, yn, len(sbad) + len(ybad)))
    return 1 if (sbad or ybad) else 0


if __name__ == '__main__':
    sys.exit(main())
