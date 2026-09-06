# -*- coding: utf-8 -*-
"""대화형 창 — 입력을 명령으로 바꾸고 프레임버퍼를 화면에 올린다 (SPEC §12·§23).

   구조는 한 줄로 요약된다: **입력 → 명령 → net(§19) → sim.step → render → 화면.**
   반대 방향의 화살표는 없다. UI 가 `sim.w.tx[i] = ...` 를 쓰는 순간 §12.5 가
   깨지고, 그러면 같은 명령을 먹은 두 기계가 다른 그림을 그린다.

   그래서 STOP 하나를 보내는 데에도 net 의 지연 큐를 지난다 — 사람의 클릭이
   AI·스크립트와 **완전히 같은 경로**를 통과하는지 눈으로 확인할 수 있는 것이
   이 프런트엔드의 존재 이유다.

   화면 배율은 정수배(×2·×3)만 쓴다. 팔레트 인덱스 화면을 부드럽게 늘리면
   경계에 없는 색이 생기고, 그러면 §22 의 색 256개라는 전제가 무너진다.
"""

import os
import sys

import pygame

from rts import const as C
from rts import fixed as F
from rts import main as MA
from rts import net as NET
from rts import raster as RS
from rts import render as RD
from rts import select as SEL
from rts import sim as SIM
from rts import spatial as S
from rts import tmap as T

SCALE = 3
KEY_SCROLL = 8                    # 화살표는 가장자리 스크롤(4px/틱)의 두 배
DRAG_MIN = 3                      # 이보다 짧게 끈 것은 상자가 아니라 클릭이다
CYCLE_EVERY = 2                   # §22.6 물 색은 두 틱에 한 칸 — 18Hz 에서 적당하다

# F1..F5 로 생산. 숫자 키는 §12.3 컨트롤 그룹이 이미 쓰고 있어서 비켜 놨다.
TRAIN_KEYS = ((pygame.K_F1, C.INF), (pygame.K_F2, C.ARCHER),
              (pygame.K_F3, C.TANK), (pygame.K_F4, C.MORTAR),
              (pygame.K_F5, C.HARV))
GROUP_KEYS = ((pygame.K_1, 1), (pygame.K_2, 2), (pygame.K_3, 3),
              (pygame.K_4, 4), (pygame.K_5, 5), (pygame.K_6, 6),
              (pygame.K_7, 7), (pygame.K_8, 8), (pygame.K_9, 9),
              (pygame.K_0, 0))

_MASK = {}


def sprite_mask(kind, d, lx, ly):
    """§12.1 픽킹이 쓰는 알파 마스크. RLE 를 한 번 펴서 (종류, 방향)마다 캐시한다.

       국소 좌표를 그대로 쓸 수 있는 이유: 블릿 기준점이 px + TILE*FOOT/2 이고
       스프라이트의 ox 가 폭의 절반이라, 스프라이트 상자의 좌상단이 §12.1 의
       AABB 좌상단과 정확히 겹친다. 겹치지 않았다면 여기서 보정해야 한다.
    """
    ent = _MASK.get((kind, d))
    if ent is None:
        spr, flip = RS.sprite_for(kind, d)
        ent = (spr, flip, spr.pixels() if spr is not None else None)
        _MASK[(kind, d)] = ent
    spr, flip, px = ent
    if spr is None:
        return True                          # 그림이 없으면 AABB 로 만족한다
    if flip:
        lx = spr.w - 1 - lx
    if not (0 <= lx < spr.w and 0 <= ly < spr.h):
        return False
    return px[ly * spr.w + lx] != 0


def pygame_palette(pal):
    """§22.10 과 같은 확장식. DAC 6비트를 8비트로 늘리는 자리는 한 곳뿐이어야
       PPM 과 화면의 색이 어긋나지 않는다."""
    return [(RS.expand(c[0]), RS.expand(c[1]), RS.expand(c[2])) for c in pal]


def in_minimap(sx, sy):
    return (C.MINI_X <= sx < C.MINI_X + C.MINI_W
            and C.MINI_Y <= sy < C.MINI_Y + C.MINI_H)


