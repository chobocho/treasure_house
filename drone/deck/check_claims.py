#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사실 검사 — 덱이 적은 문서 절·연도·날짜·드론 대수·조문 번호에 근거가 있는가.

    python3 deck/check_claims.py

이 덱이 가장 쉽게 틀릴 자리는 코드가 아니라 문장이다. "2018년 평창에서
1,218대", "항공안전법 제129조", "§107.35" — 전부 기억으로 적으면 반드시
어딘가 어긋나고, 어긋나도 아무 시험이 빨개지지 않는다. 그래서 규칙으로
옮겼다(PLAN.md §0.4, §6). goevo 덱의 검사를 물려받아 버전 검사를 빼고
대수·조문 검사를 더했다.

다섯 가지를 본다.

  1. **문서 절** — 조립기가 남긴 deck/cite_used.txt 의 (키·절) 이
     받아 둔 문서에 진짜 있는가(deck/cites.py).
  2. **인용 키 파일** — cite_keys.tsv 의 문서가 docs/ 에 받아져 있는가.
  3. **연도·날짜** — 산문의 네 자리 연도와 날짜가 deck/claims*.md 나
     data/*.tsv 에 적혀 있는가. 없으면 기억에서 나온 것이다.
  4. **드론 대수** — 산문의 'N대'(N ≥ 100)가 근거 글에 있는가. 쇼 기록은
     이 덱에서 가장 자주 바뀌고 가장 자주 틀리는 숫자다. 우리 시뮬레이터의
     대수(300대 판 같은 것)는 deck/counts_ok.txt 에 적는다.
  5. **조문 번호** — '제N조(의M)' 와 '§107.N' 이 근거 글(law.tsv 가
     대부분)에 있는가.

연도처럼 보이지만 연도가 아닌 수(2048 바이트)는 단위를 보고 거르고,
그래도 남는 것은 deck/years_ok.txt 에 적는다.

시간 O(조각 크기 + 문서 본문 크기).
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cites  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SECTIONS = os.path.join(HERE, 'sections')
DATA = os.path.join(BASE, 'data')
DOCS = os.path.join(BASE, 'docs')

YEAR = re.compile(r'(?<![\d.\-])(1[89]\d\d|20\d\d)(?![\d.\-])')
# 연도가 아닌 것들 — 뒤에 이런 단위가 붙으면 수치다.
NOT_YEAR_AFTER = re.compile(
    r'\s*(개|장|줄|칸|바이트|비트|글자|커밋|파일|객체|번'
    r'|MB|KB|GB|M\b|K\b|B\b|ms|ns|files?|bytes?)')
# 드론 대수 — '1,218대' '500 대'. 100 대 미만은 보지 않는다(시험 비행
# 3대 같은 말까지 근거를 요구하면 규칙이 소음이 된다). 뒤에 '역'·'학'이
# 붙은 '대역'·'대학' 같은 낱말은 대수가 아니다.
COUNT = re.compile(r'(?<![\d.,])(\d{1,3}(?:,\d{3})+|\d{3,})\s?대(?![역학표상신체부략])')
# 조문 — 한국 법령의 '제129조', '제124조의2' 와 미국 연방규정의 '§107.29'.
# 연방규정의 조는 파트 번호가 두세 자리다(§89.x, §107.x) — 'SPEC §4.3'
# 같은 이 덱의 절 번호는 조문이 아니다.
ARTICLE = re.compile(r'제\d+조(?:의\d+)?|§\s?\d{2,3}\.\d+')
# 문맥이 연도임을 못 박는 표시 — 이게 붙으면 반드시 근거가 있어야 한다.
TAG = re.compile(r'<[^>]+>')
# 날짜(2005-04-07 · 2005-04). YEAR 는 뒤에 '-' 가 오면 건너뛰므로
# 날짜는 따로 본다 — 날짜 문자열이 근거 글에 그대로 있어야 한다.
# 연도만 맞고 달·날이 틀린 날짜가 가장 흔한 사실 오류이기 때문이다.
DATE = re.compile(r'(?<![\d.\-])((?:1[89]|20)\d\d-[01]\d(?:-[0-3]\d)?)'
                  r'(?![\d.\-])')
PRE = re.compile(r'<pre.*?</pre>|<!--.*?-->|<code.*?</code>', re.S)


def read(p):
    return io.open(p, encoding='utf-8').read()


def evidence_text():
    """근거로 인정하는 글 뭉치 — claims.md 와 부마다의 deck/claims/*.md,
    data/*.tsv 전부."""
    parts = []
    p = os.path.join(HERE, 'claims.md')
    if os.path.exists(p):
        parts.append(read(p))
    for d, ext in ((os.path.join(HERE, 'claims'), '.md'),
                   (DATA, '.tsv')):
        if os.path.isdir(d):
            for name in sorted(os.listdir(d)):
                if name.endswith(ext):
                    parts.append(read(os.path.join(d, name)))
    return '\n'.join(parts)


def allowed_years():
    p = os.path.join(HERE, 'years_ok.txt')
    if not os.path.exists(p):
        return set()
    return set(l.split('#')[0].strip() for l in read(p).split('\n')
               if l.split('#')[0].strip())


def check_cites():
    """cite_used.txt 의 (키·절) 이 docs/ 의 본문에 있는가 (deck/cites.py)."""
    p = os.path.join(HERE, 'cite_used.txt')
    if not os.path.exists(p):
        return [], 0
    bad, n = [], 0
    for line in read(p).split('\n'):
        if not line.strip() or line.startswith('#'):
            continue
        cols = line.split('\t')
        if len(cols) < 2 or not cols[1]:
            # 키만 인용한 것 — 볼 절이 없다(키는 조립기가 이미 봤다)
            continue
        n += 1
        why = cites.resolve(BASE, cols[0], cols[1])
        if why:
            bad.append(why)
    return bad, n


def check_cite_keys():
    """data/cite_keys.tsv 의 문서가 docs/ 에 진짜 받아져 있는가.

    CITE 로 쓰이기 전이라도 표에 적힌 파일은 있어야 한다 — 없는 파일을
    가리키는 키가 표에 남아 있으면 언젠가 누가 그대로 인용한다. docs/ 가
    없으면(make docs 전) 건너뛴다. O(표 크기).
    """
    if not os.path.isdir(DOCS):
        return [], 0
    bad, n = [], 0
    for key, ent in sorted(cites.index(BASE).items()):
        n += 1
        if not os.path.exists(os.path.join(DOCS, ent['file'])):
            bad.append('%s: docs/%s 가 없다 (make docs)' % (key, ent['file']))
    return bad, n


def prose_of(text):
    """조각 파일 → 검사할 산문. 코드·캡처·지시자 주석·태그를 뺀다."""
    return TAG.sub(' ', PRE.sub(' ', text))


def check_years():
    """조각 산문의 연도·날짜가 근거를 갖고 있는가."""
    ev = evidence_text()
    ok = allowed_years()
    bad, n = [], 0
    if not os.path.isdir(SECTIONS):
        return bad, n
    for name in sorted(os.listdir(SECTIONS)):
        if not name.endswith('.html'):
            continue
        prose = prose_of(read(os.path.join(SECTIONS, name)))
        for m in DATE.finditer(prose):
            n += 1
            if m.group(1) not in ev:
                a = max(0, m.start() - 18)
                near = prose[a:m.end() + 12].strip()
                bad.append('%s: 날짜 %s — 근거가 없다 (앞뒤: …%s…)'
                           % (name, m.group(1), near))
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


def counts_in(prose):
    """산문의 드론 대수(≥ 100) → [(글자 그대로, 위치)]. O(산문 길이)."""
    return [(m.group(1), m.start()) for m in COUNT.finditer(prose)]


def count_known(c, ev):
    """근거 글에 이 수가 쉼표가 있든 없든 따로 떨어져 있는가.

    '1,218' 은 '1218' 로도 찾는다(표는 쉼표 없이 적는다). 더 긴 수의
    일부('11218')는 근거가 아니다."""
    plain = c.replace(',', '')
    for form in set((c, plain)):
        if re.search(r'(?<![\d,.])%s(?![\d,])' % re.escape(form), ev):
            return True
    return False


def articles_in(prose):
    """산문의 조문 번호 → [(정규형, 위치)]. '§ 107.29' 는 '§107.29' 로."""
    return [(m.group(0).replace(' ', ''), m.start())
            for m in ARTICLE.finditer(prose)]


def allowed_counts():
    p = os.path.join(HERE, 'counts_ok.txt')
    if not os.path.exists(p):
        return set()
    return set(l.split('#')[0].strip() for l in read(p).split('\n')
               if l.split('#')[0].strip())


def _sections():
    if not os.path.isdir(SECTIONS):
        return []
    return [(n, prose_of(read(os.path.join(SECTIONS, n))))
            for n in sorted(os.listdir(SECTIONS)) if n.endswith('.html')]


def check_counts():
    """조각 산문의 드론 대수가 근거 글에 있는가."""
    ev, ok = evidence_text(), allowed_counts()
    bad, n = [], 0
    for name, prose in _sections():
        for c, at in counts_in(prose):
            if c in ok or c.replace(',', '') in ok:
                continue
            n += 1
            if not count_known(c, ev):
                near = prose[max(0, at - 18):at + len(c) + 10].strip()
                bad.append('%s: %s대 — 근거가 없다 (앞뒤: …%s…)'
                           % (name, c, near))
    return bad, n


def check_articles():
    """조각 산문의 조문 번호가 근거 글에 있는가."""
    ev = evidence_text()
    evn = ev.replace('§ ', '§')
    bad, n = [], 0
    for name, prose in _sections():
        for a, at in articles_in(prose):
            n += 1
            if a not in evn:
                near = prose[max(0, at - 18):at + len(a) + 10].strip()
                bad.append('%s: %s — 근거가 없다 (앞뒤: …%s…)'
                           % (name, a, near))
    return bad, n


def main():
    sbad, sn = check_cites()
    kbad, kn = check_cite_keys()
    ybad, yn = check_years()
    cbad, cn = check_counts()
    abad, an = check_articles()
    allbad = sbad + kbad + ybad + cbad + abad
    for line in allbad:
        print('  ✗ ' + line)
    print('문서 절 인용 %d건 · 인용 키 %d개 · 연도·날짜 %d건 · 대수 %d건 · '
          '조문 %d건 — 근거 없음 %d건' % (sn, kn, yn, cn, an, len(allbad)))
    return 1 if allbad else 0


if __name__ == '__main__':
    sys.exit(main())
