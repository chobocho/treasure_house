# -*- coding: utf-8 -*-
"""harq — 재전송과 부호를 한 몸으로 묶는 장치.

   HARQ 는 "틀리면 다시 보낸다" 가 아니다. **틀린 것을 버리지 않고
   다음 것과 합친다.** 그 합치는 방식이 둘이다.

     · **체이스 결합(CC)** — 같은 것을 또 보낸다. 받은 연판정 값을
       더하면 실효 SNR 이 두 배가 된다. 곧 3 dB 다.
     · **증분 잉여(IR)** — 처음에 안 보냈던 패리티를 보낸다. 부호율이
       실질적으로 내려가므로, 같은 에너지로 더 많이 번다.

   이 파일은 LTE 의 레이트 매칭(TS 36.212 §5.1.4.1)을 따라 짰다.
   부호기가 낸 세 줄기(계통·패리티1·패리티2)를 각각 32열 부블록
   인터리버에 넣고, 이어 붙여 **순환 버퍼** 를 만들고, 잉여 판본(RV)
   마다 다른 자리에서 읽어 내보낸다.

   **그대로 옮기지 않은 곳:** 규격은 패리티2 줄기에 조금 다른 치환을
   쓰고, 꼬리 비트를 세 줄기에 나누는 규칙도 따로 있다. 여기서는 세
   줄기에 같은 부블록 치환을 쓰고 꼬리는 단순하게 나눴다. 순환 버퍼와
   RV 의 뜻을 보이는 데는 지장이 없고, 다른 곳은 규격을 인용해 본문에서
   다룬다.
"""
import math
import random

from wirelesslib import turbo

# 32열 부블록 인터리버의 열 차례. LTE 의 표는 5비트 역순과 같다 —
# 외울 표가 아니라 규칙이라는 사실을 코드로 적어 둔다.
COL_PERM = [int('{:05b}'.format(j)[::-1], 2) for j in range(32)]
NCOL = 32
RV_ORDER = [0, 2, 3, 1]      # LTE 가 흔히 쓰는 RV 차례


