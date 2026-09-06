# -*- coding: utf-8 -*-
"""전투 — 피해·표적·투사체·스플래시·란체스터 (SPEC §15).

   피해 공식은 워크래프트 II 의 공식 문서를 따랐다(§15.2). 다만 "50 %에서
   100 % 사이"의 **반올림 방향**은 블리자드 문서에 없고 팬 사이트의 역산이
   출처다. 하한 1(방어가 아무리 높아도 피해 1)은 이 덱의 규칙이다.
   16부는 이 구분을 그대로 적는다 — 어디까지가 문서이고 어디부터가 우리 규칙인지.
"""

from . import const as C
from . import fixed as F

STRAIGHT, ARC = 0, 1
G = 1638                        # 0.025 px/틱², 16.16
ARROW_SPEED = F.fp(4)           # 화살·총알 4 px/틱 (§15.3)
ARC_MIN_TICKS = 6
ARC_DIV = 24
SPLASH_RINGS = 3


# ── SPEC §15.2 피해 공식 ────────────────────────────────────────────────────
def max_damage(basic, pierce, armour):
    """최대 피해 = 기본 − 방어 + 관통, 하한 1.

       하한이 없으면 방어력이 높은 유닛은 **절대 죽지 않는다**. 이 하한은
       블리자드 문서에 없는 이 덱의 규칙이다.
    """
    mx = basic - armour + pierce
    return 1 if mx < 1 else mx


def damage_lo(mx):
    """최대치의 50 %, 올림. 올림이라는 부분은 2차 출처다(§15.2)."""
    return F.floordiv(mx + 1, 2)


def roll_damage(rng, basic, pierce, armour):
    mx = max_damage(basic, pierce, armour)
    lo = damage_lo(mx)
    return lo + rng.roll(mx - lo + 1)


def expect100(basic, pierce, armour):
    """E[dmg] × 100 (정리 15.1). 정수만 쓰려고 100배로 둔다."""
    mx = max_damage(basic, pierce, armour)
    return (damage_lo(mx) + mx) * 50


# ── SPEC §15.1 사거리와 표적 선택 ───────────────────────────────────────────
def in_range(w, i, j):
    """체비셰프 거리 — 8방향 격자에서 '몇 걸음 안'과 정확히 같다."""
    return F.dinf(w.tx[i] - w.tx[j], w.ty[i] - w.ty[j]) <= C.RANGE[w.kind[i]]


def _enemy(w, i, j):
    return (w.alive[j] == 1 and w.owner[j] != w.owner[i] and w.hp[j] > 0)


def _nearest(w, i, reach):
    """사거리 안 적 중 d83 최소, 동점이면 핸들 오름차순.

       동점 규칙이 명세인 이유는 대칭 맵에서 동점이 흔하기 때문이다.
       두 기계가 다른 표적을 고르면 그 틱부터 상태가 갈린다.
    """
    best = 0
    bd = -1
    for j in range(1, C.MAX_ENT):
        if not _enemy(w, i, j):
            continue
        d = F.dinf(w.tx[i] - w.tx[j], w.ty[i] - w.ty[j])
        if d > reach:
            continue
        s = F.d83(w.tx[i] - w.tx[j], w.ty[i] - w.ty[j])
        if bd < 0 or s < bd:               # 핸들 오름차순으로 훑으므로
            bd = s                         # 등호를 빼면 작은 핸들이 이긴다
            best = w.handle(j)
    return best


def pick_target(w, i, last_hitter, attack_move):
    """(표적 핸들, 접근이 필요한가). 규칙 순서는 §15.1 그대로다."""
    if C.BASIC[w.kind[i]] == 0:
        return 0, False                    # 채집기와 비무장 건물은 쏘지 않는다
    reach = C.RANGE[w.kind[i]]
    cur = w.target[i]
    if w.valid(cur):
        j = cur // 256
        if _enemy(w, i, j) and in_range(w, i, j):
            return cur, False              # 1) 표적 유지 — 흔들리지 않는다
    if w.valid(last_hitter):
        j = last_hitter // 256
        if _enemy(w, i, j) and in_range(w, i, j):
            return last_hitter, False      # 2) 나를 때린 적
    h = _nearest(w, i, reach)              # 3) 가장 가까운 적
    if h:
        return h, False
    if attack_move:                        # 4) ATTACK_MOVE 만 두 칸 더 본다
        h = _nearest(w, i, reach + 2)
        if h:
            return h, True
    return 0, False


# ── SPEC §15.5 스플래시 ─────────────────────────────────────────────────────
def splash_damage(dmg, ring):
    """링 단위 감쇠 — 0링 전액, 1링 1/2, 2링 1/4, 그 밖은 0. 나눗셈은 내림."""
    if ring >= SPLASH_RINGS:
        return 0
    return F.floordiv(dmg, 1 << ring)


