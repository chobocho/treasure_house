#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""정리 검사 — 덱의 정리·증명이 data/theorems.tsv 와 맞고, 증명의 규칙을 지키는가.

    python3 deck/check_thm.py [--skeleton]

이 덱은 대학 1학년이 읽을 수 있는 증명을 약속한다(PLAN.md §0.6). 그
약속은 문장으로만 두면 반드시 새어 나간다 — 2학년 과정의 정리를 슬쩍
끌어다 쓰는 증명, 증인 시험이 없는 "증명 끝", 표와 다른 문장. 그래서
기계로 옮겼다. 두 가지를 본다.

  표(theorems.tsv) —
    · id 는 하나씩, level 은 1학년·심화, proof-kind 는 full·sketch·cited
    · prerequisites 의 id 가 표에 있고, 1학년 증명이 심화 결과를 쓰지 않는다
    · full 은 증인 시험(py/tests/…::test_이름)을 가져야 하고, 그 파일과
      그 이름의 def 가 진짜 있어야 한다
    · cited 는 cite-key 를 가져야 하고, 그 키가 cite_keys.tsv 에 있어야 한다
  조각(sections/*.html) —
    · <!--THM id=…--> 의 id 가 표에 있다
    · class="proof" 가 있는 장은 등급 배지가 정확히 하나다
      (THM 상자나 'cont' 머리가 배지를 낸다)
    · --skeleton 이 아니면 표의 정리가 전부 한 번 이상 덱에 나온다

뜻이 맞는지(그 단계가 정말 앞 단계에서 나오는지)는 기계가 못 본다 —
증명 감사(PLAN.md §5 14단계)가 사람 눈으로 본다. 시간 O(표 + 조각 크기).
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
LEVELS = ('1학년', '심화')
KINDS = ('full', 'sketch', 'cited')
COLS = ('id', 'statement', 'level', 'proof-kind', 'prerequisites',
        'witness-test', 'cite-key')
ART = re.compile(r'<article[^>]*id="([^"]+)"[^>]*>(.*?)</article>', re.S)
THM = re.compile(r'<!--THM id=(\S+?)(\s+cont)?-->')


def _ids(cell):
    return [x.strip() for x in (cell or '').split(',')
            if x.strip() and x.strip() != '-']


def witness_ok(base, w):
    """'py/tests/test_x.py::test_a' 가 가리키는 def 가 진짜 있는가."""
    if '::' not in w:
        return False
    path, name = w.split('::', 1)
    name = name.split('::')[-1]
    p = os.path.join(base, path)
    if not os.path.exists(p):
        return False
    text = io.open(p, encoding='utf-8').read()
    if path.endswith('.js'):
        return re.search(r"test\(\s*['\"]%s['\"]" % re.escape(name),
                         text) is not None
    return re.search(r'^\s*def %s\b' % re.escape(name), text, re.M) is not None


def tsv_errors(rows, base):
    """표의 규칙 위반을 한 줄씩. O(행 수 × 선행 수)."""
    bad, seen = [], {}
    keys = cites.index(base)
    for r in rows:
        tid = r.get('id', '')
        if tid in seen:
            bad.append('%s 가 두 번 적혔다' % tid)
        seen[tid] = r
    for r in rows:
        tid = r.get('id', '')
        for c in COLS:
            if c not in r:
                bad.append('%s: 칸 %s 가 없다' % (tid, c))
        if r.get('level') not in LEVELS:
            bad.append('%s: level %r — 1학년·심화 중 하나' % (tid, r.get('level')))
        kind = r.get('proof-kind')
        if kind not in KINDS:
            bad.append('%s: proof-kind %r — full·sketch·cited 중 하나'
                       % (tid, kind))
        if not (r.get('statement') or '').strip():
            bad.append('%s: statement 가 비었다' % tid)
        for pre in _ids(r.get('prerequisites')):
            if pre not in seen:
                bad.append('%s: 선행 정리 %s 가 표에 없다' % (tid, pre))
            elif (r.get('level') == '1학년' and kind == 'full'
                  and seen[pre].get('level') == '심화'):
                bad.append('%s: 1학년 증명이 심화 결과 %s 를 쓴다' % (tid, pre))
        w = (r.get('witness-test') or '').strip()
        if kind == 'full':
            if not w or w == '-':
                bad.append('%s: full 증명인데 증인 시험이 없다' % tid)
            elif not witness_ok(base, w):
                bad.append('%s: 증인 시험 %s 를 찾을 수 없다' % (tid, w))
        elif w and w != '-' and not witness_ok(base, w):
            bad.append('%s: 증인 시험 %s 를 찾을 수 없다' % (tid, w))
        ck = (r.get('cite-key') or '').strip()
        if kind == 'cited' and (not ck or ck == '-'):
            bad.append('%s: cited 인데 cite-key 가 없다' % tid)
        for k in _ids(ck):
            if k not in keys:
                bad.append('%s: cite-key %s 가 cite_keys.tsv 에 없다' % (tid, k))
    return bad


def section_errors(texts, rows, skeleton):
    """조각의 THM·증명 장 규칙 위반을 한 줄씩. texts: {파일 이름: 본문}."""
    bad, used = [], set()
    known = set(r.get('id') for r in rows)
    for name in sorted(texts):
        for m in ART.finditer(texts[name]):
            aid, inner = m.group(1), m.group(2)
            refs = THM.findall(inner)
            for tid, _cont in refs:
                used.add(tid)
                if tid not in known:
                    bad.append('%s: #%s 의 THM %s 가 theorems.tsv 에 없다'
                               % (name, aid, tid))
            if 'class="proof' in inner:
                n = len(refs) + len(re.findall(r'class="lv (?:l1|adv)"', inner))
                if n != 1:
                    bad.append('%s: #%s 는 증명 장인데 등급 배지가 %d개 '
                               '(정확히 하나)' % (name, aid, n))
    if not skeleton:
        for tid in sorted(known - used):
            bad.append('theorems.tsv 의 %s 가 덱 어디에도 없다' % tid)
    return bad


def main(argv):
    rows = cites.rows(BASE, 'theorems.tsv')
    texts = {}
    for name in sorted(os.listdir(SECTIONS)):
        if name.endswith('.html'):
            texts[name] = io.open(os.path.join(SECTIONS, name),
                                  encoding='utf-8').read()
    bad = tsv_errors(rows, BASE) + section_errors(
        texts, rows, '--skeleton' in argv)
    for line in bad:
        print('  ✗ ' + line)
    full = sum(1 for r in rows if r.get('proof-kind') == 'full')
    print('정리 %d개(완전 증명 %d개) — 어긋남 %d건' % (len(rows), full, len(bad)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
