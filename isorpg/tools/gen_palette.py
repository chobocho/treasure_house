# -*- coding: utf-8 -*-
"""golden/palette.txt 생성 — VGA 6비트 DAC 팔레트 256색.

   0번은 투명(검정), 1..15는 VGA 기본 16색, 16..255는 램프 15개 x 16단계.
   램프를 16단계로 나눈 이유: 명암표(LIGHT)가 같은 램프 안에서 움직이면
   최근접 탐색이 자연스럽게 어두운 쪽으로 내려가 도스 시절 그림자와 같아진다.
"""
import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# VGA 기본 16색 (6비트 DAC 값). 0번은 투명색으로도 쓴다.
EGA = [(0, 0, 0), (0, 0, 42), (0, 42, 0), (0, 42, 42),
       (42, 0, 0), (42, 0, 42), (42, 21, 0), (42, 42, 42),
       (21, 21, 21), (21, 21, 63), (21, 63, 21), (21, 63, 63),
       (63, 21, 21), (63, 21, 63), (63, 63, 21), (63, 63, 63)]

# 램프 15개 — (이름, 어두운 끝, 밝은 끝). 인덱스는 16 + k*16 .. 16 + k*16 + 15
RAMPS = [
    ('water',  (0, 2, 14),   (18, 40, 63)),
    ('sand',   (22, 16, 6),  (63, 58, 34)),
    ('grass',  (4, 14, 4),   (34, 60, 28)),
    ('dirt',   (14, 9, 4),   (48, 36, 22)),
    ('rock',   (10, 10, 12), (52, 52, 56)),
    ('forest', (2, 9, 3),    (20, 44, 18)),
    ('road',   (21, 14, 6),  (58, 45, 25)),   # 흙길 — 돌바닥과 색이 갈려야 하고, 다른 램프와 겹쳐도 안 된다
    ('floor',  (10, 10, 13), (44, 44, 52)),   # 돌바닥 — 살짝 푸른 회색
    ('wall',   (15, 13, 11), (52, 48, 42)),
    ('wood',   (12, 7, 2),   (44, 28, 12)),
    ('snow',   (24, 26, 32), (60, 62, 63)),   # 순백(63,63,63)은 EGA 15번과 겹친다
    ('swamp',  (6, 10, 6),   (26, 38, 24)),
    ('lava',   (20, 2, 0),   (63, 44, 8)),
    ('skin',   (18, 10, 6),  (63, 46, 36)),
    ('cloth',  (10, 2, 6),   (58, 20, 28)),
]

RAMP_LO = 16
RAMP_LEN = 16
WATER_LO = RAMP_LO                     # 물 램프 = 팔레트 사이클링 구간
WATER_HI = RAMP_LO + RAMP_LEN - 1


def build():
    pal = list(EGA)
    for _, dark, bright in RAMPS:
        for i in range(RAMP_LEN):
            # 어두운 끝에서 밝은 끝까지 균등 보간. 반올림은 +7/15 (=+0.5단계)
            c = tuple((dark[k] * (RAMP_LEN - 1 - i) + bright[k] * i + 7)
                      // (RAMP_LEN - 1) for k in range(3))
            pal.append(c)
    assert len(pal) == 256, len(pal)
    for r, g, b in pal:
        assert 0 <= r <= 63 and 0 <= g <= 63 and 0 <= b <= 63
    # 중복 색이 하나라도 있으면 명암표의 항등 성질이 깨진다.
    # LIGHT[15][c] 가 c 가 아니라 더 작은 인덱스를 가리키게 되고,
    # 그 색은 최대 밝기에서도 조용히 다른 색으로 그려진다. 여기서 막는다.
    if len(set(pal)) != 256:
        dup = {}
        for i, c in enumerate(pal):
            dup.setdefault(c, []).append(i)
        bad = [(c, v) for c, v in dup.items() if len(v) > 1]
        raise ValueError('팔레트에 중복 색 %d건: %r' % (len(bad), bad[:5]))
    return pal


def main():
    pal = build()
    out = ['ISORPG-PAL 1 256']
    for i, (r, g, b) in enumerate(pal):
        out.append('%d %d %d %d' % (i, r, g, b))
    text = '\n'.join(out) + '\n'
    io.open(os.path.join(BASE, 'golden', 'palette.txt'), 'w',
            encoding='utf-8').write(text)
    print('golden/palette.txt  256색  램프 %d개  물 사이클 구간 %d..%d'
          % (len(RAMPS), WATER_LO, WATER_HI))


if __name__ == '__main__':
    main()
