# -*- coding: utf-8 -*-
"""시뮬레이션 — 유일한 진입점 (SPEC §18).

   **상태를 바꾸는 함수는 `step` 하나뿐이다.** 렌더는 읽기만 하고, UI 는 명령을
   만들 뿐이며, AI 조차 같은 자료형의 명령으로 말한다. 이 규율이 19부(락스텝)와
   20부(리플레이)의 전제 전부다.

   틱의 아홉 단계 순서는 명세다. 바꾸면 골든이 통째로 틀어진다.
"""

from . import ai as AI
from . import combat as CB
from . import const as C
from . import econ as E
from . import fixed as F
from . import flow as FL
from . import fog as FG
from . import move as M
from . import rng as R
from . import select as SEL
from . import spatial as S
from . import tmap as T

# ── §18.3 이벤트 종류 ───────────────────────────────────────────────────────
EV_SPAWN, EV_DIE, EV_HIT, EV_BUILD_DONE = 0, 1, 2, 3
EV_MINE, EV_UNLOAD, EV_ORDER, EV_WIN, EV_MESSAGE = 4, 5, 6, 7, 8

# ── §18.5 트리거 ────────────────────────────────────────────────────────────
CT_TICK_GE, CT_UNIT_COUNT, CT_BUILDING_DESTROYED = 0, 1, 2
CT_AREA_ENTERED, CT_CREDITS_GE = 3, 4
AC_SPAWN, AC_MESSAGE, AC_WIN, AC_LOSE, AC_REVEAL = 0, 1, 2, 3, 4
CMP_GE, CMP_LE, CMP_EQ = 0, 1, 2

AI_PERIOD = AI.__dict__.get('AI_PERIOD', 15)    # §17.5 빌드 오더 평가 주기

CMD = {'MOVE': SEL.MOVE, 'AMOVE': SEL.ATTACK_MOVE, 'ATTACK': SEL.ATTACK,
       'HARVEST': SEL.HARVEST, 'STOP': SEL.STOP, 'HOLD': SEL.HOLD,
       'BUILD': SEL.BUILD, 'TRAIN': SEL.TRAIN}


def _at(t, k):
    """트리거 인자는 길이가 들쭉날쭉하다 — 없는 칸은 0 으로 읽는다."""
    return t[k] if k < len(t) else 0


class Script(object):
    def __init__(self):
        self.ticks = 0
        self.players = 0
        self.lines = []


def parse_script(text):
    """§18.6 시나리오 스크립트. `#` 로 시작하는 줄은 주석이다."""
    sc = Script()
    for raw in text.split('\n'):
        ln = raw.strip()
        if not ln or ln.startswith('#') or ln.startswith('RTSS'):
            continue
        if ln.startswith('ticks '):
            sc.ticks = int(ln.split()[1])
            continue
        if ln.startswith('players '):
            sc.players = int(ln.split()[1])
            continue
        p = ln.split()
        sc.lines.append((int(p[0]), int(p[1]), p[2], p[3],
                         int(p[4]), int(p[5]), int(p[6])))
    return sc


