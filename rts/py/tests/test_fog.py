# -*- coding: utf-8 -*-
"""시야와 안개 — 참조 카운트와 4단계 렌더 (SPEC §14)."""
from __future__ import print_function

import harness as H
from rts import circle as CI
from rts import const as C
from rts import fog as FG
from rts import rng as R
from rts import spatial as S

H.title('fog')

W = H_ = 64


def report(fg, p):
    """골든 10절과 같은 형식의 통계 — 가시 칸·합·최대·도수."""
    cnt = fg.count[p]
    vis = len([1 for v in cnt if v > 0])
    tot = sum(cnt)
    mx = max(cnt) if cnt else 0
    hist = [0] * max(3, mx + 1)
    for v in cnt:
        if v:
            hist[v] += 1
    return vis, tot, mx, hist


def golden_line(tag):
    for ln in H.golden('prim.txt').split('\n'):
        if ln.startswith(tag):
            return [int(s) for s in ln.replace('·', ' ').split() if s.isdigit()]
    return None


# ── 골든 10절 ───────────────────────────────────────────────────────────────
fg = FG.Fog(W, H_)
UNITS = [((10, 10), 3), ((12, 11), 5), ((30, 30), 8)]
for (x, y), r in UNITS:
    fg.add_sight(0, x, y, r)
vis, tot, mx, hist = report(fg, 0)
H.check('초기 가시 칸·합·최대', [vis, tot, mx], [279, 307, 2])
H.check('초기 도수 1·2', [hist[1], hist[2]], [251, 28])

fg.remove_sight(0, 10, 10, 3)
fg.add_sight(0, 11, 10, 3)
vis, tot, mx, hist = report(fg, 0)
H.check('1번 유닛 이동 뒤', [vis, tot, mx, hist[1], hist[2]], [278, 307, 2, 249, 29])

fg.remove_sight(0, 30, 30, 8)
vis, tot, mx, hist = report(fg, 0)
H.check('3번 유닛 사망 뒤', [vis, tot, mx, hist[1], hist[2]], [81, 110, 2, 52, 29])

fg.remove_sight(0, 11, 10, 3)
fg.remove_sight(0, 12, 11, 5)
H.check('전원 제거 후 카운트 합', sum(fg.count[0]), 0)
H.check_true('그래도 탐험 표시는 남는다', sum(fg.explored[0]) > 0)
H.note('증분 갱신이 정확히 0 으로 돌아온다 — 이것이 불변식 F 의 최소 조건이다')

# ── 평면은 플레이어마다 따로다 ──────────────────────────────────────────────
H.check('다른 플레이어의 카운트는 그대로 0', sum(fg.count[1]), 0)
H.check('다른 플레이어는 탐험도 0', sum(fg.explored[1]), 0)
H.check('플레이어 수는 MAX_PLAYER', len(fg.count), C.MAX_PLAYER)

# ── 가장자리 잘림 ───────────────────────────────────────────────────────────
fg2 = FG.Fog(W, H_)
fg2.add_sight(0, 0, 0, 3)
H.check('(0,0) 반경 3 은 원의 1/4 만 맵 안',
        sum(fg2.count[0]), len([1 for dx, dy in CI.offsets(3)
                                if 0 <= dx < W and 0 <= dy < H_]))
H.check('맵 밖은 세지 않는다', max(fg2.count[0]), 1)
fg2.remove_sight(0, 0, 0, 3)
H.check('잘린 원도 정확히 0 으로 돌아온다', sum(fg2.count[0]), 0)
fg2.add_sight(0, 5, 5, 0)
H.check('반경 0 은 자기 칸 하나', sum(fg2.count[0]), 1)
fg2.remove_sight(0, 5, 5, 0)
H.check('카운트는 음수가 되지 않는다', min(fg2.count[0]), 0)
fg2.remove_sight(0, 5, 5, 0)
H.check('없는 시야를 또 빼도 0 이다', min(fg2.count[0]), 0)

# ── 불변식 F — 무작위 이동 중 매 틱 전수 검증 ───────────────────────────────
w = S.World(W, H_)
fg3 = FG.Fog(W, H_)
rand = R.LCG(31)
ents = []
for k in range(12):
    kind = [C.INF, C.ARCHER, C.TANK, C.HARV][k % 4]
    x, y = 4 + rand.roll(56), 4 + rand.roll(56)
    i = S.index(w.spawn(k % 2, kind, x, y))
    fg3.add_sight(w.owner[i], x, y, C.SIGHT[kind])
    ents.append(i)
