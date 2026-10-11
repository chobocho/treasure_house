#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_data — 받아 둔 문서(docs/)에서 덱이 쓰는 표를 만들고, 손으로 적은 표를 대조한다.

   덱에서 가장 틀리기 쉬운 것은 코드가 아니라 "몇 버전" 과 "몇 년" 이다.
   그래서 날짜는 공식 RELEASES.md 에서 만들고(releases.tsv), "이 문법은 1.N 부터"
   는 그 버전의 릴리스 노트 절에서 근거 정규식이 맞아야 하며(features.tsv),
   역사 주장은 출처 글에서 근거가 맞아야 한다(facts.tsv → evidence.tsv).

     python3 tools/make_data.py           data/releases.tsv · data/evidence.tsv 를 만든다
     python3 tools/make_data.py --check   만든 표가 최신인지 + features·facts 근거 대조
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEADING = re.compile(r'^Version (\d[^\s(]*)\s+\((\d{4}-\d{2}-\d{2})\)\s*$', re.M)
MAX_EVIDENCE = 300


def short(v):
    """1.65.0 → 1.65, 1.62.1 → 그대로, 0.12.0 → 0.12, 시험판(-alpha)은 그대로."""
    m = re.match(r'^(\d+\.\d+)\.0$', v)
    return m.group(1) if m else v


def parse_releases(text):
    """[(버전, 날짜)] — 파일에 나온 순서(최신이 먼저)."""
    return [(short(m.group(1)), m.group(2)) for m in HEADING.finditer(text)]


def sections(text):
    """{버전: 그 버전의 릴리스 노트 본문}. O(n)."""
    out = {}
    ms = list(HEADING.finditer(text))
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        out[short(m.group(1))] = text[m.end():end]
    return out


def releases_tsv(text):
    return 'version\tdate\n' + ''.join('%s\t%s\n' % r for r in parse_releases(text))


def read_tsv(path):
    if not os.path.isfile(path):
        return []
    with io.open(path, encoding='utf-8') as f:
        lines = [ln for ln in f.read().split('\n') if ln and not ln.startswith('#')]
    if not lines:
        return []
    head = lines[0].split('\t')
    return [dict(zip(head, ln.split('\t') + [''] * len(head))) for ln in lines[1:]]


def check_features(rows, secs):
    """features.tsv 의 각 행 — 근거 정규식이 '그 버전' 의 릴리스 노트에 있어야 한다."""
    errs, seen = [], set()
    for r in rows:
        key, v, ev = r.get('key', ''), r.get('version', ''), r.get('evidence', '')
        if key in seen:
            errs.append('features: 키가 겹친다 — %s' % key)
            continue
        seen.add(key)
        if v not in secs:
            errs.append('features: %s — 릴리스 노트에 없는 버전 %s' % (key, v))
            continue
        if not ev:
            errs.append('features: %s — 근거(evidence)가 비었다' % key)
            continue
        try:
            found = re.search(ev, secs[v], re.I | re.S)
        except re.error as e:
            errs.append('features: %s — 정규식 오류 %s' % (key, e))
            continue
        if not found:
            errs.append('features: %s — %s 의 릴리스 노트에 /%s/ 가 없다' % (key, v, ev))
    return errs


def match_facts(rows, docs):
    """facts.tsv → ([(id, 출처, 맞은 글)], 오류). 맞은 글은 공백을 하나로 줄이고 300자에서 끊는다."""
    out, errs, cache = [], [], {}
    for r in rows:
        fid, src, ev = r.get('id', ''), r.get('source', ''), r.get('evidence', '')
        if src not in cache:
            p = os.path.join(docs, src + '.txt')
            if os.path.isfile(p):
                with io.open(p, encoding='utf-8') as f:
                    cache[src] = f.read()
            else:
                cache[src] = None
        if cache[src] is None:
            errs.append('facts: %s — 받아 둔 출처가 없다(docs/%s.txt, make docs)' % (fid, src))
            continue
        try:
            # 받아 둔 글은 문장 가운데서 줄이 바뀐다. 근거의 공백 하나는 공백 연속과 맞춘다.
            m = re.search(ev.replace(' ', r'\s+'), cache[src], re.S) if ev else None
        except re.error as e:
            errs.append('facts: %s — 정규식 오류 %s' % (fid, e))
            continue
        if not m:
            errs.append('facts: %s — 출처 %s 에 /%s/ 가 없다' % (fid, src, ev))
            continue
        out.append((fid, src, re.sub(r'\s+', ' ', m.group(0)).strip()[:MAX_EVIDENCE]))
    return out, errs


def evidence_tsv(ev):
    return 'id\tsource\tmatched\n' + ''.join('%s\t%s\t%s\n' % e for e in ev)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    check = '--check' in argv
    data, docs = os.path.join(ROOT, 'data'), os.path.join(ROOT, 'docs')
    rel_src = os.path.join(docs, 'releases.txt')
    if not os.path.isfile(rel_src):
        print('  ✗ docs/releases.txt 가 없다 — make docs 를 먼저 돌린다')
        return 1
    with io.open(rel_src, encoding='utf-8') as f:
        rel = f.read()
    want = {'releases.tsv': releases_tsv(rel)}
    ev, errs = match_facts(read_tsv(os.path.join(data, 'facts.tsv')), docs)
    want['evidence.tsv'] = evidence_tsv(ev)
    feats = read_tsv(os.path.join(data, 'features.tsv'))
    errs += check_features(feats, sections(rel))
    for name, text in sorted(want.items()):
        p = os.path.join(data, name)
        if check:
            old = io.open(p, encoding='utf-8').read() if os.path.isfile(p) else None
            if old != text:
                errs.append('data/%s 가 docs/ 와 다르다 — make data' % name)
        else:
            with io.open(p, 'w', encoding='utf-8', newline='') as f:
                f.write(text)
    for e in errs:
        print('  ✗ ' + e)
    print('  릴리스 %d개 · 버전 표기 %d건 · 역사 근거 %d건 — 오류 %d건'
          % (len(parse_releases(rel)), len(feats), len(ev), len(errs)))
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main())
