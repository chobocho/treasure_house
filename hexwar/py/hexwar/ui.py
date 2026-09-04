# -*- coding: utf-8 -*-
"""GUI 셸 — SPEC §11.

   도스 게임의 GUI 는 툴킷이 없었다. 위젯 트리를 직접 만들고, 마우스 위치로
   히트 테스트를 하고, 상태 기계로 '지금 클릭이 무슨 뜻인지'를 정했다.
   여기 있는 세 조각이 그때 GUI 코드의 전부라고 봐도 된다.

     1. 위젯 트리 — 사각형과 부모/자식. 그리기 순서 = 히트 테스트 역순.
     2. 상태 기계 — 같은 클릭이 상태에 따라 선택·이동·공격이 된다.
     3. 명령 스택 — 상태를 바꾸는 길이 하나뿐이어야 언두가 성립한다.
"""

from . import los
from . import path as P
from . import picker as PK
from .hexmap import FOG_VISIBLE, MAP_W
from .render import CAM_MAX_X, CAM_MAX_Y, MSG, PANEL, VIEW
from .units import K_RNG, NO_UNIT

# 위젯 종류
PANEL_W, BUTTON, LABEL, MINIMAP, MAPVIEW, LOG, DIALOG = range(7)

# 상태 기계 (SPEC §11.2)
IDLE, SELECTED, TARGETING, DIALOG_ST, GAMEOVER = range(5)
STATE_NAMES = ('IDLE', 'SELECTED', 'TARGETING', 'DIALOG', 'GAMEOVER')


class Widget(object):
    __slots__ = ('id', 'x', 'y', 'w', 'h', 'kind', 'label', 'enabled', 'visible', 'children')

    def __init__(self, wid, x, y, w, h, kind, label='', children=None):
        self.id = wid
        self.x, self.y, self.w, self.h = x, y, w, h
        self.kind = kind
        self.label = label
        self.enabled = True
        self.visible = True
        self.children = children or []

    def contains(self, px, py):
        return self.x <= px < self.x + self.w and self.y <= py < self.y + self.h


def build_ui():
    """화면 배치는 코드에 박아 둔다. 리소스 파일로 뺄 수도 있지만, 320x200
       한 해상도만 지원하던 시절에는 이렇게 두는 편이 흔했다."""
    minimap = Widget('minimap', PANEL[0] + 6, 24, 48, 36, MINIMAP)
    btn_end = Widget('end', PANEL[0] + 4, 150, 56, 12, BUTTON, 'END TURN')
    btn_undo = Widget('undo', PANEL[0] + 4, 164, 56, 12, BUTTON, 'UNDO')
    btn_next = Widget('next', PANEL[0] + 4, 178, 56, 12, BUTTON, 'NEXT UNIT')
    panel = Widget('panel', PANEL[0], PANEL[1], PANEL[2], PANEL[3], PANEL_W, '',
                   [minimap, btn_end, btn_undo, btn_next])
    mapview = Widget('map', VIEW[0], VIEW[1], VIEW[2], VIEW[3], MAPVIEW)
    logw = Widget('log', MSG[0], MSG[1], MSG[2], MSG[3], LOG)
    yes = Widget('yes', 100, 112, 40, 14, BUTTON, 'YES')
    no = Widget('no', 180, 112, 40, 14, BUTTON, 'NO')
    dlg = Widget('dialog', 80, 74, 160, 56, DIALOG, 'END TURN?', [yes, no])
    dlg.visible = False
    root = Widget('root', 0, 0, 320, 200, PANEL_W, '', [mapview, logw, panel, dlg])
    return root


def hit_test(w, px, py):
    """뒤에서 앞으로 훑어 가장 위의 위젯을 찾는다. 자식이 부모보다 위다.
       모달 대화상자가 아래를 가리는 것도 이 순서 하나로 해결된다."""
    if not w.visible or not w.contains(px, py):
        return None
    for c in reversed(w.children):
        hit = hit_test(c, px, py)
        if hit is not None:
            return hit
    return w if w.enabled else None


