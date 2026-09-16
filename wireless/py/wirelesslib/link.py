# -*- coding: utf-8 -*-
"""link — 링크 버짓. 이 책에서 가장 실무에 가까운 계산.

   할 일은 dB 를 더하고 빼는 것뿐이다.

       수신 전력 = 송신 전력 + 송신 이득 − 경로손실 + 수신 이득
                  − 그 밖의 손실
       잡음 바닥 = −174 dBm/Hz + 10·log₁₀(대역폭) + 잡음지수
       SNR      = 수신 전력 − 잡음 바닥
       여유     = SNR − 요구 SNR

   그런데 항을 하나 빠뜨리거나 부호를 뒤집으면 셀 반지름이 두 배로
   틀린다. 경로손실이 거리의 네 제곱쯤이라, 6 dB 를 잘못 세면
   거리로는 √2 배가 어긋난다.
   그래서 이 파일은 항을 **이름표와 함께** 돌려주고, 시험이 손으로
   계산한 표와 0.1 dB 안에서 맞대어 본다.

   −174 라는 수는 볼츠만 상수 k 와 290 K 에서 나온다.

       kT = 1.380649e-23 × 290 = 4.0039e-21 W/Hz = −173.98 dBm/Hz

   290 K 는 실제 온도가 아니라 국제적으로 정한 기준 온도다.
"""
import math

from wirelesslib import channel, modem

BOLTZMANN = 1.380649e-23
T0 = 290.0                 # 기준 잡음온도 [K]


def thermal_noise_dbm(bw_hz, temp_k=T0):
    """열잡음 전력 [dBm]. 대역폭 1 Hz·290 K 에서 −173.98 dBm 이다."""
    if bw_hz <= 0 or temp_k <= 0:
        raise ValueError('대역폭과 온도는 양수여야 한다')
    watts = BOLTZMANN * temp_k * bw_hz
    return 10.0 * math.log10(watts * 1000.0)


def noise_temp_k(nf_db, temp_k=T0):
    """잡음지수를 등가 잡음온도로. T = T₀(F − 1).

    위성 쪽은 잡음지수 대신 잡음온도로 말한다. 저잡음 증폭기의
    0.5 dB 는 35 K 인데, dB 로는 작아 보여도 하늘의 온도(수십 K)와
    견주면 큰 값이다 — 그래서 위성에서는 K 로 세는 편이 낫다.
    """
    return temp_k * (10.0 ** (nf_db / 10.0) - 1.0)


def noise_figure_db(t_k, temp_k=T0):
    """등가 잡음온도를 잡음지수로 되돌린다."""
    return 10.0 * math.log10(1.0 + t_k / temp_k)


def noise_floor_dbm(bw_hz, nf_db, temp_k=T0):
    """수신기가 보는 잡음 바닥 [dBm]."""
    return thermal_noise_dbm(bw_hz, temp_k) + nf_db


def eirp_dbm(ptx_dbm, gtx_dbi, loss_db=0.0):
    """등가 등방 복사 전력 — 송신 쪽을 한 수로 묶은 것."""
    return ptx_dbm + gtx_dbi - loss_db


def gt_db(gain_dbi, tsys_k):
    """G/T [dB/K] — 수신 쪽을 한 수로 묶은 것. 위성 지구국의 잣대다."""
    if tsys_k <= 0:
        raise ValueError('시스템 잡음온도는 양수여야 한다')
    return gain_dbi - 10.0 * math.log10(tsys_k)


def budget(ptx_dbm, gtx_dbi, grx_dbi, path_loss_db, bw_hz, nf_db,
           required_snr_db, tx_loss_db=0.0, other_loss_db=0.0,
           temp_k=T0):
    """링크 버짓 한 판. 항을 이름표와 함께 돌려준다.

    이름표를 붙여 돌려주는 까닭: 여유가 모자랄 때 '어디서 잃었는지'
    를 봐야 고칠 수 있다. 숫자 하나만 돌려주면 그 정보가 사라진다.
    """
    eirp = eirp_dbm(ptx_dbm, gtx_dbi, tx_loss_db)
    prx = eirp - path_loss_db + grx_dbi - other_loss_db
    noise = noise_floor_dbm(bw_hz, nf_db, temp_k)
    snr = prx - noise
    return {
        'eirp_dbm': eirp,
        'path_loss_db': path_loss_db,
        'grx_dbi': grx_dbi,
        'other_loss_db': other_loss_db,
        'prx_dbm': prx,
        'noise_dbm': noise,
        'snr_db': snr,
        'required_snr_db': required_snr_db,
        'margin_db': snr - required_snr_db,
    }


