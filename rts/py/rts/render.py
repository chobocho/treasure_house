# -*- coding: utf-8 -*-
"""화면 구성 — 레이어·스크롤·y 정렬·미니맵·패널 (SPEC §23).

   렌더는 **상태를 읽기만 한다.** sim 을 건드리는 줄이 하나라도 생기면
   락스텝이 끝난다(§18.1). 팔레트 사이클 위상도 인자로만 받는다.

   지형 타일은 그림이 아니라 색이다(§23.1). 아티스트가 없으므로 한 칸을
   MINI_COLOR 로 채우고, 오토타일 마스크가 가리키는 "나와 다른 지형" 쪽
   가장자리 1px 만 어둡게 긋는다. 5부는 그 선으로 마스크가 화면에서 무엇을
   바꾸는지 보인다.
"""

from . import const as C
from . import econ as E
from . import fixed as F
from . import raster as RS
from . import spatial as S
from . import tmap as T

TILES_X = C.VIEW_W // C.TILE + 1
TILES_Y = C.VIEW_H // C.TILE + 1
EDGE_SPEED = 4
EDGE_MARGIN = 8
MAX_CAM_X = C.MAP_W * C.TILE - C.VIEW_W
MAX_CAM_Y = C.MAP_H * C.TILE - C.VIEW_H

UI_DARK, UI_MID, UI_LIGHT, UI_TEXT = 193, 195, 197, 198
UI_HP_GOOD, UI_HP_BAD, UI_SELECT = 201, 200, 199


# ── SPEC §23.2 스크롤 ───────────────────────────────────────────────────────
class View(object):
    """카메라는 **정수 픽셀**이다. 서브픽셀 스크롤은 도스 시절 흔치 않았고,
       정수로 두면 타일 그리기가 오프셋 하나로 끝난다."""

    def __init__(self, cam_x=0, cam_y=0):
        self.cam_x = cam_x
        self.cam_y = cam_y

    def _clamp(self, m):
        mx = m.w * C.TILE - C.VIEW_W
        my = m.h * C.TILE - C.VIEW_H
        if self.cam_x < 0:
            self.cam_x = 0
        if self.cam_y < 0:
            self.cam_y = 0
        if self.cam_x > mx:
            self.cam_x = mx
        if self.cam_y > my:
            self.cam_y = my

    def move(self, m, dx, dy):
        self.cam_x += dx
        self.cam_y += dy
        self._clamp(m)

    def center_on(self, m, tx, ty):
        self.cam_x = tx * C.TILE - C.VIEW_W // 2
        self.cam_y = ty * C.TILE - C.VIEW_H // 2
        self._clamp(m)

    def first_tile(self):
        """(첫 타일 x, 첫 타일 y, 픽셀 오프셋 x, 오프셋 y)."""
        return (F.floordiv(self.cam_x, C.TILE), F.floordiv(self.cam_y, C.TILE),
                F.fmod(self.cam_x, C.TILE), F.fmod(self.cam_y, C.TILE))


def edge_scroll(mx, my):
    """마우스가 뷰포트 가장자리 8px 안이면 그 방향으로 4px/틱."""
    if not (0 <= mx < C.VIEW_W and 0 <= my < C.VIEW_H):
        return (0, 0)
    dx = dy = 0
    if mx < EDGE_MARGIN:
        dx = -EDGE_SPEED
    elif mx >= C.VIEW_W - EDGE_MARGIN:
        dx = EDGE_SPEED
    if my < EDGE_MARGIN:
        dy = -EDGE_SPEED
    elif my >= C.VIEW_H - EDGE_MARGIN:
        dy = EDGE_SPEED
    return (dx, dy)


# ── SPEC §23.3 y 정렬 ───────────────────────────────────────────────────────
def sort_key(w, i):
    """발밑 y · x · 핸들. 키가 전순서라 안정 정렬 여부에 의존하지 않는다."""
    foot = C.FOOT[w.kind[i]]
    return (F.fp_floor(w.py[i]) + foot * C.TILE, F.fp_floor(w.px[i]),
            w.handle(i))


def y_order(w):
    """삽입 정렬. 프레임 사이에 목록이 거의 정렬되어 있어 거의 O(n) 이다."""
    out = []
    for i in range(1, C.MAX_ENT):
        if w.alive[i] == 0:
            continue
        k = sort_key(w, i)
        j = len(out)
        while j > 0 and sort_key(w, out[j - 1]) > k:
            j -= 1
        out.insert(j, i)
    return out


