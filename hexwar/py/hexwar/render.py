# -*- coding: utf-8 -*-
"""렌더링 — SPEC §10.

   화면은 320x200 8비트 인덱스 버퍼 하나다(모드 13h). 픽셀 하나가 팔레트
   번호 한 바이트라, 색을 바꾸는 것과 픽셀을 바꾸는 것이 분리된다 — 도스
   게임의 페이드인·팀 컬러·물결 애니메이션이 전부 팔레트만 건드려서 나온
   효과다.

   그리는 순서는 화가 알고리즘 그대로다. 헥스가 세로로 8픽셀씩 겹치므로
   위 행부터 그리면 아래 행이 자연스럽게 위를 덮는다.
"""

import io
import os

from . import font as F
from . import hexcoord as H
from . import picker as PK
from .hexmap import (FOG_HIDDEN, FOG_EXPLORED, TERRAIN_MASK,
                     T_MOVE, MAP_W, MAP_H)
from .rng import fnv1a
from .units import K_CHAR, NO_UNIT

SCR_W, SCR_H = 320, 200
VIEW = (0, 0, 256, 168)          # 맵이 보이는 창
PANEL = (256, 0, 64, 200)        # 오른쪽 정보 패널
MSG = (0, 168, 256, 32)          # 아래 메시지 줄

MAP_PX_W = MAP_W * PK.HEX_W + PK.ODD_SHIFT
MAP_PX_H = MAP_H * PK.ROW_STEP + (PK.HEX_H - PK.ROW_STEP)
CAM_MAX_X = max(0, MAP_PX_W - VIEW[2])
CAM_MAX_Y = max(0, MAP_PX_H - VIEW[3])

GOLDEN = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), 'golden')


class Sprite(object):
    __slots__ = ('w', 'h', 'data')

    def __init__(self, w, h, data):
        self.w = w
        self.h = h
        self.data = data


def load_palette(path=None):
    path = path or os.path.join(GOLDEN, 'palette.txt')
    pal = []
    for line in io.open(path, encoding='utf-8'):
        line = line.strip()
        if line:
            pal.append(tuple(int(x) for x in line.split()))
    return pal


def load_sprites(path=None):
    """RLE 코퍼스를 푼다. SPEC §10.2 — 이름 w h 다음에 (개수, 값) 쌍."""
    path = path or os.path.join(GOLDEN, 'tiles.rle')
    sprites = {}
    name = None
    w = h = 0
    buf = None
    need = 0
    for raw in io.open(path, encoding='utf-8'):
        line = raw.strip()
        if not line or line.startswith(';'):
            continue
        if need == 0:
            parts = line.split()
            name, w, h = parts[0], int(parts[1]), int(parts[2])
            buf = bytearray()
            need = w * h
            continue
        nums = [int(x) for x in line.split()]
        for i in range(0, len(nums), 2):
            c, v = nums[i], nums[i + 1]
            buf.extend(bytes([v]) * c)
            need -= c
        if need == 0:
            sprites[name] = Sprite(w, h, bytes(buf))
    return sprites


