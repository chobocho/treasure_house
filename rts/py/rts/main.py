# -*- coding: utf-8 -*-
"""CLI — 세 언어가 같은 부명령을 갖는다 (SPEC §24).

   `prim` 의 출력은 `golden/prim.txt` 와 **바이트 단위로 같아야 한다.** 절 구분
   `== N. 제목 ==` 은 명세이며, 덱의 `<!--OUT sec=N-->` 지시자가 이 표시로 절을
   잘라 온다.

   여기에 박힌 시험 입력들(거리 쌍·제곱근 인자·피해 조합…)은 `tools/gen_prim.py`
   의 것과 **같아야 한다.** 두 곳에 적히는 유일한 자료이며, 둘이 어긋나면
   `cmp` 가 그 자리에서 잡는다 — 그래서 굳이 한 곳으로 합치지 않았다.
   합치면 "둘 다 같은 실수를 했다"는 사고를 막을 수 없다.
"""

import io
import os
import sys
import time

from . import ai as AI
from . import circle as CI
from . import combat as CB
from . import const as C
from . import econ as E
from . import fixed as F
from . import flow as FL
from . import fog as FG
from . import hpa as HP
from . import jps as JP
from . import path as P
from . import raster as RS
from . import render as RD
from . import replay as RP
from . import rng as R
from . import sim as SIM
from . import speaker as SK
from . import spatial as S
from . import tmap as T

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOLDEN = os.path.join(BASE, 'golden')

PAIRS_M = [(1, 0), (0, 1), (1, 1), (2, 1), (3, 1), (3, 2), (4, 3), (5, 5),
           (8, 3), (10, 0), (10, 10), (-7, 4), (-6, -6), (0, -9), (12, -5),
           (-3, 11)]
SQ_N = [0, 1, 2, 3, 15, 16, 17, 99, 100, 65535, 65536, 1000000, 2147483647]
ANG_V = [(12, 5), (12, -5), (12, 6), (5, 12), (12, 4), (-12, 5), (-5, -12),
         (0, 0), (1, 0), (0, -1), (7, 3), (3, 7), (-9, -4), (4, -9),
         (100, 41), (100, 42)]
DMG_CASE = [(6, 3, 0), (6, 3, 2), (6, 3, 5), (6, 3, 9), (9, 1, 0), (9, 1, 4),
            (12, 8, 3), (12, 8, 11), (4, 0, 0), (4, 0, 3), (20, 12, 6),
            (2, 2, 4)]
LAN_CASE = [(10, 10, 6554, 6554), (20, 10, 6554, 6554), (10, 20, 6554, 6554),
            (30, 20, 3277, 6554), (5, 5, 13107, 13107), (50, 40, 1311, 1311),
            (12, 8, 6554, 9830), (100, 100, 655, 655)]
ECON_CASE = [(0, 6554), (4, 6554), (8, 6554), (16, 6554), (8, 13107),
             (8, 3277)]
FOG_UNITS = [((10, 10), 3), ((12, 11), 5), ((30, 30), 8)]
FLOWMAP = [
    '............',
    '.##########.',
    '.#........#.',
    '.#.######.#.',
    '.#.#....#.#.',
    '.#.#.##.#.#.',
    '.#.#.##.#.#.',
    '.#.#....#.#.',
    '.#.######.#.',
    '.#........#.',
    '.##########.',
    '............',
]


def golden(name):
    return io.open(os.path.join(GOLDEN, name), encoding='utf-8').read()


def maps():
    return [T.TMap.load_text(golden('map_%d.txt' % i)) for i in range(1, 7)]


def flowmap():
    m = T.TMap(len(FLOWMAP[0]), len(FLOWMAP))
    for y, row in enumerate(FLOWMAP):
        for x, ch in enumerate(row):
            m.terrain[y * m.w + x] = T.ROCK if ch == '#' else T.DIRT
            m._repass(y * m.w + x)
    m._bump()
    return m


