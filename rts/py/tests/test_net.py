# -*- coding: utf-8 -*-
"""락스텝 네트워크 — 지연·지터·디싱크 주입 (SPEC §19)."""
from __future__ import print_function

import harness as H
from rts import const as C
from rts import net as N
from rts import select as SEL
from rts import sim as SIM
from rts import tmap as T

H.title('net')

O1 = (0, 256, SEL.MOVE, 3, 3, 0)
O2 = (1, 512, SEL.MOVE, 4, 4, 0)

# ── SPEC §19.2 모형 ─────────────────────────────────────────────────────────
n = N.Net(2)
H.check('기본 지연은 ORDER_DELAY', n.latency, C.ORDER_DELAY)
H.check('보낸 명령의 실행 틱은 보낼 때 정해진다', n.send(10, 0, O1), 12)
H.check('지터가 없으면 도착도 같은 틱', n.arrive_of(10, 0), 12)
n.flush(10, 0)
H.check('한 플레이어만 보냈으면 아직 준비되지 않았다', n.ready(12), False)
n.flush(10, 1)
H.check('둘 다 보냈으면 준비 완료', n.ready(12), True)
H.check('그 틱의 명령을 정렬해 돌려준다', n.take(12), [O1])
H.check('가져간 뒤에는 비어 있다', n.take(12), [])
H.check('명령이 없는 틱도 준비될 수 있다', n.ready(13), False)

n2 = N.Net(2)
n2.send(0, 1, O2)
n2.send(0, 0, O1)
n2.flush(0, 0)
n2.flush(0, 1)
H.check('정렬은 플레이어·핸들 순', n2.take(2), [O1, O2])
H.check('빈 턴도 보내야 한다 — 그래야 상대가 기다리지 않는다',
        (N.Net(2).ready(2)), False)

# ── SPEC §19.2 지터 ─────────────────────────────────────────────────────────
n3 = N.Net(2, C.ORDER_DELAY, jitter_seed=99, jitter_max=2)
delays = set()
for t in range(40):
    n3.send(t, 0, (0, 256, SEL.MOVE, t % 8, 0, 0))
    n3.flush(t, 0)
    n3.flush(t, 1)
    delays.add(n3.arrive_of(t, 0) - (t + C.ORDER_DELAY))
H.check('지터는 0..2 틱', sorted(delays), [0, 1, 2])
H.check('실행 틱은 지터와 무관하다', n3.exec_of(7, 0), 7 + C.ORDER_DELAY)
H.check_true('늦게 도착한 턴이 실제로 있다', n3.stalls > 0)
H.note('늦게 도착한 명령을 앞당겨 실행하는 경로는 존재하지 않는다')

n4 = N.Net(2, C.ORDER_DELAY, jitter_seed=5, jitter_max=2)
n4.send(0, 0, O1)
n4.flush(0, 0)
n4.flush(0, 1)
late = max(n4.arrive_of(0, 0), n4.arrive_of(0, 1))
H.check('도착 전에는 준비되지 않는다', n4.ready(2, late - 1) if late > 2 else False,
        False)
H.check('도착하면 준비된다', n4.ready(2, late), True)
H.check('기다린 뒤에도 명령은 그대로', n4.take(2), [O1])

# ── 지터가 있어도 결과가 같아야 한다 ────────────────────────────────────────
def play(jit_seed, jit_max):
    m = T.TMap.load_text(H.golden('map_start.txt'))
    s = SIM.Sim(m, 1, 2)
    s.setup_start()
    net = N.Net(2, C.ORDER_DELAY, jitter_seed=jit_seed, jitter_max=jit_max)
    sc = SIM.parse_script(H.golden('script.txt'))
    hs = []
    wall = 0
    for t in range(1, 61):
        for o in s.script_orders(sc, t):
            net.send(t, o[0], o)
        for p in range(2):
            net.flush(t, p)
        et = t + C.ORDER_DELAY
        guard = 0
        while not net.ready(et, wall) and guard < 100:   # 늦으면 기다린다
            wall += 1
            guard += 1
        hs.append(s.step(net.take(et)))
        wall += 1
    return hs


clean = play(0, 0)
jit = play(1234, 2)
H.check('지터가 있어도 60틱의 해시열이 같다', clean, jit)
H.check_true('해시가 실제로 변한다', len(set(clean)) > 30)

# ── SPEC §19.4 디싱크 주입 ──────────────────────────────────────────────────
def run(bug, n_ticks):
    m = T.TMap.load_text(H.golden('map_start.txt'))
    s = SIM.Sim(m, 1, 2, float_bug=bug)
    s.setup_start()
    return [s.step([]) for _ in range(n_ticks)]


a = run(False, 80)
b = run(False, 80)
c = run(True, 80)
H.check('버그가 없으면 두 시뮬이 같다', a, b)
first = -1
for k in range(len(a)):
    if a[k] != c[k]:
        first = k + 1
        break
H.check_true('실수 누적을 켜면 갈린다 (처음 어긋난 틱 %d)' % first, first > 0)


def tiles_diverge(n_ticks):
    """눈에 보이는 차이(타일 좌표)가 처음 나는 틱. 없으면 -1."""
    m1 = T.TMap.load_text(H.golden('map_start.txt'))
    m2 = T.TMap.load_text(H.golden('map_start.txt'))
    s1 = SIM.Sim(m1, 1, 2, float_bug=False)
    s2 = SIM.Sim(m2, 1, 2, float_bug=True)
    s1.setup_start()
    s2.setup_start()
    for t in range(1, n_ticks + 1):
        s1.step([])
        s2.step([])
        p1 = [(s1.w.alive[i], s1.w.tx[i], s1.w.ty[i])
              for i in range(1, C.MAX_ENT)]
        p2 = [(s2.w.alive[i], s2.w.tx[i], s2.w.ty[i])
              for i in range(1, C.MAX_ENT)]
        if p1 != p2:
            return t
    return -1


H.check('80틱 동안 타일 좌표는 한 칸도 어긋나지 않는다', tiles_diverge(80), -1)
H.note('해시는 1틱에 갈리는데 화면은 그대로다 — 상태 해시가 없으면')
H.note('이 버그는 한참 뒤 "어쩐지 결과가 다른 게임"으로만 나타난다')
H.note('일부러 넣은 버그다 — "부동소수점이면 반드시 디싱크"가 아니라')
H.note('"이 조건에서 이렇게 어긋났다"가 말할 수 있는 전부다')

# 명세가 정정한 부분: fpmul 을 실수로 해도 이 크기에서는 어긋나지 않는다
from rts import fixed as F                                        # noqa: E402
bad = 0
for a_ in (6144, 4344, 65536, 1048576, 46341, 4194304):
    for b_ in (46341, 65536, 27146, 32768):
        if F.fp_mul(a_, b_) != int(a_ * b_ / 65536.0):
            bad += 1
H.check('16.16 곱은 실수로 해도 정수와 비트 단위로 같다 (SPEC §19.4 의 정정)',
        bad, 0)
H.note('배정밀도 가수 53비트 · 곱은 커야 2^42 · 65536 은 2의 거듭제곱')

H.done()
