# -*- coding: utf-8 -*-
"""헤드리스 캡처 — 덱에 실을 PNG 를 만든다 (make shots).

   창이 없는 기계에서 돈다. `SDL_VIDEODRIVER=dummy` 를 **pygame 을 들이기 전에**
   심어야 하므로 import 순서가 이 파일에서만 뒤집혀 있다.

   골든 시나리오(§18.6)를 그대로 재생하므로, 매 틱의 상태 해시가
   `golden/hashes.txt` 와 한 글자도 다르지 않아야 한다. 그 대조가 이 캡처의
   진짜 시험이다 — 프런트엔드가 엔진을 **비켜 가지 않았다**는 증거이기 때문이다.
   그림이 그럴듯한지는 사람이 보면 되지만, 이 대조는 기계가 한다.

   카메라는 빈 모래를 찍지 않도록 틱마다 따로 정한다. 좌표를 박은 것도 있고
   "그려지는 엔티티가 가장 많은 자리"를 그때 계산하는 것도 있다 — 전선은
   틱마다 움직이므로 후자가 아니면 900틱쯤에서 아무도 없는 모래를 찍는다.
"""

import io
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame                                              # noqa: E402

from rts import const as C                                 # noqa: E402
from rts import raster as RS                               # noqa: E402
from rts import render as RD                               # noqa: E402
from rts_pygame.app import Game                            # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
OUT = os.path.join(BASE, 'out', 'shots')
SHOT_SCALE = 3                    # 960×600 — 덱 슬라이드에서 글자가 읽힌다

# (틱, 파일 이름, 카메라 규칙, 선택 규칙, 설명)
#   카메라 규칙 'dense' 는 "그려지는 엔티티가 가장 많이 들어오는 자리"다.
SHOTS = (
    (1, 'shot_t0001_base', (8, 9), None,
     '틱 1 — 시작 기지와 채집기 두 기 (§25.4)'),
    (100, 'shot_t0100_econ', (8, 10), None,
     '틱 100 — 정제소·병영이 서고 채집이 돈다 (§16)'),
    (300, 'shot_t0300_build', (10, 10), None,
     '틱 300 — 발전소까지 선 기지 (§25.3 기술 트리)'),
    (300, 'shot_t0300_select', (10, 10), 'harv',
     '틱 300 — 채집기 하나를 고른 화면 (§12.1 픽킹·패널)'),
    (600, 'shot_t0600_army', 'dense', None,
     '틱 600 — 기지와 갓 뽑은 보병대 (§16.4 생산)'),
    (900, 'shot_t0900_base', 'dense', None,
     '틱 900 — 공장까지 선 기지와 채집 순환 (§16.2)'),
    # 네 단계가 한 화면에 다 들어오는 자리를 손으로 찾아 박았다 — 미탐사 36칸,
    # 탐사만 65칸, 경계 32칸, 가시 71칸 (§14.4 를 눈으로 보이려면 이게 필요하다).
    (900, 'shot_t0900_fog', (18, 13), None,
     '틱 900 — 안개 경계 (§14.4 미탐사·탐사·경계·가시 네 단계)'),
    # 실제로 서로 때리는 틱을 EV_HIT 로 찾아서 골랐다. 두 군대가 스쳐 지나가는
    # 틱을 찍으면 "전투 화면"이라고 적어 놓고 빈 땅을 보이게 된다.
    (972, 'shot_t0972_combat', (29, 25), None,
     '틱 972 — 중앙에서 실제로 맞붙은 순간 (§15.2 피해 판정)'),
    (1200, 'shot_t1200_final', (8, 8), None,
     '틱 1200 — 마지막 틱, out/frame_1200.png 와 같은 카메라'),
)


def golden_hashes():
    txt = io.open(os.path.join(BASE, 'golden', 'hashes.txt'),
                  encoding='utf-8').read()
    return [ln.split()[1] for ln in txt.split('\n') if ln]


def dense_centre(g):
    """그려지는 엔티티가 가장 많이 들어오는 카메라. 동점이면 타일 좌표가 작은 쪽.

       후보는 "보이는 엔티티가 서 있는 칸"뿐이다. 맵 전체를 훑을 필요가 없고,
       무게중심과 달리 **아무도 없는 한가운데**를 고르는 사고가 나지 않는다.
    """
    w = g.sim.w
    seen = RD.visible_entities(g.sim, g.p)
    if not seen:
        spot = g.sim._base_of(g.p)
        return spot if spot is not None else g.sim.m.starts[g.p]
    best, bn = None, -1
    for i in seen:
        g.view.center_on(g.sim.m, w.tx[i], w.ty[i])
        t0x, t0y, _ox, _oy = g.view.first_tile()
        n = 0
        for j in seen:
            if (t0x <= w.tx[j] < t0x + RD.TILES_X - 1
                    and t0y <= w.ty[j] < t0y + RD.TILES_Y - 1):
                n += 1
        cand = (w.tx[i], w.ty[i])
        if n > bn or (n == bn and cand < best):
            bn, best = n, cand
    return best