b = w.spawn(0, C.HQ, 20, 20)
fg3.add_sight(0, 20, 20, C.SIGHT[C.HQ])
bad = 0
for t in range(120):
    for i in ents:
        d = rand.roll(8)
        nx = min(W - 1, max(0, w.tx[i] + [0, 1, 1, 1, 0, -1, -1, -1][d]))
        ny = min(H_ - 1, max(0, w.ty[i] + [-1, -1, 0, 1, 1, 1, 0, -1][d]))
        if (nx, ny) == (w.tx[i], w.ty[i]):
            continue
        r = C.SIGHT[w.kind[i]]
        fg3.remove_sight(w.owner[i], w.tx[i], w.ty[i], r)     # 먼저 빼고
        w.move_tile(i, nx, ny)
        fg3.add_sight(w.owner[i], nx, ny, r)                  # 나중에 더한다
    bad += fg3.recount(w)
H.check('불변식 F — 120틱 × 4플레이어 전수 재계산 불일치', bad, 0)

dead = ents[0]
fg3.remove_sight(w.owner[dead], w.tx[dead], w.ty[dead], C.SIGHT[w.kind[dead]])
w.kill(w.handle(dead))
H.check('죽으면 remove 만 한다 — 그 뒤에도 불변식 F', fg3.recount(w), 0)

# 일부러 어긋뜨리면 recount 가 잡아내는가
fg3.count[0][7 * W + 7] += 1
H.check('어긋난 칸을 recount 가 센다', fg3.recount(w), 1)
fg3.count[0][7 * W + 7] -= 1
H.check('되돌리면 다시 0', fg3.recount(w), 0)
H.note('recount 는 고치지 않고 세기만 한다 — 고치면 버그가 조용히 묻힌다')

# ── SPEC §14.4 4단계 ────────────────────────────────────────────────────────
fg4 = FG.Fog(16, 16)
H.check('아무것도 안 봤으면 0(미탐험)', fg4.level(0, 8, 8), 0)
fg4.add_sight(0, 8, 8, 3)
H.check('보고 있으면 3(가시)', fg4.level(0, 8, 8), 3)
H.check('원 밖은 아직 0', fg4.level(0, 8, 15), 0)
fg4.remove_sight(0, 8, 8, 3)
H.check('시야가 빠지면 1(탐험됨)', fg4.level(0, 8, 8), 1)
fg4.add_sight(0, 8, 8, 1)
H.check('가시 칸에 인접한 탐험 칸은 2(경계)', fg4.level(0, 10, 8), 2)
H.check('가시 칸에서 두 칸 떨어진 탐험 칸은 1', fg4.level(0, 11, 8), 1)
H.check('가시 칸 자신은 3', fg4.level(0, 8, 9), 3)
H.check('맵 밖은 0', fg4.level(0, -1, 0), 0)
H.check('단계는 0..3 뿐',
        sorted(set(fg4.level(0, x, y) for y in range(16) for x in range(16))),
        [0, 1, 2, 3])

# ── SPEC §14.2 비트 플레인 (저장·전송용) ────────────────────────────────────
packed = fg4.pack_bits(0)
H.check('16×16 = 256칸이 32바이트로 접힌다', len(packed), 32)
H.check_true('바이트 범위', all(0 <= v <= 255 for v in packed))
fg5 = FG.Fog(16, 16)
fg5.unpack_bits(0, packed)
H.check('풀면 원래 탐험 평면', fg5.explored[0], fg4.explored[0])
H.check('한 칸도 안 본 평면은 전부 0', FG.Fog(8, 8).pack_bits(0), [0] * 8)
full = FG.Fog(8, 8)
for _i in range(64):
    full.explored[0][_i] = 1
H.check('전부 본 평면은 전부 255', full.pack_bits(0), [255] * 8)
odd = FG.Fog(4, 3)                       # 12칸 — 8의 배수가 아니다
odd.explored[0][11] = 1
H.check('8의 배수가 아니면 마지막 바이트를 0으로 채운다', len(odd.pack_bits(0)), 2)
H.check('마지막 칸은 마지막 바이트의 3번 비트', odd.pack_bits(0), [0, 8])

H.done()
