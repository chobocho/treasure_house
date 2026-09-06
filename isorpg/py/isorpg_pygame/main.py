# -*- coding: utf-8 -*-
"""pygame-ce 프런트엔드 — 창을 띄우고 실제로 노는 쪽.

   SPEC §13 의 `play` 자리다. 엔진은 320x200 짜리 8비트 인덱스 버퍼를 내놓고,
   여기서는 그 버퍼에 팔레트를 씌워 창에 올릴 뿐이다. 엔진 상태를 읽기만 하고
   쓰지 않는다 — 프런트엔드가 게임 규칙을 조금이라도 건드리면
   파이썬/루아/타입스크립트 트레이스가 갈라지고, 그 순간 이 저장소의 근거가 무너진다.

   실행:
       cd py && python3 -m isorpg_pygame.main [--scale N] [--nohud]

   조작:
       화살표 / 숫자패드   여덟 방향 이동 (화면 기준. 아래 SCREEN_DIR 주석 참조)
       스페이스            공격
       엔터 / E            상호작용 (상자 열기)
       F5 / F9             빠른 저장 / 불러오기
       Tab                 HUD 켜고 끄기
       Esc                 종료
"""
from __future__ import print_function

import os
import sys
import time

# `python3 py/isorpg_pygame/main.py` 처럼 직접 실행해도 엔진을 찾게 한다.
# 엔진 쪽 main.py 가 `arg[0]` 로 package.path 를 잡는 것과 같은 이유다.
_HERE = os.path.dirname(os.path.abspath(__file__))
_PYROOT = os.path.dirname(_HERE)
if _PYROOT not in sys.path:
    sys.path.insert(0, _PYROOT)

import pygame                                            # noqa: E402

from isorpg import path as P                             # noqa: E402
from isorpg import raster as RA                          # noqa: E402
from isorpg import save as SV                            # noqa: E402
from isorpg.game import Game                             # noqa: E402

SCR_W = RA.SCR_W
SCR_H = RA.SCR_H

# SPEC §0. PIT 기본 분주(18.2065 Hz) 한 번. round(65536*1e6/1193182) 이 아니라
# 정확히 이 정수로 못 박은 값이라, 프런트엔드도 이 값 말고 다른 수를 쓰면 안 된다.
TICK_US = 54925

# 한 프레임에 몰아서 돌릴 틱의 상한. 창을 끌거나 잠깐 멈췄다 돌아오면
# 실시간이 몇 초씩 밀리는데, 그걸 전부 따라잡으려 들면 프레임이 더 길어지고
# 다음 프레임은 더 많이 밀리는 악순환(spiral of death)에 빠진다. 그냥 버린다.
MAX_CATCHUP_TICKS = 8

DEFAULT_SCALE = 3

# 화면 기준 여덟 방향 -> 월드 방향 인덱스(P.DIR_NAME).
#
#   기저가 e_x = (16, 8), e_y = (-16, 8) 이라 월드 축과 화면 축이 45도 어긋나 있다.
#   그래서 월드 E 는 화면에서 '오른쪽아래'로 간다. 화살표 ↑ 를 월드 N 에 그대로
#   이으면 캐릭터가 비스듬히 올라가 조작이 어긋나 보인다. 도스 시절 쿼터뷰 게임들이
#   전부 그랬듯 여기서도 **화면에서 보이는 방향**에 맞춘다.
#     ↑ = NW(화면 정위)  ↓ = SE  ← = SW  → = NE
#   숫자패드는 키 배치 그대로 여덟 방향에 맞아떨어진다.
SCREEN_DIR = {
    (0, -1): 5,     # NW  화면 위
    (1, -1): 6,     # N   화면 오른쪽위
    (1, 0): 7,      # NE  화면 오른쪽
    (1, 1): 0,      # E   화면 오른쪽아래
    (0, 1): 1,      # SE  화면 아래
    (-1, 1): 2,     # S   화면 왼쪽아래
    (-1, 0): 3,     # SW  화면 왼쪽
    (-1, -1): 4,    # W   화면 왼쪽위
}

