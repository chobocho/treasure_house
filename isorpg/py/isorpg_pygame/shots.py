# -*- coding: utf-8 -*-
"""헤드리스 스크린샷 — 덱에 실을 PNG 를 만들고, 그 PNG 가 맞는지 검사한다.

   창을 띄울 수 없는 기계에서도 돌아야 하므로 pygame 을 들이기 **전에**
   SDL_VIDEODRIVER=dummy 를 박는다. 순서가 뒤바뀌면 SDL 이 이미 초기화된 뒤라
   환경변수가 먹지 않는다.

   그리고 이 파일의 절반은 '검사'다. 스크린샷은 증거로 쓰려고 만드는 것인데,
   보기에 그럴듯한 그림이 나왔다고 해서 엔진 출력과 같다는 보장은 없다.
   그래서 만든 PNG 를 다시 읽어 CLI 가 낸 PPM 과 픽셀 단위로 대조한다.
   한 픽셀이라도 다르면 0 이 아닌 값으로 끝난다.

   실행:
       cd py && python3 -m isorpg_pygame.shots
"""
from __future__ import print_function

import os
import subprocess
import sys

# pygame import 보다 먼저. 이 두 줄의 위치가 곧 헤드리스 동작의 조건이다.
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

_HERE = os.path.dirname(os.path.abspath(__file__))
_PYROOT = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_PYROOT)
if _PYROOT not in sys.path:
    sys.path.insert(0, _PYROOT)

import pygame                                            # noqa: E402

from isorpg.game import Game                             # noqa: E402
from isorpg_pygame.main import SCR_H, SCR_W, Screen      # noqa: E402

OUT = os.path.join(_ROOT, 'out')
SHOTS = os.path.join(OUT, 'shots')

# `make frames` 가 PPM 을 뽑는 틱과 같은 목록. 같은 장면을 나란히 놓아야
# 덱에서 "PPM 과 PNG 가 같은 그림"이라는 주장을 그림으로 보일 수 있다.
TICKS = (1, 25, 45, 83, 97, 146, 194)

# 3배 확대본을 뽑을 틱. 기본 배율이 3배(960x600)라 창을 그대로 옮긴 셈이다.
SCALED_TICK = 97
SCALE = 3

PPM_HEAD = b'P6\n320 200\n255\n'


def render_at(screen, n):
    """골든 시나리오를 n 틱 돌린 뒤 한 프레임. main.py 의 render 명령과 같은 경로다.

       HUD 는 그리지 않는다. HUD 를 얹으면 더 이상 엔진 출력이 아니게 되어
       PPM 과의 픽셀 대조가 성립하지 않는다 — 스크린샷의 값어치는 그 대조에 있다.
    """
    g = Game()
    g.run_script(limit=n)
    fb = g.render()
    screen.set_phase(g.pal_phase)
    screen.upload(fb)
    return g


def to_rgb_bytes(surf):
    """표면을 RGB 바이트열로. pygame-ce 2.5 에서 tostring 이 tobytes 로 바뀌었다."""
    fn = getattr(pygame.image, 'tobytes', None) or pygame.image.tostring
    return fn(surf, 'RGB')


def read_ppm(path):
    """CLI 가 낸 P6 PPM 의 화소부만. 머리말은 SPEC §7.7 에 못 박혀 있어 그대로 비교한다."""
    data = open(path, 'rb').read()
    if not data.startswith(PPM_HEAD):
        raise ValueError('PPM 머리말이 다르다: %r' % data[:16])
    body = data[len(PPM_HEAD):]
    if len(body) != SCR_W * SCR_H * 3:
        raise ValueError('PPM 화소부가 %d바이트' % len(body))
    return body


def ensure_ppm(n):
    """out/frame_<n>.ppm 이 없으면 CLI 로 만든다.

       프런트엔드 안에서 다시 계산하지 않고 굳이 별도 프로세스로 CLI 를 부르는 이유는
       하나다 — 비교 대상이 '엔진이 스스로 내놓은 파일'이어야 증거가 된다.
       같은 프로세스에서 만든 두 값을 견주면 아무것도 증명하지 못한다.
    """
    path = os.path.join(OUT, 'frame_%d.ppm' % n)
    if os.path.exists(path):
        return path
    subprocess.check_call([sys.executable, '-m', 'isorpg.main', 'render', path,
                           str(n)], cwd=_PYROOT)
    return path


def expand_rows(body, scale):
    """PPM 화소부를 최근접 이웃으로 정수배 확대. 확대본 검사의 기대값이다."""
    out = []
    row_len = SCR_W * 3
    for y in range(SCR_H):
        row = body[y * row_len:(y + 1) * row_len]
        wide = bytearray()
        for x in range(SCR_W):
            wide += row[x * 3:x * 3 + 3] * scale
        wide = bytes(wide)
        for _ in range(scale):
            out.append(wide)
    return b''.join(out)


def first_diff(a, b):
    """다른 첫 바이트의 위치. 없으면 -1. 어디가 어긋났는지 말할 수 있어야 보고가 된다."""
    if a == b:
        return -1
    n = len(a) if len(a) < len(b) else len(b)
    for i in range(n):
        if a[i] != b[i]:
            return i
    return n


def main():
    if not os.path.isdir(SHOTS):
        os.makedirs(SHOTS)
    pygame.display.init()
    screen = Screen()
    made = []
    for n in TICKS:
        render_at(screen, n)
        path = os.path.join(SHOTS, 'pygame_%d.png' % n)
        pygame.image.save(screen.surf, path)
        made.append((n, path))
        print('찍음  %s' % os.path.relpath(path, _ROOT))

    render_at(screen, SCALED_TICK)
    scaled = pygame.transform.scale(screen.surf, (SCR_W * SCALE, SCR_H * SCALE))
    scaled_path = os.path.join(SHOTS, 'pygame_scaled.png')
    pygame.image.save(scaled, scaled_path)
    print('찍음  %s  (%d틱, %d배 = %dx%d)'
          % (os.path.relpath(scaled_path, _ROOT), SCALED_TICK, SCALE,
             SCR_W * SCALE, SCR_H * SCALE))

    print('')
    print('== 검사: PNG 와 CLI 가 낸 PPM 을 픽셀 단위로 ==')
    bad = 0
    for n, path in made:
        body = read_ppm(ensure_ppm(n))
        got = to_rgb_bytes(pygame.image.load(path))
        d = first_diff(got, body)
        if d < 0:
            print('  tick %-4d  %6d픽셀 전부 일치' % (n, SCR_W * SCR_H))
        else:
            bad += 1
            print('  tick %-4d  ★ 어긋남 — 첫 차이 바이트 %d (픽셀 %d)'
                  % (n, d, d // 3))
    body = read_ppm(ensure_ppm(SCALED_TICK))
    got = to_rgb_bytes(pygame.image.load(scaled_path))
    want = expand_rows(body, SCALE)
    d = first_diff(got, want)
    if d < 0:
        print('  scaled     %6d픽셀 전부 일치 (최근접 %d배 확대와 대조)'
              % (SCR_W * SCALE * SCR_H * SCALE, SCALE))
    else:
        bad += 1
        print('  scaled     ★ 어긋남 — 첫 차이 바이트 %d' % d)
    print('')
    print('결과: 이미지 %d장 중 어긋남 %d장' % (len(made) + 1, bad))
    pygame.quit()
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