def subblock_perm(n):
    """부블록 인터리버. 결과의 i번째가 입력의 몇 번째인지(없으면 None).

    행으로 쓰고 열을 뒤섞어 읽는다. 길이를 32의 배수로 맞추려고 앞에
    더미 자리를 넣는데, 그 자리는 None 으로 남아 전송되지 않는다.
    """
    rows = (n + NCOL - 1) // NCOL
    kpi = rows * NCOL
    pad = kpi - n
    grid = [None] * kpi
    for k in range(kpi):
        grid[k] = None if k < pad else k - pad
    out = [None] * kpi
    for i in range(kpi):
        r = i % rows
        c = COL_PERM[i // rows]
        out[i] = grid[r * NCOL + c]
    return out


def streams(k, f1, f2, seed=1, msg=None):
    """터보 부호기의 출력을 세 줄기로 가른다.

    돌려주는 것은 [계통, 패리티1, 패리티2] 이고, 길이는 모두 K+6 이다.
    쓰지 않는 자리는 None 이라 순환 버퍼가 알아서 건너뛴다.
    """
    rnd = random.Random(seed)
    if msg is None:
        msg = [rnd.getrandbits(1) for _ in range(k)]
    y = turbo.encode(msg, f1, f2)
    sysb = y[:k]
    p1 = y[k:2 * k]
    p2 = y[2 * k:3 * k]
    t1 = y[3 * k:3 * k + 6]
    t2 = y[3 * k + 6:3 * k + 12]
    d0 = sysb + [t1[0], t1[2], t1[4]] + [t2[0], t2[2], t2[4]]
    d1 = p1 + [t1[1], t1[3], t1[5]] + [None, None, None]
    d2 = p2 + [t2[1], t2[3], t2[5]] + [None, None, None]
    return [d0, d1, d2]


def circular_buffer(d):
    """순환 버퍼. 각 칸은 (줄기 번호, 그 줄기 안의 자리) 또는 None.

    계통 줄기를 통째로 앞에 놓고 그 뒤에 패리티 둘을 번갈아 끼운다.
    그래서 버퍼 앞쪽을 읽으면 계통 비트가 많이 나오고(RV0, 혼자서도
    복호된다), 뒤쪽을 읽으면 패리티가 많이 나온다(RV2·RV3).
    """
    n = len(d[0])
    perm = subblock_perm(n)
    kpi = len(perm)
    v = []
    for s in range(3):
        v.append([None if p is None or d[s][p] is None else (s, p)
                  for p in perm])
    buf = list(v[0])
    for i in range(kpi):
        buf.append(v[1][i])
        buf.append(v[2][i])
    return buf


def _k0(d, rv):
    """RV 마다의 읽기 시작 자리. LTE TS 36.212 §5.1.4.1.2 의 식이다."""
    rows = (len(d[0]) + NCOL - 1) // NCOL
    ncb = 3 * rows * NCOL
    return rows * (2 * int(math.ceil(ncb / (8.0 * rows))) * rv + 2)


def rate_match_positions(d, e, rv=0):
    """내보낼 버퍼 자리의 목록. None 칸은 건너뛰고, 끝나면 되감는다."""
    buf = circular_buffer(d)
    ncb = len(buf)
    if not any(v is not None for v in buf):
        raise ValueError('버퍼가 비었다')
    out = []
    j = _k0(d, rv) % ncb
    while len(out) < e:
        if buf[j] is not None:
            out.append(j)
        j = (j + 1) % ncb
    return out


def rate_match(d, e, rv=0):
    """실제로 내보낼 비트들."""
    buf = circular_buffer(d)
    pos = rate_match_positions(d, e, rv)
    return [d[buf[p][0]][buf[p][1]] for p in pos]


def soft_buffer(d, rxs):
    """받은 것들을 자리마다 더한다 — 이 덧셈이 곧 결합이다.

    rxs 는 [(rv, LLR 목록), …] 이다. 같은 자리에 두 번 왔으면 두 값이
    더해진다. 체이스 결합이 3 dB 를 버는 까닭이 이 한 줄이다.
    """
    buf = circular_buffer(d)
    acc = [0.0] * len(buf)
    for rv, llr in rxs:
        for p, v in zip(rate_match_positions(d, len(llr), rv), llr):
            acc[p] += v
    return acc


def _turbo_llr(d, acc, k):
    """순환 버퍼의 값을 터보 복호기가 기대하는 차례로 되돌린다."""
    buf = circular_buffer(d)
    lin = [[0.0] * len(d[0]) for _ in range(3)]
    for p, who in enumerate(buf):
        if who is not None:
            lin[who[0]][who[1]] += acc[p]
    ls = lin[0][:k]
    lp1 = lin[1][:k]
    lp2 = lin[2][:k]
    t1 = [lin[0][k], lin[1][k], lin[0][k + 1], lin[1][k + 1],
          lin[0][k + 2], lin[1][k + 2]]
    t2 = [lin[0][k + 3], lin[2][k], lin[0][k + 4], lin[2][k + 1],
          lin[0][k + 5], lin[2][k + 2]]
    return ls + lp1 + lp2 + t1 + t2


def _run(ebn0_db, transmissions, frames, k, elen, seed, mode, iters=6):
    """(성공 수, 쓴 전송 횟수 합). bler·throughput 이 함께 쓴다."""
    if mode not in ('chase', 'ir'):
        raise ValueError('mode 는 chase 나 ir 이다: %s' % mode)
    rnd = random.Random(seed)
    f1, f2 = 3, 10
    rate = float(k) / elen
    esn0 = 10.0 ** ((ebn0_db + 10.0 * math.log10(rate)) / 10.0)
    sigma2 = 1.0 / (2.0 * esn0)
    sd = math.sqrt(sigma2)
    perm = turbo.qpp(k, f1, f2)
    good = 0
    used = 0
    for _ in range(frames):
        msg = [rnd.getrandbits(1) for _ in range(k)]
        d = streams(k, f1, f2, msg=msg)
        rxs = []
        ok = False
        for t in range(transmissions):
            rv = 0 if mode == 'chase' else RV_ORDER[t % 4]
            bits = rate_match(d, elen, rv)
            llr = [2.0 * ((1.0 - 2.0 * b) + rnd.gauss(0.0, sd)) / sigma2
                   for b in bits]
            rxs.append((rv, llr))
            used += 1
            acc = soft_buffer(d, rxs)
            got = turbo._decode_llr(_turbo_llr(d, acc, k), k, perm,
                                    iters, False)[-1]
            if got == msg:
                ok = True
                break
        if ok:
            good += 1
    return good, used


def bler(ebn0_db, transmissions, frames, k, elen, seed=1, mode='ir'):
    """정해진 횟수 안에 못 받아 낸 블록의 비율."""
    good, _used = _run(ebn0_db, transmissions, frames, k, elen, seed,
                       mode)
    return 1.0 - good / float(frames)


def throughput(ebn0_db, transmissions, frames, k, elen, seed=1,
               mode='ir'):
    """채널 사용 한 번당 실어 나른 정보 비트 수.

    성공한 블록의 정보 비트를 **실제로 쓴 전송 전부** 로 나눈다.
    그래서 재전송이 많아지면 처리율이 떨어진다 — HARQ 를 켠다고
    공짜로 좋아지는 것이 아니라는 사실이 이 나눗셈에 들어 있다.
    """
    good, used = _run(ebn0_db, transmissions, frames, k, elen, seed,
                      mode)
    return good * float(k) / (used * float(elen))