# (키, 화면 dx, 화면 dy). 화살표와 숫자패드를 같은 표에 넣어 둘을 동시에 눌러도
# 벡터가 그냥 더해지게 한다 — ↑ 와 → 를 같이 누르면 (1,-1) 이 되어 N 이다.
DIR_KEYS = (
    (pygame.K_UP, 0, -1), (pygame.K_DOWN, 0, 1),
    (pygame.K_LEFT, -1, 0), (pygame.K_RIGHT, 1, 0),
    (pygame.K_KP8, 0, -1), (pygame.K_KP2, 0, 1),
    (pygame.K_KP4, -1, 0), (pygame.K_KP6, 1, 0),
    (pygame.K_KP7, -1, -1), (pygame.K_KP9, 1, -1),
    (pygame.K_KP1, -1, 1), (pygame.K_KP3, 1, 1),
)

# HUD 색. 팔레트 앞 16색은 EGA 계열 고정색이라 물 사이클링(16..31)에 휩쓸리지 않는다.
HUD_FRAME = 15          # 흰색 테두리
HUD_BACK = 8            # 어두운 회색 바탕
HUD_HP_HI = 10          # 밝은 초록
HUD_HP_LO = 12          # 밝은 빨강


def palette_rgb(pal):
    """6비트 DAC 팔레트 -> pygame 이 받는 8비트 (r,g,b) 목록.

       expand6 을 그대로 쓴다. PPM 출력과 같은 함수를 타야 창에 뜬 그림과
       out/frame_*.ppm 이 픽셀 단위로 같아진다 — shots.py 가 그걸 검사한다.
    """
    return [(RA.expand6(r), RA.expand6(g), RA.expand6(b)) for r, g, b in pal]


class Screen(object):
    """8비트 인덱스 표면 하나. 엔진 버퍼를 그대로 받아 팔레트만 갈아 끼운다.

       인덱스 -> RGB 변환은 **하지 않는다**. 320x200 짜리 8비트 Surface 를 만들고
       set_palette 로 DAC 를 흉내 낸 뒤, get_buffer().write() 로 64,000바이트를
       통째로 밀어 넣는다. 파이썬 쪽에서 픽셀마다 표를 뒤지면 프레임당 64,000번의
       인덱싱이 붙어 18.2 Hz 도 못 지킨다. 이 경로는 memcpy 한 번이다.
       (numpy 가 없는 환경이라 surfarray 는 쓸 수 없다 — 아래 upload 주석 참조.)
    """
    __slots__ = ('surf', 'scaled', 'base_pal', '_phase')

    def __init__(self, scale=1):
        # depth=8 로 만들면 SDL 이 팔레트 표면을 잡아 준다. 폭 320 은 4의 배수라
        # 줄 간격(pitch)이 정확히 320바이트가 되고, 그래서 프레임버퍼를
        # 한 번의 write 로 밀어 넣을 수 있다. 폭이 4의 배수가 아니면 이 최적화는 깨진다.
        self.surf = pygame.Surface((SCR_W, SCR_H), depth=8)
        if self.surf.get_pitch() != SCR_W:
            raise RuntimeError('8비트 표면의 pitch 가 %d — 통짜 write 를 쓸 수 없다'
                               % self.surf.get_pitch())
        # 확대 결과를 받을 8비트 표면을 미리 잡아 둔다. transform.scale 은
        # 대상 표면을 주면 그 자리에 쓰지만 원본과 형식이 같아야 한다 —
        # 32비트인 창을 대상으로 바로 주면 "compatible formats" 오류가 난다.
        # 매 프레임 새 표면을 만드는 대신 하나를 돌려 쓴다.
        self.scaled = None
        if scale > 1:
            self.scaled = pygame.Surface((SCR_W * scale, SCR_H * scale), depth=8)
        self.base_pal = RA.load_palette()
        self._phase = None

    def set_phase(self, phase):
        """물 램프 위상. 프레임버퍼는 손대지 않고 DAC 만 돌린다 — SPEC §7.6 그대로.

           위상이 그대로면 아무것도 하지 않는다. pal_phase 는 4틱에 한 번만 바뀌므로
           대부분의 프레임에서 이 함수는 비교 한 번으로 끝난다.
           확대본에도 같은 팔레트를 물린다. 확대는 인덱스만 복제하므로
           팔레트가 어긋나면 색이 통째로 뒤집힌다.
        """
        if phase == self._phase:
            return
        self._phase = phase
        rgb = palette_rgb(RA.cycle_palette(self.base_pal, phase))
        self.surf.set_palette(rgb)
        if self.scaled is not None:
            self.scaled.set_palette(rgb)

    def upload(self, fb):
        """엔진 프레임버퍼를 표면에 올린다.

           surfarray.pixels2d 를 쓰면 더 짧게 쓸 수 있지만 numpy 를 끌고 온다.
           엔진이 순수 표준 라이브러리라는 약속을 프런트엔드에서 깨고 싶지 않아
           BufferProxy 로 직접 쓴다. 어차피 하는 일은 같은 memcpy 다.
           write 는 표면을 잠그므로 반드시 풀고 나가야 한다(아래 del).
        """
        buf = self.surf.get_buffer()
        buf.write(bytes(fb), 0)
        del buf

    def present_to(self, window):
        """확대해서 창에 올린다. 8비트 -> 창의 32비트 변환은 blit 이 한 번에 한다.

           부드럽게(smoothscale) 늘리면 픽셀이 뭉개져 모드 13h 의 계단이 사라진다 —
           그건 이 문서가 보이려는 것과 정반대다. 그래서 정수배 최근접만 쓴다.
        """
        if self.scaled is None:
            window.blit(self.surf, (0, 0))
            return
        pygame.transform.scale(self.surf, self.scaled.get_size(), self.scaled)
        window.blit(self.scaled, (0, 0))


