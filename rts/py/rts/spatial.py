# -*- coding: utf-8 -*-
"""엔티티와 공간 분할 — SoA·세대 핸들·균일 격자 버킷 (SPEC §7).

   엔티티를 구조체의 배열이 아니라 배열의 구조체로 담는다. 성능도 이유지만
   더 큰 이유는 **직렬화 순서가 배열 순서로 자동으로 고정**된다는 것이다.
   상태 해시(SPEC §18.4)가 언어별 필드 순서에 영향을 받지 않는다.
"""

from . import fixed as F

MAX_ENT = 256
GEN_MOD = 256
BUCKET = 8


def index(h):
    return h // 256


def generation(h):
    return h % 256


class World(object):
    """엔티티 배열과 버킷. 시뮬레이션 규칙은 여기 없다 — 담는 그릇일 뿐이다."""

    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.bw = (w + BUCKET - 1) // BUCKET
        self.bh = (h + BUCKET - 1) // BUCKET
        n = MAX_ENT
        self.alive = [0] * n
        self.gen = [0] * n
        self.owner = [0] * n
        self.kind = [0] * n
        self.tx = [0] * n
        self.ty = [0] * n
        self.px = [0] * n
        self.py = [0] * n
        self.hp = [0] * n
        self.dir = [0] * n
        self.state = [0] * n
        self.target = [0] * n
        self.load = [0] * n
        self.prog = [0] * n
        self.from_t = [0] * n
        self.to_t = [0] * n
        self.cool = [0] * n
        self.timer = [0] * n
        self.buckets = [[] for _ in range(self.bw * self.bh)]

    # ── SPEC §7.2 핸들 ─────────────────────────────────────────────────────
    def handle(self, i):
        return i * 256 + self.gen[i]

    def valid(self, h):
        if h == 0:
            return False
        i = index(h)
        return (0 < i < MAX_ENT and self.alive[i] == 1
                and generation(h) == self.gen[i])

    def bucket_of(self, tx, ty):
        return (ty // BUCKET) * self.bw + (tx // BUCKET)

    # ── 생성·소멸 ──────────────────────────────────────────────────────────
    def spawn(self, owner, kind, tx, ty):
        """슬롯 0 은 절대 쓰지 않는다 — 핸들 0 이 "없음"을 뜻해야 하기 때문이다."""
        for i in range(1, MAX_ENT):
            if self.alive[i] == 0:
                self.alive[i] = 1
                self.owner[i] = owner
                self.kind[i] = kind
                self.tx[i] = tx
                self.ty[i] = ty
                self.px[i] = F.fp(tx * 16)
                self.py[i] = F.fp(ty * 16)
                self.dir[i] = 4
                self.state[i] = 0
                self.target[i] = 0
                self.load[i] = 0
                self.prog[i] = 0
                self.from_t[i] = ty * self.w + tx
                self.to_t[i] = ty * self.w + tx
                self.cool[i] = 0
                self.timer[i] = 0
                self._bucket_add(i)
                return self.handle(i)
        return 0                      # 상한 초과 — 조용히 실패한다

    def kill(self, h):
        if not self.valid(h):
            return False
        i = index(h)
        self._bucket_del(i)
        self.alive[i] = 0
        self.gen[i] = (self.gen[i] + 1) % GEN_MOD
        return True

    # ── SPEC §7.3 버킷 ─────────────────────────────────────────────────────
    def _bucket_add(self, i):
        b = self.buckets[self.bucket_of(self.tx[i], self.ty[i])]
        k = 0
        while k < len(b) and b[k] < i:      # 오름차순 유지 — 결정론을 위해서다
            k += 1
        b.insert(k, i)

    def _bucket_del(self, i):
        b = self.buckets[self.bucket_of(self.tx[i], self.ty[i])]
        if i in b:
            b.remove(i)

    def move_tile(self, i, tx, ty):
        """타일을 넘을 때만 부른다. 픽셀 이동마다 부르는 것이 아니다."""
        if self.bucket_of(self.tx[i], self.ty[i]) != self.bucket_of(tx, ty):
            self._bucket_del(i)
            self.tx[i] = tx
            self.ty[i] = ty
            self._bucket_add(i)
        else:
            self.tx[i] = tx
            self.ty[i] = ty

    def query(self, tx, ty, r):
        """반경 r(체비셰프) 안의 엔티티 인덱스. 오름차순으로 돌려준다."""
        out = []
        x0 = max(0, tx - r) // BUCKET
        x1 = min(self.w - 1, tx + r) // BUCKET
        y0 = max(0, ty - r) // BUCKET
        y1 = min(self.h - 1, ty + r) // BUCKET
        for by in range(y0, y1 + 1):
            for bx in range(x0, x1 + 1):
                for i in self.buckets[by * self.bw + bx]:
                    if (F.dinf(self.tx[i] - tx, self.ty[i] - ty) <= r):
                        out.append(i)
        out.sort()
        return out
