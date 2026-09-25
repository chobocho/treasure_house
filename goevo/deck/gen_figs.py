#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""이 덱의 도해 — data/·out/ 에서만 그린다 (PLAN.md §3.5).

    python3 deck/gen_figs.py            # deck/figs/*.svg 를 다시 만든다
    python3 deck/gen_figs.py --check    # 지금 것과 같은지만 본다

그림은 손으로 그리지 않는다. 점 하나, 막대 하나가 모두 data/*.tsv 의 한
행이다 — 릴리스 날짜는 releases.tsv, API 증가는 api_added.tsv. 그림이
가정하는 것(예: 큰 릴리스는 28개 이상, 1.28 은 아직 초안)은 need() 로
적어 두고, 자료가 바뀌어 가정이 깨지면 그림을 만들지 않는다.

viewBox 폭은 340(svgkit.W). 글자는 svgkit 의 클래스로만 적는다.
git/deck/gen_figs.py 의 틀(FIGURES·need·--check)을 물려받았다.
"""
import datetime
import io
import math
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


def minor_of(version):
    """'go1' → 0, 'go1.22.0' → 22."""
    parts = version[2:].split('.')
    return 0 if len(parts) == 1 else int(parts[1])


@fig('cadence')
def cadence():
    """큰 릴리스마다 점 하나 — 가로는 날짜, 세로는 1.N 의 N."""
    rel = [r for r in tsv('releases.tsv') if r['kind'] == 'major']
    need(len(rel) >= 28, '큰 릴리스가 28개 이상(go1 … go1.27)')
    draft = [r for r in tsv('timeline.tsv') if r['event'].startswith(
        'Go 1.28 예정')]
    need(len(draft) == 1, '연표에 1.28 초안 예정 행이 하나')
    f = Fig(h=210, title='Go 1 이후 큰 릴리스의 날짜')
    ax = Axes(f, 34, 14, 292, 150, (2012, 2027.5), (0, 29))
    ax.grid(xs=range(2012, 2028, 2), ys=range(0, 29, 4))
    ax.frame()
    ax.xticks(range(2012, 2028, 2), '%d', '출시 연도')
    ax.yticks(range(0, 29, 4), '1.%d', '')
    pts = [(year_frac(r['date']), minor_of(r['version'])) for r in rel]
    ax.curve(pts, 'cvd')
    ax.dots(pts, 2.0, 'dot')
    x, y = ax.at(year_frac(draft[0]['date']), 28)
    f.circle(x, y, 2.4, 'dotn')
    # 글자는 점들과 겹치지 않게 왼편 빈자리에 두고 화살표로 잇는다
    f.text(ax.at(2025.4, 28)[0], y + 3, '1.28 초안 →', 'tick', 'end')
    f.text(40, 26, '점 하나 = 큰 릴리스 하나 (releases.tsv)', 'cap', 'start')
    return f


@fig('api_growth')
def api_growth():
    """버전마다 API 목록에 새로 오른 기호 — syscall 을 뺀 막대 + 전체 점.

    봉우리(1.1·1.13·1.14·1.16·1.20)는 새 플랫폼 이식이 syscall 상수를
    수천 개 올린 것이다. 막대를 syscall 을 뺀 수로 그리고, 전체는 점으로
    얹어 둘을 가른다. 세로는 로그 눈금이다."""
    rows = tsv('api_added.tsv')
    need(rows[0]['version'] == '1.0', '첫 행이 Go 1(1.0)')
    go1 = rows[0]
    rows = rows[1:]
    tot = [int(r['new-symbols']) for r in rows]
    sysc = [int(r['syscall-symbols']) for r in rows]
    rest = [t - c for t, c in zip(tot, sysc)]
    need(min(rest) >= 10 and max(tot) < 20000, '기호 수가 10~20000 사이')
    f = Fig(h=232, title='버전마다 API 목록에 오른 기호 수')
    ax = Axes(f, 38, 14, 290, 150, (0, len(rows)), (10, 20000), ylog=True)
    ax.grid(ys=(100, 1000, 10000))
    ax.frame()
    ax.yticks((10, 100, 1000, 10000), '%d', '')
    bw = 290.0 / len(rows)
    for i, r in enumerate(rows):
        x0, y0 = ax.at(i + 0.15, rest[i])
        _, yb = ax.at(i, 10)
        f.rect(x0, y0, bw * 0.7, yb - y0, 'bar')
        if sysc[i]:
            xc, yc = ax.at(i + 0.5, tot[i])
            f.circle(xc, yc, 2.2, 'dot5')
        if i % 2 == 0 or r['version'] == '1.27':
            f.text(x0 + bw * 0.35, 176, r['version'][2:], 'tick')
    # 범례는 그림 아래에 — 위쪽 왼편은 1.1 의 점(7918)과 겹친다
    f.rect(40, 186, 9, 7, 'bar key')          # 범례의 견본 막대
    f.text(53, 193, '막대 = syscall 을 뺀 새 기호', 'cap', 'start')
    f.circle(188, 189.5, 2.2, 'dot5 key')      # 범례의 견본 점
    f.text(194, 193, '점 = syscall 까지 더한 전체', 'cap', 'start')
    f.text(183, 208, '버전(1.N 의 N) — Go 1 은 그림 밖(%s개, syscall %s개)'
           % (go1['new-symbols'], go1['syscall-symbols']), 'cap')
    f.text(183, 222, '출처: api/go1.N.txt (플랫폼 꼬리를 뗀 기호 수)', 'cap')
    return f


LADDER_COLS = ['1.%d' % n for n in range(8, 28)]


def vkey(v):
    return tuple(int(x) for x in v.split('.'))


def ladder_rows():
    """out/ladder_data.txt — exps/p10.py 가 실제로 돌려 확인한 (예제, 판, 이름)."""
    with io.open(os.path.join(OUT, 'ladder_data.txt'), encoding='utf-8') as f:
        return [tuple(l.rstrip('\n').split('\t')) for l in f if l.strip()]


@fig('ladder')
def ladder():
    """go.mod 의 go 줄 사다리 — 가로는 go 줄(1.8…1.27), 세로는 기능.

    칸이 칠해졌으면 그 go 줄에서 컴파일된다. 칸의 시작은 exps/p10 이
    '막는 판에서 통과, 한 판 아래에서 거절' 을 돌려 본 결과다."""
    rows = ladder_rows()
    need(len(rows) >= 14, '사다리 기능이 14개 이상')
    need(all(vkey(g) >= (1, 9) for _, g, _ in rows), '막는 판이 1.9 이상')
    x0, y0, cw, rh = 118, 22, 10.5, 11
    f = Fig(h=y0 + rh * len(rows) + 34, title='go.mod 의 go 줄 사다리')
    for j, c in enumerate(LADDER_COLS):
        if (j % 3 == 0 and c != '1.26') or c == '1.27':
            f.text(x0 + j * cw + cw / 2, y0 - 6, c[2:], 'tick')
    for i, (_, gate, name) in enumerate(rows):
        y = y0 + i * rh
        f.text(x0 - 4, y + 8, name, 'tick', 'end')
        for j, c in enumerate(LADDER_COLS):
            cls = 'cell on' if vkey(c) >= vkey(gate) else 'cell off'
            f.rect(x0 + j * cw, y, cw - 1, rh - 1.5, cls)
    yb = y0 + rh * len(rows)
    f.text(x0 + len(LADDER_COLS) * cw / 2, yb + 12,
           'go.mod 의 go 1.N (N) — 칠한 칸 = 그 줄에서 컴파일된다', 'cap')
    f.text(x0 + len(LADDER_COLS) * cw / 2, yb + 25,
           '출처: go 1.27.1 로 돌린 out/10-ladder-*', 'cap')
    return f


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