def draw_hp_bar(fb, cur, mx):
    """HUD 를 320x200 인덱스 버퍼에 직접 그린다. pygame 폰트를 쓰지 않는 이유가 있다.

       pygame 으로 글자를 얹으면 그 픽셀은 8비트 세계 바깥에 있게 되어
       '모드 13h 를 흉내 낸다'는 이 저장소의 전제가 깨진다. 그래서 채우기만으로
       막대 하나를 그린다. render() 가 매 프레임 clear(0) 로 시작하므로
       여기서 버퍼를 덧칠해도 다음 프레임에 남지 않고, 엔진 상태도 건드리지 않는다.
    """
    x0, y0, w, h = 4, 4, 64, 6
    for y in range(y0 - 1, y0 + h + 1):
        base = y * SCR_W
        for x in range(x0 - 1, x0 + w + 1):
            fb[base + x] = HUD_FRAME
    inner = w
    fill = 0 if mx <= 0 else (cur * inner) // mx
    if fill < 0:
        fill = 0
    elif fill > inner:
        fill = inner
    # 3분의 1 아래면 빨강. 도스 게임의 관례이고, 색상 두 개면 충분히 읽힌다.
    color = HUD_HP_LO if mx > 0 and cur * 3 <= mx else HUD_HP_HI
    for y in range(y0, y0 + h):
        base = y * SCR_W
        for x in range(x0, x0 + w):
            fb[base + x] = color if x - x0 < fill else HUD_BACK