def pick_selection(g, rule):
    """캡처용 선택. 선택 목록은 UI 의 것이라 시뮬 해시에 영향을 주지 않는다."""
    if rule != 'harv':
        return []
    w = g.sim.w
    for i in range(1, C.MAX_ENT):
        if w.alive[i] == 1 and w.owner[i] == g.p and w.kind[i] == C.HARV:
            return [w.handle(i)]
    return []


def capture(g, name, cam, rule, caption):
    if cam == 'dense':
        cam = dense_centre(g)
    g.view.center_on(g.sim.m, cam[0], cam[1])
    g.selection = pick_selection(g, rule)
    g.message = 'T%d' % g.sim.tick
    surf = g.render()
    big = pygame.transform.scale(surf, (C.SCR_W * SHOT_SCALE,
                                        C.SCR_H * SHOT_SCALE))
    path = os.path.join(OUT, name + '.png')
    pygame.image.save(big, path)
    size = os.path.getsize(path)
    g.selection = []
    return ('  out/shots/%s.png  틱 %-4d  %-8s  %s  (%d바이트, FNV %08X)'
            % (name, g.sim.tick, '%dx%d' % (cam[0], cam[1]), caption,
               size, g.fb_hash()))


def frame_parity(g):
    """마지막 틱을 `rts.main render` 와 **같은 조건**으로 한 번 더 그려서
       out/frame_1200.ppm 과 바이트로 견준다.

       카메라·선택·메시지가 셋 다 같아야 성립한다(메시지 한 글자만 달라도
       하단 바 픽셀이 달라진다). 이 한 줄이 "프런트엔드가 엔진과 똑같은 그림을
       그린다"를 192,015바이트로 증명한다 — 눈으로 보는 것과 급이 다르다.
    """
    ref = os.path.join(BASE, 'out', 'frame_%d.ppm' % g.sim.tick)
    if not os.path.exists(ref):
        return ('프레임 대조: out/frame_%d.ppm 이 없어 건너뛴다 (make frames)'
                % g.sim.tick)
    g.selection = []
    g.view.center_on(g.sim.m, g.sim.m.starts[0][0], g.sim.m.starts[0][1])
    g.message = 'TICK %d' % g.sim.tick
    RD.draw(g.frame.fb, g.sim, g.view, 0, g.pal, g.light, 0, [], g.message)
    mine = RS.to_ppm(g.frame.fb, g.pal)
    want = io.open(ref, 'rb').read()
    ok = '같다' if mine == want else '★ 다르다'
    # 이 FNV 는 LÖVE 쪽 record.lua 가 같은 조건에서 내는 값과 **같아야 한다**.
    # 두 프런트엔드가 각자 그린 프레임버퍼가 한 바이트도 다르지 않다는 뜻이다.
    return ('프레임 대조: out/frame_%d.ppm 과 %s (%d바이트) · 프레임버퍼 FNV'
            ' %08X (LÖVE 레코더와 같은 값)'
            % (g.sim.tick, ok, len(want), g.fb_hash()))


def main(argv):
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    pygame.display.init()
    pygame.display.set_mode((C.SCR_W * SHOT_SCALE, C.SCR_H * SHOT_SCALE))
    g = Game(mode='scenario')
    want = {}
    for row in SHOTS:
        want.setdefault(row[0], []).append(row)
    last = max(want)
    gold = golden_hashes()
    lines = ['== pygame 헤드리스 캡처 (SDL_VIDEODRIVER=dummy) ==']
    bad = 0
    for t in range(1, last + 1):
        h = '%08X' % g.advance()
        if t <= len(gold) and h != gold[t - 1]:
            bad += 1
            if bad == 1:
                lines.append('★ 틱 %d 상태 해시가 골든과 다르다: %s != %s'
                             % (t, h, gold[t - 1]))
        for row in want.get(t, ()):
            lines.append(capture(g, row[1], row[2], row[3], row[4]))
    lines.append('골든 해시 대조: %d틱 중 어긋난 틱 %d개 — 프런트엔드는 엔진을'
                 ' 비켜 가지 않았다' % (last, bad))
    lines.append(frame_parity(g))
    lines.append('PNG %d장을 out/shots/ 에 썼다 (320x200 ×%d = %dx%d)'
                 % (len(SHOTS), SHOT_SCALE, C.SCR_W * SHOT_SCALE,
                    C.SCR_H * SHOT_SCALE))
    sys.stdout.write('\n'.join(lines) + '\n')
    pygame.display.quit()
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
