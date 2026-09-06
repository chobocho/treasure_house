# -*- coding: utf-8 -*-
"""AI — 영향 지도·유령 기억·건물 배치·빌드 오더·정찰 (SPEC §17).

   AI 는 **시뮬레이션의 일부**다. sim.step 안에서 돌고 명령을 자기 큐에 바로
   넣는다. 네트워크 지연을 거치지 않아도 되는 이유는 모든 기계가 같은 AI 를
   같은 틱에 돌리기 때문이다 — 결정론이 통신을 대신한다.

   AI 는 안개를 존중한다(§17.3). 이 제약이 없으면 AI 가 전지적이 되고,
   그건 게임이 아니다. 대신 마지막으로 본 위치를 30틱 기억해서 정찰에
   값어치를 만든다.
"""

from . import combat as CB
from . import const as C
from . import econ as E
from . import fixed as F
from . import select as SEL
from . import spatial as S

GHOST_TICKS = 30                 # §17.3 마지막으로 본 위치를 기억하는 틱
PLACE_R = 12                     # §17.4 건물 후보 반경 (타일)
CHASE_R = 3                      # §17.1 추격은 사거리 + 이만큼까지
SPREAD = 3                       # §17.2 확산 반복 횟수
FLEE_NUM, FLEE_DEN = 1, 4        # §17.1 hp 가 1/4 아래면 도망
ARMY_MIN = 6                     # §17.5 이만큼 모이면 나간다
HARV_MIN = 4


# ── SPEC §17.2 영향 지도 ────────────────────────────────────────────────────
def strength(w, i):
    """전력 = 기본 + 관통 + hp/4. 이 덱의 규칙이다."""
    return C.BASIC[w.kind[i]] + C.PIERCE[w.kind[i]] + F.floordiv(w.hp[i], 4)


def _spread(m, seed):
    """3회 확산. 가중치 4 + 8 = 12 로 나눈다.

       정수 나눗셈의 내림 때문에 매 반복 조금씩 줄어드는데, 그 감쇠가 곧
       "멀수록 영향이 적다"이다. 별도의 감쇠 계수를 두지 않는 이유가 이것이다.
       O(3 × 칸수 × 9).
    """
    cur = seed
    for _ in range(SPREAD):
        nxt = [0] * (m.w * m.h)
        for y in range(m.h):
            for x in range(m.w):
                acc = 4 * cur[y * m.w + x]
                for d in range(8):
                    u, v = x + F.DX[d], y + F.DY[d]
                    if 0 <= u < m.w and 0 <= v < m.h:
                        acc += cur[v * m.w + u]
                nxt[y * m.w + x] = F.floordiv(acc, 12)
        cur = nxt
    return cur


def _seeds(w, fog, p, m, enemy_only):
    seed = [0] * (m.w * m.h)
    for i in range(1, C.MAX_ENT):
        if w.alive[i] == 0 or w.hp[i] <= 0:
            continue
        t = w.ty[i] * m.w + w.tx[i]
        if w.owner[i] == p:
            if not enemy_only:
                seed[t] += strength(w, i)
        elif fog.visible(p, t):            # 보이는 적만 (§17.3)
            seed[t] += strength(w, i) if enemy_only else -strength(w, i)
    return seed


def influence(w, fog, p, m):
    return _spread(m, _seeds(w, fog, p, m, False))


def threat(w, fog, p, m):
    return _spread(m, _seeds(w, fog, p, m, True))


