# -*- coding: utf-8 -*-
"""1200틱 2인 시나리오를 만든다 — golden/script.txt

   SPEC §18.6 의 선택자 형식으로 쓴다. 건설 위치는 손으로 찍지 않는다 —
   map_start.txt 를 읽어 규칙으로 고른다. 그래야 맵을 다시 만들었을 때
   스크립트가 조용히 물 위에 건물을 세우려 드는 일이 없다.

   실행:  python3 tools/gen_script.py
"""
import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(BASE, 'golden')

CH = '.#~,*^;='
SAND, ROCK, WATER, DIRT, ORE, HILL, RUBBLE, ROAD = range(8)
BUILDABLE = (SAND, DIRT, RUBBLE, ROAD)

HQ, REF, BARR, FACT, POW, TOWER = 10, 11, 12, 13, 14, 15
INF, ARCHER, TANK, MORTAR, HARV = 0, 1, 2, 3, 4
FOOT = {HQ: 3, REF: 2, BARR: 2, FACT: 3, POW: 2, TOWER: 1}


def load_start():
    lines = io.open(os.path.join(GOLDEN, 'map_start.txt'),
                    encoding='utf-8').read().split('\n')
    i = lines.index('terrain')
    w, h = (int(v) for v in lines[i - 1].split()[1:])
    g = [[CH.index(c) for c in lines[i + 1 + y]] for y in range(h)]
    j = [k for k, l in enumerate(lines) if l.startswith('start ')][0]
    n = int(lines[j].split()[1])
    starts = [tuple(int(v) for v in lines[j + 1 + k].split()) for k in range(n)]
    return g, w, h, starts


def occupied_hq(bx, by):
    """사령부 3×3 과 시작 채집기 두 칸 (SPEC §25.4).

       채집기 칸을 빼먹으면 시나리오가 채집기가 서 있는 자리에 정제소를
       세우려 들고, 그 명령은 조용히 실패한다 — 실제로 한 번 그랬다.
    """
    cells = set((bx - 1 + dx, by - 1 + dy) for dx in range(3) for dy in range(3))
    cells.add((bx + 2, by + 1))
    cells.add((bx + 2, by + 2))
    return cells


def mirror_spot(spot, kind):
    """2회 대칭 — 발자국이 뒤집혀도 같은 칸들을 덮도록 좌상단을 옮긴다."""
    f = FOOT[kind]
    return (63 - spot[0] - (f - 1), 63 - spot[1] - (f - 1))


def foot_cells(kind, spot, pad=0):
    """발자국(pad>0 이면 그만큼 둘러싼 고리까지).

       정제소 둘레는 채집기가 계속 드나드는 **도크**다(SPEC §16.2). 거기에
       다음 건물을 예약해 두면 배치가 영원히 실패한다 — 실제로 플레이어 1 의
       발전소가 그래서 1200틱 내내 서지 않았다.
    """
    f = FOOT[kind]
    return set((spot[0] + dx, spot[1] + dy)
               for dx in range(-pad, f + pad) for dy in range(-pad, f + pad))


def find_spot(g, w, h, base, kind, taken, want_ore=False):
    """기지 주변에서 발자국이 들어가는 첫 자리를 규칙으로 고른다.

       훑는 순서는 '기지에서의 체비셰프 거리 오름차순, 같으면 y 그다음 x'.
       가까운 곳부터 채우므로 기지가 한 덩어리로 남는다(SPEC §16.5 의 4타일 규칙).
    """
    f = FOOT[kind]
    bx, by = base
    best = None
    for r in range(2, 10):
        cands = []
        for y in range(by - r, by + r + 1):
            for x in range(bx - r, bx + r + 1):
                if max(abs(x - bx), abs(y - by)) != r:
                    continue
                cells = [(x + dx, y + dy) for dx in range(f) for dy in range(f)]
                if any(not (0 <= u < w and 0 <= v < h) for u, v in cells):
                    continue
                if any(g[v][u] not in BUILDABLE for u, v in cells):
                    continue
                if any((u, v) in taken for u, v in cells):
                    continue
                score = 0
                if want_ore:
                    d = 99
                    for oy in range(max(0, y - 12), min(h, y + 13)):
                        for ox in range(max(0, x - 12), min(w, x + 13)):
                            if g[oy][ox] == ORE:
                                d = min(d, max(abs(ox - x), abs(oy - y)))
                    score = d
                cands.append((score, y, x))
        if cands:
            cands.sort()
            best = (cands[0][2], cands[0][1])
            break
    if best is None:
        raise SystemExit('건설 자리를 찾지 못했다: kind=%d base=%s' % (kind, base))
    for dx in range(f):
        for dy in range(f):
            taken.add((best[0] + dx, best[1] + dy))
    return best


