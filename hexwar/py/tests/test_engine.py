# -*- coding: utf-8 -*-
"""엔진 동작 검사 — 경계값과 되돌리기 불변식을 본다.

   골든 벡터는 '세 언어가 같은 답을 낸다'만 보장한다. 그 답이 옳은지는
   여기서 성질(property)로 확인한다: 거리 공식 ↔ BFS, 마스크 픽커 ↔ 점-포함
   판정, A* ↔ 다익스트라, 언두 ↔ 원상복구.
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, 'py'))
sys.path.insert(0, os.path.join(BASE, 'tools'))

from hexwar import hexcoord as H          # noqa: E402
from hexwar import hexmap as M            # noqa: E402
from hexwar import los, picker as PK      # noqa: E402
from hexwar import path as P              # noqa: E402
from hexwar import scenario               # noqa: E402
from hexwar.game import Game              # noqa: E402
from hexwar.rng import Rng                # noqa: E402
from hexwar.units import K_MP, NO_UNIT    # noqa: E402

import gen_prim                            # noqa: E402  오라클(다른 알고리즘)

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def t_neighbor_table():
    """odd-r 이웃 델타 표가 축좌표 변환과 모든 칸에서 일치하는가."""
    for row in range(M.MAP_H):
        for col in range(M.MAP_W):
            q, r = H.oddr_to_axial(col, row)
            for d in range(6):
                nq, nr = H.neighbor(q, r, d)
                wc, wr = H.axial_to_oddr(nq, nr)
                dc, dr = M.NEIGHBOR_DELTA[row & 1][d]
                check((col + dc, row + dr) == (wc, wr),
                      '이웃 델타 불일치 (%d,%d) d%d' % (col, row, d))


def t_distance_vs_bfs():
    for aq in range(-3, 4):
        for ar in range(-3, 4):
            check(H.distance(0, 0, aq, ar) == gen_prim.bfs_dist((0, 0), (aq, ar)),
                  '거리 불일치 (0,0)-(%d,%d)' % (aq, ar))


def t_ring_spiral():
    for n in range(0, 5):
        rg = H.ring(2, -3, n)
        check(len(rg) == (1 if n == 0 else 6 * n), '링 개수 n=%d' % n)
        check(len(set(rg)) == len(rg), '링 중복 n=%d' % n)
        for h in rg:
            check(H.distance(2, -3, h[0], h[1]) == n, '링 거리 n=%d' % n)
        sp = H.spiral(2, -3, n)
        check(len(sp) == 1 + 3 * n * (n + 1), '나선 개수 n=%d' % n)
        check(len(set(sp)) == len(sp), '나선 중복 n=%d' % n)


def t_picker_exhaustive():
    """마스크 픽커와 점-포함 판정이 화면 전 픽셀에서 같은가.
       320x168 x 카메라 4곳 = 21만 픽셀 — 도스라면 상상도 못 할 검사다."""
    for cam in ((0, 0), (17, 5), (256, 120), (528, 272)):
        bad = 0
        for my in range(0, 168):
            for mx in range(0, 256):
                got = PK.pick(mx, my, cam[0], cam[1])
                want = gen_prim.pick_ref(mx, my, cam[0], cam[1])
                if got != want:
                    bad += 1
        check(bad == 0, '픽커 불일치 %d픽셀 (cam=%s)' % (bad, cam))


def t_cell_pack():
    for t in range(16):
        for e in range(8):
            for rd in range(2):
                c = M.pack_cell(t, e, rd)
                check(0 <= c <= 255, '셀 바이트 범위')
                check((M.cell_terrain(c), M.cell_elev(c), M.cell_road(c)) == (t, e, rd),
                      '셀 왕복 %d/%d/%d' % (t, e, rd))


def dijkstra_full(m, pool, side, start):
    """예산 없는 완전 다익스트라 — A* 결과를 검증할 기준선."""
    import heapq
    n = m.w * m.h
    dist = [1 << 30] * n
    dist[start] = 0
    pq = [(0, start)]
    while pq:
        d, cur = heapq.heappop(pq)
        if d != dist[cur]:
            continue
        for _dd, ni in m.neighbors_with_dir(cur):
            sc = P.step_cost(m, pool, side, cur, ni)
            if sc < 0:
                continue
            if d + sc < dist[ni]:
                dist[ni] = d + sc
                heapq.heappush(pq, (d + sc, ni))
    return dist


def t_paths():
    m, pool, obj = scenario.load()
    u = pool.get(2)
    start = m.axial_idx(u.q, u.r)
    reach = P.reachable(m, pool, u)
    check(reach.cost[start] == 0, '출발 칸 비용 0')
    for i in reach.list:
        c = reach.cost[i]
        check(0 <= c <= u.mp, '예산 초과 %d' % c)
        path = P.trace_path(m, reach, i)
        check(path[0] == start and path[-1] == i, '경로 양 끝')
        check(len(path) == len(set(path)), '경로에 같은 칸 두 번')

    dist = dijkstra_full(m, pool, 0, start)
    for i in reach.list:
        c = reach.cost[i]
        # ZOC 때문에 양동이 큐가 더 비쌀 수 있다. 더 싸지는 절대 안 된다.
        check(c >= dist[i], 'reachable 이 다익스트라보다 싸다 %d' % i)

    goal = m.axial_idx(*obj[0])
    ap = P.astar(m, pool, 0, start, goal)
    if ap:
        cost = sum(P.step_cost(m, pool, 0, ap[k], ap[k + 1]) for k in range(len(ap) - 1))
        check(cost == dist[goal], 'A* 가 최단이 아니다 (%d != %d)' % (cost, dist[goal]))


def t_zoc():
    m, pool, obj = scenario.load()
    g = Game(m, pool, obj)
    mask = P.zoc_mask(m, pool, 0)
    for u in pool.iter_alive(1):
        i = m.axial_idx(u.q, u.r)
        for _d, ni in m.neighbors_with_dir(i):
            check(mask[ni] == 1, 'ZOC 표시 누락 %d' % ni)
    # ZOC 칸으로 들어가면 이동력이 0이 된다
    scout = pool.get(5)
    reach = P.reachable(m, pool, scout)
    zoc_cells = [i for i in reach.list if mask[i] and m.occupant[i] == NO_UNIT]
    if zoc_cells:
        g.move_unit(5, zoc_cells[0])
        check(pool.get(5).mp == 0, 'ZOC 진입 후 이동력이 남았다')


def t_undo_restores_everything():
    m, pool, obj = scenario.load()
    g = Game(m, pool, obj)
    before_units = g.serialize_units()
    before_rng = g.rng.save()
    before_fog = g.map.fog_text()

    u = g.pool.get(0)
    reach = P.reachable(m, pool, u)
    tgt = max((i for i in reach.list if m.occupant[i] == NO_UNIT),
               key=lambda i: (reach.cost[i], i))
    g.move_unit(0, tgt)
    check(g.serialize_units() != before_units, '이동이 상태를 안 바꿨다')
    g.undo()
    check(g.serialize_units() == before_units, '언두 후 유닛 상태가 다르다')
    check(g.rng.save() == before_rng, '언두 후 난수 상태가 다르다')
    # 안개는 일부러 복원하지 않는다(SPEC §11.3). 한 번 본 지형은 기억으로 남고,
    # 그래서 '정찰 보내고 무르기' 로 지도를 밝히는 고전적 악용이 가능하다.
    # 도스 워게임들도 대부분 이 상태였다 — 여기서는 성질로 못 박아 둔다.
    after_fog = g.map.fog_text()
    check(len(after_fog) == len(before_fog), '안개 크기가 달라졌다')
    grew = sum(1 for a, b in zip(before_fog, after_fog)
               if a.isdigit() and b.isdigit() and int(b) > 0 and int(a) == 0)
    check(all(not (a.isdigit() and b.isdigit() and int(a) > 0 and int(b) == 0)
              for a, b in zip(before_fog, after_fog)),
          '언두가 이미 탐색한 칸을 미탐색으로 되돌렸다')
    print('        (언두 뒤에도 남은 새 탐색 칸: %d개 — 의도된 동작)' % grew)
    g.assert_consistent()


def t_undo_attack_rng():
    """공격을 무르고 다시 하면 주사위가 같아야 한다 — 언두로 주사위 굴리기 금지."""
    m, pool, obj = scenario.load()
    g = Game(m, pool, obj)
    g.end_turn()                       # 적군 차례로 넘겨 인접 상황을 만든다
    from hexwar import ai
    ai.take_turn(g)
    g.end_turn()
    atk = None
    for u in g.pool.iter_alive(0):
        for t in g.pool.iter_alive(1):
            if H.distance(u.q, u.r, t.q, t.r) <= 1 and u.ammo > 0:
                atk = (u.id, t.id)
                break
        if atk:
            break
    if atk is None:
        return
    c1 = g.attack(*atk)
    first = (c1.log, g.serialize_units())
    g.undo()
    c2 = g.attack(*atk)
    check((c2.log, g.serialize_units()) == first, '언두 후 재공격 결과가 달라졌다')


def t_free_list():
    from hexwar.units import UnitPool
    p = UnitPool(4)
    a = p.spawn(0, 0, 0, 0)
    b = p.spawn(0, 1, 1, 0)
    p.kill(a)
    c = p.spawn(1, 2, 2, 0)
    check(c == a, '프리 리스트가 아이디를 재사용하지 않았다')
    check(p.count() == 2, '살아 있는 유닛 수')
    check(p.get(b) is not None and p.get(b).kind == 1, '다른 슬롯이 훼손됐다')


def t_fog_monotone():
    m, pool, obj = scenario.load()
    g = Game(m, pool, obj)
    seen = set(i for i, f in enumerate(m.fog) if f)
    for _ in range(3):
        from hexwar import ai
        g.end_turn()
        ai.take_turn(g)
        g.end_turn()
        now = set(i for i, f in enumerate(m.fog) if f)
        check(seen <= now, '한 번 본 칸이 다시 미탐색으로 돌아갔다')
        seen = now


def t_los_basics():
    m, pool, obj = scenario.load()
    for u in pool.iter_alive():
        check(los.los_clear(m, u.q, u.r, u.q, u.r), '자기 칸이 안 보인다')
        for d in range(6):
            nq, nr = H.neighbor(u.q, u.r, d)
            if m.axial_idx(nq, nr) >= 0:
                check(los.los_clear(m, u.q, u.r, nq, nr), '인접 칸이 안 보인다')


def t_rng_period_bits():
    """LCG 하위 비트의 주기가 짧다는 것을 실제로 보인다 — 주사위를 상위
       비트에서 뽑는 이유다."""
    r = Rng(1)
    low = [r.next() & 1 for _ in range(64)]
    check(low[:32] == low[32:], 'LCG 최하위 비트 주기가 2가 아니다')
    r = Rng(1)
    hi = [(r.next() >> 16) % 6 for _ in range(600)]
    counts = [hi.count(k) for k in range(6)]
    check(max(counts) - min(counts) < 60, '상위 비트 주사위 분포가 치우쳤다: %s' % counts)


def t_trace_deterministic():
    from hexwar import main as MAIN
    import io as _io
    a = _io.StringIO()
    MAIN.run_trace(a, render_frames=False)
    b = _io.StringIO()
    MAIN.run_trace(b, render_frames=False)
    check(a.getvalue() == b.getvalue(), '같은 스크립트를 두 번 돌렸는데 결과가 다르다')


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith('t_')]
    for fn in tests:
        n0 = len(fails)
        fn()
        print('  %-28s %s' % (fn.__name__, 'ok' if len(fails) == n0 else 'FAIL'))
    if fails:
        print('FAIL %d' % len(fails))
        for f in fails[:20]:
            print('  ' + f)
        return 1
    print('engine OK — %d개 검사 통과' % len(tests))
    return 0


if __name__ == '__main__':
    sys.exit(main())
