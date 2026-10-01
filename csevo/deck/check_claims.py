#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사실 검사 — 덱이 적은 문서 절·연도·버전이 근거를 갖고 있는가.

    python3 deck/check_claims.py

이 덱이 가장 쉽게 틀릴 자리는 코드가 아니라 문장이다. "2002년 2월 13일",
"C# 12 문서의 그 절", "튜플은 C# 7.0 에 들어왔다" — 전부 기억으로 적으면
반드시 어딘가 어긋나고, 어긋나도 아무 시험이 빨개지지 않는다. 그래서
규칙으로 옮겼다. (goevo 덱의 검사를 물려받아 C# 의 문서와 버전에 맞춘
것이다 — PLAN.md §0.3–0.4.)

세 가지를 본다.

  1. **문서 절** — 조립기가 남긴 deck/cite_used.txt 의 (키·절) 이
     받아 둔 문서에 진짜 있는가. 키 해석과 절 규칙은 deck/cites.py 하나가
     정한다(보통 문서는 '§<TAB>제목' 줄, API 목록은 한 줄 전체).
     docs/ 는 커밋하지 않는 캐시라 비어 있으면 `make docs` 로 받는다.
  2. **연도·날짜** — 조각 파일의 산문에 적힌 네 자리 연도와 날짜가
     deck/claims/*.md 나 data/*.tsv 에 적혀 있는가. 없으면 기억에서 나온 것이다.
  3. **버전** — 산문의 'C# N' · 'C# N.M' 이 releases.tsv 의 버전이거나
     claims 에 'C# N' 으로 적힌 것인가(C# 15 처럼 아직 안 나온 것). 끝의
     .0 은 있어도 없어도 같다(cites.vnorm). "C# 7.2 에 들어왔다" 를
     "C# 7.3" 으로 잘못 적은 것은 이 검사가 못 잡는다 — 그것은 기능 표의
     버전 칸(data-check)과 배지(check_xref)가 잡는다. 여기서는 없는 버전
     ("C# 7.4")과 오타를 잡는다.

연도처럼 보이지만 연도가 아닌 수(2048 바이트)는 단위를 보고 거르고,
그래도 남는 것은 deck/years_ok.txt 에 적는다. 버전은 'C#' 이 앞에 붙은
것만 보므로 'TLS 1.3' · '.NET 8' 은 걸리지 않는다(.NET 판은 3단계에서
dotnet.tsv 와 대조한다). deck/versions_ok.txt 는 'C# 언어' 처럼 C# 뒤에 오는
수가 버전이 아닌 낱말을 적는 곳이다.

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
# 산문의 C# 버전 — 'C#' 바로 뒤(공백 하나까지)의 N 또는 N.M. 뒤에 숫자나
# 영문, '.숫자' 가 이어지면 아니다(C# 1.5.2 는 버전 꼴이 아니다). 한글은
# 막지 않는다 — 'C# 9에서' 처럼 조사가 바로 붙는 것이 보통이기 때문이다.
VERSION = re.compile(r'(?<![\w#])C#\s?(\d{1,2}(?:\.\d)?)'
                     r'(?![\dA-Za-z_%]|\.\d)')
NOT_VERSION_AFTER = re.compile(r'\s*(배|초|퍼센트|칸|줄|장|개|MB|KB|GB|ms)')
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
    data/*.tsv 와 부마다의 data/features/*.tsv 전부."""
    parts = []
    p = os.path.join(HERE, 'claims.md')
    if os.path.exists(p):
        parts.append(read(p))
    for d, ext in ((os.path.join(HERE, 'claims'), '.md'),
                   (DATA, '.tsv'), (os.path.join(DATA, 'features'), '.tsv')):
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


def versions_in(prose, skip_words=()):
    """산문에서 'C# N' 꼴 → [(버전, 위치)]. O(산문 길이).

    skip_words 는 'C#' 과 수 사이에 오면 버전이 아닌 낱말이다 — 정규식이
    공백 하나만 허용하므로 'C# 언어 7.3' 은 애초에 안 걸린다. 남겨 둔
    것은 goevo 와 같은 자리(deck/versions_ok.txt)를 쓰기 위해서다."""
    out = []
    for m in VERSION.finditer(prose):
        if NOT_VERSION_AFTER.match(prose[m.end():m.end() + 6]):
            continue
        out.append((m.group(1), m.start(1)))
    return out


def known_versions(releases, claims_text):
    """근거로 인정하는 버전들(끝의 .0 을 뗀 꼴) — releases.tsv 의 버전 칸과
    claims 글에 'C# N' 으로 적힌 것. O(행 수 + 글 길이)."""
    out = set(cites.vnorm(r['version']) for r in releases if r.get('version'))
    out.update(cites.vnorm(v) for v in
               re.findall(r'(?<![\w#])C#\s?(\d{1,2}(?:\.\d)?)(?!\d|\.\d)',
                          claims_text))
    return out


def version_known(v, known):
    """이 버전이 근거 집합에 있는가. '8.0' 과 '8' 은 같다."""
    return cites.vnorm(v) in known


def allowed_version_words():
    p = os.path.join(HERE, 'versions_ok.txt')
    if not os.path.exists(p):
        return set()
    return set(l.split('#')[0].strip() for l in read(p).split('\n')
               if l.split('#')[0].strip())


def check_versions():
    """조각 산문의 C# 버전이 근거에 있는가."""
    ev = known_versions(cites._rows(BASE, 'releases.tsv'), evidence_text())
    words = allowed_version_words()
    bad, n = [], 0
    if not os.path.isdir(SECTIONS):
        return bad, n
    for name in sorted(os.listdir(SECTIONS)):
        if not name.endswith('.html'):
            continue
        prose = prose_of(read(os.path.join(SECTIONS, name)))
        for v, at in versions_in(prose, words):
            n += 1
            if not version_known(v, ev):
                near = prose[max(0, at - 18):at + len(v) + 12].strip()
                bad.append('%s: 버전 %s — 근거가 없다 (앞뒤: …%s…)'
                           % (name, v, near))
    return bad, n


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


def main():
    sbad, sn = check_cites()
    kbad, kn = check_cite_keys()
    ybad, yn = check_years()
    vbad, vn = check_versions()
    allbad = sbad + kbad + ybad + vbad
    for line in allbad:
        print('  ✗ ' + line)
    print('문서 절 인용 %d건 · 인용 키 %d개 · 연도·날짜 %d건 · 버전 %d건'
          ' — 근거 없음 %d건' % (sn, kn, yn, vn, len(allbad)))
    return 1 if allbad else 0


if __name__ == '__main__':
    sys.exit(main())
