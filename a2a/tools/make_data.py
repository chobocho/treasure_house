#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_data — 손으로 적은 역사 주장(data/facts.tsv)을 받아 둔 출처 글
(docs/<source>.txt)에 대 보고, 맞은 글을 data/evidence.tsv 로 남긴다.

   덱에서 가장 틀리기 쉬운 것은 코드가 아니라 "언제·누가·몇 곳" 이다.
   그래서 1부의 주장은 출처 글에서 근거 정규식이 맞아야만 FACT 로 쓸 수
   있다(조립기가 evidence.tsv 에 없는 FACT 를 막는다). ../rust 의 같은
   이름 도구에서 릴리스 표 부분을 덜어 낸 것이다.

     python3 tools/make_data.py           data/evidence.tsv 를 만든다
     python3 tools/make_data.py --check   evidence.tsv 가 최신인지 + 근거 대조
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_EVIDENCE = 300


def read_tsv(path):
    if not os.path.isfile(path):
        return []
    with io.open(path, encoding='utf-8') as f:
        lines = [ln for ln in f.read().split('\n')
                 if ln and not ln.startswith('#')]
    if not lines:
        return []
    head = lines[0].split('\t')
    return [dict(zip(head, ln.split('\t') + [''] * len(head)))
            for ln in lines[1:]]


def check_sources(rows, sources):
    """facts.tsv 의 출처 키가 sources.tsv 에 있어야 한다(출처 목록에 실린다)."""
    keys = {s.get('key') for s in sources}
    return ['facts: %s — sources.tsv 에 없는 출처 %s' % (r['id'], r['source'])
            for r in rows if r.get('source') not in keys]


def match_facts(rows, docs):
    """facts.tsv → ([(id, 출처, 맞은 글)], 오류).

    맞은 글은 공백을 하나로 줄이고 300자에서 끊는다. O(주장 수 × 글 길이).
    """
    out, errs, cache, seen = [], [], {}, set()
    for r in rows:
        fid, src, ev = r.get('id', ''), r.get('source', ''), r.get('evidence', '')
        if fid in seen:
            errs.append('facts: id 가 겹친다 — %s' % fid)
            continue
        seen.add(fid)
        if src not in cache:
            p = os.path.join(docs, src + '.txt')
            if os.path.isfile(p):
                with io.open(p, encoding='utf-8') as f:
                    cache[src] = f.read()
            else:
                cache[src] = None
        if cache[src] is None:
            errs.append('facts: %s — 받아 둔 출처가 없다(docs/%s.txt, make sources)'
                        % (fid, src))
            continue
        if not ev:
            errs.append('facts: %s — 근거(evidence)가 비었다' % fid)
            continue
        try:
            # 받아 둔 글은 문장 가운데서 줄이 바뀐다. 근거의 공백 하나는 공백 연속과 맞춘다.
            m = re.search(ev.replace(' ', r'\s+'), cache[src], re.S)
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
    facts = read_tsv(os.path.join(data, 'facts.tsv'))
    errs = check_sources(facts, read_tsv(os.path.join(data, 'sources.tsv')))
    ev, more = match_facts(facts, docs)
    errs += more
    text = evidence_tsv(ev)
    p = os.path.join(data, 'evidence.tsv')
    if check:
        old = io.open(p, encoding='utf-8').read() if os.path.isfile(p) else None
        if old != text:
            errs.append('data/evidence.tsv 가 facts.tsv·docs/ 와 다르다 — make data')
    else:
        with io.open(p, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
    for e in errs:
        print('  ✗ ' + e)
    print('  역사 근거 %d건 — 오류 %d건' % (len(ev), len(errs)))
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main())
