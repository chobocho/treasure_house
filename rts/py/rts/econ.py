# -*- coding: utf-8 -*-
"""경제 — 자원·채집기 FSM·생산 큐·기술 트리·인구 (SPEC §16).

   생산은 **선불**이다. 큐에 넣는 순간 크레딧이 빠진다. 후불로 두면 "완성
   시점에 돈이 없는" 상태가 생기고, 그 처리 규칙이 언어마다 미묘하게 갈릴
   여지가 생긴다 — 결정론을 위해 게임 디자인을 고른 자리다.
"""

from . import const as C
from . import fixed as F
from . import tmap as T

ORE_PER_TILE = 500
LOAD_MAX = 100
MINE_PER_TICK = 5
UNLOAD_TICKS = 12
QUEUE_MAX = 5
SUPPLY_MAX = 100
BASE_R = 4                       # §16.5 기지 반경 (체비셰프, 건물 원점 기준)
TOUCH_R = 1                      # 채집기가 "닿았다"고 보는 거리

# §16.2 채집기 FSM 상태 — 번호는 const 가 소유한다(§17.1 의 표).
H_SEEK, H_TO_ORE, H_MINE = C.ST_SEEK, C.ST_TO_ORE, C.ST_MINE
H_TO_BASE, H_UNLOAD, H_IDLE = C.ST_TO_BASE, C.ST_UNLOAD, C.ST_IDLE

DEPOT = (C.HQ, C.REF)            # 자원 반납처 (§25.2)


# ── SPEC §16.3 수입률 (정리 16.1) ───────────────────────────────────────────
def round_trip_ticks(d, v):
    """왕복 d 타일, 속도 v(16.16 타일/틱)인 채집기 한 기의 주기 (틱).

       세 항은 왕복 이동·채굴·반납이다. d 가 0 이어도 20 + 12 = 32틱이 든다 —
       **정제소를 광맥에 붙여도 상한이 있다.**
    """
    return (F.floordiv(F.fp(2 * d), v)
            + F.floordiv(LOAD_MAX, MINE_PER_TICK) + UNLOAD_TICKS)


def income10000(d, v):
    """크레딧/틱 × 10000. 나눗셈 한 번으로 끝내려고 정수 배율을 쓴다."""
    return F.floordiv(LOAD_MAX * 10000, round_trip_ticks(d, v))


# ── SPEC §16.6 기술 트리 = DAG (정리 16.2) ──────────────────────────────────
def topo_order(extra=None):
    """칸(Kahn) 위상 정렬. 진입차수 0 은 **번호 오름차순**으로 꺼낸다.

       순환이 있으면 None 을 돌려준다 — 조용히 넘어가지 않는다. 기술 트리는
       데이터이고, 데이터가 잘못되면 터지는 편이 낫다.
    """
    pre = [list(C.PREREQ[k]) for k in range(C.KIND_COUNT)]
    for (k, p) in (extra or []):
        pre[k] = pre[k] + [p]
    indeg = [len(pre[k]) for k in range(C.KIND_COUNT)]
    out = []
    done = [0] * C.KIND_COUNT
    while True:
        pick = -1
        for k in range(C.KIND_COUNT):          # 오름차순 선형 탐색 — 16개다
            if done[k] == 0 and indeg[k] == 0:
                pick = k
                break
        if pick < 0:
            break
        done[pick] = 1
        out.append(pick)
        for k in range(C.KIND_COUNT):
            if done[k] == 0 and pick in pre[k]:
                indeg[k] -= 1
    if len(out) != C.KIND_COUNT:
        return None                            # 남은 노드가 있으면 순환이다
    return out