# ── prim 의 절들 ────────────────────────────────────────────────────────────
def sec1(o):
    o.append('== 1. 거리 척도 ==')
    o.append('  dx   dy     d1  dinf   d83   dab   doct     eu3  d83pm  dabpm'
             ' doctpm')
    for dx, dy in PAIRS_M:
        eu = F.isqrt((dx * dx + dy * dy) * 1000000)
        o.append('%4d %4d %6d %5d %5d %5d %6d %7d %6d %6d %6d'
                 % (dx, dy, F.d1(dx, dy), F.dinf(dx, dy), F.d83(dx, dy),
                    F.dab(dx, dy), F.doct(dx, dy), eu,
                    F.d83(dx, dy) * 1000000 // eu - 1000,
                    F.dab(dx, dy) * 1000000 // eu - 1000,
                    F.doct(dx, dy) * 100000 // eu - 1000))
    o.append('eu3 = floor(sqrt(dx^2+dy^2) * 1000)')
    o.append('d83pm dabpm = 유클리드 대비 천분율 편차')
    o.append('doctpm = 유클리드*10 대비. 옥타일은 유클리드 근사가 아니므로'
             ' 참고값이며,')
    o.append('참 옥타일과의 비교는 out/analysis.txt 2절에 있다.')


def sec2(o):
    o.append('== 2. 정수 제곱근 ==')
    o.append('          n     isqrt          isqrt^2      (isqrt+1)^2')
    for n in SQ_N:
        r = F.isqrt(n)
        o.append('%11d %9d %16d %16d' % (n, r, r * r, (r + 1) * (r + 1)))


def sec3(o):
    o.append('== 3. 8방향 판별 ==')
    o.append('  dx   dy  12*mn  5*mx  대각  방향  이름')
    for dx, dy in ANG_V:
        ax, ay = abs(dx), abs(dy)
        mx, mn = max(ax, ay), min(ax, ay)
        d = F.atan8(dx, dy)
        o.append('%4d %4d %6d %5d %5d %5d  %s'
                 % (dx, dy, 12 * mn, 5 * mx, 1 if 12 * mn > 5 * mx else 0,
                    d, F.DNAME[d]))


def sec4(o):
    o.append('== 4. LCG ==')
    r = R.LCG(1)
    o.append('  i           상태   next15')
    for i in range(10):
        v = r.next15()
        o.append('%3d %14d %8d' % (i + 1, r.s, v))
    o.append('하위 비트의 짧은 주기 — 상태의 최하위 1·2비트')
    r2 = R.LCG(1)
    b1, b2 = [], []
    for _ in range(16):
        r2.next15()
        b1.append(r2.s % 2)
        b2.append(r2.s % 4)
    o.append('  bit0: ' + ' '.join(str(v) for v in b1))
    o.append('  bit10: ' + ' '.join(str(v) for v in b2))
    r3 = R.LCG(2026)
    o.append('roll(6) x20: ' + ' '.join(str(r3.roll(6)) for _ in range(20)))
    o.append('기각 횟수 %d' % r3.rejects)
    r4 = R.LCG(2026)
    hist = [0] * 6
    for _ in range(6000):
        hist[r4.roll(6)] += 1
    o.append('roll(6) x6000 도수: ' + ' '.join(str(v) for v in hist))
    o.append('기각 횟수 %d' % r4.rejects)


def sec5(o):
    o.append('== 5. 오토타일 ==')
    o.append('클래스 %d개' % T.CLASS_COUNT)
    o.append('정규화 인덱스 (마스크 0..255, 16개씩)')
    for row in range(16):
        o.append('  ' + ' '.join('%3d' % T.canon_index(T.canon(row * 16 + c))
                                 for c in range(16)))
    o.append('클래스별 마스크 개수')
    cls = sorted(set(T.canon(m) for m in range(256)))
    for row in range(0, len(cls), 8):
        o.append('  ' + ' '.join(
            '%3d:%-3d' % (cls[i], len([1 for k in range(256)
                                       if T.canon(k) == cls[i]]))
            for i in range(row, min(row + 8, len(cls)))))


def sec6(o):
    o.append('== 6. 원 마스크 ==')
    o.append(' r    개수  span')
    for r in range(1, 9):
        o.append('%2d %7d  %s' % (r, CI.count(r),
                                  ' '.join(str(v) for v in CI.spans(r))))


def sec7(o, ms):
    o.append('== 7. 경로 탐색 ==')
    o.append('맵 출발      도착      BFS걸음  다익스트라   A*비용  A*연노드')
    for i, m in enumerate(ms):
        for (s, t) in m.pairs:
            b = P.bfs(m, 0, s, t)
            dj = P.dijkstra(m, 0, [s[1] * m.w + s[0]],
                            t[1] * m.w + t[0])[t[1] * m.w + t[0]]
            if dj >= P.INF:
                dj = -1
            a, _tiles, ex = P.astar(m, 0, s, t)
            o.append('%2d (%2d,%2d) -> (%2d,%2d) %8d %11d %8d %9d'
                     % (i + 1, s[0], s[1], t[0], t[1], b, dj, a, ex))
    o.append('다익스트라와 A* 의 비용은 모든 줄에서 같아야 한다 (정리 8.1)')


def sec8(o, ms):
    o.append('== 8. HPA* 와 JPS ==')
    o.append('맵 출발      도착        A*   JPS  JPS연노드   HPA*  HPA*/A*(pm)')
    for i, m in enumerate(ms):
        for (s, t) in m.pairs:
            a = P.astar(m, 0, s, t)[0]
            j, _tiles, jx = JP.search(m, 0, s, t)
            hp = HP.search(m, 0, s, t)[0]
            ratio = -1 if (a <= 0 or hp <= 0) else hp * 1000 // a
            o.append('%2d (%2d,%2d) -> (%2d,%2d) %6d %5d %10d %6d %12d'
                     % (i + 1, s[0], s[1], t[0], t[1], a, j, jx, hp, ratio))
    o.append('JPS 비용은 모든 줄에서 A* 와 같아야 한다 (정리 10.1)')


def sec9(o):
    o.append('== 9. 흐름장과 클리어런스 ==')
    m = flowmap()
    integ = FL.integration(m, 0, [(4, 4)])
    fl = FL.flow_dirs(m, 0, integ)
    cl = FL.clearance(m, 0)
    o.append('목표 (4,4) · 적분장')
    for y in range(m.h):
        o.append('  ' + ' '.join('%5d' % integ[y * m.w + x]
                                 for x in range(m.w)))
    o.append('경사장 (방향 번호, 255=정지)')
    for y in range(m.h):
        o.append('  ' + ' '.join('%3d' % fl[y * m.w + x] for x in range(m.w)))
    o.append('클리어런스 (좌상단 기준 정사각 여유)')
    for y in range(m.h):
        o.append('  ' + ' '.join('%2d' % cl[y * m.w + x] for x in range(m.w)))


def sec10(o):
    o.append('== 10. 안개 참조 카운트 ==')

    def report(tag, us):
        fg = FG.Fog(64, 64, 1)
        for (x, y), r in us:
            fg.add_sight(0, x, y, r)
        cnt = fg.count[0]
        tot = sum(cnt)
        vis = len([1 for v in cnt if v > 0])
        mx = max(cnt)
        hist = [0] * (mx + 1)
        for v in cnt:
            if v:
                hist[v] += 1
        o.append('%s 가시 칸 %d · 카운트 합 %d · 최대 %d' % (tag, vis, tot, mx))
        o.append('  도수: ' + ' '.join('%d:%d' % (k, hist[k])
                                       for k in range(1, mx + 1)))

    report('초기', FOG_UNITS)
    moved = [((11, 10), 3)] + FOG_UNITS[1:]
    report('1번 유닛 (10,10)->(11,10)', moved)
    report('3번 유닛 사망', moved[:2])
    fg = FG.Fog(64, 64, 1)
    o.append('전원 제거 후 카운트 합 %d' % sum(fg.count[0]))


def sec11(o):
    o.append('== 11. 전투 ==')
    o.append('기본 관통 방어    mx    lo    n   E*100  모의평균*100')
    for basic, pierce, armour in DMG_CASE:
        mx = CB.max_damage(basic, pierce, armour)
        lo = CB.damage_lo(mx)
        r = R.LCG(12345)
        tot = sum(CB.roll_damage(r, basic, pierce, armour)
                  for _ in range(1000))
        o.append('%4d %4d %4d %5d %5d %4d %7d %13d'
                 % (basic, pierce, armour, mx, lo, mx - lo + 1,
                    CB.expect100(basic, pierce, armour), tot * 100 // 1000))
    o.append('란체스터 제곱 법칙 시뮬 (A0 B0 alpha beta -> 틱 A남음 B남음)')
    for a0, b0, al, be in LAN_CASE:
        t, a, b = CB.lanchester_sim(a0, b0, al, be)
        o.append('%4d %4d %6d %6d %8d %8d %8d' % (a0, b0, al, be, t, a, b))


def sec12(o):
    o.append('== 12. 경제 ==')
    o.append('왕복타일 속도(fp)   총틱   수입*10000')
    for d, v in ECON_CASE:
        o.append('%8d %10d %6d %12d'
                 % (d, v, E.round_trip_ticks(d, v), E.income10000(d, v)))
    o.append('적재 %d · 틱당 채굴 %d · 반납 %d틱'
             % (E.LOAD_MAX, E.MINE_PER_TICK, E.UNLOAD_TICKS))


def sec13(o):
    o.append('== 13. CRC 와 FNV ==')
    for s in ['123456789', '', 'A', 'RTSM', 'the quick brown fox']:
        b = s.encode('ascii')
        o.append('crc16 %-20r %6d 0x%04X' % (s, F.crc16(b), F.crc16(b)))
    for s in ['', 'a', 'foobar', 'RTSM']:
        b = s.encode('ascii')
        o.append('fnv1a %-20r %12d 0x%08X' % (s, F.fnv1a(b), F.fnv1a(b)))
    b = bytes(bytearray(range(16)))
    o.append('fnv1a bytes(0..15) %12d 0x%08X' % (F.fnv1a(b), F.fnv1a(b)))


def sec14(o):
    o.append('== 14. PIT 분주값 ==')
    o.append('음   목표Hz  분주값   실제Hz*100   차이*100')
    for k in range(len(SK.NOTE_NAME)):
        f = SK.NOTE_HZ[k]
        div = SK.divisor(f)
        act = SK.actual100(f)
        o.append('%-4s %6d %7d %12d %10d'
                 % (SK.NOTE_NAME[k], f, div, act, act - f * 100))


def cmd_prim():
    ms = maps()
    o = []
    sec1(o)
    o.append('')
    sec2(o)
    o.append('')
    sec3(o)
    o.append('')
    sec4(o)
    o.append('')
    sec5(o)
    o.append('')
    sec6(o)
    o.append('')
    sec7(o, ms)
    o.append('')
    sec8(o, ms)
    o.append('')
    sec9(o)
    o.append('')
    sec10(o)
    o.append('')
    sec11(o)
    o.append('')
    sec12(o)
    o.append('')
    sec13(o)
    o.append('')
    sec14(o)
    return '\n'.join(o) + '\n'


# ── 시나리오 ────────────────────────────────────────────────────────────────
def scenario(ticks=None, float_bug=False):
    m = T.TMap.load_text(golden('map_start.txt'))
    sc = SIM.parse_script(golden('script.txt'))
    s = SIM.Sim(m, 1, sc.players, float_bug=float_bug)
    s.setup_start(ai=False)              # §18.6 — 스크립트가 몬다
    return s, sc, (sc.ticks if ticks is None else ticks)


def ai_game(ticks, seed=1, seven=False):
    """§17.5 의 러시 타이밍을 재는 별도 실행. 스크립트 없이 AI 끼리 붙인다."""
    m = T.TMap.load_text(golden('map_start.txt'))
    s = SIM.Sim(m, seed, 2)
    s.setup_start(ai=True)
    if seven:
        s.ai_rules = AI.RULES7
    return s, ticks


def ev_json(e):
    v = list(e) + [0, 0, 0, 0]
    return '[%d,%d,%d,%d]' % (v[0], v[1], v[2], v[3])


def cmd_trace(ticks=None):
    """§18.3 — 키 순서와 공백까지 명세다. JSON 직렬화기를 믿지 않는다."""
    s, sc, n = scenario(ticks)
    out = []
    for t in range(1, n + 1):
        h = s.step(s.script_orders(sc, t))
        alive = len([1 for i in range(1, C.MAX_ENT) if s.w.alive[i]])
        out.append('{"t":%d,"h":"%08X","cr":[%s],"su":[%s],"sc":[%s],'
                   '"n":%d,"ev":[%s]}'
                   % (t, h,
                      ','.join(str(s.ec.credits[p]) for p in range(sc.players)),
                      ','.join(str(s.ec.supply_used[p])
                               for p in range(sc.players)),
                      ','.join(str(s.ec.supply_cap[p])
                               for p in range(sc.players)),
                      alive,
                      ','.join(ev_json(e) for e in s.events)))
    return '\n'.join(out) + '\n'


def cmd_aigame(ticks=1200, seven=False):
    s, n = ai_game(ticks, 1, seven)
    out = []
    for t in range(1, n + 1):
        h = s.step([])
        alive = len([1 for i in range(1, C.MAX_ENT) if s.w.alive[i]])
        out.append('{"t":%d,"h":"%08X","cr":[%d,%d],"su":[%d,%d],"sc":[%d,%d],'
                   '"n":%d,"ev":[%s]}'
                   % (t, h, s.ec.credits[0], s.ec.credits[1],
                      s.ec.supply_used[0], s.ec.supply_used[1],
                      s.ec.supply_cap[0], s.ec.supply_cap[1], alive,
                      ','.join(ev_json(e) for e in s.events)))
    return '\n'.join(out) + '\n'


def cmd_hashes(ticks=None):
    s, sc, n = scenario(ticks)
    out = []
    for t in range(1, n + 1):
        out.append('%d %08X' % (t, s.step(s.script_orders(sc, t))))
    return '\n'.join(out) + '\n'


def cmd_render(path, tick=1):
    s, sc, _n = scenario()
    for t in range(1, tick + 1):
        s.step(s.script_orders(sc, t))
    pal = RS.build_palette()
    light = RS.build_light(pal)
    view = RD.View()
    view.center_on(s.m, s.m.starts[0][0], s.m.starts[0][1])
    fb = RS.Frame()
    RD.draw(fb.fb, s, view, 0, pal, light, 0, [], 'TICK %d' % tick)
    io.open(path, 'wb').write(RS.to_ppm(fb.fb, pal))
    return '%s — 틱 %d\n' % (path, tick)


def cmd_lockstep(ticks=300):
    """§19.3·§19.4 — 두 시뮬 대조와 부동소수점 주입 실험."""
    out = []
    a, sc, _n = scenario(ticks)
    b, sc2, _n2 = scenario(ticks)
    same = True
    for t in range(1, ticks + 1):
        ha = a.step(a.script_orders(sc, t))
        hb = b.step(b.script_orders(sc2, t))
        if ha != hb:
            same = False
            out.append('%d틱에서 갈렸다 %08X vs %08X' % (t, ha, hb))
            break
    if same:
        out.append('락스텝 %d틱 일치' % ticks)
    c, sc3, _n3 = scenario(ticks)
    d, sc4, _n4 = scenario(ticks, float_bug=True)
    first_hash = -1
    first_tile = -1
    for t in range(1, ticks + 1):
        hc = c.step(c.script_orders(sc3, t))
        hd = d.step(d.script_orders(sc4, t))
        if first_hash < 0 and hc != hd:
            first_hash = t
        if first_tile < 0:
            pc = [(c.w.alive[i], c.w.tx[i], c.w.ty[i])
                  for i in range(1, C.MAX_ENT)]
            pd = [(d.w.alive[i], d.w.tx[i], d.w.ty[i])
                  for i in range(1, C.MAX_ENT)]
            if pc != pd:
                first_tile = t
    out.append('float_bug: 해시가 갈린 틱 %d · 타일 좌표가 갈린 틱 %d'
               % (first_hash, first_tile))
    out.append('타일이 -1 이면 %d틱 동안 화면에서는 같아 보였다는 뜻이다'
               % ticks)
    return '\n'.join(out) + '\n'


def cmd_replay(path, ticks=None):
    """§20.2 — **상태는 한 바이트도 저장하지 않는다.** 명령이 없는 틱은 아예
       적지 않고, 재생은 머리의 총 틱 수만큼 돌면서 해당 틱에만 명령을 먹인다."""
    s, sc, n = scenario(ticks)
    log = []
    for t in range(1, n + 1):
        orders = s.script_orders(sc, t)
        if orders:
            log.append((t, orders))
        s.step(orders)
    blob = RP.save(1, sc.players, n, log)
    io.open(path, 'wb').write(blob)
    seed, players, tk, log2 = RP.load(blob)
    s2 = SIM.Sim(T.TMap.load_text(golden('map_start.txt')), seed, players)
    s2.setup_start(ai=False)             # 원본과 같은 조건이어야 한다
    at = dict(log2)
    for t in range(1, tk + 1):
        s2.step(at.get(t, []))
    same = s2.state_hash() == s.state_hash()
    return ('리플레이 %d바이트 · %d틱 · 명령 %d줄 · 재생 해시 %08X %s\n'
            % (len(blob), tk, sum(len(o) for (_t, o) in log2),
               s2.state_hash(), '일치' if same else '불일치'))


def cmd_bench():
    out = []
    ms = maps()
    t0 = time.time()
    for _k in range(20):
        for m in ms:
            for (s, t) in m.pairs:
                P.astar(m, 0, s, t)
    out.append('1. A* %d회 %.3f초' % (20 * 6 * 4, time.time() - t0))
    t0 = time.time()
    for _k in range(20):
        for m in ms:
            for (s, t) in m.pairs:
                JP.search(m, 0, s, t)
    out.append('2. JPS %d회 %.3f초' % (20 * 6 * 4, time.time() - t0))
    m = T.TMap.load_text(golden('map_start.txt'))
    t0 = time.time()
    for _k in range(5):
        FL.integration(m, 0, [(32, 32)])
    out.append('3. 흐름장 5회 %.3f초' % (time.time() - t0))
    t0 = time.time()
    s, sc, _n = scenario(200)
    for t in range(1, 201):
        s.step(s.script_orders(sc, t))
    out.append('4. 시뮬 200틱 %.3f초' % (time.time() - t0))
    pal = RS.build_palette()
    t0 = time.time()
    RS.build_light(pal)
    out.append('5. 명암표 1회 %.3f초' % (time.time() - t0))
    fb = RS.Frame()
    light = RS.build_light(pal)
    t0 = time.time()
    for _k in range(10):
        RD.draw(fb.fb, s, RD.View(), 0, pal, light, 0, [], '')
    out.append('6. 렌더 10프레임 %.3f초' % (time.time() - t0))
    return '\n'.join(out) + '\n'


def cmd_speaker(path):
    notes = [(SK.NOTE_HZ[k], 2200) for k in (0, 4, 7, 12)]
    blob = SK.tune(notes)
    io.open(path, 'wb').write(blob)
    return '%s — %d바이트 · FNV %08X\n' % (path, len(blob), F.fnv1a(blob))


def main(argv):
    if not argv:
        sys.stdout.write('부명령: prim trace hashes aigame render lockstep'
                         ' replay bench speaker\n')
        return 1
    cmd = argv[0]
    if cmd == 'prim':
        sys.stdout.write(cmd_prim())
    elif cmd == 'trace':
        sys.stdout.write(cmd_trace(int(argv[1]) if len(argv) > 1 else None))
    elif cmd == 'aigame':
        sys.stdout.write(cmd_aigame(int(argv[1]) if len(argv) > 1 else 1200))
    elif cmd == 'aigame7':
        sys.stdout.write(cmd_aigame(int(argv[1]) if len(argv) > 1 else 1200,
                                    True))
    elif cmd == 'hashes':
        sys.stdout.write(cmd_hashes(int(argv[1]) if len(argv) > 1 else None))
    elif cmd == 'render':
        sys.stdout.write(cmd_render(argv[1],
                                    int(argv[2]) if len(argv) > 2 else 1))
    elif cmd == 'lockstep':
        sys.stdout.write(cmd_lockstep(int(argv[1]) if len(argv) > 1 else 300))
    elif cmd == 'replay':
        sys.stdout.write(cmd_replay(argv[1],
                                    int(argv[2]) if len(argv) > 2 else None))
    elif cmd == 'bench':
        sys.stdout.write(cmd_bench())
    elif cmd == 'speaker':
        sys.stdout.write(cmd_speaker(argv[1]))
    else:
        sys.stdout.write('모르는 부명령: %s\n' % cmd)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
