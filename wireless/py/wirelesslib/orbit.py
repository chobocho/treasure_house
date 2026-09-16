# -*- coding: utf-8 -*-
"""orbit — 하늘에 있는 기지국의 기하와 시간.

   위성 통신의 숫자는 전부 케플러 한 줄에서 나온다.

       T = 2π √(a³/μ),   v = √(μ/a),   a = R + h

   높이 h 를 정하면 주기·속도가 정해지고, 거기서 지연·도플러·발자국이
   줄줄이 따라 나온다. 그리고 그 값들이 3GPP NTN 규격의 모양을 정한다.

     · **지연** — 정지궤도는 편도 119 ms, 왕복 238 ms 다. HARQ 타이머와
       RTT 를 그대로 쓸 수 없는 이유가 이 숫자다. 저궤도는 편도
       2~4 ms 라 지상망과 비슷해진다.
     · **도플러** — 저궤도는 2 GHz 에서 ±47 kHz 를 오간다. 부반송파
       간격이 15 kHz 인데 그 세 배다. 그래서 NTN 은 위성이 제 궤도를
       알려 주고 단말이 **미리 보정** 한다.
     · **가시 시간** — 저궤도 위성 하나는 몇 분 보이다 사라진다.
       그래서 위성 간 핸드오버가 지상 핸드오버보다 훨씬 잦다.

   정지궤도의 주기는 24시간이 아니라 **항성일**(23시간 56분 4초)이다.
   지구가 태양을 도는 만큼 하루에 1도쯤 더 돌기 때문이다.
"""
import math

MU = 3.986004418e14        # 지구 중력 상수 GM [m³/s²]
EARTH_R_KM = 6371.0        # 평균 반지름 — 기하 계산은 이것으로 한다
# 정지궤도 고도는 **적도** 반지름 위로 재는 값이다. 평균 반지름으로
# 재면 35,793 km 가 나와 흔히 쓰는 35,786 km 와 7 km 어긋난다.
EARTH_EQ_R_KM = 6378.137
SIDEREAL_DAY_S = 86164.0905
EARTH_RATE = 2.0 * math.pi / SIDEREAL_DAY_S   # 지구 자전 각속도 [rad/s]
C_KM_MS = 299.792458       # 빛의 속도 [km/ms]


def _check_alt(alt_km):
    if alt_km <= 0:
        raise ValueError('고도는 양수여야 한다: %s' % alt_km)


def period_s(alt_km, r_km=EARTH_R_KM):
    """원 궤도의 주기. T = 2π √(a³/μ).

    고도를 어느 반지름 위로 쟀는지가 중요하다. 정지궤도 고도(35,786 km)
    는 적도 반지름 위의 값이므로, 그 고도로 주기를 구하려면 r_km 에도
    적도 반지름을 넣어야 한다. 평균 반지름을 섞어 쓰면 22초가 어긋난다.
    """
    _check_alt(alt_km)
    a = (r_km + alt_km) * 1000.0
    return 2.0 * math.pi * math.sqrt(a ** 3 / MU)


def speed_ms(alt_km, r_km=EARTH_R_KM):
    """원 궤도의 속도. v = √(μ/a). 높을수록 느리다."""
    _check_alt(alt_km)
    return math.sqrt(MU / ((r_km + alt_km) * 1000.0))


def geo_altitude_km():
    """주기가 항성일과 같아지는 고도 — 약 35,786 km."""
    a = (MU * SIDEREAL_DAY_S ** 2 / (4.0 * math.pi ** 2)) ** (1.0 / 3.0)
    return a / 1000.0 - EARTH_EQ_R_KM


# ── 기하 ──────────────────────────────────────────────────────────


def _check_el(el_deg):
    if not 0.0 <= el_deg <= 90.0:
        raise ValueError('앙각은 0~90도다: %s' % el_deg)


def slant_range_km(alt_km, el_deg):
    """지상국에서 위성까지의 비스듬한 거리.

        d = R(√(((R+h)/R)² − cos²ε) − sin ε)

    천정(ε=90°)에서는 정확히 h 가 되고, 앙각이 낮아질수록 길어진다.
    저궤도에서 이 차이가 지연을 두 배로 벌린다 — NTN 의 타이밍
    어드밴스 범위를 정하는 것이 바로 이 폭이다.
    """
    _check_alt(alt_km)
    _check_el(el_deg)
    r = EARTH_R_KM
    e = math.radians(el_deg)
    ratio = (r + alt_km) / r
    return r * (math.sqrt(ratio ** 2 - math.cos(e) ** 2) - math.sin(e))


