# -*- coding: utf-8 -*-
"""지형 맵 — 한 칸 두 바이트, 오토타일, 연결 성분, RLE (SPEC §4).

   맵은 두 평면으로 나뉜다. 한 배열에 비트로 우겨 넣지 않는다.
     terrain[i]  지형 종류
     pass[i]     통행 비트 — 지형에서 파생되지만 건물이 서면 달라지므로 별도 상태다

   비트마스크는 전부 산술로 다룬다(SPEC §1.1). 루아 5.1 에 비트 연산자가 없고,
   타입스크립트의 & 는 32비트로 잘린다. 오토타일 마스크는 8비트뿐이라
   잘릴 일이 없어 보이지만, 규칙을 한 군데서만 어기면 반드시 다른 곳에서 샌다.
"""

from . import fixed as F

# ── SPEC §4.1 지형표 ────────────────────────────────────────────────────────
SAND, ROCK, WATER, DIRT, ORE, HILL, RUBBLE, ROAD = range(8)
TERRAIN_CH = '.#~,*^;='
TERRAIN_NAME = ['모래', '바위', '물', '흙', '광맥', '언덕', '잔해', '도로']
MINI_COLOR = [216, 220, 232, 214, 240, 218, 222, 226]

# 보병 통행 · 차량 통행 · 건설 가능
FOOT_OK = [1, 0, 0, 1, 1, 1, 1, 1]
VEHICLE_OK = [1, 0, 0, 1, 1, 0, 1, 1]      # 차량은 언덕에 올라가지 못한다
BUILD_OK = [1, 0, 0, 1, 0, 0, 1, 1]

FOOT_BIT, VEH_BIT, BUILD_BIT, OCC_BIT = 0, 1, 2, 3

# ── SPEC §4.4 오토타일 ──────────────────────────────────────────────────────
# (모서리 방향, 양옆 변 방향 둘). 방향 번호는 fixed.DX/DY 와 같다.
_CORNERS = ((1, 0, 2), (3, 4, 2), (5, 4, 6), (7, 0, 6))


def canon(m):
    """모서리 비트는 양옆 변이 둘 다 있을 때만 살린다 (SPEC 정리 4.1)."""
    r = m
    for c, a, b in _CORNERS:
        if not (F.bit(m, a) and F.bit(m, b)):
            r = F.clrbit(r, c)
    return r


_CLASSES = sorted(set(canon(m) for m in range(256)))
_CLASS_INDEX = dict((m, i) for i, m in enumerate(_CLASSES))
CLASS_COUNT = len(_CLASSES)


def canon_index(cm):
    """정규화된 마스크 → 0..46 그림 번호."""
    return _CLASS_INDEX[cm]


def corner_mask(v):
    """4모서리(마칭 스퀘어) 16케이스. v = [좌상, 우상, 우하, 좌하] 의 0/1."""
    return v[0] + 2 * v[1] + 4 * v[2] + 8 * v[3]