class Ui(object):
    __slots__ = ('g', 'root', 'state', 'cam_x', 'cam_y', 'cursor_idx', 'sel_idx',
                 'sel_unit', 'move_overlay', 'attack_overlay', 'reach', 'prev_state',
                 'dialog', 'msg', 'objective_idx')

    def __init__(self, g):
        self.g = g
        self.root = build_ui()
        self.state = IDLE
        self.prev_state = IDLE
        self.cam_x = 0
        self.cam_y = 0
        self.cursor_idx = -1
        self.sel_idx = -1
        self.sel_unit = -1
        self.move_overlay = set()
        self.attack_overlay = set()
        self.reach = {}
        self.dialog = None
        self.msg = []
        self.objective_idx = set(g.map.axial_idx(q, r) for (q, r) in g.objectives)

    # ------------------------------------------------------------- 표시용
    def state_name(self):
        return STATE_NAMES[self.state]

    def ascii_log(self, g, n):
        rows = [a for (_k, a) in g.log[-n:]]
        return list(reversed(rows))

    # --------------------------------------------------------------- 카메라
    def clamp_cam(self):
        self.cam_x = max(0, min(CAM_MAX_X, self.cam_x))
        self.cam_y = max(0, min(CAM_MAX_Y, self.cam_y))

    def scroll(self, dx, dy):
        self.cam_x += dx
        self.cam_y += dy
        self.clamp_cam()

    def center_on(self, idx):
        """헥스가 화면 가운데 오도록. 맵 끝에서는 잘리지 않게 물린다."""
        row, col = divmod(idx, MAP_W)
        cx, cy = PK.hex_center(col, row)
        self.cam_x = cx - VIEW[2] // 2
        self.cam_y = cy - VIEW[3] // 2
        self.clamp_cam()

    # --------------------------------------------------------------- 선택
    def select(self, uid):
        u = self.g.pool.get(uid)
        if u is None or u.side != self.g.side:
            return False
        self.sel_unit = uid
        self.sel_idx = self.g.map.axial_idx(u.q, u.r)
        self.reach = P.reachable(self.g.map, self.g.pool, u)
        self.move_overlay = set(i for i in self.reach.list
                                if i != self.sel_idx and self.g.map.occupant[i] == NO_UNIT)
        self.attack_overlay = self._attack_targets(u)
        self.state = SELECTED
        return True

    def _attack_targets(self, u):
        """사거리 안에 있고, 보이고, 상대편인 유닛이 선 칸."""
        out = set()
        if u.ammo <= 0 or u.mp <= 0:
            return out
        m = self.g.map
        for t in self.g.pool.iter_alive():
            if t.side == u.side:
                continue
            i = m.axial_idx(t.q, t.r)
            if i < 0 or m.fog[i] != FOG_VISIBLE:
                continue
            from . import hexcoord as H
            if H.distance(u.q, u.r, t.q, t.r) <= K_RNG[u.kind]:
                out.add(i)
        return out

    def deselect(self):
        self.sel_unit = -1
        self.sel_idx = -1
        self.reach = {}
        self.move_overlay = set()
        self.attack_overlay = set()
        self.state = IDLE

    def next_unit(self):
        """이동력이 남은 아군을 순서대로 돈다. 도스 워게임의 관용 조작."""
        ids = [u.id for u in self.g.pool.iter_alive(self.g.side) if u.mp > 0]
        if not ids:
            return False
        if self.sel_unit in ids:
            nxt = ids[(ids.index(self.sel_unit) + 1) % len(ids)]
        else:
            nxt = ids[0]
        if self.select(nxt):
            self.center_on(self.sel_idx)
            return True
        return False

    # ---------------------------------------------------------------- 입력
    def handle(self, ev):
        """이벤트 문자열 하나를 처리한다. 골든 트레이스가 이 문자열을 재생한다."""
        parts = ev.split()
        kind = parts[0]
        if kind == 'click':
            return self.on_click(int(parts[1]), int(parts[2]))
        if kind == 'key':
            return self.on_key(parts[1])
        if kind == 'render':
            return True
        raise ValueError('알 수 없는 이벤트: %r' % ev)

    def on_click(self, x, y):
        w = hit_test(self.root, x, y)
        if w is None:
            return False
        if self.state == DIALOG_ST:
            # 모달: 대화상자 밖의 클릭은 통째로 버린다
            if w.id == 'yes':
                self.close_dialog()
                self.g.end_turn()
                self.after_turn()
                return True
            if w.id == 'no':
                self.close_dialog()
                return True
            return False
        if w.kind == BUTTON:
            return self.on_button(w.id)
        if w.id == 'minimap':
            return self.on_minimap(x, y, w)
        if w.kind == MAPVIEW:
            return self.on_map_click(x, y)
        return False

    def on_button(self, wid):
        if wid == 'end':
            self.open_dialog()
            return True
        if wid == 'undo':
            ok = self.g.undo()
            if ok and self.sel_unit >= 0:
                if self.g.pool.get(self.sel_unit) is None:
                    self.deselect()
                else:
                    self.select(self.sel_unit)
            return ok
        if wid == 'next':
            return self.next_unit()
        return False

    def on_minimap(self, x, y, w):
        """미니맵 클릭 = 그 자리로 카메라 이동. 2픽셀이 헥스 하나다."""
        col = min(MAP_W - 1, max(0, (x - w.x) // 2))
        row = min(17, max(0, (y - w.y) // 2))
        self.center_on(row * MAP_W + col)
        return True

    def on_map_click(self, x, y):
        hexpos = PK.pick(x, y, self.cam_x, self.cam_y)
        if hexpos is None:
            return False
        col, row = hexpos
        i = row * MAP_W + col
        self.cursor_idx = i
        m = self.g.map
        uid = m.occupant[i]

        if self.state == TARGETING:
            if i in self.attack_overlay and uid != NO_UNIT:
                self.g.attack(self.sel_unit, uid)
                self.after_action()
                return True
            self.state = SELECTED
            return False

        if self.state == SELECTED:
            if i in self.attack_overlay and uid != NO_UNIT:
                self.g.attack(self.sel_unit, uid)
                self.after_action()
                return True
            if i in self.move_overlay:
                self.g.move_unit(self.sel_unit, i)
                self.after_action()
                return True

        if uid != NO_UNIT and m.fog[i] == FOG_VISIBLE:
            u = self.g.pool.get(uid)
            if u is not None and u.side == self.g.side:
                return self.select(uid)
        self.deselect()
        return True

    def on_key(self, k):
        if self.state == DIALOG_ST:
            if k == 'ESC':
                self.close_dialog()
                return True
            if k == 'ENTER':
                self.close_dialog()
                self.g.end_turn()
                self.after_turn()
                return True
            return False
        if k == 'LEFT':
            self.scroll(-PK.HEX_W, 0)
        elif k == 'RIGHT':
            self.scroll(PK.HEX_W, 0)
        elif k == 'UP':
            self.scroll(0, -PK.ROW_STEP)
        elif k == 'DOWN':
            self.scroll(0, PK.ROW_STEP)
        elif k == 'TAB':
            return self.next_unit()
        elif k == 'U':
            return self.on_button('undo')
        elif k == 'E':
            self.open_dialog()
        elif k == 'T':
            if self.state == SELECTED and self.attack_overlay:
                self.state = TARGETING
            else:
                return False
        elif k == 'ESC':
            if self.state == TARGETING:
                self.state = SELECTED
            else:
                self.deselect()
        else:
            return False
        return True

    # ------------------------------------------------------------ 대화상자
    def open_dialog(self):
        self.prev_state = self.state
        self.state = DIALOG_ST
        self._dlg().visible = True

    def close_dialog(self):
        self._dlg().visible = False
        self.state = self.prev_state

    def _dlg(self):
        for c in self.root.children:
            if c.id == 'dialog':
                return c
        raise KeyError('dialog')

    # -------------------------------------------------------------- 뒤처리
    def after_action(self):
        u = self.g.pool.get(self.sel_unit)
        if self.g.over:
            self.state = GAMEOVER
            self.move_overlay = set()
            self.attack_overlay = set()
            return
        if u is None or (u.mp <= 0 and u.ammo <= 0):
            self.deselect()
        else:
            self.select(self.sel_unit)

    def after_turn(self):
        self.deselect()
        if self.g.over:
            self.state = GAMEOVER

    # -------------------------------------------------------------- 요약값
    def digest(self):
        return '%s|sel=%d|cur=%d|cam=%d,%d|mov=%d|atk=%d' % (
            self.state_name(), self.sel_unit, self.cursor_idx,
            self.cam_x, self.cam_y, len(self.move_overlay), len(self.attack_overlay))