# ── SPEC §23.4 미니맵 ───────────────────────────────────────────────────────
def minimap_nearest(m, sx, sy):
    return m.terrain[(sy * m.h // C.MINI_H) * m.w + (sx * m.w // C.MINI_W)]


def minimap_majority(m, sx, sy):
    """블록에서 가장 많이 나온 지형, 동점이면 지형 번호 최소. 128 맵을 대비한다."""
    x0 = sx * m.w // C.MINI_W
    x1 = (sx + 1) * m.w // C.MINI_W
    y0 = sy * m.h // C.MINI_H
    y1 = (sy + 1) * m.h // C.MINI_H
    if x1 <= x0:
        x1 = x0 + 1
    if y1 <= y0:
        y1 = y0 + 1
    cnt = [0] * 8
    for y in range(y0, min(y1, m.h)):
        for x in range(x0, min(x1, m.w)):
            cnt[m.terrain[y * m.w + x]] += 1
    best, bn = 0, -1
    for t in range(8):
        if cnt[t] > bn:
            bn, best = cnt[t], t
    return best


def minimap_to_tile(sx, sy):
    return (sx * C.MAP_W // C.MINI_W, sy * C.MAP_H // C.MINI_H)


# ── 안개가 가리는 것 ────────────────────────────────────────────────────────
def visible_entities(sim, p):
    """§23.1 — **유닛 숨기기는 명암표가 못 한다.** 보이는 칸의 것만 그린다."""
    out = []
    for i in y_order(sim.w):
        t = sim.w.ty[i] * sim.m.w + sim.w.tx[i]
        if sim.fog.visible(p, t):
            out.append(i)
    return out


def credits_text(v):
    """자릿수 고정 — 숫자가 흔들리면 더티 렉트가 커진다."""
    if v > 99999:
        v = 99999
    s = '%d' % v
    return ' ' * (5 - len(s)) + s


# ── SPEC §23.1 레이어 ───────────────────────────────────────────────────────
def _draw_terrain(fb, sim, view, light, p):
    m = sim.m
    tx0, ty0, ox, oy = view.first_tile()
    for ty in range(ty0, min(m.h, ty0 + TILES_Y)):
        for tx in range(tx0, min(m.w, tx0 + TILES_X)):
            px = (tx - tx0) * C.TILE - ox
            py = (ty - ty0) * C.TILE - oy
            level = sim.fog.level(p, tx, ty)
            if level == 0:
                _fill(fb, px, py, C.TILE, C.TILE, 0)
                continue
            t = m.terrain[ty * m.w + tx]
            base = T.MINI_COLOR[t]
            edge = base - 2 if base % 8 >= 2 else base + 1
            if level < 3:
                base = light[level][base]
                edge = light[level][edge]
            _fill(fb, px, py, C.TILE, C.TILE, base)
            mask = m.mask(tx, ty)              # §4.4 — 다른 지형 쪽만 긋는다
            if F.bit(mask, 0) == 0:
                _fill(fb, px, py, C.TILE, 1, edge)
            if F.bit(mask, 4) == 0:
                _fill(fb, px, py + C.TILE - 1, C.TILE, 1, edge)
            if F.bit(mask, 6) == 0:
                _fill(fb, px, py, 1, C.TILE, edge)
            if F.bit(mask, 2) == 0:
                _fill(fb, px + C.TILE - 1, py, 1, C.TILE, edge)


def _fill(fb, x, y, w, h, v):
    for j in range(max(0, y), min(C.VIEW_H, y + h)):
        row = j * C.SCR_W
        for i in range(max(0, x), min(C.VIEW_W, x + w)):
            fb[row + i] = v


def _draw_entities(fb, sim, view, light, p, selection):
    w = sim.w
    sel = set(selection)
    for i in visible_entities(sim, p):
        spr, flip = RS.sprite_for(w.kind[i], w.dir[i])
        if spr is None:
            continue
        sx = F.fp_floor(w.px[i]) - view.cam_x
        sy = F.fp_floor(w.py[i]) - view.cam_y
        anchor_x = sx + C.TILE * C.FOOT[w.kind[i]] // 2
        anchor_y = sy + C.TILE * C.FOOT[w.kind[i]] - 2
        RS.blit(fb, spr, anchor_x, anchor_y, w.owner[i], flip)
        _bars(fb, w, i, anchor_x - spr.ox, anchor_y - spr.oy, spr,
              w.handle(i) in sel)


def _bars(fb, w, i, x0, y0, spr, selected):
    """체력바와 선택 표시. 뷰포트 안에서만 그린다."""
    hp = w.hp[i]
    full = C.HP[w.kind[i]]
    if full <= 0:
        return
    wdt = spr.w - 2
    fill = wdt * hp // full
    y = y0 - 2
    if 0 <= y < C.VIEW_H:
        for k in range(wdt):
            x = x0 + 1 + k
            if 0 <= x < C.VIEW_W:
                fb[y * C.SCR_W + x] = UI_HP_GOOD if k < fill else UI_HP_BAD
    if selected:
        for k in range(spr.w):
            x = x0 + k
            for yy in (y0, y0 + spr.h - 1):
                if 0 <= x < C.VIEW_W and 0 <= yy < C.VIEW_H:
                    fb[yy * C.SCR_W + x] = UI_SELECT


def _draw_projectiles(fb, sim, view):
    for k in range(sim.pj.n()):
        x = F.fp_floor(sim.pj.x[k]) - view.cam_x
        y = F.fp_floor(sim.pj.y[k]) - view.cam_y
        if 0 <= x < C.VIEW_W and 0 <= y < C.VIEW_H:
            fb[y * C.SCR_W + x] = UI_TEXT


def _draw_panel(fb, sim, view, p, selection):
    m = sim.m
    for y in range(C.SCR_H):
        row = y * C.SCR_W
        for x in range(C.PANEL_X, C.SCR_W):
            fb[row + x] = UI_DARK
    for sy in range(C.MINI_H):                 # 미니맵 — 한 타일이 한 픽셀
        row = (C.MINI_Y + sy) * C.SCR_W
        for sx in range(C.MINI_W):
            tx, ty = minimap_to_tile(sx, sy)
            level = sim.fog.level(p, tx, ty)
            if level == 0:
                fb[row + C.MINI_X + sx] = 0
            else:
                fb[row + C.MINI_X + sx] = T.MINI_COLOR[minimap_nearest(m, sx,
                                                                       sy)]
    for i in range(1, C.MAX_ENT):              # 미니맵 위의 유닛
        if sim.w.alive[i] == 0:
            continue
        t = sim.w.ty[i] * m.w + sim.w.tx[i]
        if not sim.fog.visible(p, t):
            continue
        sx = sim.w.tx[i] * C.MINI_W // m.w
        sy = sim.w.ty[i] * C.MINI_H // m.h
        fb[(C.MINI_Y + sy) * C.SCR_W + C.MINI_X + sx] = \
            RS.PLAYER_BASE + sim.w.owner[i] * 8 + 5
    RS.text(fb, 'SEL', C.PANEL_X + 2, C.MINI_H + 4, UI_TEXT)
    if selection:
        h = selection[0]
        if sim.w.valid(h):
            j = S.index(h)
            RS.text(fb, C.NAME[sim.w.kind[j]][:1].upper()
                    + '%d' % sim.w.kind[j], C.PANEL_X + 2, C.MINI_H + 14,
                    UI_TEXT)
            RS.text(fb, credits_text(sim.w.hp[j]), C.PANEL_X + 2,
                    C.MINI_H + 24, UI_HP_GOOD)


def _draw_bottom(fb, sim, p, message):
    for y in range(C.BAR_Y, C.SCR_H):
        row = y * C.SCR_W
        for x in range(0, C.PANEL_X):
            fb[row + x] = UI_MID
    RS.text(fb, 'CREDITS' + credits_text(sim.ec.credits[p]), 4, C.BAR_Y + 2,
            UI_TEXT)
    RS.text(fb, 'POP' + credits_text(sim.ec.supply_used[p])
            + '/' + credits_text(sim.ec.supply_cap[p]), 4, C.BAR_Y + 12,
            UI_TEXT)
    if message:
        RS.text(fb, message[:24], 130, C.BAR_Y + 12, UI_LIGHT)


def draw(fb, sim, view, phase, pal, light, p, selection, message):
    """§23.1 의 여덟 층을 순서대로. 팔레트 위상은 그림을 바꾸지 않는다."""
    _draw_terrain(fb, sim, view, light, p)
    _draw_entities(fb, sim, view, light, p, selection)
    _draw_projectiles(fb, sim, view)
    _draw_panel(fb, sim, view, p, selection)
    _draw_bottom(fb, sim, p, message)