class TMap(object):
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.terrain = [SAND] * (w * h)
        self.pass_ = [0] * (w * h)
        self.version = 0
        self.starts = []
        self.pairs = []
        self._labels = {}
        for i in range(w * h):
            self._repass(i)

    # ── SPEC §4.2 좌표 ─────────────────────────────────────────────────────
    def idx(self, x, y):
        return y * self.w + x

    def in_map(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def terrain_at(self, x, y):
        """맵 밖은 ROCK 이다 — 호출자가 경계 검사를 하지 않아도 되고,
           오토타일 마스크가 가장자리에서 자연스럽게 닫힌다."""
        if not self.in_map(x, y):
            return ROCK
        return self.terrain[y * self.w + x]

    # ── SPEC §4.3 통행 비트 ────────────────────────────────────────────────
    def _repass(self, i):
        t = self.terrain[i]
        occ = F.bit(self.pass_[i], OCC_BIT)
        self.pass_[i] = (FOOT_OK[t] + 2 * VEHICLE_OK[t] + 4 * BUILD_OK[t]
                         + 8 * occ)

    def set_terrain(self, x, y, t):
        i = y * self.w + x
        if self.terrain[i] == t:
            return
        self.terrain[i] = t
        self._repass(i)
        self._bump()

    def occupy(self, x, y, on):
        i = y * self.w + x
        self.pass_[i] = (F.setbit(self.pass_[i], OCC_BIT) if on
                         else F.clrbit(self.pass_[i], OCC_BIT))

    def walkable(self, x, y, kind):
        if not self.in_map(x, y):
            return False
        p = self.pass_[y * self.w + x]
        return F.bit(p, kind) == 1 and F.bit(p, OCC_BIT) == 0

    def passable_terrain(self, x, y, kind):
        """점유를 보지 않는 통행 판정 — 경로 탐색은 이것을 쓴다(SPEC §4.3)."""
        if not self.in_map(x, y):
            return False
        return F.bit(self.pass_[y * self.w + x], kind) == 1

    def buildable(self, x, y):
        if not self.in_map(x, y):
            return False
        p = self.pass_[y * self.w + x]
        return F.bit(p, BUILD_BIT) == 1 and F.bit(p, OCC_BIT) == 0

    def _bump(self):
        self.version += 1
        self._labels = {}

    # ── SPEC §4.4 이웃 마스크 ──────────────────────────────────────────────
    def mask(self, x, y):
        """이웃 8칸 중 나와 같은 지형인 방향의 비트합."""
        t = self.terrain_at(x, y)
        m = 0
        for d in range(8):
            if self.terrain_at(x + F.DX[d], y + F.DY[d]) == t:
                m = F.setbit(m, d)
        return m

    def tile_index(self, x, y):
        return canon_index(canon(self.mask(x, y)))

    # ── SPEC §4.6 연결 성분 (유니온–파인드) ────────────────────────────────
    def labels(self, kind):
        """통행 가능 칸을 8방향으로 묶은 대표 원소 배열. 막힌 칸은 -1.

           지형이 바뀌면 통째로 다시 계산한다. 증분 삭제가 되는 유니온–파인드는
           복잡하고, 4096칸 재계산은 측정상 1 ms 미만이다.
        """
        if kind in self._labels:
            return self._labels[kind]
        n = self.w * self.h
        parent = list(range(n))

        def find(a):
            root = a
            while parent[root] != root:
                root = parent[root]
            while parent[a] != root:               # 경로 압축
                parent[a], a = root, parent[a]
            return root

        for y in range(self.h):
            for x in range(self.w):
                if not self.passable_terrain(x, y, kind):
                    continue
                a = find(y * self.w + x)
                for d in range(8):
                    u, v = x + F.DX[d], y + F.DY[d]
                    if self.passable_terrain(u, v, kind):
                        b = find(v * self.w + u)
                        if a != b:
                            parent[b] = a
                            a = find(a)
        out = [-1] * n
        for y in range(self.h):
            for x in range(self.w):
                if self.passable_terrain(x, y, kind):
                    out[y * self.w + x] = find(y * self.w + x)
        self._labels[kind] = out
        return out

    # ── SPEC §4.7 RLE ──────────────────────────────────────────────────────
    def save_rle(self):
        body = bytearray()
        body += b'RTSM'
        body.append(1)
        body.append(self.w)
        body.append(self.h)
        for plane in (self.terrain, self.pass_):
            run, val = 0, -1
            for v in plane:
                if v == val and run < 255:
                    run += 1
                else:
                    if run:
                        body.append(run)
                        body.append(val)
                    run, val = 1, v
            if run:
                body.append(run)
                body.append(val)
        c = F.crc16(bytes(body))
        body.append(c // 256)
        body.append(c % 256)
        return bytes(body)

    @staticmethod
    def load_rle(blob):
        b = bytearray(blob)
        if bytes(b[:4]) != b'RTSM':
            raise ValueError('맵 파일이 아니다')
        want = b[-2] * 256 + b[-1]
        if F.crc16(bytes(b[:-2])) != want:
            raise ValueError('CRC 불일치 — 맵이 깨졌다')
        w, h = b[5], b[6]
        m = TMap(w, h)
        pos = 7
        for plane in (m.terrain, m.pass_):
            i = 0
            while i < w * h:
                run, val = b[pos], b[pos + 1]
                pos += 2
                for _ in range(run):
                    plane[i] = val
                    i += 1
        m._bump()
        return m

    # ── 골든 맵 텍스트 (시험용) ────────────────────────────────────────────
    @staticmethod
    def load_text(text):
        """golden/map_*.txt 를 읽는다. '.'/'#' 격자와 지형 문자 격자 둘 다."""
        lines = text.split('\n')
        w = h = 0
        m = None
        i = 0
        while i < len(lines):
            ln = lines[i]
            if ln.startswith('size '):
                w, h = (int(v) for v in ln[5:].split())
            elif ln in ('map', 'terrain'):
                m = TMap(w, h)
                for y in range(h):
                    row = lines[i + 1 + y]
                    for x in range(w):
                        ch = row[x]
                        if ln == 'map':
                            m.terrain[y * w + x] = ROCK if ch == '#' else DIRT
                        else:
                            m.terrain[y * w + x] = TERRAIN_CH.index(ch)
                        m._repass(y * w + x)
                i += h
            elif ln.startswith('pairs '):
                n = int(ln[6:])
                for k in range(n):
                    a, b, c, d = (int(v) for v in lines[i + 1 + k].split())
                    m.pairs.append(((a, b), (c, d)))
                i += n
            elif ln.startswith('start '):
                n = int(ln[6:])
                for k in range(n):
                    a, b = (int(v) for v in lines[i + 1 + k].split())
                    m.starts.append((a, b))
                i += n
            i += 1
        m._bump()
        return m