class Frontend(object):
    """창 하나 + 게임 하나. 고정 타임스텝을 지키는 것이 이 클래스의 전부다."""

    def __init__(self, scale=DEFAULT_SCALE, hud=True, save_path=None):
        self.game = Game()
        self.screen = Screen(scale)
        self.scale = scale
        self.hud = hud
        self.save_path = save_path or os.path.join(_PYROOT, 'quick.sav')
        self.window = pygame.display.set_mode((SCR_W * scale, SCR_H * scale))
        pygame.display.set_caption('IsoRPG — 320x200 / 8bit / %dx' % scale)
        self.running = True
        # 한 틱만 서는 명령들. 스크립트의 act/atk 이 정확히 한 틱짜리라
        # 키를 누르고 있어도 매 틱 발동하지 않도록 눌린 순간에만 세운다.
        self.pending_act = False
        self.pending_atk = False

    # ------------------------------------------------------------ 입력
    def poll(self):
        """이벤트 큐를 비우고, 한 틱짜리 명령을 예약한다."""
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN:
                k = ev.key
                if k == pygame.K_ESCAPE:
                    self.running = False
                elif k == pygame.K_SPACE:
                    self.pending_atk = True
                elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
                    self.pending_act = True
                elif k == pygame.K_F5:
                    self.quick_save()
                elif k == pygame.K_F9:
                    self.quick_load()
                elif k == pygame.K_TAB:
                    self.hud = not self.hud

    def held_dir(self):
        """지금 눌려 있는 방향키들을 합쳐 여덟 방향 중 하나로. 없으면 -1.

           벡터를 더한 뒤 부호만 남긴다. ←→ 를 같이 누르면 0 이 되어 서지 않는데,
           그게 도스 게임의 관례이자 가장 덜 놀라운 동작이다.
        """
        keys = pygame.key.get_pressed()
        dx = 0
        dy = 0
        for key, kx, ky in DIR_KEYS:
            if keys[key]:
                dx += kx
                dy += ky
        if dx > 0:
            dx = 1
        elif dx < 0:
            dx = -1
        if dy > 0:
            dy = 1
        elif dy < 0:
            dy = -1
        return SCREEN_DIR.get((dx, dy), -1)

    # ------------------------------------------------------------ 저장
    def quick_save(self):
        """SPEC §11 의 세이브를 그대로 파일로. 메모리 슬롯에도 같이 넣어 둔다.

           엔진의 save/load 명령과 완전히 같은 바이트열이라, 여기서 만든 세이브를
           트레이스 쪽 load 가 그대로 먹는다. 프런트엔드가 형식을 따로 만들지 않는다.
        """
        blob = SV.pack_state(self.game)
        self.game.slot = blob
        try:
            open(self.save_path, 'wb').write(blob)
        except IOError as e:
            sys.stderr.write('저장 실패: %s\n' % e)

    def quick_load(self):
        blob = self.game.slot
        if blob is None:
            try:
                blob = open(self.save_path, 'rb').read()
            except IOError:
                return
        SV.unpack_state(blob, self.game)

    # ------------------------------------------------------------ 한 틱
    def step(self):
        self.game.in_dir = self.held_dir()
        self.game.in_act = 1 if self.pending_act else 0
        self.game.in_atk = 1 if self.pending_atk else 0
        self.pending_act = False
        self.pending_atk = False
        self.game.tick()

    # ------------------------------------------------------------ 한 프레임
    def present(self):
        fb = self.game.render()
        if self.hud:
            p = self.game.ents[0]
            draw_hp_bar(fb, p.hp, p.maxhp)
        self.screen.set_phase(self.game.pal_phase)
        self.screen.upload(fb)
        self.screen.present_to(self.window)
        pygame.display.flip()

    # ------------------------------------------------------------ 루프
    def run(self):
        """고정 타임스텝. 실제 시간을 마이크로초로 모아 두고 온전한 틱만 돌린다.

           '남은 시간으로 반 틱' 같은 것은 절대 하지 않는다. 반 틱을 허용하는 순간
           프레임률에 따라 결과가 달라져 트레이스 대조가 무의미해진다.
           그리기는 남은 시간과 무관하게 매 프레임 한 번 — 렌더는 상태를 바꾸지 않으므로
           몇 번을 그리든 안전하다.
        """
        acc = 0
        prev = time.perf_counter()
        while self.running:
            now = time.perf_counter()
            dt_us = int((now - prev) * 1000000.0)
            prev = now
            if dt_us < 0:
                dt_us = 0
            acc += dt_us
            if acc > TICK_US * MAX_CATCHUP_TICKS:
                acc = TICK_US * MAX_CATCHUP_TICKS
            self.poll()
            while acc >= TICK_US and self.running:
                acc -= TICK_US
                self.step()
            self.present()
            # 18.2 Hz 짜리 게임을 200 fps 로 그려 봐야 같은 그림이다. 남는 시간은 돌려준다.
            pygame.time.wait(1)


def parse_args(argv):
    scale = DEFAULT_SCALE
    hud = True
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == '--scale' and i + 1 < len(argv):
            scale = int(argv[i + 1])
            i += 2
            continue
        if a == '--nohud':
            hud = False
        elif a in ('-h', '--help'):
            sys.stdout.write(__doc__)
            return None
        else:
            sys.stderr.write('모르는 인자: %s\n' % a)
            return None
        i += 1
    if scale < 1:
        scale = 1
    return scale, hud


def main(argv):
    opts = parse_args(argv)
    if opts is None:
        return 1
    scale, hud = opts
    pygame.init()
    try:
        Frontend(scale=scale, hud=hud).run()
    finally:
        pygame.quit()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
