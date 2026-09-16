#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사실 검사 — 덱이 적은 논문 절과 연도가 근거를 갖고 있는가.

    python3 deck/check_claims.py

이 덱이 가장 쉽게 틀릴 자리는 코드가 아니라 문장이다. "2017년 6월",
"Vaswani 외 3.2.1절", "GPT-2 는 117M" — 전부 기억으로 적으면 반드시
어딘가 어긋나고, 어긋나도 아무 시험이 빨개지지 않는다. 그래서 규칙으로 옮겼다.
(무선 덱의 규격 조항 검사를 논문 절 검사로 바꾼 것이다 — PLAN.md §1.)

두 가지를 본다.

  1. **논문 절** — 조립기가 남긴 deck/cite_used.txt 의 (키·절) 이
     papers/<키>.txt 에 진짜 절 제목 줄("3.2.1<TAB>제목")로 있는가.
     papers/ 는 커밋하지 않는 캐시라 비어 있으면 `make papers` 로 받는다.
  2. **연도** — 조각 파일의 산문에 적힌 네 자리 연도가 deck/claims.md 나
     data/*.tsv 에 근거와 함께 적혀 있는가. 없으면 그 연도는 기억에서
     나온 것이다.

연도처럼 보이지만 연도가 아닌 수(2048 토큰 문맥, 1024 차원)는
단위를 보고 걸러 내고, 그래도 남는 것은 deck/years_ok.txt 에 적는다.

시간 O(조각 크기 + 논문 본문 크기).
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SECTIONS = os.path.join(HERE, 'sections')
DATA = os.path.join(BASE, 'data')
PAPERS = os.path.join(BASE, 'papers')

YEAR = re.compile(r'(?<![\d.\-])(1[89]\d\d|20\d\d)(?![\d.\-])')
# 연도가 아닌 것들 — 뒤에 이런 단위가 붙으면 수치다.
NOT_YEAR_AFTER = re.compile(
    r'\s*(토큰|차원|개|장|줄|칸|스텝|바이트|비트|글자|층'
    r'|MB|KB|GB|M\b|K\b|B\b|ms|dim|tokens?|steps?)')
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


def check_cites():
    """cite_used.txt 의 절이 papers/ 의 본문에 있는가."""
    p = os.path.join(HERE, 'cite_used.txt')
    if not os.path.exists(p):
        return [], 0
    bad, n = [], 0
    for line in read(p).split('\n'):
        if not line.strip() or line.startswith('#'):
            continue
        cols = line.split('\t')
        if len(cols) < 2:
            continue
        key, sec = cols[0], cols[1]
        if not sec:
            # 키만 인용한 것 — 볼 절이 없다
            continue
        n += 1
        f = os.path.join(PAPERS, '%s.txt' % key)
        if not os.path.exists(f):
            bad.append('%s — papers/%s.txt 가 없다 (make papers)' % (key, key))
            continue
        # 절 제목은 "3.2.1\t제목" 꼴로 한 줄을 연다 (tools/paper_text.py).
        pat = re.compile(r'^%s\t' % re.escape(sec), re.M)
        if not pat.search(read(f)):
            bad.append('%s §%s — 그런 절이 본문에 없다' % (key, sec))
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
    sbad, sn = check_cites()
    ybad, yn = check_years()
    for line in sbad + ybad:
        print('  ✗ ' + line)
    print('논문 절 인용 %d건 · 연도 %d건 — 근거 없음 %d건'
          % (sn, yn, len(sbad) + len(ybad)))
    return 1 if (sbad or ybad) else 0


if __name__ == '__main__':
    sys.exit(main())