class Framebuffer(object):
    """한 장의 화면. 도스라면 A000:0000 이 가리키던 64KB 그 자체다."""

    __slots__ = ('w', 'h', 'data')

    def __init__(self, w=SCR_W, h=SCR_H):
        self.w = w
        self.h = h
        self.data = bytearray(w * h)

    def clear(self, v=0):
        for i in range(len(self.data)):
            self.data[i] = v

    def fill_rect(self, x, y, w, h, v):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        row = bytes([v]) * max(0, x1 - x0)
        for yy in range(y0, y1):
            self.data[yy * self.w + x0:yy * self.w + x1] = row

    def frame_rect(self, x, y, w, h, v):
        self.fill_rect(x, y, w, 1, v)
        self.fill_rect(x, y + h - 1, w, 1, v)
        self.fill_rect(x, y, 1, h, v)
        self.fill_rect(x + w - 1, y, 1, h, v)

    def blit(self, sp, x, y, clip=None):
        """인덱스 0을 건너뛰는 마스크 블릿. 클리핑은 원본 좌표를 잘라서 한다 —
           픽셀마다 범위 검사를 하면 8086 에서는 그 검사가 그리기보다 비쌌다."""
        cx, cy, cw, ch = clip if clip else (0, 0, self.w, self.h)
        x0 = max(x, cx)
        y0 = max(y, cy)
        x1 = min(x + sp.w, cx + cw)
        y1 = min(y + sp.h, cy + ch)
        if x0 >= x1 or y0 >= y1:
            return
        data = self.data
        src = sp.data
        for yy in range(y0, y1):
            srow = (yy - y) * sp.w - x
            drow = yy * self.w
            for xx in range(x0, x1):
                v = src[srow + xx]
                if v:
                    data[drow + xx] = v

    def text(self, s, x, y, color, clip=None):
        cx, cy, cw, ch = clip if clip else (0, 0, self.w, self.h)
        for ch_i, c in enumerate(s):
            gx = x + ch_i * F.ADV
            rows = F.rows(c)
            for ry in range(F.FH):
                bits = rows[ry]
                if not bits:
                    continue
                py = y + ry
                if py < cy or py >= cy + ch:
                    continue
                base = py * self.w
                for bx in range(F.FW):
                    if bits & (1 << (F.FW - 1 - bx)):
                        px = gx + bx
                        if cx <= px < cx + cw:
                            self.data[base + px] = color

    def to_ppm(self, palette):
        """P6 이진 PPM. 6비트 DAC 값을 8비트로 편다(v*255//63)."""
        head = ('P6\n%d %d\n255\n' % (self.w, self.h)).encode('ascii')
        out = bytearray(head)
        lut = bytearray()
        for (r, g, b) in palette:
            lut.extend((r * 255 // 63, g * 255 // 63, b * 255 // 63))
        for v in self.data:
            out.extend(lut[v * 3:v * 3 + 3])
        return bytes(out)


class Dirty(object):
    """더티 사각형 목록. SPEC §10.3 — 합집합이 너무 커지면 하나로 합친다.

       도스에서 이 최적화가 결정적이었던 이유: 320x200 전체를 다시 그리면
       64,000 바이트를 옮겨야 하는데, ISA 버스의 VRAM 쓰기는 느려서 그것만으로
       프레임을 다 썼다. 바뀐 칸 몇 개만 다시 그리면 수백 바이트로 끝난다.
    """

    __slots__ = ('rects',)

    def __init__(self):
        self.rects = []

    def add(self, x, y, w, h):
        if w <= 0 or h <= 0:
            return
        nr = [x, y, x + w, y + h]
        for r in self.rects:
            ux0, uy0 = min(r[0], nr[0]), min(r[1], nr[1])
            ux1, uy1 = max(r[2], nr[2]), max(r[3], nr[3])
            ua = (ux1 - ux0) * (uy1 - uy0)
            a = (r[2] - r[0]) * (r[3] - r[1]) + (nr[2] - nr[0]) * (nr[3] - nr[1])
            if a * 2 > ua:          # 합쳐도 낭비가 절반 미만이면 합친다
                r[0], r[1], r[2], r[3] = ux0, uy0, ux1, uy1
                return
        self.rects.append(nr)

    def area(self):
        return sum((r[2] - r[0]) * (r[3] - r[1]) for r in self.rects)

    def clear(self):
        self.rects = []


class Renderer(object):
    """맵·패널·메시지 줄을 그린다. 상태는 전부 밖(Game/Ui)에서 받는다."""

    __slots__ = ('fb', 'pal', 'sp', 'dirty')

    def __init__(self):
        self.fb = Framebuffer()
        self.pal = load_palette()
        self.sp = load_sprites()
        self.dirty = Dirty()

    # ---------------------------------------------------------------- 맵
    def visible_rows(self, cam_y):
        """화면에 걸치는 행 범위. 헥스가 32 높이인데 행 간격이 24라
           위아래로 한 행씩 더 그려야 잘리지 않는다."""
        top = (cam_y - (PK.HEX_H - PK.ROW_STEP)) // PK.ROW_STEP
        bot = (cam_y + VIEW[3]) // PK.ROW_STEP + 1
        return (max(0, top), min(MAP_H - 1, bot))

    def draw_map(self, g, ui):
        fb = self.fb
        m = g.map
        camx, camy = ui.cam_x, ui.cam_y
        fb.fill_rect(VIEW[0], VIEW[1], VIEW[2], VIEW[3], 0)
        r0, r1 = self.visible_rows(camy)
        for row in range(r0, r1 + 1):
            for col in range(MAP_W):
                ox, oy = PK.hex_origin(col, row)
                x = ox - camx
                y = oy - camy
                if x <= -PK.HEX_W or x >= VIEW[2] or y <= -PK.HEX_H or y >= VIEW[3]:
                    continue
                i = row * MAP_W + col
                fog = m.fog[i]
                if fog == FOG_HIDDEN:
                    self.fb.blit(self.sp['ov_black'], x, y, VIEW)
                    continue
                t = m.cells[i] & TERRAIN_MASK
                fb.blit(self.sp[TILE_NAME[t]], x, y, VIEW)
                if m.cells[i] & 0x80:
                    self._draw_roads(m, i, col, row, x, y)
                if fog == FOG_EXPLORED:
                    fb.blit(self.sp['ov_dim'], x, y, VIEW)
                    continue
                if i in ui.objective_idx:
                    fb.blit(self.sp['ov_obj'], x, y, VIEW)
                if i in ui.move_overlay:
                    fb.blit(self.sp['ov_move'], x, y, VIEW)
                if i in ui.attack_overlay:
                    fb.blit(self.sp['ov_attack'], x, y, VIEW)
                uid = m.occupant[i]
                if uid != NO_UNIT:
                    u = g.pool.get(uid)
                    if u is not None:
                        self._draw_unit(u, x, y)
                if ui.sel_idx == i:
                    fb.blit(self.sp['ov_sel'], x, y, VIEW)
                if ui.cursor_idx == i:
                    fb.blit(self.sp['ov_cursor'], x, y, VIEW)

    def _draw_roads(self, m, i, col, row, x, y):
        """이웃도 도로일 때만 그 방향으로 연결선을 그린다 — 도로가 끊기지 않는다."""
        for d, ni in m.neighbors_with_dir(i):
            if m.cells[ni] & 0x80:
                self.fb.blit(self.sp['road%d' % d], x, y, VIEW)

    def _draw_unit(self, u, x, y):
        self.fb.blit(self.sp['u%d_%d' % (u.side, u.kind)], x + 8, y + 8, VIEW)
        # 체력 막대 — 유닛 아이콘 아래 12x2
        w = max(0, u.hp * 12 // 10)
        self.fb.fill_rect(x + 10, y + 25, 12, 2, 8)
        self.fb.fill_rect(x + 10, y + 25, w, 2, 10 if u.hp > 5 else 12)

    # -------------------------------------------------------------- 패널
    def draw_panel(self, g, ui):
        fb = self.fb
        px, py, pw, ph = PANEL
        fb.fill_rect(px, py, pw, ph, 8)
        fb.frame_rect(px, py, pw, ph, 7)
        fb.text('TURN %d' % g.turn, px + 4, py + 4, 15)
        fb.text('SIDE %d' % g.side, px + 4, py + 13, 15)
        self.draw_minimap(g, ui, px + 6, py + 24)
        u = g.pool.get(ui.sel_unit) if ui.sel_unit >= 0 else None
        ty = py + 70
        if u is not None:
            from .units import KINDS
            fb.text(KINDS[u.kind][0], px + 4, ty, 14)
            fb.text('HP %d' % u.hp, px + 4, ty + 10, 15)
            fb.text('MP %d' % u.mp, px + 4, ty + 19, 15)
            fb.text('AM %d' % u.ammo, px + 4, ty + 28, 15)
            fb.text('EN %d' % u.ent, px + 4, ty + 37, 15)
        else:
            fb.text('NO UNIT', px + 4, ty, 7)
        fb.text(ui.state_name(), px + 4, py + 136, 11)

    def draw_minimap(self, g, ui, x, y):
        """헥스 하나를 2x2 픽셀로. 도스 워게임의 미니맵이 정확히 이 크기였다."""
        m = g.map
        for row in range(MAP_H):
            for col in range(MAP_W):
                i = row * MAP_W + col
                if m.fog[i] == FOG_HIDDEN:
                    v = 0
                else:
                    t = m.cells[i] & TERRAIN_MASK
                    v = MINI_COLOR[t]
                    uid = m.occupant[i]
                    if uid != NO_UNIT and m.fog[i] != FOG_EXPLORED:
                        u = g.pool.get(uid)
                        if u is not None:
                            v = 155 if u.side == 1 else 170
                self.fb.fill_rect(x + col * 2, y + row * 2, 2, 2, v)
        # 현재 보이는 영역 테두리
        vx = x + ui.cam_x * 2 // PK.HEX_W
        vy = y + ui.cam_y * 2 // PK.ROW_STEP
        self.fb.frame_rect(vx, vy, VIEW[2] * 2 // PK.HEX_W, VIEW[3] * 2 // PK.ROW_STEP, 15)

    # ---------------------------------------------------------- 메시지 줄
    def draw_msg(self, g, ui):
        fb = self.fb
        mx, my, mw, mh = MSG
        fb.fill_rect(mx, my, mw, mh, 0)
        fb.frame_rect(mx, my, mw, mh, 7)
        lines = ui.ascii_log(g, 3)
        for i, line in enumerate(lines):
            fb.text(line[:41], mx + 3, my + 4 + i * 9, 7 if i else 15, MSG)

    # ------------------------------------------------------------ 위젯
    def draw_widgets(self, ui):
        """위젯 트리를 앞에서 뒤로 그린다 — 히트 테스트와 정확히 반대 순서다.
           같은 트리를 두 방향으로 훑는 것이 도스 GUI 의 기본 골격이었다."""
        from .ui import BUTTON, DIALOG
        stack = [ui.root]
        while stack:
            w = stack.pop(0)
            if not w.visible:
                continue
            if w.kind == BUTTON:
                on = w.enabled
                self.fb.fill_rect(w.x, w.y, w.w, w.h, 7 if on else 8)
                self.fb.frame_rect(w.x, w.y, w.w, w.h, 15 if on else 7)
                self.fb.text(w.label, w.x + 3, w.y + 3, 0 if on else 8)
            elif w.kind == DIALOG:
                self.fb.fill_rect(w.x + 4, w.y + 4, w.w, w.h, 0)      # 그림자
                self.fb.fill_rect(w.x, w.y, w.w, w.h, 8)
                self.fb.frame_rect(w.x, w.y, w.w, w.h, 15)
                self.fb.frame_rect(w.x + 2, w.y + 2, w.w - 4, w.h - 4, 7)
                self.fb.text(w.label, w.x + 12, w.y + 14, 15)
            stack.extend(w.children)

    def draw(self, g, ui):
        self.draw_map(g, ui)
        self.draw_panel(g, ui)
        self.draw_msg(g, ui)
        self.draw_widgets(ui)
        return self.fb

    def frame_hash(self):
        return fnv1a(self.fb.to_ppm(self.pal))


TILE_NAME = ('t_clear', 't_forest', 't_hill', 't_mountain',
             't_city', 't_river', 't_swamp', 't_sea')
MINI_COLOR = (24, 38, 56, 72, 120, 88, 104, 84)
