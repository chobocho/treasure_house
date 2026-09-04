# -*- coding: utf-8 -*-
"""스프라이트 코퍼스 생성 — golden/tiles.rle.

   도스 게임의 타일은 그림 파일에서 잘라 왔지만, 이 교재는 외부 리소스를
   쓸 수 없으므로 절차적으로 만든다. 대신 '한 번 만들어 파일로 굳히고, 세
   언어가 모두 그 파일을 읽는다'는 원본의 구조는 그대로다 — 렌더링 결과가
   바이트 단위로 같은지 검사하려면 타일이 생성 코드가 아니라 데이터여야 한다.

   타일 모양은 SPEC §4.2 의 반열린 점-포함 판정을 그대로 쓴다. 그래야 타일을
   붙였을 때 틈도 겹침도 생기지 않는다.
"""
import io, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = H = 32
CENTER = (16, 16)

# 방향별 변 중점 — 도로 연결 스프라이트가 여기로 뻗는다 (SPEC §1.5 순서)
EDGE_MID = ((31, 16), (24, 4), (8, 4), (0, 16), (8, 28), (24, 28))


def inside(px, py):
    if py < 0 or py >= 32:
        return False
    if py < 8:
        return 16 - 2 * py <= px < 16 + 2 * py
    if py < 24:
        return 0 <= px < 32
    return 2 * (py - 24) <= px < 32 - 2 * (py - 24)


def blank():
    return bytearray(W * H)


def put(buf, x, y, v):
    if 0 <= x < W and 0 <= y < H:
        buf[y * W + x] = v


def fill_hex(buf, fn):
    for y in range(H):
        for x in range(W):
            if inside(x, y):
                buf[y * W + x] = fn(x, y)


def outline(buf, v):
    """육각형 테두리 — 안쪽인데 이웃 한 칸이 바깥이면 테두리다."""
    for y in range(H):
        for x in range(W):
            if not inside(x, y):
                continue
            if not (inside(x - 1, y) and inside(x + 1, y) and
                    inside(x, y - 1) and inside(x, y + 1)):
                buf[y * W + x] = v