class Game(object):
    """시뮬 하나 + 그 시뮬을 보는 눈(카메라·선택). **상태는 시뮬 쪽에만 있다.**

       선택 목록과 명령 큐는 UI 의 것이라 여기 둔다 — 이 둘은 해시에 들어가지
       않고, 들어가서도 안 된다(플레이어마다 다르니까).
    """

    def __init__(self, mode='play', player=0, seed=1):
        m = T.TMap.load_text(MA.golden('map_start.txt'))
        self.script = None
        if mode == 'scenario':
            # 골든 시나리오를 그대로 재생한다. 스크립트가 몰기 때문에 AI 는 끈다
            # (§18.6 — 한 지갑을 둘이 쓰면 서로의 건설을 굶긴다).
            self.script = SIM.parse_script(MA.golden('script.txt'))
            self.sim = SIM.Sim(m, seed, self.script.players)
            self.sim.setup_start(ai=False)
        else:
            self.sim = SIM.Sim(m, seed, 2)
            self.sim.setup_start(ai=False)
            for p in range(1, self.sim.players):
                self.sim.ai_enabled[p] = True   # 사람은 0번, 나머지는 §17 의 AI
        self.p = player
        self.pal = RS.build_palette()
        self.light = RS.build_light(self.pal)   # 262,144회 비교 — 시작할 때 한 번
        self.frame = RS.Frame()
        self.view = RD.View()
        self.view.center_on(self.sim.m, self.sim.m.starts[player][0],
                            self.sim.m.starts[player][1])
        self.net = NET.Net(1, latency=C.ORDER_DELAY)
        self.outbox = []
        self.uq = SEL.Orders()                  # §12.4 — UI 쪽 명령 큐
        self.wait = [0] * C.MAX_ENT
        self.groups = SEL.Groups()
        self.selection = []
        self.phase = 0
        self.message = ''
        self.drag = None                        # (x0, y0) — 끌고 있는 중이면
        self.mouse = None                       # 마지막 마우스 위치(320×200 좌표)
        self.amove = False
        self.surf = pygame.Surface((C.SCR_W, C.SCR_H), depth=8)
        self.surf.set_palette(pygame_palette(self.pal))

    # ── 명령 ───────────────────────────────────────────────────────────────
    def issue(self, kind, a=0, b=0, c=0, shift=False):
        """선택된 전원에게 같은 명령. 여기서 큐에 넣을 뿐 시뮬은 건드리지 않는다.

           STOP 만 큐를 지나지 않는다 — §12.4 의 push 가 STOP 을 "큐를 비우는
           신호"로 정의했기 때문이다. 비운 뒤 곧바로 보내야 실제로 선다.
        """
        w = self.sim.w
        for h in self.selection:
            if not w.valid(h):
                continue
            i = S.index(h)
            self.uq.push(i, (kind, a, b, c), shift)
            if kind == SEL.STOP:
                self.outbox.append((self.p, h, SEL.STOP, 0, 0, 0))
                self.wait[i] = C.ORDER_DELAY + 1
            elif not shift:
                self.wait[i] = 0                # 새 명령은 다음 틱에 바로 나간다

    def _pump(self):
        """큐의 머리를 하나씩 내보낸다. 유닛이 놀고 있을 때만 다음 것을 꺼낸다.

           보낸 뒤 ORDER_DELAY+1 틱을 기다리는 이유: 명령은 §12.5 대로 2틱 뒤에
           도착하므로, 그 사이에 상태를 보면 아직 ST_IDLE 이라 같은 명령을 두 번
           보내게 된다.
        """
        w = self.sim.w
        for i in range(1, C.MAX_ENT):
            if w.alive[i] == 0:
                if self.uq.q[i]:
                    self.uq.clear(i)
                continue
            if self.wait[i] > 0:
                self.wait[i] -= 1
                continue
            if not self.uq.q[i] or w.state[i] != C.ST_IDLE:
                continue
            kind, a, b, c = self.uq.pop(i)
            self.outbox.append((self.p, w.handle(i), kind, a, b, c))
            self.wait[i] = C.ORDER_DELAY + 1

    def advance(self):
        """한 틱. 사람·스크립트·AI 의 명령이 여기 한 곳에서 합쳐져 정렬된다."""
        self._pump()
        now = self.sim.tick
        for o in self.outbox:
            self.net.send(now, self.p, o)
        self.outbox = []
        self.net.flush(now, self.p)             # 빈 턴도 보낸다(§19.2)
        nt = now + 1
        orders = list(self.net.take(nt))
        if self.script is not None:
            orders.extend(self.sim.script_orders(self.script, nt))
        orders.sort()                           # §18.1 — 정렬은 sim 이 검사한다
        h = self.sim.step(orders)
        self.phase = (self.sim.tick // CYCLE_EVERY) % RS.WATER_N
        self.selection = [x for x in self.selection if self.sim.w.valid(x)]
        return h

    # ── 입력 ───────────────────────────────────────────────────────────────
    def cam(self):
        return (self.view.cam_x, self.view.cam_y)

    def scroll(self, keys, mouse):
        """카메라는 정수 픽셀이다(§23.2). 화살표가 눌렸으면 가장자리는 쉰다."""
        dx = dy = 0
        if keys[pygame.K_LEFT]:
            dx -= KEY_SCROLL
        if keys[pygame.K_RIGHT]:
            dx += KEY_SCROLL
        if keys[pygame.K_UP]:
            dy -= KEY_SCROLL
        if keys[pygame.K_DOWN]:
            dy += KEY_SCROLL
        if dx == 0 and dy == 0 and mouse is not None:
            dx, dy = RD.edge_scroll(mouse[0], mouse[1])
        if dx or dy:
            self.view.move(self.sim.m, dx, dy)

    def left_down(self, sx, sy):
        if SEL.in_view(sx, sy):
            self.drag = (sx, sy)

    def left_up(self, sx, sy, shift):
        start = self.drag
        self.drag = None
        if in_minimap(sx, sy):
            tx, ty = RD.minimap_to_tile(sx - C.MINI_X, sy - C.MINI_Y)
            self.view.center_on(self.sim.m, tx, ty)
            return
        if not SEL.in_view(sx, sy):
            return
        if self.amove:                          # A 다음의 좌클릭은 공격 이동
            self.amove = False
            wx, wy = SEL.screen_to_world(self.cam(), sx, sy)
            self.issue(SEL.ATTACK_MOVE, wx // C.TILE, wy // C.TILE, 0, shift)
            self.message = ''
            return
        if start is not None and (abs(sx - start[0]) >= DRAG_MIN
                                  or abs(sy - start[1]) >= DRAG_MIN):
            self.selection = SEL.box_select(self.sim.w, self.p, self.cam(),
                                            start[0], start[1], sx, sy)
            return
        h = SEL.pick(self.sim.w, self.cam(), sx, sy, sprite_mask)
        if h and self.sim.w.owner[S.index(h)] == self.p:
            self.selection = [h]
        else:
            self.selection = []                 # 남의 것은 고르지 않는다

    def right_click(self, sx, sy, shift):
        """§12.4 의 문맥 규칙을 그대로 따른다 — 판정 순서가 곧 명세다."""
        if in_minimap(sx, sy):
            tx, ty = RD.minimap_to_tile(sx - C.MINI_X, sy - C.MINI_Y)
            self.issue(SEL.MOVE, tx, ty, 0, shift)
            return
        if not SEL.in_view(sx, sy):
            return
        self.amove = False
        wx, wy = SEL.screen_to_world(self.cam(), sx, sy)
        tx, ty = wx // C.TILE, wy // C.TILE
        h = SEL.pick(self.sim.w, self.cam(), sx, sy, sprite_mask)
        kind = SEL.context_order(self.sim.w, self.sim.ec, self.sim.m,
                                 self.p, tx, ty, h)
        self.issue(kind, tx, ty, h if kind == SEL.ATTACK else 0, shift)

    def key_down(self, key, mods):
        w = self.sim.w
        ctrl = mods & pygame.KMOD_CTRL
        shift = bool(mods & pygame.KMOD_SHIFT)
        for (k, g) in GROUP_KEYS:
            if key != k:
                continue
            if ctrl:
                self.groups.set(g, self.selection)     # §12.3 — 핸들만 담는다
                self.message = 'GROUP %d SET' % g
            else:
                self.selection = self.groups.recall(w, g)
                if self.selection:
                    j = S.index(self.selection[0])
                    self.view.center_on(self.sim.m, w.tx[j], w.ty[j])
            return
        for (k, kind) in TRAIN_KEYS:
            if key == k:
                self.issue(SEL.TRAIN, kind, 0, 0, shift)
                return
        if key == pygame.K_s:
            self.issue(SEL.STOP)
        elif key == pygame.K_h:
            self.issue(SEL.HOLD)
        elif key == pygame.K_a:
            self.amove = True
            self.message = 'ATTACK MOVE'
        elif key == pygame.K_SPACE and self.selection:
            j = S.index(self.selection[0])
            self.view.center_on(self.sim.m, w.tx[j], w.ty[j])

    # ── 그리기 ─────────────────────────────────────────────────────────────
    def _drag_box(self, fb):
        """드래그 상자는 시뮬과 무관한 UI 라 프레임버퍼에 직접 긋는다.
           `_fill` 이 뷰포트로 잘라 주므로 경계 검사를 다시 하지 않는다."""
        if self.drag is None or self.mouse is None:
            return
        x0, y0 = self.drag
        x1, y1 = self.mouse
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        RD._fill(fb, x0, y0, x1 - x0 + 1, 1, RD.UI_SELECT)
        RD._fill(fb, x0, y1, x1 - x0 + 1, 1, RD.UI_SELECT)
        RD._fill(fb, x0, y0, 1, y1 - y0 + 1, RD.UI_SELECT)
        RD._fill(fb, x1, y0, 1, y1 - y0 + 1, RD.UI_SELECT)

    def render(self, mouse=None):
        """프레임버퍼를 채우고 8비트 서피스로 옮긴다. 반환값은 320×200 서피스다.

           팔레트 사이클(§22.6)은 프레임버퍼를 건드리지 않는다 — 팔레트만
           갈아 끼운다. 도스 시절 이것이 공짜 애니메이션이었던 이유 그대로다.
        """
        self.mouse = mouse
        pal = RS.cycle_water(self.pal, self.phase)
        RD.draw(self.frame.fb, self.sim, self.view, self.phase, pal,
                self.light, self.p, self.selection, self.message)
        self._drag_box(self.frame.fb)
        self.surf.set_palette(pygame_palette(pal))
        buf = self.surf.get_buffer()
        buf.write(bytes(bytearray(self.frame.fb)))
        del buf                                 # 버퍼가 살아 있으면 서피스가 잠긴다
        return self.surf

    def fb_hash(self):
        """프레임버퍼의 FNV-1a. 세 언어·두 프런트엔드가 같은 그림을 그렸는지
           한 줄로 비교하는 값이다 (LÖVE 쪽 record.lua 가 같은 값을 낸다)."""
        return F.fnv1a(bytes(bytearray(self.frame.fb)))


class App(object):
    """창 하나. 시뮬은 고정 틱(18.2Hz)으로, 그리기는 그릴 수 있는 만큼 한다."""

    def __init__(self, mode='play', scale=SCALE):
        pygame.display.init()
        self.scale = scale
        self.screen = pygame.display.set_mode((C.SCR_W * scale,
                                               C.SCR_H * scale))
        pygame.display.set_caption('DOS-RTS — %s' % mode)
        self.game = Game(mode)
        self.clock = pygame.time.Clock()
        self.acc = 0                            # 밀린 시간(µs)
        self.paused = False
        self.running = True

    def _screen_xy(self, pos):
        """창 좌표를 320×200 좌표로. 정수 나눗셈이다 — §23.2 는 실수를 모른다."""
        return (pos[0] // self.scale, pos[1] // self.scale)

    def _events(self):
        g = self.game
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                sx, sy = self._screen_xy(e.pos)
                if e.button == 1:
                    g.left_down(sx, sy)
            elif e.type == pygame.MOUSEBUTTONUP:
                sx, sy = self._screen_xy(e.pos)
                shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                if e.button == 1:
                    g.left_up(sx, sy, shift)
                elif e.button == 3:
                    g.right_click(sx, sy, shift)
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self.running = False
                elif e.key == pygame.K_p:
                    self.paused = not self.paused
                elif e.key == pygame.K_f and self.paused:
                    g.advance()                 # 한 틱만 — 버그를 볼 때 쓴다
                else:
                    # 이벤트에 실려 온 mod 를 쓴다. get_mods() 는 "지금" 눌린
                    # 것이라, 키를 뗀 뒤 늦게 처리되면 Ctrl 을 놓친다.
                    g.key_down(e.key, e.mod)

    def run(self):
        g = self.game
        while self.running:
            dt = self.clock.tick(60)
            self._events()
            mouse = self._screen_xy(pygame.mouse.get_pos())
            g.scroll(pygame.key.get_pressed(), mouse)
            if not self.paused:
                # 남은 시간을 다 소진하지 않고 한 프레임에 최대 세 틱만 따라간다.
                # 못 따라가는 기계에서 무한히 밀리는 것보다 느려지는 편이 낫다.
                self.acc += dt * 1000
                n = 0
                while self.acc >= C.TICK_US and n < 3:
                    self.acc -= C.TICK_US
                    g.advance()
                    n += 1
                if self.acc >= C.TICK_US:
                    self.acc = 0
            g.message = 'PAUSED' if self.paused else 'T%d' % g.sim.tick
            surf = g.render(mouse)
            # 팔레트 서피스를 바로 늘려 창에 넣을 수는 없다(형식이 다르다).
            # 320×200 에서 한 번 변환한 뒤 늘린다 — 64,000픽셀만 변환하면 된다.
            shown = surf.convert(self.screen)
            pygame.transform.scale(shown, self.screen.get_size(), self.screen)
            pygame.display.flip()
        pygame.display.quit()


HELP = """DOS-RTS pygame 프런트엔드
  사용법: python3 -m rts_pygame.app [play|scenario] [배율]
  좌드래그 상자 선택 · 좌클릭 픽킹 · 우클릭 문맥 명령(§12.4)
  화살표/가장자리 스크롤 · 숫자키 그룹 복귀 · Ctrl+숫자 그룹 지정
  A 공격이동 · S 정지 · H 대기 · F1..F5 생산 · P 일시정지 · F 한 틱 · Esc 종료
"""


def main(argv):
    if argv and argv[0] in ('-h', '--help'):
        sys.stdout.write(HELP)
        return 0
    mode = argv[0] if argv and argv[0] in ('play', 'scenario') else 'play'
    scale = int(argv[1]) if len(argv) > 1 else SCALE
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')   # 소리는 쓰지 않는다
    App(mode, scale).run()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
