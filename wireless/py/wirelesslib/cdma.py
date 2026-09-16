# -*- coding: utf-8 -*-
"""cdma — IS-95 순방향 링크의 축소 모형, RAKE, 전력 제어, 용량.

   CDMA 의 주장은 셋이고, 이 파일은 그 셋을 각각 돌려서 보인다.

     1. **직교 부호로 사람을 가른다.** 순방향은 기지국 하나가 모든
        신호를 같은 시각에 내보내므로 왈시 부호가 완벽히 직교한다.
        파일럿(W0)·동기(W32)·페이징(W1~W7)·트래픽이 그렇게 나뉜다.
     2. **역확산이 처리 이득만큼 SNR 을 올린다.** 잡음보다 낮게 묻힌
        신호를 꺼내 쓰는 근거다.
     3. **다중경로는 잡음이 아니라 이득이다.** 갈래마다 따로 받아
        모으면(RAKE) 더 좋아진다. 갈퀴로 긁어모은다는 이름 그대로다.

   그리고 이 셋을 떠받치는 조건이 **전력 제어** 다. 역방향에서는 모든
   단말이 기지국에 같은 세기로 닿아야 한다. 안 그러면 가까운 단말
   하나가 셀 전체를 묻어 버린다(원근 문제). IS-95 는 이것을 초당 800번
   고쳤다.
"""
import math
import random

from wirelesslib import spread

# IS-95 순방향의 왈시 배정 — TIA/EIA/IS-95 §7.1.3.1
CHANNELS = {'pilot': 0, 'sync': 32, 'paging': 1, 'traffic': 8}
SF = 64


def _walsh_table(sf=SF):
    return spread.hadamard(sf)


def forward_roundtrip(nusers, nsym, seed=1):
    """잡음 없는 순방향 링크에서 틀린 심볼의 수. 0 이어야 한다.

    사용자마다 왈시 부호를 하나씩 주고, 다 더해 내보내고, 각자 제
    부호로 역확산한다. 직교하니 남의 신호는 정확히 0 으로 지워진다.
    """
    h = _walsh_table()
    rnd = random.Random(seed)
    users = list(range(1, nusers + 1))       # 0번은 파일럿
    syms = {u: [1 - 2 * rnd.getrandbits(1) for _ in range(nsym)]
            for u in users}
    bad = 0
    for t in range(nsym):
        chips = [0] * SF
        for u in users:
            w = h[u]
            s = syms[u][t]
            for i in range(SF):
                chips[i] += s * w[i]
        for u in users:
            w = h[u]
            acc = sum(chips[i] * w[i] for i in range(SF)) / float(SF)
            if (1 if acc > 0 else -1) != syms[u][t]:
                bad += 1
    return bad


def despread_gain_db(sf, chips, seed=1):
    """역확산이 벌어 주는 SNR [dB]. 확산율의 로그와 같아야 한다.

    칩마다 잡음이 독립이므로, SF 칩을 코히어런트하게 더하면 신호는
    SF 배가 되고 잡음은 √SF 배가 된다 — 전력비로 SF 배,
    곧 처리 이득이다.
    """
    rnd = random.Random(seed)
    w = spread.walsh(sf, 1)
    nsym = chips // sf
    sig = 0.0
    noi = 0.0
    for _ in range(nsym):
        s = 1 - 2 * rnd.getrandbits(1)
        acc = 0.0
        for i in range(sf):
            acc += (s * w[i] + rnd.gauss(0.0, 1.0)) * w[i]
        acc /= sf
        sig += s * s
        noi += (acc - s) ** 2
    # 칩 하나의 SNR 은 1/1 = 0 dB 였다. 역확산 뒤의 SNR 이 곧 이득이다.
    return 10.0 * math.log10(sig / noi)


def multiuser_sinr_db(nusers, seed=1, sf=SF, noise=0.1):
    """직교가 깨진 상황(역방향·비동기)에서의 SINR.

    순방향은 기지국이 한꺼번에 내보내니 왈시가 직교하지만, **역방향은
    단말마다 도착 시각이 달라 직교가 성립하지 않는다.** 게다가 실물
    IS-95 는 왈시 위에 긴 PN 을 덧씌우므로, 어긋난 시각에서 남의 부호는
    사실상 임의의 ±1 열로 보인다. 여기서는 그 사실을 그대로 모형으로
    삼는다 — 간섭원의 실효 부호를 임의 ±1 로 둔다.

    그러면 간섭 전력이 사용자 수에 비례해 늘고(1/SF 씩), SINR 이
    사용자 수에 따라 떨어진다. 이것이 CDMA 셀의 '부드러운 용량' 이다.
    """
    rnd = random.Random(seed)
    want = spread.walsh(sf, 1)
    sig = 0.0
    inter = 0.0
    for _ in range(400):
        s = 1 - 2 * rnd.getrandbits(1)
        err = 0.0
        for _u in range(nusers):
            v = 1 - 2 * rnd.getrandbits(1)
            code = [1 - 2 * rnd.getrandbits(1) for _ in range(sf)]
            err += v * sum(code[i] * want[i]
                           for i in range(sf)) / float(sf)
        err += rnd.gauss(0.0, noise)
        sig += s * s
        inter += err * err
    return 10.0 * math.log10(sig / max(inter, 1e-12))


