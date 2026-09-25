# -*- coding: utf-8 -*-
"""무선 링크의 두 장난감 — 자유 공간 손실 예산과 주파수 도약 (6부).

1) 자유 공간 손실 FSPL = 20·log10(4π·d·f/c) dB. 벽·땅 반사·페이딩·
   잡음이 없는 '가장 좋은 경우' 의 모델이라, 여기서 나온 거리는 실제
   도달 거리의 윗한계일 뿐이다(슬라이드가 문서 값과 견준다).
2) 도약: 묶음 문구를 해시해 씨앗으로 삼고 한 주기마다 채널 N 개를
   한 번씩 섞어 도는 수열. ExpressLRS 문서는 "문구를 해시해 난수의
   씨앗으로 쓴다" 고만 적는다 — 해시(x25)·섞는 법은 이 덱이 고른
   것이지 어느 제품의 알고리즘도 아니다.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py'))
from droneshow import rng  # noqa: E402
from mavlink_parse import x25  # noqa: E402

C = 299792458.0                 # 빛의 속도 [m/s]


def dbm(mw):
    """밀리와트 → dBm."""
    return 10 * math.log10(mw)


def fspl_db(d, f):
    """거리 d[m], 주파수 f[Hz] 의 자유 공간 손실[dB]."""
    return 20 * math.log10(4 * math.pi * d * f / C)


def range_m(loss, f):
    """손실 loss[dB] 를 다 쓰는 거리 — fspl_db 의 역함수."""
    return 10 ** (loss / 20) * C / (4 * math.pi * f)


def budget(p, gt, gr, sens):
    """쓸 수 있는 손실 = 송신[dBm] + 두 안테나 이득[dBi] − 감도[dBm]."""
    return p + gt + gr - sens


def wavelength(f):
    return C / f


def hops(phrase, n, cycles):
    """주기마다 채널 0…n−1 을 한 번씩 — 피셔-예이츠 섞기.

    O(n · cycles) 시간."""
    r = rng.Rng(x25(phrase))
    seq = []
    for _ in range(cycles):
        ch = list(range(n))
        for i in range(n - 1, 0, -1):
            j = r.next() % (i + 1)
            ch[i], ch[j] = ch[j], ch[i]
        seq.extend(ch)
    return seq


def lost(seq, blocked):
    """막힌 채널에 떨어진 칸의 비율."""
    return sum(1 for c in seq if c in blocked) / len(seq)


def collide(a, b):
    """같은 칸에서 두 링크가 같은 채널을 쓴 비율."""
    return sum(1 for x, y in zip(a, b) if x == y) / min(len(a), len(b))


if __name__ == '__main__':
    for f in (915e6, 2.44e9, 5.8e9):
        print('%5.0f MHz  파장 %.3f m  1 km 손실 %.1f dB'
              % (f / 1e6, wavelength(f), fspl_db(1000.0, f)))
    s = hops(b'my phrase', 8, 2)
    print('도약 두 주기(채널 8개):', s)