def line(buf, x0, y0, x1, y1, v, thick=1):
    """정수 브레젠험. 도로 연결선에 쓴다."""
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        for oy in range(-(thick // 2), thick // 2 + 1):
            for ox in range(-(thick // 2), thick // 2 + 1):
                if inside(x0 + ox, y0 + oy):
                    put(buf, x0 + ox, y0 + oy, v)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def dither(base, span, x, y):
    """좌표 해시로 램프 안에서 흔든다. 난수를 쓰지 않으므로 재생성해도 같다.

       가로로 4픽셀씩 같은 값이 나오게 만든 것은 미관이 아니라 압축 때문이다.
       픽셀마다 색을 흔들면 RLE 가 전혀 줄지 않는다 — 도스 시절 타일 아트가
       점묘가 아니라 넓은 색면으로 그려진 데에는 이런 실무적 이유가 있었다."""
    return base + (((x >> 2) + (y >> 1) * 3) % span)


def terrain_tiles():
    out = []

    # 0 평지
    b = blank()
    fill_hex(b, lambda x, y: dither(18, 8, x, y))
    outline(b, 16)
    out.append(('t_clear', b))

    # 1 숲 — 나무 세 그루
    b = blank()
    fill_hex(b, lambda x, y: dither(34, 6, x, y))
    for (cx, cy) in ((11, 12), (20, 10), (15, 21)):
        for dy in range(-4, 5):
            wdt = 4 - abs(dy) // 2
            for dx in range(-wdt, wdt + 1):
                put(b, cx + dx, cy + dy, 44 if dy < 2 else 36)
    outline(b, 32)
    out.append(('t_forest', b))

    # 2 언덕 — 등고선 두 줄
    b = blank()
    fill_hex(b, lambda x, y: dither(50, 8, x, y))
    for (cy, half) in ((14, 9), (19, 6)):
        for dx in range(-half, half + 1):
            put(b, 16 + dx, cy + abs(dx) // 3, 60)
    outline(b, 48)
    out.append(('t_hill', b))

    # 3 산 — 삼각 봉우리와 만년설
    b = blank()
    fill_hex(b, lambda x, y: dither(66, 6, x, y))
    for dy in range(0, 16):
        half = dy
        for dx in range(-half, half + 1):
            put(b, 16 + dx, 8 + dy, 76 if dy < 4 else 70)
    outline(b, 64)
    out.append(('t_mountain', b))

    # 4 도시 — 건물 세 채
    b = blank()
    fill_hex(b, lambda x, y: dither(114, 6, x, y))
    for (bx, by, bw, bh) in ((8, 14, 5, 8), (15, 11, 6, 11), (22, 16, 4, 6)):
        for y in range(by, by + bh):
            for x in range(bx, bx + bw):
                put(b, x, y, 124 if (x - bx) % 2 == 0 and (y - by) % 2 == 0 else 118)
    outline(b, 112)
    out.append(('t_city', b))

    # 5 강 — 물결
    b = blank()
    fill_hex(b, lambda x, y: dither(82, 8, x, y))
    for y in range(6, 28, 5):
        for x in range(2, 30):
            put(b, x, y + (x % 4) // 2, 92)
    outline(b, 80)
    out.append(('t_river', b))

    # 6 늪 — 어두운 웅덩이
    b = blank()
    fill_hex(b, lambda x, y: dither(98, 6, x, y))
    for (cx, cy, rr) in ((12, 13, 3), (20, 18, 4), (14, 22, 2)):
        for dy in range(-rr, rr + 1):
            for dx in range(-rr, rr + 1):
                if dx * dx + dy * dy <= rr * rr:
                    put(b, cx + dx, cy + dy, 84)
    outline(b, 96)
    out.append(('t_swamp', b))

    # 7 바다 — 수평 파도
    b = blank()
    fill_hex(b, lambda x, y: dither(80, 6, x, y))
    for y in range(4, 30, 4):
        for x in range(3, 29):
            if (x + y) % 6 < 3:
                put(b, x, y, 90)
    outline(b, 80)
    out.append(('t_sea', b))
    return out


def road_tiles():
    out = []
    for d, (ex, ey) in enumerate(EDGE_MID):
        b = blank()
        line(b, CENTER[0], CENTER[1], ex, ey, 138, thick=3)
        line(b, CENTER[0], CENTER[1], ex, ey, 133, thick=1)
        out.append(('road%d' % d, b))
    return out


def overlay_tiles():
    out = []
    # 이동 가능 표시 — 성긴 격자 점만 찍는다. 반투명이 없던 시절의 관용구다.
    b = blank()
    for y in range(H):
        for x in range(W):
            if inside(x, y) and (x + y) % 4 == 0:
                b[y * W + x] = 186
    out.append(('ov_move', b))

    b = blank()
    for y in range(H):
        for x in range(W):
            if inside(x, y) and (x + y) % 3 == 0:
                b[y * W + x] = 156
    out.append(('ov_attack', b))

    b = blank()
    outline(b, 190)
    out.append(('ov_cursor', b))

    b = blank()
    outline(b, 175)
    out.append(('ov_sel', b))

    # 안개: 탐색됨은 절반 점찍기, 미탐색은 꽉 채운 검정
    b = blank()
    for y in range(H):
        for x in range(W):
            if inside(x, y) and (x + y) % 2 == 0:
                b[y * W + x] = 192
    out.append(('ov_dim', b))

    b = blank()
    fill_hex(b, lambda x, y: 192)
    out.append(('ov_black', b))

    # 목표 헥스 깃발 — 워게임에서 '여기를 뺏으면 이긴다' 는 표시
    b = blank()
    for y in range(6, 24):
        put(b, 15, y, 15)
        put(b, 16, y, 8)
    for y in range(6, 14):
        for x in range(17, 17 + (14 - y) // 2 + 4):
            put(b, x, y, 188 if (x + y) % 2 else 190)
    out.append(('ov_obj', b))
    return out


def unit_icons():
    """16x16 유닛 아이콘 — 진영 색 상자에 병종 기호."""
    out = []
    shapes = {
        0: [(6, 3, 4, 10)],                                   # 보병: 세로 막대
        1: [(3, 6, 10, 5), (5, 4, 6, 2)],                     # 전차: 차체+포탑
        2: [(4, 9, 8, 3), (7, 3, 3, 6)],                      # 포병: 포신
        3: [(3, 7, 10, 3), (11, 4, 2, 3)],                    # 정찰: 낮고 긴 차체
    }
    for side in (0, 1):
        base = 160 if side == 0 else 144
        for kind in range(4):
            b = bytearray(16 * 16)
            for y in range(16):
                for x in range(16):
                    if 1 <= x < 15 and 1 <= y < 15:
                        b[y * 16 + x] = base + 3 + ((x + y) % 2)
            for x in range(1, 15):
                b[1 * 16 + x] = base + 12
                b[14 * 16 + x] = base + 1
            for y in range(1, 15):
                b[y * 16 + 1] = base + 12
                b[y * 16 + 14] = base + 1
            for (rx, ry, rw, rh) in shapes[kind]:
                for y in range(ry, ry + rh):
                    for x in range(rx, rx + rw):
                        if 0 <= x < 16 and 0 <= y < 16:
                            b[y * 16 + x] = 15 if side == 0 else 14
            out.append(('u%d_%d' % (side, kind), b, 16, 16))
    return out


def rle_encode(data):
    out = []
    i = 0
    n = len(data)
    while i < n:
        v = data[i]
        c = 1
        while i + c < n and data[i + c] == v and c < 255:
            c += 1
        out.append((c, v))
        i += c
    return out


def main():
    sprites = [(n, b, W, H) for n, b in terrain_tiles() + road_tiles() + overlay_tiles()]
    sprites += unit_icons()

    lines = [';; HexWar 스프라이트 코퍼스 — tools/gen_tiles.py 가 만든다',
             ';; 형식: "이름 w h" 다음 줄부터 "개수 값" 쌍, 합이 w*h 가 되면 다음 블록']
    total = 0
    for name, buf, w, h in sprites:
        pairs = rle_encode(buf)
        total += len(pairs)
        lines.append('%s %d %d' % (name, w, h))
        row = []
        for c, v in pairs:
            row.append('%d %d' % (c, v))
            if len(row) == 12:
                lines.append(' '.join(row))
                row = []
        if row:
            lines.append(' '.join(row))
    p = os.path.join(BASE, 'golden', 'tiles.rle')
    io.open(p, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    raw = sum(w * h for _n, _b, w, h in sprites)
    print('스프라이트 %d개 · 원본 %d바이트 · RLE 쌍 %d개(%d바이트) · %.1f%%'
          % (len(sprites), raw, total, total * 2, total * 2 * 100.0 / raw))
    print('wrote %s' % p)


if __name__ == '__main__':
    main()
