#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""이 덱의 도해 — data/·out/ 에서만 그린다 (PLAN.md §3.5).

    python3 deck/gen_figs.py            # deck/figs/*.svg 를 다시 만든다
    python3 deck/gen_figs.py --check    # 지금 것과 같은지만 본다

그림은 손으로 그리지 않는다. 점 하나, 막대 하나가 모두 data/*.tsv 의 한
행이다 — 버전 날짜는 releases.tsv, 기능 게이트는 langgates.tsv. 그림이
가정하는 것(예: C# 버전은 1.0 부터 14 까지 18개)은 need() 로
적어 두고, 자료가 바뀌어 가정이 깨지면 그림을 만들지 않는다.

viewBox 폭은 340(svgkit.W). 글자는 svgkit 의 클래스로만 적는다.
git/deck/gen_figs.py 의 틀(FIGURES·need·--check)을 물려받았다.
"""
import datetime
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, 'data')
OUT = os.path.join(BASE, 'out')
FIGS = os.path.join(HERE, 'figs')
sys.path.insert(0, HERE)
import svgkit                                           # noqa: E402
from svgkit import Axes, Fig                            # noqa: E402

FIGURES = {}


def fig(name):
    def deco(fn):
        FIGURES[name] = fn
        return fn
    return deco


def need(cond, what):
    """그림의 가정이 자료와 맞는지. 어긋나면 그림을 만들지 않는다."""
    if not cond:
        raise SystemExit('gen_figs: 자료가 그림의 가정과 다르다 — ' + what)


def tsv(name):
    """data/<name> — '#' 줄을 건너뛰고 머리줄을 열쇠로 한 dict 들."""
    rows, head = [], None
    with io.open(os.path.join(DATA, name), encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line or line.startswith('#'):
                continue
            cols = line.split('\t')
            if head is None:
                head = cols
            else:
                rows.append(dict(zip(head, cols)))
    return rows


def year_frac(date):
    """'2012-03-28' · '2027-02' → 연도 + 그해의 몇 분의 몇 (x 축 값)."""
    parts = [int(x) for x in date.split('-')] + [1]
    y, m, d = parts[0], parts[1], parts[2]
    start = datetime.date(y, 1, 1)
    days = (datetime.date(y + 1, 1, 1) - start).days
    return y + (datetime.date(y, m, d) - start).days / float(days)


# 그림 함수(@fig)는 6단계에서 goevo/deck/gen_figs.py 를 본떠 C# 자료로 더한다.


def render_all():
    made = {}
    for name in sorted(FIGURES):
        made[name + '.svg'] = FIGURES[name]().render() + '\n'
    return made


def main(argv):
    made = render_all()
    if '--check' in argv:
        bad = []
        for name, want in sorted(made.items()):
            p = os.path.join(FIGS, name)
            cur = ''
            if os.path.exists(p):
                with io.open(p, encoding='utf-8') as f:
                    cur = f.read()
            if cur != want:
                bad.append(name)
        for name in bad:
            print('  ✗ %s 가 자료와 어긋난다' % name)
        print('그림 %d장 — 어긋남 %d건' % (len(made), len(bad)))
        return 1 if bad else 0
    os.makedirs(FIGS, exist_ok=True)
    for name, text in sorted(made.items()):
        with io.open(os.path.join(FIGS, name), 'w', encoding='utf-8',
                     newline='\n') as f:
            f.write(text)
    print('그림 %d장 → deck/figs/' % len(made))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
