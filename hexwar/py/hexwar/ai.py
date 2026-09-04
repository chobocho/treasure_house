# -*- coding: utf-8 -*-
"""적군 AI — 도스 워게임의 '충분히 그럴듯한' 수준을 목표로 한다.

   1994년의 AI 는 탐색 트리가 아니라 점수표였다. 유닛마다
     · 때릴 수 있으면 제일 이득인 상대를 때린다
     · 아니면 목표(또는 가장 가까운 적)에 가까워지는 칸으로 간다
   두 규칙이면 사람이 보기에 '싸우는 것처럼' 보인다. 8086 에서 한 턴을
   1초 안에 끝내야 했으므로 이 이상은 애초에 불가능했다.

   결정성이 중요하다: 유닛 아이디 오름차순으로 처리하고, 점수 동점은 항상
   더 작은 인덱스를 고른다. 그래야 골든 트레이스에 적군 턴을 담을 수 있다.
"""

from . import hexcoord as H
from . import path as P
from .combat import attack_of, defense_of
from .units import K_RNG, NO_UNIT


def score_attack(m, pool, a, d):
    """공격 매력도 — 전력차가 클수록, 상대 체력이 낮을수록 높다."""
    return (attack_of(a) - defense_of(m, pool, d)) * 4 + (10 - d.hp) * 2


def best_attack(g, u):
    best, bs = None, -999
    for t in g.pool.iter_alive():
        if t.side == u.side:
            continue
        if H.distance(u.q, u.r, t.q, t.r) > K_RNG[u.kind]:
            continue
        s = score_attack(g.map, g.pool, u, t)
        if s > bs or (s == bs and best is not None and t.id < best.id):
            best, bs = t, s
    return best


def nearest_enemy(g, u):
    best, bd = None, 1 << 30
    for t in g.pool.iter_alive():
        if t.side == u.side:
            continue
        d = H.distance(u.q, u.r, t.q, t.r)
        if d < bd or (d == bd and best is not None and t.id < best.id):
            best, bd = t, d
    return best


def take_turn(g):
    """적군 한 턴 전체. 실행한 명령 수를 돌려준다."""
    acted = 0
    for uid in sorted(u.id for u in g.pool.iter_alive(g.side)):
        u = g.pool.get(uid)
        if u is None:
            continue
        if u.ammo > 0 and u.mp > 0:
            t = best_attack(g, u)
            if t is not None and score_attack(g.map, g.pool, u, t) > -6:
                g.attack(uid, t.id)
                acted += 1
                continue
        tgt = nearest_enemy(g, u)
        if tgt is None or u.mp <= 0:
            continue
        reach = P.reachable(g.map, g.pool, u)
        goal, gs = -1, 1 << 30
        for i in reach.list:
            cost = reach.cost[i]
            if g.map.occupant[i] != NO_UNIT:
                continue
            q, r = g.map.idx_axial(i)
            d = H.distance(q, r, tgt.q, tgt.r)
            key = d * 100 + cost          # 가까울수록, 같으면 싸게
            if key < gs or (key == gs and i < goal):
                goal, gs = i, key
        if goal >= 0 and goal != g.map.axial_idx(u.q, u.r):
            g.move_unit(uid, goal)
            acted += 1
            u = g.pool.get(uid)
            if u is not None and u.ammo > 0 and u.mp > 0:
                t = best_attack(g, u)
                if t is not None:
                    g.attack(uid, t.id)
                    acted += 1
    return acted
