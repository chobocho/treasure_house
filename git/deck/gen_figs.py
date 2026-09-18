#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""덱에 실을 그림(SVG)을 만든다. 손으로 그리지 않는다.

    python3 deck/gen_figs.py            # deck/figs/*.svg 를 다시 만든다
    python3 deck/gen_figs.py --check    # 지금 것과 같은지만 본다

그림에 찍히는 객체 이름·크기·개수·날짜는 전부 run_all.py 가 남긴
out/ 의 캡처, tools/make_golden.py 가 진짜 git 으로 만든 golden/,
data/*.tsv 에서 읽는다(PLAN.md §4). 손으로 적은 것은 배치(좌표)와
설명 글뿐이다. 캡처가 바뀌어 그림의 가정(커밋 둘, 트리 셋 …)이
깨지면 조용히 틀린 그림을 내지 않고 여기서 멈춘다(need()).

세 영역 그림 하나만 설명용(ill)이다 — 명령과 화살표의 대응은 6부의
캡처들이 뒷받침한다.

만든 뒤에는 **눈으로 본다**. `make figs-png` 가 .svgrender/ 에 PNG 를
뽑는다. 글자가 겹치거나 축이 잘리는 것은 기계가 못 잡는다.
(transformer/deck/gen_figs.py 의 틀을 물려받았다.)
"""
import io
import os
import re
import sys
import zlib
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
FIGS = os.path.join(HERE, 'figs')
OUT = os.path.join(BASE, 'out')
GOLDEN = os.path.join(BASE, 'golden')
DATA = os.path.join(BASE, 'data')
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(BASE, 'py'))

from svgkit import Axes, Fig                          # noqa: E402
from mygit import pack as P                           # noqa: E402

FIGURES = {}


def fig(name):
    def deco(fn):
        FIGURES[name] = fn
        return fn
    return deco


def need(cond, what):
    """그림의 가정이 캡처와 맞는지. 어긋나면 그림을 만들지 않는다."""
    if not cond:
        raise SystemExit('gen_figs: 캡처가 그림의 가정과 다르다 — '
                         + what)


def cap(name):
    """out/<name> 의 줄들 — 첫 줄 '$ 명령' 은 뗀다."""
    text = io.open(os.path.join(OUT, name), encoding='utf-8').read()
    lines = text.rstrip('\n').split('\n')
    need(lines[0].startswith('$ '), name + ' 의 첫 줄')
    return lines[1:]


def tsv(name):
    """data/<name> — '#' 줄을 건너뛰고 머리줄을 열쇠로 한 dict 들."""
    rows, head = [], None
    for line in io.open(os.path.join(DATA, name), encoding='utf-8'):
        line = line.rstrip('\n')
        if not line or line.startswith('#'):
            continue
        cols = line.split('\t')
        if head is None:
            head = cols
        else:
            rows.append(dict(zip(head, cols)))
    return rows


def tbl(name):
    """out/tbl_<name>.html 의 몸 칸들(머리줄 빼고)."""
    text = io.open(os.path.join(OUT, 'tbl_%s.html' % name),
                   encoding='utf-8').read()
    return [re.findall(r'<td>(.*?)</td>', r)
            for r in re.findall(r'<tr>(.*?)</tr>', text) if '<td>' in r]


def arrow(f, x1, y1, x2, y2, hot=False, dim=False, head=5.0):
    """선 + 끝의 삼각 촉. 촉은 끝점에 닿게 그린다."""
    cls = 'edge' + (' hot' if hot else '') + (' dim' if dim else '')
    dx, dy = x2 - x1, y2 - y1
    n = (dx * dx + dy * dy) ** 0.5 or 1.0
    ux, uy = dx / n, dy / n
    bx, by = x2 - ux * head, y2 - uy * head
    f.line(x1, y1, bx, by, cls)
    w = head * 0.55
    f.poly([(x2, y2), (bx - uy * w, by + ux * w),
            (bx + uy * w, by - ux * w)], 'ah' + (' hot' if hot else ''))


def link(f, p1, p2, r1, r2=None, hot=False, dim=False):
    """두 원(중심 p1·p2, 반지름 r1·r2)의 테두리에서 테두리로 화살표."""
    (x1, y1), (x2, y2) = p1, p2
    r2 = r1 if r2 is None else r2
    dx, dy = x2 - x1, y2 - y1
    n = (dx * dx + dy * dy) ** 0.5 or 1.0
    arrow(f, x1 + dx / n * r1, y1 + dy / n * r1,
          x2 - dx / n * r2, y2 - dy / n * r2, hot, dim)


def node(f, x, y, label, sub='', w=58, h=30, cls='box'):
    """이름표 상자 — 위에 종류(작게), 아래에 이름(고정폭)."""
    f.rect(x - w / 2, y - h / 2, w, h, cls)
    if sub:
        f.text(x, y - 3, sub, 'tick')
        f.text(x, y + 9, label, 'mono')
    else:
        f.text(x, y + 3, label, 'mono')


def ymd(s):
    """'2005-04-07' · '2005-04' · '2005' → 해의 소수(2005.26)."""
    parts = [int(p) for p in s.split('-')]
    y = parts[0]
    m = parts[1] if len(parts) > 1 else 7   # 해만 있으면 한가운데
    d = parts[2] if len(parts) > 2 else 1
    return y + (date(y, m, d).timetuple().tm_yday - 1) / 365.25


# ── 2·3부: hello 저장소의 객체 그래프 ──────────────────────────


@fig('hello_objects')
def hello_objects():
    """커밋 둘 · 트리 셋 · blob 셋 · 태그 하나 — 전부 캡처의 이름."""
    kind = {}
    for line in cap('hello__cat-file-batch-all-objects-batch-check.txt'):
        oid, t, _ = line.split()
        kind[oid[:7]] = t
    log = [re.match(r'(\w+) tree=(\w+) parents=(\S*) ', l).groups()
           for l in cap('hello__log-format-h-tree-t-parents-p-s.txt')]
    need(len(log) == 2 and log[0][2] == log[1][0], '커밋 둘, 부모 하나')
    tag, tagged = [l[:7] for l in
                   cap('hello__rev-parse-v1.0-v1.0-commit.txt')]
    need(tagged == log[0][0], '태그가 새 커밋을 가리킨다')

    def entries(name):
        return [(l.split()[1], l.split()[2], l.split('\t')[1])
                for l in cap(name)]
    new = entries('hello__ls-tree-r-t-abbrev-head.txt')
    old = entries('hello__ls-tree-r-t-abbrev-head-1.txt')
    need([p for _, _, p in new] == ['hello.txt', 'src', 'src/main.c']
         and [p for _, _, p in old] == ['hello.txt'], '트리 모양')
    f = Fig(222, title='hello 저장소의 객체 %d개와 그 사이의 이름'
            % len(kind))
    X = (32, 99, 166, 236, 304)
    c2, c1 = log[0], log[1]
    pos = {tag: (X[0], 45), c2[0]: (X[1], 45), c1[0]: (X[1], 165),
           c2[1]: (X[2], 45), c1[1]: (X[2], 165),
           new[0][1]: (X[3], 20), new[1][1]: (X[3], 80),
           new[2][1]: (X[4], 80), old[0][1]: (X[3], 165)}
    names = {new[0][1]: 'hello.txt', new[1][1]: 'src/',
             new[2][1]: 'main.c', old[0][1]: 'hello.txt'}
    edges = [(tag, c2[0], 'object'), (c2[0], c1[0], 'parent'),
             (c2[0], c2[1], 'tree'), (c1[0], c1[1], 'tree'),
             (c2[1], new[0][1], ''), (c2[1], new[1][1], ''),
             (new[1][1], new[2][1], ''), (c1[1], old[0][1], '')]
    for a, b, lab in edges:
        (xa, ya), (xb, yb) = pos[a], pos[b]
        if xa == xb:
            arrow(f, xa, ya + 15, xb, yb - 15)
            f.text(xa + 4, (ya + yb) / 2 + 3, lab, 'cap', 'start')
        else:                       # 상자 사이가 좁아 이름표는 아래 줄에
            arrow(f, xa + 29, ya, xb - 29, yb)
    need(sorted(pos) == sorted(kind), '그린 객체 = 저장소의 객체 전부')
    tone = {'commit': 'box g3', 'tree': 'box g1', 'blob': 'box g2',
            'tag': 'box g4'}
    for oid, (x, y) in pos.items():
        node(f, x, y, oid, kind[oid], cls=tone[kind[oid]])
        if oid in names:
            f.text(x, y + 25, names[oid], 'cap')
    f.text(X[0], 72, 'v1.0', 'cap')
    f.text(X[1], 190, '첫 커밋', 'cap')
    f.text(170, 206, '태그 → 커밋 → (tree · parent) · 트리 → 항목',
           'cap')
    f.text(170, 218, '상자: 객체 종류와 이름 앞 7자리 · 파일 이름은 트리에'
           ' 있다', 'cap')
    return f


# ── 7·9부: criss-cross 역사와 merge-base 둘 ────────────────────


@fig('dag_bases')
def dag_bases():
    rows = []
    for line in cap('dag__log-all-format-h-p-s.txt'):
        toks = line.split(' ')
        par = []
        k = 1
        while k < len(toks) and re.fullmatch(r'[0-9a-f]{7}', toks[k]):
            par.append(toks[k])
            k += 1
        rows.append((toks[0], par, ' '.join(toks[k:]).strip()))
    rows.reverse()                          # 오래된 것부터
    main = [l.split()[0] for l in
            cap('dag__log-oneline-first-parent-main.txt')]
    bases = [l[:7] for l in cap('dag__merge-base-all-main-side.txt')]
    need(len(rows) == 8 and len(bases) == 2, '커밋 여덟, 베이스 둘')
    f = Fig(172, title='서로를 두 번 합친 역사 — 가장 좋은 공통 조상이 둘')
    pos = {}
    for i, (oid, _, _) in enumerate(rows):
        pos[oid] = (26 + i * 40, 50 if oid in main else 118)
    for oid, par, _ in rows:                # 자식 → 부모
        for p in par:
            link(f, pos[oid], pos[p], 10)
    for oid, par, subj in rows:
        x, y = pos[oid]
        if oid in bases:
            f.circle(x, y, 13, 'dot2', ' style="opacity:.25"')
        f.circle(x, y, 9, 'box g3' if len(par) > 1 else 'box')
        f.text(x, y + 3, subj if len(subj) == 1 else 'M', 'key')
        f.text(x, y + (22 if y > 80 else -15), oid, 'mono')
    tip_main, tip_side = pos[main[0]], pos[rows[-1][0]]
    need(rows[-1][0] not in main, 'side 의 끝이 마지막 커밋')
    f.text(tip_main[0] + 14, tip_main[1] + 3, 'main', 'hot', 'start')
    f.text(tip_side[0], tip_side[1] - 15, 'side', 'hot')
    f.text(170, 158, 'M = 머지 커밋 · 옅은 원 = merge-base --all 의 답 '
           '%s·%s' % tuple(bases), 'cap')
    return f


# ── 2·6부: 세 영역과 명령 (설명용) ──────────────────────────────


@fig('three_areas')
def three_areas():
    f = Fig(178, title='작업 트리 · 인덱스 · HEAD 와 그 사이를 옮기는 명령')
    boxes = (('작업 트리', 'g2', 55), ('인덱스', 'g1', 170),
             ('HEAD 의 커밋', 'g3', 285))
    for name, g, x in boxes:
        f.rect(x - 46, 72, 92, 36, 'box ' + g)
        f.text(x, 94, name, 'key')
    # 꺾인 화살표: 상자 위(아래)에서 나가 가로로 건너 상자에 꽂힌다.
    # 끝이 겹치지 않게 상자마다 드나드는 x 를 조금씩 비킨다.
    fw = (('git add', 65, 160, 58), ('git commit', 180, 275, 58),
          ('git commit -a', 35, 305, 30))
    for lab, a, b, y in fw:
        f.line(a, 72, a, y, 'edge hot')
        f.line(a, y, b, y, 'edge hot')
        arrow(f, b, y, b, 72, hot=True)
        f.text((a + b) / 2, y - 4, lab, 'mono')
    bw = (('git restore', 160, 65, 124),
          ('git restore --staged', 275, 180, 124),
          ('git switch · git checkout', 305, 35, 154))
    for lab, a, b, y in bw:
        f.line(a, 108, a, y, 'edge')
        f.line(a, y, b, y, 'edge')
        arrow(f, b, y, b, 108)
        f.text((a + b) / 2, y + 11, lab, 'mono')
    return f


# ── 3부: 트리 항목의 차례 ─────────────────────────────────────


@fig('tree_sort')
def tree_sort():
    """git 은 트리 항목을 바이트로 견주되 디렉터리 이름 뒤에 '/' 를
    붙인 것처럼 견준다. 두 번째 바이트가 차례를 정한다."""
    ents = [(l.split()[1], l.split('\t')[1])
            for l in cap('tree_sort__ls-tree-git-write-tree.txt')]
    keys = [n + ('/' if t == 'tree' else '') for t, n in ents]
    need(keys == sorted(keys), 'ls-tree 차례 = / 를 붙인 바이트 차례')
    f = Fig(40 + 22 * len(ents), title='트리 항목의 차례 — 디렉터리 a 는 '
            'a/ 로 견준다')
    f.text(24, 16, 'ls-tree 차례', 'key', 'start')
    f.text(150, 16, '견주는 열쇠', 'key', 'start')
    f.text(262, 16, '둘째 바이트', 'key', 'start')
    for i, ((t, n), k) in enumerate(zip(ents, keys)):
        y = 36 + 22 * i
        hot = t == 'tree'
        f.text(24, y, '%d. %s' % (i + 1, n), 'mono' + (' hot' if hot
                                                       else ''), 'start')
        f.text(95, y, t, 'tick', 'start')
        for j, ch in enumerate(k):
            f.rect(150 + j * 16, y - 11, 15, 15,
                   'box g1' if j == 1 else 'box')
            f.text(157.5 + j * 16, y, ch, 'mono')
        f.text(262, y, '0x%02x' % ord(k[1]), 'mono' + (' hot' if hot
                                                       else ''), 'start')
    return f


# ── 5부: 인덱스 항목 하나의 바이트 ─────────────────────────────


def byte_rows(f, rows, y0, x_off=30, x_hex=38, x_val=170, dy=13.5):
    """(자리, 바이트, 뜻) 줄들을 표처럼. 바이트는 16진, 길면 줄인다."""
    for i, (off, raw, what) in enumerate(rows):
        y = y0 + i * dy
        if i % 2 == 0:
            f.rect(4, y - 10, 332, dy, 'cell f')
        h = raw.hex()
        if len(h) > 24:
            h = h[:10] + '…' + h[-8:]
        f.text(x_off, y, str(off), 'tick', 'end')
        f.text(x_hex, y, h, 'mono', 'start')
        f.text(x_val, y, what, 'tick', 'start')


@fig('index_entry')
def index_entry():
    """golden/index/plain.bin 의 머리와 첫 항목. stat 칸은 golden 이
    0 으로 정규화했다(기계마다 다른 값이라)."""
    data = open(os.path.join(GOLDEN, 'index', 'plain.bin'), 'rb').read()
    first = cap_first_path()
    need(data[:4] == b'DIRC', '인덱스 서명')
    u32 = lambda o: int.from_bytes(data[o:o + 4], 'big')
    e = 12
    flags = int.from_bytes(data[e + 60:e + 62], 'big')
    nlen = flags & 0xfff
    name = data[e + 62:e + 62 + nlen]
    need(name.decode() == first, '첫 항목 이름 = ls-files 첫 줄')
    size = (62 + nlen + 8) & ~7         # NUL 1~8 개로 8의 배수
    rows = [(0, data[0:4], "서명 'DIRC'"),
            (4, data[4:8], '판 %d' % u32(4)),
            (8, data[8:12], '항목 %d개' % u32(8)),
            (12, data[12:20], 'ctime 초·나노초'),
            (20, data[20:28], 'mtime 초·나노초'),
            (28, data[28:36], 'dev · ino'),
            (36, data[36:40], 'mode %o' % u32(36)),
            (40, data[40:48], 'uid · gid'),
            (48, data[48:52], '파일 크기 %d' % u32(48)),
            (52, data[52:72], 'blob 이름(SHA-1 20바이트)'),
            (72, data[72:74], '플래그 — 이름 길이 %d' % nlen),
            (74, name, "경로 '%s'" % first),
            (74 + nlen, data[e + 62 + nlen:e + size],
             'NUL %d개 — 항목을 8바이트 배수로' % (size - 62 - nlen))]
    f = Fig(40 + 13.5 * len(rows), title='index v2 — 머리 12바이트와 '
            '첫 항목 %d바이트' % size)
    f.text(30, 14, '자리', 'key', 'end')
    f.text(38, 14, '바이트(16진)', 'key', 'start')
    f.text(170, 14, '뜻', 'key', 'start')
    byte_rows(f, rows, 30)
    f.line(4, 30 + 13.5 * 3 - 10.5, 336, 30 + 13.5 * 3 - 10.5, 'ax')
    f.text(334, 30 + 13.5 * 3 - 13, '↑ 머리 · ↓ 첫 항목', 'cap', 'end')
    f.text(170, 34 + 13.5 * len(rows), 'golden/index/plain.bin · stat 칸은 '
           '0 으로 정규화', 'cap')
    return f


def cap_first_path():
    line = io.open(os.path.join(GOLDEN, 'index', 'ls-stage.txt'),
                   encoding='utf-8').readline()
    return line.rstrip('\n').split('\t')[1]


# ── 10부: 팩 안의 OFS_DELTA 항목 하나 ──────────────────────────


@fig('pack_delta')
def pack_delta():
    """golden/pack/ofs.pack 의 첫 델타 항목을 mygit.pack 의 함수로
    풀어 머리·거리·델타 명령을 그대로 보인다."""
    data = open(os.path.join(GOLDEN, 'pack', 'ofs.pack'), 'rb').read()
    ver = [l.split() for l in io.open(os.path.join(
        GOLDEN, 'pack', 'ofs.verify'), encoding='utf-8')]
    ents = [r for r in ver if len(r) == 7]
    oid, _, osize, _, off, _, base = ents[0]
    base_off = int([r for r in ver if r[0] == base][0][4])
    off, osize = int(off), int(osize)
    typ, dsize, p1 = P._entry_header(data, off)
    dist, p2 = P._ofs(data, p1)
    need(typ == P.OFS_DELTA and off - dist == base_off,
         'OFS_DELTA 의 거리 = verify-pack 의 바탕 자리')
    z = zlib.decompressobj()
    delta = z.decompress(data[p2:])
    # verify-pack -v 의 크기 열은 델타 항목에서 델타 자체의 길이다
    need(len(delta) == dsize == osize, '델타 길이 = 머리 = verify-pack')
    src, q = P._varint_le(delta, 0)
    dst, q = P._varint_le(delta, q)
    rows = [(off, data[off:p1], '형식 %d(OFS_DELTA) · 델타 %d바이트'
             % (typ, dsize)),
            (p1, data[p1:p2], '거리 %d → 바탕은 자리 %d' % (dist, off -
                                                          dist)),
            (p2, data[p2:p2 + 2], 'zlib 스트림 시작(%d바이트 압축)'
             % (len(data[p2:]) - len(z.unused_data)))]
    ops = []
    head_end = q
    while q < len(delta):
        op = delta[q]
        s = q
        q += 1
        if op & 0x80:
            o = n = 0
            for k in range(4):
                if op & (1 << k):
                    o |= delta[q] << (8 * k)
                    q += 1
            for k in range(3):
                if op & (0x10 << k):
                    n |= delta[q] << (8 * k)
                    q += 1
            ops.append((s, delta[s:q], '복사 바탕[%d:%d] %d바이트'
                        % (o, o + (n or 0x10000), n or 0x10000)))
        else:
            ops.append((s, delta[s:s + 1 + min(op, 6)],
                        '끼움 %d바이트 %s' % (op, short(delta[q:q + op]))))
            q += op
    drows = [(0, delta[:head_end], '바탕 크기 %d · 결과 크기 %d'
              % (src, dst))] + ops
    shown = drows[:9]
    h = 30 + 13.5 * len(rows) + 22 + 13.5 * len(shown) + 10
    f = Fig(h, title='팩 항목 하나 — OFS_DELTA 머리와 풀어 낸 델타 명령')
    f.text(30, 14, '자리', 'key', 'end')
    f.text(38, 14, '팩 파일의 바이트', 'key', 'start')
    byte_rows(f, rows, 30)
    y2 = 30 + 13.5 * len(rows) + 22
    f.text(30, y2 - 12, '델타', 'key', 'end')
    f.text(38, y2 - 12, '압축을 푼 델타(%d바이트)' % len(delta), 'key',
           'start')
    byte_rows(f, shown, y2)
    more = len(drows) - len(shown)
    f.text(170, h - 6, 'golden/pack/ofs.pack · 대상 %s%s' % (
        oid[:7], ' · 명령 %d개 더' % more if more else ''), 'cap')
    return f


def short(b):
    """끼움 바이트를 사람이 읽게 — 앞 10자, 줄바꿈은 ⏎."""
    t = b[:10].decode('latin-1').replace('\n', '⏎')
    return "'%s%s'" % (t, '…' if len(b) > 10 else '')


# ── 11부: 프로토콜 v2 로 clone 할 때의 pkt-line 대화 ────────────


def pkt_blocks(lines, tag):
    """'clone< …' 줄들 → [(방향, [본문…])]. 방향 '<' 는 서버가 보낸 것.
    fold 로 접힌 이어진 줄(tag 로 시작하지 않는 줄)은 앞 줄에 붙인다."""
    blocks = []
    for line in lines:
        if not line.startswith(tag):
            blocks[-1][1][-1] += line
            continue
        d, body = line[len(tag)], line[len(tag) + 1:].strip()
        if not blocks or blocks[-1][0] != d:
            blocks.append((d, []))
        blocks[-1][1].append(body)
    return blocks


def pkt_text(body):
    body = re.sub(r'\b([0-9a-f]{7})[0-9a-f]{33}\b', r'\1', body)
    return {'0000': '0000 (flush)', '0001': '0001 (delim)'}.get(body,
                                                                 body)


@fig('pkt_v2_clone')
def pkt_v2_clone():
    lines = cap('proto_work__git_trace_packet-1-git-clone-q-file-pwd-'
                '..-proto_origin-v2-2.txt')
    blocks = pkt_blocks(lines, 'clone')
    need([d for d, _ in blocks] == ['<', '>', '<', '>', '<'],
         '서버 기능 → ls-refs → 참조 → fetch → packfile')
    KEEP, LH = 8, 10.5

    def shown_of(body):
        """긴 덩이는 첫 줄(command=…)과 끝 줄들(want·ref-prefix·done)만.
        가운데는 agent·object-format 같은 되풀이다."""
        if len(body) <= KEEP:
            return body
        tail = body[-(KEEP - 2):]
        return [body[0], '… %d줄 생략' % (len(body) - 1 - len(tail))] + tail
    h = 22 + sum(14 + LH * len(shown_of(b)) + 16 for _, b in blocks)
    f = Fig(h, title='프로토콜 v2 로 clone — 대화 다섯 덩이')
    f.text(8, 11, '클라이언트(git clone)', 'key', 'start')
    f.text(332, 11, '서버(upload-pack)', 'key', 'end')
    y = 22
    for d, body in blocks:
        srv = d == '<'
        x0 = 70 if srv else 6
        shown = shown_of(body)
        bh = 14 + LH * len(shown)
        f.rect(x0, y, 264, bh, 'box ' + ('g2' if srv else 'g1'))
        for k, b in enumerate(shown):
            f.text(x0 + 6, y + 12 + LH * k, pkt_text(b),
                   'tick' if b.startswith('…') else 'mono', 'start')
        ay = y + bh / 2
        if srv:
            arrow(f, 68, ay, 4, ay)
        else:
            arrow(f, 272, ay, 336, ay)
        f.text(336 if srv else 4, y + bh + 9, 'pkt %d줄' % len(body),
               'cap', 'end' if srv else 'start')
        y += bh + 16
    return f


@fig('proto_v0_v2')
def proto_v0_v2():
    """ls-remote 한 번: v0 은 서버가 먼저 참조를 전부 쏟고, v2 는 기능만
    알린 뒤 클라이언트가 ls-refs 로 묻는다."""
    v0 = pkt_blocks(cap('proto_work.v0__git_trace_packet-1-git-ls-remote-'
                        '..-proto_origin-2-1-grep-o.txt'), 'ls-remote')
    v2 = pkt_blocks(cap('proto_work.v2__git_trace_packet-1-git-ls-remote-'
                        '..-proto_origin-2-1-grep-o.txt'), 'ls-remote')
    need([d for d, _ in v0] == ['<'] and
         [d for d, _ in v2] == ['<', '>', '<', '>'], 'v0 한 덩이·v2 넷')
    nref = lambda body: sum(1 for b in body
                            if re.match(r'[0-9a-f]{40} ', b))
    f = Fig(196, title='ls-remote 한 번 — 프로토콜 v0 과 v2')
    for col, (name, blocks) in enumerate((('v0', v0), ('v2', v2))):
        cx = 88 + col * 170
        f.text(cx, 14, 'protocol.version=%s' % name[1], 'key')
        f.line(cx - 60, 22, cx - 60, 186, 'grid')
        f.line(cx + 60, 22, cx + 60, 186, 'grid')
        f.text(cx - 60, 190, '클라이언트', 'cap')
        f.text(cx + 60, 190, '서버', 'cap')
        y = 38
        for d, body in blocks:
            srv = d == '<'
            what = ('참조 %d개' % nref(body)) if nref(body) else \
                ('기능 목록' if srv else
                 ('command=ls-refs' if len(body) > 1 else '끝(flush)'))
            if srv and nref(body) and name == 'v0':
                what += ' + 기능'
            arrow(f, cx + 60 if srv else cx - 60, y,
                  cx - 60 if srv else cx + 60, y, hot=srv and
                  nref(body) > 0)
            f.text(cx, y - 4, what, 'tick')
            f.text(cx, y + 9, 'pkt %d줄' % len(body), 'cap')
            y += 36
    f.text(88, 90, 'v0 캡처는 서버가', 'cap')
    f.text(88, 101, '보낸 줄만 걸렀다', 'cap')
    return f


# ── 7·8부: 머지와 리베이스의 전후 ─────────────────────────────


def graph(name):
    """log --oneline --graph 캡처 → [(칸, 이름, 제목)]. 칸은 '*' 의
    열을 2로 나눈 것(0 = 첫 줄기)."""
    out = []
    for line in cap(name):
        # 그래프 기호(|, /, \, *, 공백) 다음에 이름이 온다 — '* | abc' 도 있다
        m = re.match(r'([ |/\\*]*)([0-9a-f]{7}) (.*)$', line)
        if m and '*' in m.group(1):
            out.append((line.index('*') // 2, m.group(2), m.group(3)))
    return out


def commit_dot(f, x, y, subj, oid, below=True, cls='box', dim=False):
    f.circle(x, y, 10, cls + (' off' if dim else ''))
    f.text(x, y + 3, subj, 'key')
    f.text(x, y + (21 if below else -14), oid, 'mono')


@fig('rebase_before_after')
def rebase_before_after():
    before = graph('rebase_basic__log-oneline-graph-all.txt')
    after = graph('rebase_basic.after__log-oneline-graph-all.txt')
    orig = [l.split() for l in
            cap('rebase_basic__log-oneline-orig_head.txt')]
    subj = lambda g, s: [o for _, o, t in g if t == s][0]
    need([t for _, _, t in before] == ['M1', 'F3', 'F2', 'F1', 'base']
         and [t for _, _, t in after] == ['F3', 'F2', 'F1', 'M1', 'base']
         and [t for _, t in orig] == ['F3', 'F2', 'F1', 'base'],
         'rebase_basic 의 모양')
    f = Fig(250, title='git rebase main — 전과 후')
    f.text(6, 12, '전', 'key', 'start')
    base = subj(before, 'base')
    P0 = {'base': (30, 45), 'M1': (90, 30), 'F1': (90, 80),
          'F2': (150, 80), 'F3': (210, 80)}
    for a, b in (('M1', 'base'), ('F1', 'base'), ('F2', 'F1'),
                 ('F3', 'F2')):
        link(f, P0[a], P0[b], 10)
    for s, (x, y) in P0.items():
        commit_dot(f, x, y, s, subj(before, s), below=y > 40)
    f.text(104, 34, 'main', 'hot', 'start')
    f.text(224, 84, 'topic', 'hot', 'start')
    f.line(4, 118, 336, 118, 'grid')
    f.text(6, 134, '후', 'key', 'start')
    P1 = {'base': (30, 160), 'M1': (90, 160), 'F1': (150, 160),
          'F2': (210, 160), 'F3': (270, 160)}
    chain = ['F3', 'F2', 'F1', 'M1', 'base']
    for a, b in zip(chain, chain[1:]):
        link(f, P1[a], P1[b], 10, hot=a[0] == 'F')
    for s, (x, y) in P1.items():
        commit_dot(f, x, y, s + ("'" if s[0] == 'F' else ''),
                   subj(after, s), below=False,
                   cls='box g1' if s[0] == 'F' else 'box')
    f.text(284, 164, 'topic', 'hot', 'start')
    old = {'F1': (150, 212), 'F2': (210, 212), 'F3': (270, 212)}
    link(f, old['F1'], P1['base'], 10, dim=True)
    for a, b in (('F2', 'F1'), ('F3', 'F2')):
        link(f, old[a], old[b], 10, dim=True)
    for s, (x, y) in old.items():
        commit_dot(f, x, y, s, subj(before, s), dim=True)
    need(subj(before, 'base') == subj(after, 'base') == base, '바탕 같음')
    for k, t in enumerate(('옛 커밋은', 'ORIG_HEAD·reflog', '로만 닿는다')):
        f.text(6, 200 + 11 * k, t, 'cap', 'start')
    return f


@fig('ff_vs_3way')
def ff_vs_3way():
    ff = graph('merge_ff__log-oneline-all-graph.txt')
    orig = cap('merge_ff__cat-.git-orig_head.txt')[0][:7]
    said = cap('merge_ff__merge-topic.txt')
    three = graph('merge_clean__log-oneline-graph.txt')
    head = cap('merge_clean__cat-file-p-head.txt')
    need([t for _, _, t in ff] == ['theirs', 'base'] and
         ff[1][1] == orig and said[1] == 'Fast-forward', 'ff 의 모양')
    need([t for _, _, t in three][1:] == ['theirs', 'ours', 'base'],
         '3-way 의 모양')
    pars = [l.split()[1][:7] for l in head if l.startswith('parent ')]
    need(pars == [three[2][1], three[1][1]], '머지 부모 = ours, theirs')
    f = Fig(244, title='fast-forward 와 3-way 머지')
    f.text(6, 12, 'fast-forward — 새 커밋 없음, main 이 앞으로 간다',
           'key', 'start')
    a, b = (50, 50), (130, 50)
    link(f, b, a, 10)
    commit_dot(f, a[0], a[1], 'b', ff[1][1])
    commit_dot(f, b[0], b[1], 't', ff[0][1])
    f.text(a[0], 28, 'main(전)', 'tick')
    f.text(b[0], 28, 'main(후) = topic', 'hot')
    f.text(160, 54, said[0], 'mono', 'start')
    f.line(4, 92, 336, 92, 'grid')
    f.text(6, 108, '3-way — 부모가 둘인 새 커밋', 'key', 'start')
    P = {'base': (50, 170), 'ours': (130, 140), 'theirs': (130, 200),
         'merge': (215, 170)}
    for x, y in ((P['ours'], P['base']), (P['theirs'], P['base']),
                 (P['merge'], P['ours']), (P['merge'], P['theirs'])):
        link(f, x, y, 10, hot=x == P['merge'])
    ids = {t: o for _, o, t in three}
    ids['merge'] = three[0][1]
    for s, (x, y) in P.items():
        commit_dot(f, x, y, s[0] if s != 'merge' else 'M', ids.get(
            s, ''), below=y >= 170, cls='box g3' if s == 'merge'
            else 'box')
    f.text(229, 174, 'main', 'hot', 'start')
    f.text(144, 204, 'topic', 'hot', 'start')
    f.text(170, 238, 'b = base · o = ours · t = theirs · M 의 부모는 '
           '1 = o, 2 = t', 'cap')
    return f


# ── 4부: HEAD 의 reflog ───────────────────────────────────────


@fig('reflog_path')
def reflog_path():
    ents = []
    for line in cap('refs__reflog.txt'):
        m = re.match(r'([0-9a-f]{7}) HEAD@\{(\d+)\}: (.*)', line)
        ents.append((m.group(1), int(m.group(2)), m.group(3)))
    ents.reverse()                          # 오래된 것부터
    names = {}
    for oid, _, what in ents:
        m = re.match(r'commit(?: \(initial\))?: (\S+)$', what)
        if m:
            names[oid] = m.group(1)
    need(len(ents) == 5 and len(names) == 3, 'reflog 다섯 줄·커밋 셋')
    order = list(names)
    f = Fig(40 + 28 * len(ents), title='HEAD 가 지나온 길 — git reflog')
    for k, oid in enumerate(order):
        x = 30 + 40 * k
        f.text(x, 14, names[oid], 'key')
        f.line(x, 20, x, 30 + 28 * len(ents) - 10, 'grid')
    prev = None
    for i, (oid, n, what) in enumerate(ents):
        x, y = 30 + 40 * order.index(oid), 34 + 28 * i
        if prev:
            link(f, prev, (x, y), 5, hot=True)
        f.circle(x, y, 5, 'dot2')
        what = re.sub(r'\b([0-9a-f]{7})[0-9a-f]{33}\b', r'\1', what)
        f.text(150, y - 2, 'HEAD@{%d}  %s' % (n, oid), 'mono', 'start')
        f.text(150, y + 9, what, 'tick', 'start')
        prev = (x, y)
    return f


# ── 1부: 연표 띠 · 릴리스 · 성장 ─────────────────────────────


# 연표 띠에 이름을 붙일 사건 — (timeline.tsv 의 event 에 든 글, 짧은
# 이름). 어느 것을 고를지는 편집이지만 날짜는 전부 tsv 에서 온다.
MILESTONES = [('첫 커밋 e83c5163', '첫 커밋'),
              ('Meet the new maintainer', 'Hamano 인계'),
              ('[ANNOUNCE] GIT 1.0.0', '1.0'),
              ('GitHub is officially live', 'GitHub 개장'),
              ('2.0.0 까지 커밋', '2.0'),
              ('SHAttered', 'SHA-1 충돌'),
              ('75억 달러', 'MS 가 GitHub 인수'),
              ('2.34.0 — ort', 'ort 기본'),
              ('2.45.0 — reftable', 'reftable'),
              ('2.55.0 —', '2.55')]


@fig('timeline_ribbon')
def timeline_ribbon():
    rows = [r for r in tsv('timeline.tsv') if r['date'] >= '2005']
    rel = [r for r in rows if re.match(r'git \d+\.\d+\.0 릴리스',
                                       r['event'])]
    ev = [r for r in rows if r not in rel]
    f = Fig(200, title='2005 → 2026 — 사건 %d건과 x.y.0 릴리스 %d개'
            % (len(ev), len(rel)))
    ax = Axes(f, 16, 150, 312, 20, (2005, 2027), (0, 1))
    for yr in range(2005, 2028, 3):
        x, _ = ax.at(yr, 0)
        f.line(x, 150, x, 174, 'grid')
        f.text(x, 184, str(yr), 'tick')
    for r in rel:
        x, _ = ax.at(ymd(r['date']), 0)
        f.line(x, 162, x, 172, 'cv2')
    for r in ev:
        x, _ = ax.at(ymd(r['date']), 0)
        f.circle(x, 156, 2.2, 'dot')
    f.circle(20, 193, 2.2, 'dot')
    f.text(26, 196, '사건(data/events.tsv)', 'cap', 'start')
    f.line(128, 189, 128, 197, 'cv2')
    f.text(133, 196, 'x.y.0 릴리스(data/releases.tsv)', 'cap', 'start')
    # 이름표는 한 줄에 하나. 오른쪽 무리(글자가 왼쪽으로 뻗음)는 늦은
    # 것부터 위에, 왼쪽 무리는 그 아래에 이른 것부터 — 그러면 어느
    # 안내선도 아래 줄의 글자를 지나지 않는다(아래에서 검사한다).
    # 폭은 어림(한글 8px·그 밖 4.6px, 글자 8px 기준).
    labs = []
    for key, name in MILESTONES:
        hit = [r for r in ev if key in r['event']]
        need(len(hit) == 1, '연표에 한 번: ' + key)
        x, _ = ax.at(ymd(hit[0]['date']), 0)
        lab = '%s %s' % (name, hit[0]['date'][:7])
        w = sum(8 if ord(c) > 0x1100 else 4.6 for c in lab)
        labs.append((x, lab, w))
    right = sorted((l for l in labs if l[0] > 140), reverse=True)
    left = sorted(l for l in labs if l[0] <= 140)
    rows = []
    for k, (x, lab, w) in enumerate(right + left):
        ly = 14 + 12.5 * k
        span = (x - w - 2, x + 2) if k < len(right) else (x - 2, x + w)
        rows.append((x, span))
        f.line(x, ly + 3, x, 153, 'tie')
        f.text(x, ly, lab, 'tick', 'end' if k < len(right) else 'start')
    for k, (x, _) in enumerate(rows):
        need(all(not (a <= x <= b) for _, (a, b) in rows[k + 1:]),
             '연표 안내선이 글자를 지난다')
    return f


@fig('release_cadence')
def release_cadence():
    rel = tsv('releases.tsv')
    years = {}
    for r in rel:
        y = int(r['date'][:4])
        years[y] = years.get(y, 0) + 1
    lo, hi = min(years), max(years)
    top = max(years.values())
    f = Fig(192, title='해마다 나온 x.y.0 판 — 모두 %d개' % len(rel))
    ax = Axes(f, 30, 16, 300, 128, (lo - 0.5, hi + 0.5), (0, top + 1))
    ax.frame()
    ax.yticks(range(0, top + 2, 2), label='판 수')
    ax.grid(ys=range(2, top + 2, 2))
    for y in range(lo, hi + 1):
        x0, y0 = ax.at(y - 0.35, years.get(y, 0))
        x1, y1 = ax.at(y + 0.35, 0)
        if years.get(y):
            f.rect(x0, y0, x1 - x0, y1 - y0, 'bar')
        if (y - lo) % 3 == 0:
            f.text((x0 + x1) / 2, 156, str(y), 'tick')
    f.text(180, 172, 'data/releases.tsv(mirror 태그의 taggerdate) · '
           '%d년은 9월까지' % hi, 'cap')
    # 2007~2013 이 비어 보이는 까닭 — mirror 에서 확인: v1.7.1(2010-04-23)
    # 이 기능 판이고 v1.7.1.1 이 그 유지보수 판이다
    f.text(180, 185, '1.x 시절엔 v1.7.1 처럼 셋째 자리 판도 기능 판이었다'
           ' — 여기엔 없다', 'cap')
    return f


@fig('growth')
def growth():
    rows = tsv('growth.tsv')
    pts = [(ymd(r['date']), int(r['commits'])) for r in rows]
    ppl = [(ymd(r['date']), int(r['contributors'])) for r in rows]
    f = Fig(186, title='릴리스까지 쌓인 커밋(머지 빼고)과 기여자')
    top = (max(c for _, c in pts) // 10000 + 1) * 10000
    ax = Axes(f, 40, 14, 250, 130, (2005, 2027), (0, top))
    ax.frame()
    ax.grid(ys=range(20000, top, 20000))
    ax.yticks(range(0, top + 1, 20000), fmt='%d')
    ax.xticks(range(2005, 2028, 5))
    ax.curve(pts, 'cv2')
    ptop = (max(c for _, c in ppl) // 500 + 1) * 500
    bx = Axes(f, 40, 14, 250, 130, (2005, 2027), (0, ptop))
    bx.curve(ppl, 'cv')
    for v in range(0, ptop + 1, 500):
        x, y = bx.at(2027, v)
        f.text(x + 4, y + 3, str(v), 'tick', 'start')
    last = rows[-1]
    f.text(46, 30, '%s 까지 커밋 %s개 · 기여자 %s명' % (
        last['version'], format(int(last['commits']), ','),
        format(int(last['contributors']), ',')), 'tick', 'start')
    sk_legend(f, 46, 176, last)
    return f


def sk_legend(f, x, y, last):
    f.line(x, y - 3, x + 12, y - 3, 'cv2')
    f.text(x + 16, y, '커밋(왼쪽 눈금)', 'tick', 'start')
    f.line(x + 110, y - 3, x + 122, y - 3, 'cv')
    f.text(x + 126, y, '기여자(오른쪽) · %s 기준' % last['version'],
           'tick', 'start')


# ── 10부: 델타 사슬 · 델타 창 ─────────────────────────────────


@fig('delta_chains')
def delta_chains():
    lines = cap('pack__verify-pack-v-.git-objects-pack-.idx-grep-e-'
                'non-delta-chain.txt')
    nondelta = int(re.match(r'non delta: (\d+)', lines[0]).group(1))
    hist = [tuple(int(v) for v in re.match(
        r'chain length = (\d+): (\d+) objects?', l).groups())
        for l in lines[1:]]
    top = max(n for _, n in hist)
    deep = max(d for d, _ in hist)
    f = Fig(176, title='델타 사슬 길이의 분포 — 40커밋 저장소')
    ax = Axes(f, 30, 14, 300, 120, (0.3, deep + 0.7), (0, top + 1))
    ax.frame()
    ax.yticks(range(0, top + 2, 3), label='객체 수')
    ax.grid(ys=range(3, top + 2, 3))
    ax.xticks([1, 5, 10, 15, 20, 25, deep], fmt='%d',
              label='사슬 길이(바탕까지 델타 몇 번)')
    for d, n in hist:
        x0, y0 = ax.at(d - 0.4, n)
        x1, y1 = ax.at(d + 0.4, 0)
        f.rect(x0, y0, x1 - x0, y1 - y0, 'bar')
    f.text(326, 28, '델타 아님 %d개(막대 밖)' % nondelta, 'tick', 'end')
    f.text(326, 40, 'pack.depth=50 · window=10', 'cap', 'end')
    return f


def hbars(f, rows, y0, x0=92, w=160, dy=19):
    """(이름, 값, 글) 가로 막대. 값의 최댓값이 w."""
    top = max(v for _, v, _ in rows)
    for i, (name, v, lab) in enumerate(rows):
        y = y0 + i * dy
        f.text(x0 - 5, y + 4, name, 'tick', 'end')
        f.rect(x0, y - 6, w * v / top, 12, 'bar')
        f.text(x0 + w * v / top + 4, y + 4, lab, 'tick', 'start')


@fig('pack_window')
def pack_window():
    rows = [(int(w), int(d), int(s), p) for w, d, s, p in
            tbl('pack_window')]
    f = Fig(40 + 19 * len(rows), title='델타 창·깊이와 팩 크기')
    f.text(87, 12, 'window / depth', 'key', 'end')
    f.text(92, 12, '팩 크기(바이트)', 'key', 'start')
    hbars(f, [('%d / %d' % (w, d), s, '%s (%s)' % (format(s, ','), p))
              for w, d, s, p in rows], 28)
    f.text(170, 34 + 19 * len(rows), '같은 40커밋을 repack -a -d -f 로',
           'cap')
    return f


@fig('limits_churn')
def limits_churn():
    rows = tbl('limits_churn')
    f = Fig(110, title='1 MiB 파일의 판 넷 — 팩이 원래 크기의 몇 %인가')
    hbars(f, [(r[0], float(r[3].split()[0]), '%s / %s = %s' % (
        r[3], r[2], r[4])) for r in rows], 22, x0=120, w=90, dy=24)
    f.text(170, 100, '판마다 1 % 수정 · gc --aggressive 뒤', 'cap')
    return f


# ── 만들기 ────────────────────────────────────────────────────


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
            cur = (io.open(p, encoding='utf-8').read()
                   if os.path.exists(p) else '')
            if cur != want:
                bad.append(name)
        for name in bad:
            print('  ✗ %s 가 소스와 어긋난다' % name)
        print('그림 %d장 — 어긋남 %d건' % (len(made), len(bad)))
        return 1 if bad else 0
    if not os.path.isdir(FIGS):
        os.makedirs(FIGS)
    for name, text in sorted(made.items()):
        io.open(os.path.join(FIGS, name), 'w', encoding='utf-8',
                newline='\n').write(text)
    print('그림 %d장 → deck/figs/' % len(made))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
