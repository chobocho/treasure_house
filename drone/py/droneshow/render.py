# -*- coding: utf-8 -*-
"""render — 쇼의 한 프레임을 그림으로: SVG 스냅숏과 PNG (SPEC §9.5).

덱의 SHOW 지시자가 snapshot_svg() 를 조립 때 부른다. 그래서 편대
그림은 언제나 시뮬레이터가 그린 것이다. 글자 모양은 고정 소수점
(%.2f)으로 적어 두 번 그려도 바이트가 같다.
"""
import math
import struct
import zlib

from . import show as SH
from . import vec3 as V

W = 340
GAMMA = 2.2


def decode(v):
    """8비트 부호 값 → 빛의 양 [0,1] (T34)."""
    return (v / 255.0) ** GAMMA


def encode(light):
    return SH.rnd(255.0 * max(0.0, min(1.0, light)) ** (1.0 / GAMMA))


def mix_codes(a, b, u, linear):
    """두 색을 u 만큼 섞는다. linear 면 빛의 양으로 섞는다."""
    if not linear:
        return [SH.rnd(a[k] + u * (b[k] - a[k])) for k in range(3)]
    return [encode(decode(a[k]) + u * (decode(b[k]) - decode(a[k])))
            for k in range(3)]


def apparent_size(w, d):
    """거리 d 에서 너비 w 가 보이는 각 2·atan(w/2d) ≈ w/d (T33)."""
    return 2 * math.atan(w / (2 * d))


def camera(centre, dist, height):
    """관객 자리 (중심 x, 중심 y − dist, height) 에서 중심을 본다."""
    pos = [centre[0], centre[1] - dist, height]
    f = V.normalize(V.sub(centre, pos))
    r = V.normalize(V.cross(f, [0.0, 0.0, 1.0]))
    u = V.cross(r, f)
    return {'pos': pos, 'f': f, 'r': r, 'u': u}


def project(cam, p):
    """핀홀 투영 — 화면 좌표는 (가로 tan, 세로 tan)."""
    q = V.sub(p, cam['pos'])
    z = V.dot(q, cam['f'])
    return V.dot(q, cam['r']) / z, V.dot(q, cam['u']) / z


def _proj(show, view):
    """view 이름 → 점을 평면 좌표로 보내는 함수."""
    if view == 'top':
        return lambda p: (p[0], p[1])
    if view == 'audience':
        pts = [k[1:4] for d in show['drones'] for k in d['keyframes']]
        c = [sum(q[i] for q in pts) / len(pts) for i in range(3)]
        cam = camera(c, 150.0, 1.7)
        return lambda p: project(cam, p)
    return lambda p: (p[0], p[2])


def _frame_box(show, view):
    """쇼 전체의 키프레임을 담는 상자 — 프레임마다 배율이 같게."""
    pr = _proj(show, view)
    xy = [pr(k[1:4]) for d in show['drones'] for k in d['keyframes']]
    x0, x1 = min(a for a, _ in xy), max(a for a, _ in xy)
    y0, y1 = min(b for _, b in xy), max(b for _, b in xy)
    return pr, x0, x1, y0, y1


def _layout(show, view, width):
    pr, x0, x1, y0, y1 = _frame_box(show, view)
    m = 12.0
    sx = (width - 2 * m) / max(x1 - x0, 1e-9)
    h = max(120.0, min(300.0, (y1 - y0) * sx + 2 * m))
    s = min(sx, (h - 2 * m) / max(y1 - y0, 1e-9))
    ox = (width - (x1 - x0) * s) / 2
    oy = (h - (y1 - y0) * s) / 2

    def to_screen(p):
        a, b = pr(p)
        return ox + (a - x0) * s, h - (oy + (b - y0) * s)
    return to_screen, h


def snapshot_svg(show, frame, view):
    """f 번째 프레임을 viewBox 340 폭의 SVG 로. 켜진 드론은 원 둘."""
    to_screen, h = _layout(show, view, W)
    hh = SH.rnd(h)
    out = ['<svg class="show" viewBox="0 0 %d %d" role="img">'
           % (W, hh),
           '<rect width="%d" height="%d" fill="#05081a"/>' % (W, hh)]
    for pos, c in SH.frame(show, frame):
        x, y = to_screen(pos)
        if c == [0, 0, 0]:
            out.append('<circle cx="%.2f" cy="%.2f" r="1.4" '
                       'fill="#26314f"/>' % (x, y))
            continue
        col = 'rgb(%d,%d,%d)' % tuple(c)
        out.append('<circle cx="%.2f" cy="%.2f" r="5" fill="%s" '
                   'opacity="0.28"/>' % (x, y, col))
        out.append('<circle cx="%.2f" cy="%.2f" r="1.8" fill="%s"/>'
                   % (x, y, col))
    out.append('</svg>')
    return ''.join(out)


def png(show, frame, w, h, view):
    """PNG 바이트 (RGB, zlib 9단계). 드론은 3×3 가산 점."""
    to_screen, hh = _layout(show, view, w)
    buf = [[[0.0, 0.0, 0.0] for _ in range(w)] for _ in range(h)]
    ker = {(0, 0): 1.0, (1, 0): .35, (-1, 0): .35, (0, 1): .35,
           (0, -1): .35, (1, 1): .15, (1, -1): .15, (-1, 1): .15,
           (-1, -1): .15}
    for pos, c in SH.frame(show, frame):
        x, y = to_screen(pos)
        cx, cy = int(x), int(y * h / hh)
        for (dx, dy), k in sorted(ker.items()):
            if 0 <= cx + dx < w and 0 <= cy + dy < h:
                px = buf[cy + dy][cx + dx]
                for i in range(3):
                    px[i] += k * c[i]
    raw = b''.join(b'\x00' + bytes(min(255, SH.rnd(v)) for px in row
                                   for v in px) for row in buf)

    def chunk(kind, data):
        return (struct.pack('>I', len(data)) + kind + data
                + struct.pack('>I',
                              zlib.crc32(kind + data) & 0xffffffff))
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR',
                    struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9))
            + chunk(b'IEND', b''))