class _Hash(object):
    """FNV-1a 를 흘려 넣는다 — 바이트열을 통째로 만들지 않는 편이
       세 언어 모두에서 메모리와 시간이 덜 든다 (SPEC §18.4)."""

    def __init__(self):
        self.h = F.FNV_OFFSET

    def b1(self, v):
        # int() 를 한 번 거치는 이유는 §19.4 의 주입 버그 때문이다. 그때만
        # prog·px·py 가 실수가 되고, 해시는 그 잘린 값을 그대로 본다.
        self.h = F.fnv1a_step(self.h, int(v) % 256)

    def b2(self, v):
        v = int(v) % 65536                              # 음수는 2의 보수로 접는다
        self.b1(v // 256)
        self.b1(v % 256)

    def b4(self, v):
        v = int(v) % 4294967296
        self.b2(v // 65536)
        self.b2(v % 65536)


class Sim(object):
    def __init__(self, m, seed, players=2, float_bug=False):
        self.m = m
        self.players = players
        self.w = S.World(m.w, m.h)
        self.fog = FG.Fog(m.w, m.h)
        self.ec = E.Econ(m)
        self.mv = M.Movement(self.w, m, float_bug)
        self.pj = CB.Projectiles(m.w)
        self.rng = R.LCG(seed)
        self.orders = SEL.Orders()
        self.mem = [AI.Memory(m.w, m.h) for _ in range(C.MAX_PLAYER)]
        self.ai_enabled = [False] * C.MAX_PLAYER
        self.ai_rules = None                    # None 이면 §17.5 의 여섯 줄
        self.tick = 0
        self.events = []
        self.triggers = []
        self.fired = []
        self.winner = -1
        self.loser = []
        self.last_hit = [0] * C.MAX_ENT
        self.last_spawn = [0] * C.MAX_PLAYER
        self.sight_at = [-1] * C.MAX_ENT        # 안개가 알고 있는 위치
        self._had_building = [False] * C.MAX_PLAYER
        self._map_hash = 0
        self._map_hash_version = -1
        self._fire = None
        self._fire_version = -1

    # ── 생성·소멸 ──────────────────────────────────────────────────────────
    def spawn(self, p, kind, x, y):
        h = self.w.spawn(p, kind, x, y)
        if h == 0:
            return 0
        i = S.index(h)
        self.w.hp[i] = C.HP[kind]               # 태어나는 것은 정격 hp 로
        self.mv.claim(i)
        self.fog.add_sight(p, x, y, C.SIGHT[kind])
        self.sight_at[i] = y * self.m.w + x
        if C.IS_BUILDING[kind]:
            self._had_building[p] = True
        else:
            self.last_spawn[p] = h
        if kind == C.HARV:
            self.w.state[i] = C.ST_SEEK
        return h

    def setup_start(self, ai=True):
        """§25.4 시작 조건. 골든 시나리오는 스크립트가 몰므로 AI 를 끈다 —
           한 지갑을 둘이 쓰면 서로의 건설을 굶긴다(§18.6)."""
        for p in range(min(self.players, len(self.m.starts))):
            sx, sy = self.m.starts[p]
            self.spawn(p, C.HQ, sx - 1, sy - 1)
            for k in range(C.START_HARV):
                x, y = sx + 2, sy + 1 + k
                if not self.m.passable_terrain(x, y, C.MOVE_KIND[C.HARV]):
                    x, y = sx, sy + 2 + k
                self.spawn(p, C.HARV, x, y)
            self.ec.credits[p] = C.START_CREDITS
            self.ai_enabled[p] = ai
        self.ec.recount_supply(self.w)

    def add_trigger(self, cond, act, once):
        self.triggers.append((cond, act, once))
        self.fired.append(False)

    # ── SPEC §18.2 틱의 아홉 단계 ──────────────────────────────────────────
    def step(self, orders):
        self.events = []
        self.tick += 1
        self._check_sorted(orders)
        for o in orders:                        # 1. 명령 적용
            self._apply_order(o)
        self._phase_ai()                        # 2. AI
        self._phase_econ()                      # 3. 생산·경제
        self.mv.step()                          # 4. 이동
        self._phase_combat()                    # 5. 전투
        self._phase_death()                     # 6. 사망
        self._phase_sight()                     # 7. 시야
        self._phase_triggers()                  # 8. 트리거·승패
        return self.state_hash()                # 9. 상태 해시

    def _check_sorted(self, orders):
        for k in range(1, len(orders)):
            if orders[k - 1] > orders[k]:
                raise ValueError('명령 목록이 정렬되어 있지 않다 (SPEC §18.1)')

    # ── 1단계 ──────────────────────────────────────────────────────────────
    def _apply_order(self, o):
        p, issuer, kind, a, b, c = o
        if not self.w.valid(issuer):
            return
        i = S.index(issuer)
        if self.w.owner[i] != p:
            return                              # 남의 유닛에 내린 명령은 무시
        w, m = self.w, self.m
        if kind == SEL.MOVE or kind == SEL.ATTACK_MOVE:
            if self.mv.order(i, a, b):
                w.state[i] = C.ST_MOVE
                w.target[i] = 0
        elif kind == SEL.ATTACK:
            w.target[i] = c
            w.state[i] = C.ST_ATTACK
            if w.valid(c):
                j = S.index(c)
                self.mv.order(i, w.tx[j], w.ty[j])
        elif kind == SEL.HARVEST:
            if w.kind[i] == C.HARV:
                w.state[i] = C.ST_SEEK
        elif kind == SEL.STOP:
            self.mv.stop(i)
            self.orders.clear(i)
            w.state[i] = C.ST_IDLE
        elif kind == SEL.HOLD:
            self.mv.stop(i)
            w.state[i] = C.ST_IDLE
        elif kind == SEL.TRAIN:
            self.ec.enqueue(w, i, a)
        elif kind == SEL.BUILD:
            self._do_build(p, a, b, c)
        self.events.append((EV_ORDER, p, issuer, kind))

    def _do_build(self, p, kind, x, y):
        """§16.4 — 통과하면 그 자리에 즉시 엔티티가 생기고 짓기 시작한다."""
        if C.IS_BUILDING[kind] == 0:
            return False
        if not self.ec.can_build(self.w, p, kind):
            return False
        if self.ec.credits[p] < C.COST[kind]:
            return False
        if not self.ec.placeable(self.w, self.m, self.mv, kind, x, y, p):
            self._shove(p, kind, x, y)      # §16.5 — 내 유닛이면 비키게 한다
            return False
        self.ec.credits[p] -= C.COST[kind]      # 선불
        h = self.spawn(p, kind, x, y)
        if h == 0:
            self.ec.credits[p] += C.COST[kind]
            return False
        i = S.index(h)
        self.w.state[i] = C.ST_BUILD
        self.w.hp[i] = 1
        self.w.timer[i] = C.BUILD_TICKS[kind]
        return True

    def _shove(self, p, kind, x, y):
        """발자국을 막은 내 유닛들에게 바깥으로 한 걸음 명령을 준다 (§16.5).

           밀면서 동시에 짓지는 않는다 — 아직 그 칸에 선 유닛 위에 건물을
           얹으면 불변식 R 이 깨진다. 다음 재시도에서 자리가 빈다.
        """
        w, m = self.w, self.m
        f = C.FOOT[kind]
        cx, cy = x + f // 2, y + f // 2
        for dy in range(f):
            for dx in range(f):
                u, v = x + dx, y + dy
                if not m.in_map(u, v):
                    continue
                h = self.mv.resv[v * m.w + u]
                if not w.valid(h):
                    continue
                j = S.index(h)
                if w.owner[j] != p or C.IS_BUILDING[w.kind[j]]:
                    continue
                out = F.atan8(w.tx[j] - cx, w.ty[j] - cy)
                pd = M.push_dir(self.mv, j, F.fmod(out + 4, 8))
                if pd != M.STOP_DIR:
                    t = ((w.ty[j] + F.DY[pd]) * m.w + w.tx[j] + F.DX[pd])
                    self.mv.path[j] = [t]
                    self.mv.goal[j] = t

    # ── 2단계 AI ───────────────────────────────────────────────────────────
    def _phase_ai(self):
        for p in range(self.players):
            if not self.ai_enabled[p]:
                continue
            self.mem[p].update(self.w, self.fog, p)
            if self.tick % AI_PERIOD == 0:
                self._ai_decide(p)
            for i in range(1, C.MAX_ENT):
                if (self.w.alive[i] == 1 and self.w.owner[i] == p
                        and C.IS_BUILDING[self.w.kind[i]] == 0):
                    AI.unit_tick(self.w, i, self.m, self.mv, self.orders)

    def _brushfire(self):
        if self._fire_version != self.m.version:
            self._fire = FL.brushfire(self.m, 0)
            self._fire_version = self.m.version
        return self._fire

    def _ai_decide(self, p):
        act = AI.build_order(self.w, self.ec, self.mem[p], p, self.ai_rules)
        if act[0] == 'TRAIN':
            self.ec.enqueue(self.w, act[2], act[1])
        elif act[0] == 'BUILD':
            centre = self._base_of(p)
            if centre is None:
                return
            thr = AI.threat(self.w, self.fog, p, self.m)
            spot = AI.best_placement(self.w, self.m, self.mv, self.ec,
                                     self._brushfire(), thr, p, act[1], centre)
            if spot is not None:
                self._do_build(p, act[1], spot[0], spot[1])
        elif act[0] == 'ATTACK':
            for i in self._army(p):
                self.mv.order(i, act[1], act[2])
                self.w.state[i] = C.ST_MOVE
        else:                                   # DEFEND (+ §17.6 정찰)
            centre = self._base_of(p)
            if centre is None:
                return
            army = self._army(p)
            spots = AI.scout_targets(self.m, self.fog, p)
            for k, i in enumerate(army):
                if self.w.state[i] != C.ST_IDLE or self.mv.path[i]:
                    continue
                if k == 0 and spots:
                    # 첫 유닛 하나만 정찰. 이것이 없으면 적 기지를 영영 모르고
                    # 빌드 오더의 다섯째 줄(전군 공격)이 발화하지 않는다.
                    self.mv.order(i, spots[0][0], spots[0][1])
                    self.w.state[i] = C.ST_MOVE
                else:
                    self.mv.order(i, centre[0], centre[1])

    def _base_of(self, p):
        for i in range(1, C.MAX_ENT):
            if (self.w.alive[i] == 1 and self.w.owner[i] == p
                    and C.IS_BUILDING[self.w.kind[i]] == 1):
                return (self.w.tx[i], self.w.ty[i])
        return None

    def _army(self, p):
        return [i for i in range(1, C.MAX_ENT)
                if (self.w.alive[i] == 1 and self.w.owner[i] == p
                    and C.IS_BUILDING[self.w.kind[i]] == 0
                    and C.BASIC[self.w.kind[i]] > 0)]

    # ── 3단계 생산·경제 ────────────────────────────────────────────────────
    def _phase_econ(self):
        w = self.w
        for i in range(1, C.MAX_ENT):           # 건설 진행
            if (w.alive[i] == 1 and C.IS_BUILDING[w.kind[i]]
                    and w.state[i] == C.ST_BUILD):
                total = C.BUILD_TICKS[w.kind[i]]
                done = total - w.timer[i]
                if done < 0:
                    done = 0
                w.hp[i] = 1 + done * (C.HP[w.kind[i]] - 1) // total
                w.timer[i] -= 1
                if w.timer[i] <= 0:
                    w.timer[i] = 0
                    w.hp[i] = C.HP[w.kind[i]]
                    w.state[i] = C.ST_IDLE
                    self.events.append((EV_BUILD_DONE, w.owner[i],
                                        w.handle(i), w.kind[i]))
        for (bi, kind) in self.ec.step_production(w):
            spot = self._free_near(bi, kind)
            if spot is None:
                continue
            h = self.spawn(w.owner[bi], kind, spot[0], spot[1])
            if h:
                self.events.append((EV_SPAWN, w.owner[bi], h, kind))
        for i in range(1, C.MAX_ENT):
            if w.alive[i] == 1 and w.kind[i] == C.HARV:
                before = self.ec.credits[w.owner[i]]
                self.ec.harvest_tick(w, i, self.m, self.mv)
                if self.ec.credits[w.owner[i]] > before:
                    self.events.append((EV_UNLOAD, w.owner[i], w.handle(i),
                                        self.ec.credits[w.owner[i]] - before))
        self.ec.recount_supply(w)

    def _free_near(self, bi, kind):
        """건물 둘레에서 빈 칸 하나. y 오름차순, 같은 y 안에서 x 오름차순."""
        w, m = self.w, self.m
        mk = C.MOVE_KIND[kind]
        f = C.FOOT[w.kind[bi]]
        for r in range(1, 4):
            for y in range(w.ty[bi] - r, w.ty[bi] + f + r):
                for x in range(w.tx[bi] - r, w.tx[bi] + f + r):
                    if not m.passable_terrain(x, y, mk):
                        continue
                    if self.mv.resv[y * m.w + x] != 0:
                        continue
                    return (x, y)
        return None

    # ── 5단계 전투 ─────────────────────────────────────────────────────────
    def _phase_combat(self):
        w, m = self.w, self.m
        pending = []
        for i in range(1, C.MAX_ENT):
            if w.alive[i] == 0 or w.hp[i] <= 0:
                continue
            kind = w.kind[i]
            if C.BASIC[kind] == 0:
                continue
            if w.cool[i] > 0:
                w.cool[i] -= 1
                continue
            tgt, approach = CB.pick_target(w, i, self.last_hit[i],
                                           w.state[i] == C.ST_MOVE)
            if not tgt or approach:
                continue
            j = S.index(tgt)
            w.target[i] = tgt
            dmg = CB.roll_damage(self.rng, C.BASIC[kind], C.PIERCE[kind],
                                 C.ARMOUR[w.kind[j]])
            w.cool[i] = C.RELOAD[kind]
            if kind == C.ARCHER or kind == C.MORTAR:
                pk = CB.ARC if kind == C.MORTAR else CB.STRAIGHT
                sp = 0 if kind == C.MORTAR else CB.ARROW_SPEED
                if not self.pj.launch(pk, w.px[i], w.py[i], w.px[j], w.py[j],
                                      sp, tgt, dmg):
                    pending.append((tgt, w.handle(i), dmg))
            else:
                pending.append((tgt, w.handle(i), dmg))
        for (tgt, dmg, dest, _y, pkind) in self.pj.step():
            if pkind == CB.ARC:                 # 포물선만 스플래시 (아군도 맞는다)
                for (hh, dd) in CB.splash_hits(w, dest % m.w, dest // m.w, dmg):
                    pending.append((hh, 0, dd))
            elif w.valid(tgt):
                pending.append((tgt, 0, dmg))
        pending.sort()
        for (tgt, src, dmg) in pending:         # **피해는 여기서 한꺼번에**
            if not w.valid(tgt):
                continue
            j = S.index(tgt)
            w.hp[j] -= dmg
            if src:
                self.last_hit[j] = src
            self.events.append((EV_HIT, tgt, src, dmg))

    # ── 6단계 사망 ─────────────────────────────────────────────────────────
    def _phase_death(self):
        w, m = self.w, self.m
        for i in range(1, C.MAX_ENT):
            if w.alive[i] == 0 or w.hp[i] > 0:
                continue
            self.events.append((EV_DIE, w.owner[i], w.handle(i), w.kind[i]))
            t = self.sight_at[i]                # 안개가 아는 위치에서 반납한다
            if t >= 0:
                self.fog.remove_sight(w.owner[i], t % m.w, t // m.w,
                                      C.SIGHT[w.kind[i]])
                self.sight_at[i] = -1
            f = C.FOOT[w.kind[i]]
            building = C.IS_BUILDING[w.kind[i]] == 1
            cells = [(w.tx[i] + dx, w.ty[i] + dy)
                     for dy in range(f) for dx in range(f)]
            self.mv.unclaim(i)
            if building:
                for (x, y) in cells:            # 잔해를 남긴다
                    if m.in_map(x, y):
                        m.set_terrain(x, y, T.RUBBLE)
            w.kill(w.handle(i))

    # ── 7단계 시야 ─────────────────────────────────────────────────────────
    def _phase_sight(self):
        w, m = self.w, self.m
        for (i, old, new) in self.mv.crossed:
            if w.alive[i] == 0:
                continue                        # 6단계에서 이미 반납했다
            r = C.SIGHT[w.kind[i]]
            src = self.sight_at[i]
            if src >= 0:
                self.fog.remove_sight(w.owner[i], src % m.w, src // m.w, r)
            self.fog.add_sight(w.owner[i], new % m.w, new // m.w, r)
            self.sight_at[i] = new

    # ── 8단계 트리거·승패 ──────────────────────────────────────────────────
    def _phase_triggers(self):
        for k in range(len(self.triggers)):
            cond, act, once = self.triggers[k]
            if once and self.fired[k]:
                continue
            if self._cond(cond):
                self._act(act)
                if once:
                    self.fired[k] = True
        self._check_victory()

    def _cond(self, t):
        w = self.w
        kind = t[0]
        if kind == CT_TICK_GE:
            return self.tick >= _at(t, 1)
        if kind == CT_UNIT_COUNT:
            p, uk, cmp_, n = _at(t, 1), _at(t, 2), _at(t, 3), _at(t, 4)
            cnt = len([1 for i in range(1, C.MAX_ENT)
                       if w.alive[i] and w.owner[i] == p and w.kind[i] == uk])
            if cmp_ == CMP_GE:
                return cnt >= n
            if cmp_ == CMP_LE:
                return cnt <= n
            return cnt == n
        if kind == CT_BUILDING_DESTROYED:
            return not self._has_building(_at(t, 1))
        if kind == CT_AREA_ENTERED:
            p, x, y, r = _at(t, 1), _at(t, 2), _at(t, 3), _at(t, 4)
            for i in range(1, C.MAX_ENT):
                if (w.alive[i] and w.owner[i] == p
                        and C.IS_BUILDING[w.kind[i]] == 0
                        and F.dinf(w.tx[i] - x, w.ty[i] - y) <= r):
                    return True
            return False
        if kind == CT_CREDITS_GE:
            return self.ec.credits[_at(t, 1)] >= _at(t, 2)
        return False

    def _act(self, t):
        kind = t[0]
        if kind == AC_SPAWN:
            h = self.spawn(_at(t, 1), _at(t, 2), _at(t, 3), _at(t, 4))
            if h:
                self.events.append((EV_SPAWN, _at(t, 1), h, _at(t, 2)))
        elif kind == AC_MESSAGE:
            self.events.append((EV_MESSAGE, _at(t, 1)))
        elif kind == AC_WIN:
            self._declare(_at(t, 1))
        elif kind == AC_LOSE:
            p = _at(t, 1)
            if p not in self.loser:
                self.loser.append(p)
        elif kind == AC_REVEAL:
            x, y, r = _at(t, 1), _at(t, 2), _at(t, 3)
            self.fog.add_sight(0, x, y, r)
            self.fog.remove_sight(0, x, y, r)   # 탐험만 남기고 시야는 돌려준다

    def _has_building(self, p):
        for i in range(1, C.MAX_ENT):
            if (self.w.alive[i] == 1 and self.w.owner[i] == p
                    and C.IS_BUILDING[self.w.kind[i]] == 1):
                return True
        return False

    def _declare(self, p):
        if self.winner < 0:
            self.winner = p
            self.events.append((EV_WIN, p))

    def _check_victory(self):
        """건물이 전부 파괴되면 패배. 남은 플레이어가 하나면 승리."""
        if self.winner >= 0:
            return
        alive = []
        for p in range(self.players):
            if self._has_building(p):
                alive.append(p)
            elif self._had_building[p] and p not in self.loser:
                self.loser.append(p)
        if len(alive) == 1 and len(self.loser) > 0:
            self._declare(alive[0])

    # ── SPEC §18.4 상태 해시 ───────────────────────────────────────────────
    def map_hash(self):
        """지형이 바뀔 때만 다시 계산한다. 캐시지만 상태의 순수 함수다."""
        if self._map_hash_version != self.m.version:
            hh = _Hash()
            for v in self.m.terrain:
                hh.b1(v)
            for v in self.m.pass_:
                hh.b1(v)
            self._map_hash = hh.h
            self._map_hash_version = self.m.version
        return self._map_hash

    def state_hash(self):
        w = self.w
        hh = _Hash()
        hh.b4(self.tick)
        hh.b4(self.rng.s)
        for p in range(C.MAX_PLAYER):
            hh.b4(self.ec.credits[p])
            hh.b2(self.ec.supply_used[p])
            hh.b2(self.ec.supply_cap[p])
        for i in range(1, C.MAX_ENT):
            hh.b1(w.alive[i])
            if w.alive[i] == 0:
                continue
            hh.b1(w.owner[i])
            hh.b1(w.kind[i])
            hh.b1(w.tx[i])
            hh.b1(w.ty[i])
            hh.b2(w.hp[i])
            hh.b1(w.dir[i])
            hh.b1(w.state[i])
            hh.b4(w.px[i])
            hh.b4(w.py[i])
            hh.b2(w.target[i])
            hh.b2(w.load[i])
            hh.b4(w.prog[i])
            hh.b2(w.from_t[i])
            hh.b2(w.to_t[i])
            hh.b2(w.cool[i])
            hh.b2(w.timer[i])
        hh.b2(self.pj.n())
        for k in range(self.pj.n()):
            hh.b4(self.pj.x[k])
            hh.b4(self.pj.y[k])
            hh.b4(self.pj.vx[k])
            hh.b4(self.pj.vy[k])
            hh.b2(self.pj.target[k])
            hh.b2(self.pj.dmg[k])
        for i in range(1, C.MAX_ENT):
            if w.alive[i] == 0 or C.IS_BUILDING[w.kind[i]] == 0:
                continue
            hh.b1(len(self.ec.queue[i]))
            for k in self.ec.queue[i]:
                hh.b1(k)
            hh.b2(self.ec.progress[i])
        ores = [i for i in range(len(self.ec.ore)) if self.ec.ore[i] > 0]
        hh.b2(len(ores))
        for i in ores:
            hh.b2(i)
            hh.b2(self.ec.ore[i])
        hh.b4(self.map_hash())
        return hh.h

    # ── SPEC §18.6 선택자 ──────────────────────────────────────────────────
    def _select(self, p, sel):
        w = self.w
        out = []
        if sel == 'N':
            h = self.last_spawn[p]
            return [h] if w.valid(h) else []
        for i in range(1, C.MAX_ENT):
            if w.alive[i] == 0 or w.owner[i] != p:
                continue
            k = w.kind[i]
            if sel == 'A':
                if C.IS_BUILDING[k] == 0:
                    out.append(w.handle(i))
            elif sel == 'F':
                if C.IS_BUILDING[k] == 0 and C.BASIC[k] > 0:
                    out.append(w.handle(i))
            elif sel.startswith('K'):
                if k == int(sel[1:]):
                    out.append(w.handle(i))
        out.sort()
        return out

    def script_orders(self, script, tick):
        """스크립트도 사람과 똑같은 경로를 지난다 — 뒷문을 내지 않는다."""
        out = []
        for (t, p, sel, cmd, a, b, c) in script.lines:
            if t != tick:
                continue
            for h in self._select(p, sel):
                out.append((p, h, CMD[cmd], a, b, c))
        out.sort()
        return out
