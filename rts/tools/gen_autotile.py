# -*- coding: utf-8 -*-
"""오토타일 정규화 표를 만든다 — golden/autotile.txt

   SPEC §4.4/§4.5. 256가지 8이웃 마스크가 47가지 그림으로 줄고, 그 47가지가
   정사각형 대칭군 D4 아래에서 14개 궤도로 다시 줄어든다는 것을 표로 낸다.
   엔진은 이 표를 읽는 것이 아니라 같은 규칙으로 다시 만들고, 결과를 대조한다.

   실행:  python3 tools/gen_autotile.py
"""
import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(BASE, 'golden')

# SPEC §2.7 의 방향 번호를 그대로 비트 번호로 쓴다.
N, NE, E, SE, S, SW, W, NW = [1 << i for i in range(8)]
NAME = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
CORNERS = ((NE, N, E), (SE, S, E), (SW, S, W), (NW, N, W))


def canon(m):
    """모서리 비트는 양옆 변이 둘 다 있을 때만 살린다 (SPEC 정리 4.1)."""
    r = m
    for c, a, b in CORNERS:
        if not (m & a and m & b):
            r &= ~c
    return r


def rot90(m):
    """90도 회전: 방향 번호 d -> d+2."""
    r = 0
    for i in range(8):
        if m >> i & 1:
            r |= 1 << ((i + 2) % 8)
    return r


def mirror(m):
    """좌우 반사: N 은 그대로, d -> (8-d) mod 8."""
    r = 0
    for i in range(8):
        if m >> i & 1:
            r |= 1 << ((8 - i) % 8)
    return r


def show(m):
    """3×3 글자 그림 — 가운데는 자기 자신."""
    at = {0: (1, 0), 1: (2, 0), 2: (2, 1), 3: (2, 2),
          4: (1, 2), 5: (0, 2), 6: (0, 1), 7: (0, 0)}
    g = [['.'] * 3 for _ in range(3)]
    g[1][1] = 'O'
    for d in range(8):
        if m >> d & 1:
            x, y = at[d]
            g[y][x] = '#'
    return ['' .join(row) for row in g]


def main():
    classes = sorted(set(canon(m) for m in range(256)))
    index = dict((m, i) for i, m in enumerate(classes))

    # D4 궤도
    seen, orbits = set(), []
    for m in classes:
        if m in seen:
            continue
        orb, cur = set(), m
        for _ in range(4):
            orb.add(canon(cur))
            orb.add(canon(mirror(cur)))
            cur = rot90(cur)
        seen |= orb
        orbits.append(sorted(orb))

    out = []
    out.append('== 1. 정규화 (256 -> %d) ==' % len(classes))
    out.append('mask canon idx  bits')
    for m in range(256):
        c = canon(m)
        bits = ''.join(NAME[d] + ',' for d in range(8) if m >> d & 1).rstrip(',')
        out.append('%3d %5d %3d  %s' % (m, c, index[c], bits or '-'))

    out.append('')
    out.append('== 2. 클래스 %d개 ==' % len(classes))
    out.append('idx mask cnt  그림')
    for i, m in enumerate(classes):
        cnt = sum(1 for k in range(256) if canon(k) == m)
        pic = show(m)
        out.append('%3d %4d %3d  %s' % (i, m, cnt, pic[0]))
        out.append('%16s%s' % ('', pic[1]))
        out.append('%16s%s' % ('', pic[2]))

    out.append('')
    out.append('== 3. D4 궤도 %d개 ==' % len(orbits))
    out.append('궤도 크기 대표  같은 궤도의 마스크')
    for i, orb in enumerate(orbits):
        out.append('%3d %4d %4d  %s' % (i, len(orb), orb[0],
                                        ' '.join(str(x) for x in orb)))
    out.append('')
    out.append('궤도 크기 합계 %d (클래스 수와 같아야 한다)'
               % sum(len(o) for o in orbits))

    out.append('')
    out.append('== 4. 4모서리 16케이스 (마칭 스퀘어) ==')
    out.append('mask  꼭짓점(좌상,우상,우하,좌하)')
    for m in range(16):
        v = ''.join('1' if m >> k & 1 else '0' for k in range(4))
        out.append('%4d  %s' % (m, v))

    p = os.path.join(GOLDEN, 'autotile.txt')
    io.open(p, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('autotile.txt  클래스 %d개 · D4 궤도 %d개 · %d줄'
          % (len(classes), len(orbits), len(out)))


if __name__ == '__main__':
    main()