# ── RAKE ──────────────────────────────────────────────────────────


def rake_ber(fingers, frames, ebn0_db, seed=1, paths=2, sf=16):
    """RAKE 수신기의 BER. fingers 개의 갈래를 최대비 결합한다.

    각 갈래는 서로 다른 지연과 독립인 레일리 이득을 갖는다. 갈래를
    세기가 큰 순서로 골라 위상을 맞춰 더하는 것이 최대비 결합이고,
    그것이 곧 다이버시티다.
    """
    rnd = random.Random(seed)
    w = spread.walsh(sf, 1)
    ebn0 = 10.0 ** (ebn0_db / 10.0)
    # 비트 에너지를 1 로 두면 칩 하나의 진폭은 1/√SF 다. 이 한 줄을
    # 빠뜨리면 확산이 공짜로 SNR 을 올려 주는 것처럼 보인다.
    amp = 1.0 / math.sqrt(sf)
    sd = math.sqrt(1.0 / (2.0 * ebn0))
    bad = 0
    total = 0
    for _ in range(frames):
        gains = [complex(rnd.gauss(0, math.sqrt(0.5 / paths)),
                         rnd.gauss(0, math.sqrt(0.5 / paths)))
                 for _ in range(paths)]
        order = sorted(range(paths), key=lambda i: -abs(gains[i]))
        use = order[:fingers]
        for _s in range(20):
            b = rnd.getrandbits(1)
            s = 1 - 2 * b
            # 갈래마다 독립인 잡음을 받는다(지연이 달라 겹치지 않는다)
            acc = 0j
            for i in use:
                g = gains[i]
                r = 0j
                for c in w:
                    noise = complex(rnd.gauss(0, sd), rnd.gauss(0, sd))
                    r += (g * s * amp * c + noise) * c
                acc += r * g.conjugate()
            total += 1
            if (0 if acc.real > 0 else 1) != b:
                bad += 1
    return bad / float(total)


# ── 전력 제어 ─────────────────────────────────────────────────────


def near_far_sinr_db(control, near_db=0.0, far_db=-40.0):
    """먼 단말의 신호 대 '가까운 단말 간섭' 비 [dB].

    전력 제어가 없으면 가까운 단말이 40 dB 세게 도착해 먼 단말을
    묻어 버린다(−40 dB). 켜면 둘이 같은 세기로 도착해 정확히 0 dB 가
    된다 — 대등해진다는 뜻이다. 이것이 CDMA 가 전력 제어 없이는
    성립하지 않는 이유다.
    """
    near = 10.0 ** (near_db / 10.0)
    far = 10.0 ** (far_db / 10.0)
    if control:
        near = far                        # 같은 세기로 맞춘다
    return 10.0 * math.log10(far / near)


def power_control_loop(target_db, steps, step_db=1.0, seed=1,
                       fade_db=6.0):
    """닫힌 고리 전력 제어. 매 걸음 한 비트만 올려/내려 보낸다.

    IS-95 는 이것을 초당 800번 돌렸다. 한 걸음이 1 dB 이므로 최대
    800 dB/s 를 따라갈 수 있고, 그래서 빠른 페이딩도 어느 정도 쫓는다.
    돌려주는 것은 걸음마다 기지국이 본 SINR [dB] 다.
    """
    rnd = random.Random(seed)
    tx = 0.0
    hist = []
    fade = 0.0
    for _ in range(steps):
        fade = 0.9 * fade + rnd.gauss(0.0, fade_db * 0.3)
        rx = tx + fade
        hist.append(rx)
        tx += -step_db if rx > target_db else step_db
    return hist


# ── 용량 ──────────────────────────────────────────────────────────


def pole_capacity(wr, ebn0_db, activity=1.0, f_other=0.0,
                  sectors=1.0):
    """길하우젠 식의 셀당 사용자 수.

        N = 1 + (W/R) / (Eb/N0) · G / (ν · (1+f))

    · W/R  확산율(처리 이득)
    · ν    음성 활동률 — 말을 안 할 때 안 보내면 간섭이 준다
    · f    다른 셀에서 넘어오는 간섭의 비율
    · G    섹터화 이득

    CDMA 용량이 '부드러운' 까닭이 이 식에 있다. 한 명 더 받으면
    모두의 SINR 이 조금씩 나빠질 뿐, 채널이 모자라 거절당하지 않는다.
    """
    if activity <= 0 or wr <= 0 or sectors <= 0:
        raise ValueError('W/R·활동률·섹터 이득은 양수여야 한다')
    g = 10.0 ** (ebn0_db / 10.0)
    return 1.0 + (wr / g) * sectors / (activity * (1.0 + f_other))
