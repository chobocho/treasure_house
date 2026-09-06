# -*- coding: utf-8 -*-
"""시야와 안개 — 참조 카운트 세 평면 (SPEC §14).

   안개는 **그리기 단계에서만** 쓰인다. 시뮬레이션은 안개를 무시한다 —
   안개를 시뮬레이션의 일부로 만들면 플레이어마다 상태가 갈리고, 그러면
   락스텝의 전제가 무너진다(§14.5). 도스 RTS 의 맵 핵이 그토록 쉬웠던 이유가
   정확히 이것이고, 19부에서 그 이야기를 한다.

   칸당 1바이트를 쓴다. 비트 플레인이 8배 작지만 참조 카운트는 비트로 담을 수
   없고, 루아 5.1 에서 비트 연산을 산술로 흉내내면 칸 하나에 나눗셈이 붙는다.
   비트 플레인은 저장·전송용 `pack_bits` 로만 남겼다(§14.2).
"""

from . import circle as CI
from . import const as C


class Fog(object):
    """플레이어마다 explored·count 두 평면. visible 은 count > 0 의 별칭이다."""

    def __init__(self, w, h, players=C.MAX_PLAYER):
        self.w = w
        self.h = h
        self.count = [[0] * (w * h) for _ in range(players)]
        self.explored = [[0] * (w * h) for _ in range(players)]

    def visible(self, p, i):
        return self.count[p][i] > 0

    # ── SPEC §14.3 증분 갱신 ───────────────────────────────────────────────
    def add_sight(self, p, tx, ty, r):
        """O(r²) — 원 안의 칸마다 카운트 +1 과 탐험 표시."""
        cnt, exp = self.count[p], self.explored[p]
        for dx, dy in CI.offsets(r):
            x, y = tx + dx, ty + dy
            if 0 <= x < self.w and 0 <= y < self.h:
                i = y * self.w + x
                cnt[i] += 1
                exp[i] = 1

    def remove_sight(self, p, tx, ty, r):
        """카운트 −1. 0 아래로는 내려가지 않는다 — 내려간다면 그것은 버그다."""
        cnt = self.count[p]
        for dx, dy in CI.offsets(r):
            x, y = tx + dx, ty + dy
            if 0 <= x < self.w and 0 <= y < self.h:
                i = y * self.w + x
                if cnt[i] > 0:
                    cnt[i] -= 1

    def move_sight(self, p, ox, oy, nx, ny, r):
        """타일을 넘을 때 — **빼기가 먼저다**(§14.3)."""
        self.remove_sight(p, ox, oy, r)
        self.add_sight(p, nx, ny, r)

    def recount(self, world):
        """불변식 F 를 전수로 검증하고 **어긋난 칸 수만** 돌려준다.

           고치지 않는 이유는 하나다. 증분 갱신이 새면 그것은 버그이고,
           조용히 고쳐 버리면 그 버그는 영원히 드러나지 않는다.
           O(플레이어 × 칸수 + 엔티티 × r²) 이라 매 틱 돌릴 수는 없다 —
           세이브 직후와 100틱마다 돌린다.
        """
        want = [[0] * (self.w * self.h) for _ in range(len(self.count))]
        for i in range(1, C.MAX_ENT):
            if world.alive[i] == 0:
                continue
            r = C.SIGHT[world.kind[i]]
            p = world.owner[i]
            if p >= len(want):
                continue
            for dx, dy in CI.offsets(r):        # 건물의 시야 중심은 좌상단이다
                x, y = world.tx[i] + dx, world.ty[i] + dy
                if 0 <= x < self.w and 0 <= y < self.h:
                    want[p][y * self.w + x] += 1
        bad = 0
        for p in range(len(self.count)):
            for i in range(self.w * self.h):
                if self.count[p][i] != want[p][i]:
                    bad += 1
        return bad

    # ── SPEC §14.4 4단계 렌더 ──────────────────────────────────────────────
    def level(self, p, x, y):
        """0 미탐험 · 1 탐험 · 2 경계 · 3 가시.

           2단계는 순전히 눈을 위한 것이다. 1과 3만 있으면 안개 경계가
           계단처럼 보인다. 명암 단계는 팔레트 명암표(§22.2)의 행 번호다.
        """
        if not (0 <= x < self.w and 0 <= y < self.h):
            return 0
        i = y * self.w + x
        if self.count[p][i] > 0:
            return 3
        if self.explored[p][i] == 0:
            return 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                u, v = x + dx, y + dy
                if (0 <= u < self.w and 0 <= v < self.h
                        and self.count[p][v * self.w + u] > 0):
                    return 2
        return 1

    # ── SPEC §14.2 비트 플레인 (저장·전송용) ───────────────────────────────
    def pack_bits(self, p):
        """탐험 평면 8칸을 1바이트로. 칸 i 는 바이트 i//8 의 2^(i%8) 자리다.

           비트 연산자를 쓰지 않는다(§1.1) — 곱셈과 덧셈이면 충분하다.
        """
        n = self.w * self.h
        out = [0] * ((n + 7) // 8)
        exp = self.explored[p]
        for i in range(n):
            if exp[i]:
                out[i // 8] += 1 << (i % 8)
        return out

    def unpack_bits(self, p, data):
        n = self.w * self.h
        exp = self.explored[p]
        for i in range(n):
            exp[i] = (data[i // 8] // (1 << (i % 8))) % 2
