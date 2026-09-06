# -*- coding: utf-8 -*-
"""선택과 명령 — 픽킹·상자 선택·컨트롤 그룹·명령 큐 (SPEC §12).

   이 모듈은 **상태를 바꾸지 않는다.** 명령을 만들어 큐에 넣을 뿐이고,
   그 큐는 net(§19)의 지연 큐를 거쳐 ORDER_DELAY 틱 뒤에 sim.step 의 인자로
   들어간다. UI 코드가 sim 의 상태를 직접 건드리는 경로는 존재하지 않는다 —
   이 규율 하나가 락스텝을 가능하게 한다.
"""

from . import const as C
from . import econ as E
from . import fixed as F
from . import spatial as S

MOVE, ATTACK, ATTACK_MOVE, HARVEST, BUILD, STOP, HOLD = range(7)
ORDER_MAX = 8                    # §12.4 유닛당 명령 큐 상한
SELECT_MAX = 32                  # §12.2 한 번에 고를 수 있는 유닛 수
PICK_R = 2                       # §12.1 버킷 질의 반경 (타일)


def in_view(sx, sy):
    """전장 뷰포트 안인가. 밖이면 패널·미니맵 처리로 넘어간다."""
    return (C.VIEW_X <= sx < C.VIEW_X + C.VIEW_W
            and C.VIEW_Y <= sy < C.VIEW_Y + C.VIEW_H)


def screen_to_world(cam, sx, sy):
    return (sx - C.VIEW_X + cam[0], sy - C.VIEW_Y + cam[1])


def _box(w, i):
    """엔티티의 월드 픽셀 AABB. px·py 는 이동 중에도 정확하다(§13.1)."""
    size = C.TILE * C.FOOT[w.kind[i]]
    x0 = F.fp_floor(w.px[i])
    y0 = F.fp_floor(w.py[i])
    return x0, y0, x0 + size, y0 + size


# ── SPEC §12.1 픽킹 ─────────────────────────────────────────────────────────
def pick(w, cam, sx, sy, mask=None):
    """한 점이 가리키는 엔티티 핸들. 없으면 0.

       앞에 그려진 것이 먼저 잡혀야 하므로 y 내림차순, 동점이면 핸들
       내림차순으로 훑는다 — §23.3 의 그리기 순서를 거꾸로 도는 것이다.
       `mask(kind, dir, lx, ly)` 는 스프라이트 알파 마스크다. AABB 만으로
       끝내지 않는 이유는 유닛이 사각형이 아니기 때문이다.
    """
    if not in_view(sx, sy):
        return 0
    wx, wy = screen_to_world(cam, sx, sy)
    cands = w.query(wx // C.TILE, wy // C.TILE, PICK_R)
    order = sorted(cands, key=lambda i: (-w.py[i], -w.handle(i)))
    for i in order:
        x0, y0, x1, y1 = _box(w, i)
        if not (x0 <= wx < x1 and y0 <= wy < y1):
            continue
        if mask is not None and not mask(w.kind[i], w.dir[i], wx - x0, wy - y0):
            continue
        return w.handle(i)
    return 0


# ── SPEC §12.2 상자 선택 ────────────────────────────────────────────────────
def box_select(w, p, cam, x0, y0, x1, y1):
    """드래그 상자와 겹치는 **내** 엔티티. 유닛이 하나라도 있으면 건물은 뺀다.

       정렬이 핸들 오름차순인 것은 눈에 보이지 않지만 중요하다 —
       선택 목록의 순서가 대형 슬롯 배정(§13.5)을 그대로 결정한다.
    """
    if x1 < x0:
        x0, x1 = x1, x0
    if y1 < y0:
        y0, y1 = y1, y0
    ax0, ay0 = screen_to_world(cam, x0, y0)
    ax1, ay1 = screen_to_world(cam, x1, y1)
    units, builds = [], []
    for i in range(1, C.MAX_ENT):
        if w.alive[i] == 0 or w.owner[i] != p:
            continue
        bx0, by0, bx1, by1 = _box(w, i)
        if bx1 - 1 < ax0 or ax1 < bx0 or by1 - 1 < ay0 or ay1 < by0:
            continue
        if C.IS_BUILDING[w.kind[i]]:
            builds.append(w.handle(i))
        else:
            units.append(w.handle(i))
    out = units if units else builds
    out.sort()
    return out[:SELECT_MAX]


# ── SPEC §12.3 컨트롤 그룹 ──────────────────────────────────────────────────
class Groups(object):
    """저장되는 것은 **핸들**이다. 죽은 유닛은 valid(§7.2)가 자동으로 거른다."""

    def __init__(self):
        self.g = [[] for _ in range(10)]

    def set(self, k, sel):
        self.g[k] = list(sel)

    def recall(self, w, k):
        return [h for h in self.g[k] if w.valid(h)]


# ── SPEC §12.4 명령 큐 ──────────────────────────────────────────────────────
class Orders(object):
    """유닛당 큐 하나. 기본 클릭은 비우고 하나, 시프트 클릭은 뒤에 붙인다."""

    def __init__(self):
        self.q = [[] for _ in range(C.MAX_ENT)]

    def push(self, i, order, shift):
        if order[0] == STOP:
            self.q[i] = []                     # STOP 은 큐를 비우고 끝이다
            return
        if not shift:
            self.q[i] = []
        if len(self.q[i]) < ORDER_MAX:
            self.q[i].append(order)

    def pop(self, i):
        if not self.q[i]:
            return None
        head = self.q[i][0]
        self.q[i] = self.q[i][1:]
        return head

    def clear(self, i):
        self.q[i] = []


def context_order(w, ec, m, p, tx, ty, h):
    """우클릭의 문맥 규칙. 판정 순서가 명세다 — 적 정제소는 반납이 아니라 공격이다."""
    if w.valid(h):
        j = S.index(h)
        if w.owner[j] != p:
            return ATTACK
        if w.kind[j] in E.DEPOT:
            return HARVEST
        return MOVE
    if m.in_map(tx, ty) and ec.ore[ty * m.w + tx] > 0:
        return HARVEST
    return MOVE