class Econ(object):
    """플레이어별 크레딧·인구, 타일별 광맥, 건물별 생산 큐."""

    def __init__(self, m):
        self.ore = [0] * (m.w * m.h)
        for i in range(m.w * m.h):
            if m.terrain[i] == T.ORE:
                self.ore[i] = ORE_PER_TILE
        self.credits = [0] * C.MAX_PLAYER
        self.supply_used = [0] * C.MAX_PLAYER
        self.supply_cap = [0] * C.MAX_PLAYER
        self.queue = [[] for _ in range(C.MAX_ENT)]
        self.progress = [0] * C.MAX_ENT
        self.ore_target = [-1] * C.MAX_ENT

    # ── SPEC §16.1 자원 ────────────────────────────────────────────────────
    def nearest_ore(self, m, x, y):
        """d83 최소, 동점이면 타일 번호 오름차순. 없으면 −1."""
        best, bd = -1, -1
        for i in range(m.w * m.h):
            if self.ore[i] <= 0:
                continue
            d = F.d83(i % m.w - x, i // m.w - y)
            if bd < 0 or d < bd:
                bd, best = d, i
        return best

    def mine(self, m, tile, amount):
        """캔 양을 돌려준다. 다 캐면 그 칸은 모래가 되고 지형 version 이 오른다."""
        got = self.ore[tile]
        if got > amount:
            got = amount
        self.ore[tile] -= got
        if self.ore[tile] <= 0 and m.terrain[tile] == T.ORE:
            m.set_terrain(tile % m.w, tile // m.w, T.SAND)
        return got

    # ── SPEC §16.4 생산 큐 ─────────────────────────────────────────────────
    def enqueue(self, w, bi, kind):
        p = w.owner[bi]
        if len(self.queue[bi]) >= QUEUE_MAX:
            return False
        if not self.can_build(w, p, kind):
            return False
        if self.credits[p] < C.COST[kind]:
            return False
        if C.IS_BUILDING[kind] == 0:
            if self.supply_used[p] + C.POP[kind] > self.supply_cap[p]:
                return False
        self.credits[p] -= C.COST[kind]        # 선불
        self.queue[bi].append(kind)
        return True

    def cancel(self, w, bi, k):
        """환불은 100 %. 이 덱의 규칙이며, 부분 환불은 반올림 규칙을 하나 더 만든다."""
        if k < 0 or k >= len(self.queue[bi]):
            return 0
        kind = self.queue[bi][k]
        self.queue[bi] = self.queue[bi][:k] + self.queue[bi][k + 1:]
        if k == 0:
            self.progress[bi] = 0
        self.credits[w.owner[bi]] += C.COST[kind]
        return C.COST[kind]

    def step_production(self, w):
        """한 틱. 완성된 (건물 인덱스, 종류) 목록을 인덱스 오름차순으로."""
        done = []
        for bi in range(1, C.MAX_ENT):
            if w.alive[bi] == 0 or not self.queue[bi]:
                continue
            kind = self.queue[bi][0]
            self.progress[bi] += 1
            if self.progress[bi] >= C.BUILD_TICKS[kind]:
                self.progress[bi] = 0
                self.queue[bi] = self.queue[bi][1:]
                done.append((bi, kind))
        return done

    def can_build(self, w, p, kind):
        """선행이 **완성된 채 살아 있는지** 본다. 병영이 부서지면 보병을 못 뽑는다."""
        for need in C.PREREQ[kind]:
            found = False
            for j in range(1, C.MAX_ENT):
                if (w.alive[j] == 1 and w.owner[j] == p
                        and w.kind[j] == need and w.hp[j] > 0):
                    found = True
                    break
            if not found:
                return False
        return True

    # ── SPEC §16.5 배치 판정 ───────────────────────────────────────────────
    def placeable(self, w, m, mv, kind, x, y, p):
        """발자국 전체가 건설 가능 지형이고 비어 있고, 기지에서 4타일 안."""
        f = C.FOOT[kind]
        for dy in range(f):
            for dx in range(f):
                u, v = x + dx, y + dy
                if not m.in_map(u, v):
                    return False
                i = v * m.w + u
                if F.bit(m.pass_[i], T.BUILD_BIT) != 1:
                    return False
                if mv.resv[i] != 0:
                    return False
        near = False
        any_own = False
        for j in range(1, C.MAX_ENT):
            if (w.alive[j] == 1 and w.owner[j] == p
                    and C.IS_BUILDING[w.kind[j]] == 1):
                any_own = True
                if F.dinf(w.tx[j] - x, w.ty[j] - y) <= BASE_R:
                    near = True
                    break
        return near or not any_own             # 첫 건물은 면제

    # ── SPEC §16.7 인구 ────────────────────────────────────────────────────
    def recount_supply(self, w):
        """유닛은 먹고 건물은 준다. 상한 100. 매 틱 전수로 세도 256칸이다."""
        for p in range(C.MAX_PLAYER):
            self.supply_used[p] = 0
            self.supply_cap[p] = 0
        for j in range(1, C.MAX_ENT):
            if w.alive[j] == 0 or w.hp[j] <= 0:
                continue
            p = w.owner[j]
            if p >= C.MAX_PLAYER:
                continue
            if C.IS_BUILDING[w.kind[j]]:
                self.supply_cap[p] += C.POP[w.kind[j]]
            else:
                self.supply_used[p] += C.POP[w.kind[j]]
        for p in range(C.MAX_PLAYER):
            if self.supply_cap[p] > SUPPLY_MAX:
                self.supply_cap[p] = SUPPLY_MAX

    # ── SPEC §16.2 채집기 FSM ──────────────────────────────────────────────
    def _touching(self, w, i, bi):
        """건물 발자국의 어느 칸에라도 한 칸 안으로 붙었는가."""
        f = C.FOOT[w.kind[bi]]
        dx = 0
        if w.tx[i] < w.tx[bi]:
            dx = w.tx[bi] - w.tx[i]
        elif w.tx[i] > w.tx[bi] + f - 1:
            dx = w.tx[i] - (w.tx[bi] + f - 1)
        dy = 0
        if w.ty[i] < w.ty[bi]:
            dy = w.ty[bi] - w.ty[i]
        elif w.ty[i] > w.ty[bi] + f - 1:
            dy = w.ty[i] - (w.ty[bi] + f - 1)
        return F.dinf(dx, dy) <= TOUCH_R

    def _nearest_depot(self, w, i):
        best, bd = 0, -1
        for j in range(1, C.MAX_ENT):
            if (w.alive[j] == 0 or w.owner[j] != w.owner[i]
                    or w.kind[j] not in DEPOT or w.hp[j] <= 0):
                continue
            d = F.d83(w.tx[j] - w.tx[i], w.ty[j] - w.ty[i])
            if bd < 0 or d < bd:
                bd, best = d, w.handle(j)
        return best

    def _stuck(self, w, mv, i):
        """이동이 포기된 상태 — §13.3 이 24틱 만에 명령을 버렸다는 뜻이다."""
        return mv.goal[i] < 0 and not mv.path[i] and w.prog[i] == 0

    def harvest_tick(self, w, i, m, mv):
        """채집기 한 기의 한 틱. sim 의 3단계에서 핸들 오름차순으로 부른다."""
        st = w.state[i]
        p = w.owner[i]
        if st == H_SEEK:
            tile = self.nearest_ore(m, w.tx[i], w.ty[i])
            if tile < 0:
                w.state[i] = H_IDLE            # 캘 것이 없으면 멈춘다
                return
            self.ore_target[i] = tile
            mv.order(i, tile % m.w, tile // m.w)
            w.state[i] = H_TO_ORE
            return
        if st == H_TO_ORE:
            t = self.ore_target[i]
            if t < 0 or self.ore[t] <= 0:
                w.state[i] = H_SEEK
                return
            if F.dinf(t % m.w - w.tx[i], t // m.w - w.ty[i]) <= TOUCH_R:
                w.state[i] = H_MINE
            elif self._stuck(w, mv, i):
                mv.order(i, t % m.w, t // m.w)  # 길막에 포기했으면 다시 건다
            return
        if st == H_MINE:
            room = LOAD_MAX - w.load[i]
            want = MINE_PER_TICK if MINE_PER_TICK < room else room
            got = self.mine(m, self.ore_target[i], want)
            w.load[i] += got
            if w.load[i] >= LOAD_MAX:
                h = self._nearest_depot(w, i)
                if h == 0:
                    return                     # 반납처가 없으면 실어 둔 채 기다린다
                w.target[i] = h
                bi = h // 256
                mv.order(i, w.tx[bi], w.ty[bi])
                w.state[i] = H_TO_BASE
            elif got == 0:
                w.state[i] = H_SEEK            # 칸이 말랐다
            return
        if st == H_TO_BASE:
            h = w.target[i]
            if not w.valid(h):
                w.state[i] = H_MINE if w.load[i] < LOAD_MAX else H_TO_BASE
                w.target[i] = self._nearest_depot(w, i)
                if w.target[i] == 0:
                    w.state[i] = H_SEEK
                return
            bi = h // 256
            if self._touching(w, i, bi):
                w.state[i] = H_UNLOAD
                w.timer[i] = UNLOAD_TICKS
            elif self._stuck(w, mv, i):
                mv.order(i, w.tx[bi], w.ty[bi])
            return
        if st == H_UNLOAD:
            w.timer[i] -= 1
            if w.timer[i] <= 0:
                self.credits[p] += w.load[i]
                w.load[i] = 0
                w.state[i] = H_SEEK
            return