def splash_hits(w, tx, ty, dmg):
    """(핸들, 피해) 목록, 핸들 오름차순. **아군도 맞는다**.

       아군 오사는 AI 의 제약이다(§17). 같은 유닛이 두 링에 걸치는 일은 없다 —
       유닛의 대표 타일 하나로 판정하기 때문이다.
    """
    out = []
    for j in range(1, C.MAX_ENT):
        if w.alive[j] == 0 or w.hp[j] <= 0:
            continue
        ring = F.dinf(w.tx[j] - tx, w.ty[j] - ty)
        d = splash_damage(dmg, ring)
        if d > 0:
            out.append((w.handle(j), d))
    return out


# ── SPEC §15.3·15.4 투사체 ──────────────────────────────────────────────────
class Projectiles(object):
    """SoA 로 담는다 — 상태 해시(§18.4)가 배열 순서로 자동 고정되기 때문이다."""

    def __init__(self, map_w):
        self.map_w = map_w
        self.x = []
        self.y = []
        self.vx = []
        self.vy = []
        self.ttl = []
        self.target = []
        self.dmg = []
        self.kind = []
        self.dest = []

    def n(self):
        return len(self.x)

    def _tile(self, x, y):
        return (F.fp_floor(y) // C.TILE) * self.map_w + F.fp_floor(x) // C.TILE

    def launch(self, kind, x0, y0, x1, y1, speed, target, dmg):
        """좌표는 전부 16.16 픽셀. 같은 칸이면 발사하지 않는다(즉시 명중).

           **표적을 쫓지 않는다.** 발사 시점의 위치로 날아가므로 빠른 유닛은
           화살을 피할 수 있다 — 이것도 이 덱의 규칙이고, 유도 변형은
           16부에서 나란히 비교한다.
        """
        dx = F.fp_floor(x1) - F.fp_floor(x0)
        dy = F.fp_floor(y1) - F.fp_floor(y0)
        d = F.isqrt(dx * dx + dy * dy)
        if d == 0:
            return False
        if kind == ARC:
            t = ARC_MIN_TICKS
            if F.floordiv(d, ARC_DIV) > t:
                t = F.floordiv(d, ARC_DIV)
            vx = F.fp_div(x1 - x0, F.fp(t))
            vy = F.fp_div(y1 - y0, F.fp(t)) - F.fp_mul(G, F.fp_div(F.fp(t),
                                                                   F.fp(2)))
            ttl = t
        else:
            vx = F.fp_mul(F.fp_div(F.fp(dx), F.fp(d)), speed)
            vy = F.fp_mul(F.fp_div(F.fp(dy), F.fp(d)), speed)
            ttl = F.floordiv(F.fp(d), speed) + 2
        self.x.append(x0)
        self.y.append(y0)
        self.vx.append(vx)
        self.vy.append(vy)
        self.ttl.append(ttl)
        self.target.append(target)
        self.dmg.append(dmg)
        self.kind.append(kind)
        self.dest.append(self._tile(x1, y1))
        return True

    def step(self):
        """한 틱. 명중한 것을 (핸들, 피해, 착탄 타일, 착탄 y, 종류) 로 돌려주고 지운다.

           마지막 칸이 종류인 이유는 sim 이 포물선 명중에만 스플래시(§15.5)를
           적용해야 하기 때문이다.
        """
        hits = []
        keep = []
        for k in range(len(self.x)):
            if self.kind[k] == ARC:
                self.vy[k] += G                 # 수직은 중력만, 수평은 등속
            self.x[k] += self.vx[k]
            self.y[k] += self.vy[k]
            self.ttl[k] -= 1
            if (self._tile(self.x[k], self.y[k]) == self.dest[k]
                    or self.ttl[k] <= 0):
                hits.append((self.target[k], self.dmg[k], self.dest[k],
                             self.y[k], self.kind[k]))
            else:
                keep.append(k)
        if len(keep) != len(self.x):
            for name in ('x', 'y', 'vx', 'vy', 'ttl', 'target', 'dmg',
                         'kind', 'dest'):
                a = getattr(self, name)
                setattr(self, name, [a[k] for k in keep])
        return hits


# ── SPEC §15.6 란체스터 ─────────────────────────────────────────────────────
def lanchester_sim(a0, b0, alpha, beta):
    """정수 이산 시뮬. 폐형해(정리 15.4)는 엔진이 아니라 gen_prim 이 계산한다.

       종료 조건이 `>= FP_ONE` 인 것이 중요하다. `> 0` 으로 두면 A 가 0.5 인
       상태에서 감소량이 내림으로 0 이 되어 영원히 돌지 않는다 — 골든을
       처음 만들 때 이 무한 루프에 걸렸다.
    """
    a, b, t = F.fp(a0), F.fp(b0), 0
    while a >= F.FP_ONE and b >= F.FP_ONE and t < 10000:
        da = F.fp_mul(beta, b)
        db = F.fp_mul(alpha, a)
        a -= da
        b -= db
        if a < 0:
            a = 0
        if b < 0:
            b = 0
        t += 1
    return t, F.fp_floor(a), F.fp_floor(b)