def one_way_delay_ms(alt_km, el_deg):
    """편도 전파 지연 [ms]."""
    return slant_range_km(alt_km, el_deg) / C_KM_MS


def central_angle_deg(alt_km, el_deg):
    """지구 중심에서 본 지상국과 위성 사이의 각.

    이 각이 곧 '위성이 얼마나 넓은 땅을 덮는가' 다. 앙각 조건이
    낮을수록 커지고, 고도가 높을수록 커진다.
    """
    _check_alt(alt_km)
    _check_el(el_deg)
    e = math.radians(el_deg)
    r = EARTH_R_KM
    # sin(중심각) / d = sin(90°+ε) / (R+h)
    g = math.acos(r * math.cos(e) / (r + alt_km)) - e
    return math.degrees(g)


def footprint_radius_km(alt_km, el_deg):
    """최소 앙각 조건에서의 발자국 반지름 (지표면을 따라 잰 거리)."""
    return EARTH_R_KM * math.radians(central_angle_deg(alt_km, el_deg))


# ── 도플러 ────────────────────────────────────────────────────────


def _horizon_angle_rad(alt_km):
    """지평선에 걸리는 중심각 — 여기서 도플러가 가장 크다."""
    return math.acos(EARTH_R_KM / (EARTH_R_KM + alt_km))


def doppler_hz(alt_km, fc_hz, theta_deg, earth_rotation=False):
    """천정 통과에서 중심각 θ 일 때의 도플러 편이.

    거리 변화율 ṙ 을 그대로 쓴다.

        d(θ) = √(R² + a² − 2Ra cos θ),  ṙ = R·a·ω·sin θ / d
        f_D = −ṙ · f_c / c

    θ=0(최접근)에서 0 이고, 다가올 때는 양수, 멀어질 때는 음수다.

    earth_rotation 을 켜면 **적도 궤도** 로 보고 지구 자전을 빼 준다
    (ω ← ω_sat − ω_지구). 정지궤도에서는 이 차가 정확히 0 이 되어
    도플러가 사라진다 — 정지궤도의 뜻이 바로 그것이다. 저궤도 군집은
    대개 극궤도에 가까워 자전의 몫이 작으므로 기본값은 꺼 둔다.
    """
    _check_alt(alt_km)
    r = EARTH_R_KM * 1000.0
    a = (EARTH_R_KM + alt_km) * 1000.0
    w = speed_ms(alt_km) / a
    if earth_rotation:
        w -= EARTH_RATE
    th = math.radians(theta_deg)
    d = math.sqrt(r * r + a * a - 2.0 * r * a * math.cos(th))
    if d == 0:
        return 0.0
    rate = r * a * w * math.sin(th) / d
    return -rate * fc_hz / (C_KM_MS * 1e6)


def max_doppler_hz(alt_km, fc_hz, earth_rotation=False):
    """한 통과에서 겪는 최대 도플러 — 지평선에 걸릴 때다.

    저궤도 550 km·2 GHz 에서 약 47 kHz 다. 15 kHz 부반송파의 세 배라,
    보정하지 않으면 직교가 통째로 무너진다. NTN 이 위성 궤도력을
    내려보내 단말이 미리 보정하게 한 까닭이 이것이다.
    """
    th = math.degrees(_horizon_angle_rad(alt_km))
    return abs(doppler_hz(alt_km, fc_hz, -th, earth_rotation))


# ── NTN ───────────────────────────────────────────────────────────


def ta_window_ms(alt_km, el_min_deg, el_max_deg=90.0):
    """빔 안에서 왕복 지연이 오가는 범위 [ms].

    지상 셀에서는 이 폭이 셀 반지름으로 정해져 수십 μs 지만, 위성에서는
    ms 단위다. 그래서 NR 의 타이밍 어드밴스 값 범위로는 모자라고,
    Rel-17 NTN 이 공통 TA 를 따로 두었다.
    """
    hi = 2.0 * one_way_delay_ms(alt_km, el_min_deg)
    lo = 2.0 * one_way_delay_ms(alt_km, el_max_deg)
    return lo, hi


def visibility_s(alt_km, el_min_deg):
    """천정 통과에서 최소 앙각 위로 보이는 시간 [s].

    저궤도에서는 몇 분뿐이다. 그래서 지상 이동이 없어도 위성이 바뀌는
    핸드오버가 끊임없이 일어난다 — 지상망과 가장 다른 점이다.
    """
    g = math.radians(central_angle_deg(alt_km, el_min_deg))
    w = speed_ms(alt_km) / ((EARTH_R_KM + alt_km) * 1000.0)
    return 2.0 * g / w