def max_range_m(ptx_dbm, gtx_dbi, grx_dbi, f_hz, bw_hz, nf_db,
                required_snr_db, tx_loss_db=0.0, other_loss_db=0.0,
                temp_k=T0, n=2.0):
    """여유가 정확히 0 이 되는 거리 — 그 거리가 곧 셀 반지름이다.

    자유공간이면 경로손실이 20·log₁₀ d 이므로 닫힌 식으로 풀린다.
    n 을 2 보다 크게 주면 로그거리 모형의 기울기로 푼다.
    """
    eirp = eirp_dbm(ptx_dbm, gtx_dbi, tx_loss_db)
    noise = noise_floor_dbm(bw_hz, nf_db, temp_k)
    allowed = eirp + grx_dbi - other_loss_db - noise - required_snr_db
    # allowed = 경로손실 한도. FSPL(d) = 20log10(4πdf/c) 를 뒤집는다.
    if n == 2.0:
        return 10.0 ** (allowed / 20.0) * channel.C / (4 * math.pi
                                                       * f_hz)
    d0 = 100.0
    base = channel.fspl_db(d0, f_hz)
    return d0 * 10.0 ** ((allowed - base) / (10.0 * n))


def sensitivity_dbm(bw_hz, nf_db, required_snr_db, temp_k=T0):
    """수신 감도 — 이보다 약하면 못 받는다는 전력."""
    return noise_floor_dbm(bw_hz, nf_db, temp_k) + required_snr_db


def required_ebn0_db(name, ber, lo=-10.0, hi=60.0, tol=1e-9):
    """목표 BER 을 내는 Eb/N0 [dB]. 이분법으로 거꾸로 푼다.

    BER 은 Eb/N0 에 대해 단조 감소하므로 이분법이 언제나 모인다.
    링크 버짓의 '요구 SNR' 칸은 대개 이렇게 정해진다 — 변조와 부호를
    고르면 필요한 Eb/N0 가 정해지고, 그 값이 곧 여유의 기준이 된다.
    """
    if not 0.0 < ber < modem.ber_theory(name, lo):
        raise ValueError('그 BER 은 이 변조로 닿을 수 없다: %g' % ber)
    while hi - lo > tol:
        mid = (lo + hi) / 2.0
        if modem.ber_theory(name, mid) > ber:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ── 미리 담아 둔 링크들 ───────────────────────────────────────────
#
# 숫자는 전형적인 값이다. 규격이 못 박은 값이 아니라 설계 예시이므로,
# 덱에서도 "이런 규모" 로만 쓴다.
PRESETS = {
    # LTE 단말 상향 — 23 dBm, 1 PRB 를 다 쓰지 않고 10 MHz 로 잡았다
    'lte_uplink': dict(ptx_dbm=23.0, gtx_dbi=0.0, grx_dbi=17.0,
                       dist_m=1000.0, f_hz=2.0e9, bw_hz=1.0e7,
                       nf_db=3.0, required_snr_db=0.0,
                       other_loss_db=20.0),
    # NR 기지국 하향 — 섹터 안테나와 3.5 GHz
    'nr_downlink': dict(ptx_dbm=46.0, gtx_dbi=23.0, grx_dbi=0.0,
                        dist_m=500.0, f_hz=3.5e9, bw_hz=1.0e8,
                        nf_db=7.0, required_snr_db=5.0,
                        other_loss_db=20.0),
    # 정지궤도 하향 — 경로손실이 200 dB 대라 안테나로 메운다
    'geo_downlink': dict(ptx_dbm=53.0, gtx_dbi=38.0, grx_dbi=41.0,
                         dist_m=38000000.0, f_hz=12.0e9, bw_hz=3.6e7,
                         nf_db=1.5, required_snr_db=6.0,
                         other_loss_db=2.0),
}


def preset_budget(name):
    """미리 담아 둔 링크 하나를 계산한다."""
    if name not in PRESETS:
        raise ValueError('모르는 링크: %s' % name)
    p = dict(PRESETS[name])
    d = p.pop('dist_m')
    f = p.pop('f_hz')
    p['path_loss_db'] = channel.fspl_db(d, f)
    return budget(**p)