# 플레이어 0 의 계획. 플레이어 1 은 같은 계획을 대칭 좌표로, DELAY 틱 늦게 쓴다.
DELAY = 45


BUILD_RETRY = (0, 25, 50, 75, 100)   # SPEC §18.6 — 유닛이 지나가면 배치가 실패한다


def plan(pid, base, spots, mirror):
    """(틱, 플레이어, 선택자, 명령, a, b, c) 목록.

       건설 명령은 **세 번** 낸다. 유닛이 그 칸을 지나가는 중이면 배치 판정이
       실패하고(§16.5), 한 번만 내면 그 건물은 게임 내내 서지 않는다.
       사람 플레이어도 그럴 때 다시 클릭한다 — 스크립트도 그렇게 한다.
       이미 지어졌으면 뒤따르는 시도는 조용히 실패하고 돈도 나가지 않는다.
    """
    def build(o, t, kind, spot):
        for r in BUILD_RETRY:
            o.append((t + r, pid, 'K10', 'BUILD', kind, spot[0], spot[1]))

    def M(p):
        return (63 - p[0], 63 - p[1]) if mirror else p
    ref, barr, pow_, fact = spots
    d = DELAY if mirror else 0
    enemy = M((55, 55)) if not mirror else (8, 8)
    o = []
    o.append((1 + d, pid, 'K4', 'HARVEST', 0, 0, 0))
    build(o, 4 + d, BARR, barr)
    build(o, 8 + d, REF, ref)
    o.append((12 + d, pid, 'K10', 'TRAIN', HARV, 0, 0))
    o.append((110 + d, pid, 'N', 'HARVEST', 0, 0, 0))
    o.append((115 + d, pid, 'K10', 'TRAIN', HARV, 0, 0))
    o.append((215 + d, pid, 'N', 'HARVEST', 0, 0, 0))
    build(o, 220 + d, POW, pow_)
    for k, t in enumerate((215, 280, 345, 410, 475, 540, 605, 670)):
        o.append((t + d, pid, 'K12', 'TRAIN', INF if k % 3 else ARCHER, 0, 0))
    build(o, 520 + d, FACT, fact)
    # 모아서 전진 — 기지 앞 집결지를 거쳐 적 기지로
    rally = (base[0] + (6 if not mirror else -6), base[1] + (6 if not mirror else -6))
    o.append((480 + d, pid, 'F', 'MOVE', rally[0], rally[1], 0))
    o.append((540 + d, pid, 'F', 'AMOVE', enemy[0], enemy[1], 0))
    o.append((900 + d, pid, 'K13', 'TRAIN', TANK, 0, 0))
    o.append((900 + d, pid, 'F', 'AMOVE', enemy[0], enemy[1], 0))
    return o


def main():
    g, w, h, starts = load_start()
    rows = []
    # 배치는 **플레이어 0 것만 고르고 1 은 2회 대칭으로 뒤집는다.** 각자 고르게
    # 두면 정제소가 광맥에서 서로 다른 거리에 서고, 그 차이가 그대로 수입 차이가
    # 되어 시나리오가 한쪽으로 기운다 — 실제로 360틱에 560 대 1460 이었다.
    base0 = starts[0]
    taken = occupied_hq(*base0)
    spots = []
    for kind in (REF, BARR, POW, FACT):
        sp = find_spot(g, w, h, base0, kind, taken)              if kind != REF else find_spot(g, w, h, base0, kind, taken,
                                          want_ore=True)
        taken |= foot_cells(kind, sp, 1 if kind == REF else 0)
        spots.append(sp)
    ref, barr, pw, fact = spots
    rows += plan(0, base0, (ref, barr, pw, fact), mirror=False)
    mir = [mirror_spot(sp, kind) for sp, kind in
           zip(spots, (REF, BARR, POW, FACT))]
    rows += plan(1, starts[1], (mir[0], mir[1], mir[2], mir[3]), mirror=True)
    rows.sort(key=lambda r: (r[0], r[1], r[2], r[3]))
    out = ['RTSS 1', 'ticks 1200', 'players 2',
           '# 틱 플레이어 선택자 명령 a b c   (SPEC §18.6)']
    for t, pid, sel, cmd, a, b, c in rows:
        out.append('%d %d %s %s %d %d %d' % (t, pid, sel, cmd, a, b, c))
    io.open(os.path.join(GOLDEN, 'script.txt'), 'w',
            encoding='utf-8').write('\n'.join(out) + '\n')
    print('script.txt  명령 %d줄 · 1200틱 2인' % len(rows))
    for pid, base in enumerate(starts):
        print('  플레이어 %d 기지 (%d,%d)' % (pid, base[0], base[1]))


if __name__ == '__main__':
    main()