# ── SPEC §17.3 유령 (마지막으로 본 위치) ────────────────────────────────────
class Memory(object):
    """적을 마지막으로 본 자리를 30틱 기억한다. 건물 자리는 잊지 않는다 —
       건물은 움직이지 않으므로 한 번 본 것을 잊는 편이 오히려 거짓말이다."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.ttl = [0] * (w * h)
        self.base_tile = -1

    def update(self, world, fog, p):
        for i in range(len(self.ttl)):
            if self.ttl[i] > 0:
                self.ttl[i] -= 1
        for j in range(1, C.MAX_ENT):
            if world.alive[j] == 0 or world.owner[j] == p or world.hp[j] <= 0:
                continue
            t = world.ty[j] * self.w + world.tx[j]
            if not fog.visible(p, t):
                continue
            self.ttl[t] = GHOST_TICKS
            if C.IS_BUILDING[world.kind[j]]:
                if self.base_tile < 0 or t < self.base_tile:
                    self.base_tile = t

    def ghosts(self):
        return [i for i in range(len(self.ttl)) if self.ttl[i] > 0]

    def enemy_base_known(self, world, fog, p):
        return self.base_tile >= 0

    def enemy_base(self, world, fog, p):
        if self.base_tile < 0:
            return None
        return (self.base_tile % self.w, self.base_tile // self.w)


# ── SPEC §17.4 건물 배치 ────────────────────────────────────────────────────
def place_score(m, ec, fire, thr, kind, x, y, cx, cy, ore):
    """점수 — fire 항이 벽에 붙지 않게 하고, threat 항이 전선을 피하게 한다."""
    i = y * m.w + x
    sc = 100 - 3 * F.d83(x - cx, y - cy) + 2 * fire[i] - thr[i]
    if kind == C.REF and ore >= 0:
        sc += 40 - 8 * F.d83(ore % m.w - x, ore // m.w - y)
    return sc


def best_placement(w, m, mv, ec, fire, thr, p, kind, centre):
    """기지 중심 반경 12 안에서 점수 최대, 동점이면 타일 번호 최소."""
    cx, cy = centre
    ore = ec.nearest_ore(m, cx, cy) if kind == C.REF else -1
    best, bs, bi = None, None, None
    for y in range(cy - PLACE_R, cy + PLACE_R + 1):
        for x in range(cx - PLACE_R, cx + PLACE_R + 1):
            if not m.in_map(x, y):
                continue
            if F.dinf(x - cx, y - cy) > PLACE_R:
                continue
            if not ec.placeable(w, m, mv, kind, x, y, p):
                continue
            i = y * m.w + x
            sc = place_score(m, ec, fire, thr, kind, x, y, cx, cy, ore)
            if bs is None or sc > bs or (sc == bs and i < bi):
                best, bs, bi = (x, y), sc, i
    return best


# ── SPEC §17.5 빌드 오더 ────────────────────────────────────────────────────
def _count(w, p, kind):
    n = 0
    for i in range(1, C.MAX_ENT):
        if (w.alive[i] == 1 and w.owner[i] == p and w.kind[i] == kind
                and w.hp[i] > 0):
            n += 1
    return n


def _army(w, p):
    n = 0
    for i in range(1, C.MAX_ENT):
        if (w.alive[i] == 1 and w.owner[i] == p and w.hp[i] > 0
                and C.IS_BUILDING[w.kind[i]] == 0 and C.BASIC[w.kind[i]] > 0):
            n += 1
    return n


def producer(w, ec, p, kind):
    """그 유닛을 뽑을 수 있는 내 건물 중 인덱스가 가장 작은 것. 없으면 -1."""
    if not C.PREREQ[kind]:
        return -1
    need = C.PREREQ[kind][0]
    for i in range(1, C.MAX_ENT):
        if (w.alive[i] == 1 and w.owner[i] == p and w.kind[i] == need
                and w.hp[i] > 0 and len(ec.queue[i]) < E.QUEUE_MAX):
            return i
    return -1


def _can_train(w, ec, p, kind):
    bi = producer(w, ec, p, kind)
    if bi < 0 or not ec.can_build(w, p, kind):
        return -1
    if ec.credits[p] < C.COST[kind]:
        return -1
    if ec.supply_used[p] + C.POP[kind] > ec.supply_cap[p]:
        return -1
    return bi


def _can_build(w, ec, p, kind, credits):
    if ec.credits[p] < credits or not ec.can_build(w, p, kind):
        return False
    return True


def _rule_harvester(w, ec, mem, p):
    if _count(w, p, C.HARV) >= HARV_MIN:
        return None
    bi = _can_train(w, ec, p, C.HARV)
    return ('TRAIN', C.HARV, bi) if bi >= 0 else None


def _rule_refinery(w, ec, mem, p):
    if _count(w, p, C.REF) > 0:
        return None
    return ('BUILD', C.REF) if _can_build(w, ec, p, C.REF, 300) else None


def _rule_barracks(w, ec, mem, p):
    if _count(w, p, C.BARR) > 0:
        return None
    return ('BUILD', C.BARR) if _can_build(w, ec, p, C.BARR, 400) else None


def _rule_infantry(w, ec, mem, p):
    if _army(w, p) >= ARMY_MIN:
        return None
    bi = _can_train(w, ec, p, C.INF)
    return ('TRAIN', C.INF, bi) if bi >= 0 else None


def _rule_attack(w, ec, mem, p):
    if _army(w, p) < ARMY_MIN or not mem.enemy_base_known(w, None, p):
        return None
    x, y = mem.enemy_base(w, None, p)
    return ('ATTACK', x, y)


def _rule_defend(w, ec, mem, p):
    return ('DEFEND',)


# 여섯 줄이 AI 전부다. 위에서부터 훑어 처음으로 조건을 만족하는 하나를 실행한다.
RULES = [_rule_harvester, _rule_refinery, _rule_barracks,
         _rule_infantry, _rule_attack, _rule_defend]


def build_order(w, ec, mem, p):
    for rule in RULES:
        act = rule(w, ec, mem, p)
        if act is not None:
            return act
    return ('DEFEND',)


# ── SPEC §17.1 유닛 FSM ─────────────────────────────────────────────────────
def unit_tick(w, i, m, mv, orders):
    """한 유닛의 상태 전이. 평가 순서가 곧 우선순위다."""
    kind = w.kind[i]
    if C.IS_BUILDING[kind]:
        return
    if kind == C.HARV:
        if w.hp[i] * FLEE_DEN < C.HP[kind] * FLEE_NUM:   # hp 25 % 아래
            h = 0
            for j in range(1, C.MAX_ENT):
                if (w.alive[j] == 1 and w.owner[j] == w.owner[i]
                        and w.kind[j] in E.DEPOT and w.hp[j] > 0):
                    h = j
                    break
            w.state[i] = C.ST_FLEE
            if h:
                mv.order(i, w.tx[h], w.ty[h])
            return
        if w.state[i] == C.ST_FLEE:
            w.state[i] = C.ST_SEEK         # 회복하면 하던 일로 돌아간다
        return
    tgt, approach = CB.pick_target(w, i, 0, w.state[i] == C.ST_MOVE)
    if tgt and not approach:
        w.target[i] = tgt
        w.state[i] = C.ST_ATTACK
        return
    if w.state[i] == C.ST_ATTACK or w.state[i] == C.ST_MOVE:
        cur = w.target[i]
        if w.valid(cur):
            j = S.index(cur)
            d = F.dinf(w.tx[j] - w.tx[i], w.ty[j] - w.ty[i])
            if d <= C.RANGE[kind] + CHASE_R:
                w.state[i] = C.ST_MOVE     # 추격
                mv.order(i, w.tx[j], w.ty[j])
                orders.push(i, (SEL.ATTACK_MOVE, w.tx[j], w.ty[j], cur), False)
                return
        w.target[i] = 0
        w.state[i] = C.ST_IDLE
        return
    if tgt:
        w.target[i] = tgt
        w.state[i] = C.ST_MOVE
        return
    if not mv.path[i] and mv.goal[i] < 0:
        w.state[i] = C.ST_IDLE


# ── SPEC §17.6 정찰 ─────────────────────────────────────────────────────────
def scout_targets(m, fog, p):
    """미탐험 클러스터의 중심, **클러스터 번호 오름차순**.

       정찰병이 죽으면 다음 유닛이 목록의 다음 항목부터 이어 간다 —
       목록이 결정론적이어야 그 이어받기가 세 언어에서 같다.
    """
    out = []
    cw = (m.w + C.CLUSTER - 1) // C.CLUSTER
    ch = (m.h + C.CLUSTER - 1) // C.CLUSTER
    for cy in range(ch):
        for cx in range(cw):
            seen = False
            for y in range(cy * C.CLUSTER, min(m.h, (cy + 1) * C.CLUSTER)):
                for x in range(cx * C.CLUSTER, min(m.w, (cx + 1) * C.CLUSTER)):
                    if fog.explored[p][y * m.w + x]:
                        seen = True
                        break
                if seen:
                    break
            if not seen:
                out.append((cx * C.CLUSTER + C.CLUSTER // 2,
                            cy * C.CLUSTER + C.CLUSTER // 2))
    return out
