# -*- coding: utf-8 -*-
"""channel — 전파가 기지국에서 단말까지 가는 동안 겪는 일.

   세 층으로 나뉜다. 이 순서가 곧 셀 설계자가 생각하는 순서다.

     1. **경로손실** — 거리가 멀면 약해진다. 자유공간·로그거리·
        오쿠무라-하타·COST-231·3GPP TR 38.901 UMa/UMi
     2. **음영(shadowing)** — 건물 뒤에 가리면 더 약해진다. 로그정규
     3. **다중경로 페이딩** — 여러 길로 온 파가 겹쳐 순간마다 출렁인다.
        레일리·라이시안, 클라크 도플러 스펙트럼, 탭 지연선

   1·2 는 dB 로 더하고 빼는 '평균' 이야기이고, 3 은 '순간' 이야기다.
   설계는 1·2 로 하고, 성능은 3 으로 갈린다.
"""
import math
import random

C = 299792458.0        # 빛의 속도 [m/s]


# ── 베셀 함수 ─────────────────────────────────────────────────────


def j0(x, steps=400):
    """제1종 0차 베셀 함수. J₀(x) = (1/π)∫₀^π cos(x sin θ) dθ.

    급수 대신 적분을 심프슨 법으로 푼다. 이 책에서 J₀ 를 쓰는 곳은
    클라크 스펙트럼의 자기상관 하나뿐이고 인수가 크지 않아서,
    짧고 틀릴 데 없는 쪽을 골랐다. 시간 O(steps).
    """
    x = abs(x)                      # J₀ 는 우함수다
    h = math.pi / steps
    s = 0.0
    for i in range(steps + 1):
        t = i * h
        w = 1.0 if i in (0, steps) else (4.0 if i % 2 else 2.0)
        s += w * math.cos(x * math.sin(t))
    return s * h / 3.0 / math.pi


# ── 경로손실 ──────────────────────────────────────────────────────


def fspl_db(d_m, f_hz):
    """자유공간 경로손실. 20·log₁₀(4πd/λ).

    거리가 두 배면 6 dB, 주파수가 두 배여도 6 dB 다. 뒤쪽 6 dB 는
    파장이 짧아져 수신 안테나의 유효 면적이 줄기 때문이지, 공기가
    높은 주파수를 더 먹어서가 아니다 — 자주 헷갈리는 자리다.
    """
    if d_m <= 0 or f_hz <= 0:
        raise ValueError('거리와 주파수는 양수여야 한다')
    return 20.0 * math.log10(4.0 * math.pi * d_m * f_hz / C)


def log_distance_db(d_m, d0_m, f_hz, n):
    """로그거리 모형.

    기준 거리 d₀ 의 자유공간 손실에 기울기 n 을 얹는다.

    PL(d) = FSPL(d₀) + 10·n·log₁₀(d/d₀)

    n 은 실측으로 정하는 값이다(도심 2.7~3.5, 실내 1.6~1.8, 차폐 4~6).
    """
    if d_m < d0_m:
        raise ValueError('d 는 기준 거리 이상이어야 한다')
    return fspl_db(d0_m, f_hz) + 10.0 * n * math.log10(d_m / d0_m)


def _hata_a(f_mhz, hm_m, area):
    """단말 높이 보정항 a(h_m). 도시 규모에 따라 식이 다르다."""
    if area == 'urban_large':
        if f_mhz >= 400.0:
            return 3.2 * (math.log10(11.75 * hm_m)) ** 2 - 4.97
        return 8.29 * (math.log10(1.54 * hm_m)) ** 2 - 1.1
    return ((1.1 * math.log10(f_mhz) - 0.7) * hm_m
            - (1.56 * math.log10(f_mhz) - 0.8))


def hata_db(f_mhz, hb_m, hm_m, d_km, area='urban_large'):
    """오쿠무라-하타 모형 (150~1500 MHz).

    오쿠무라가 도쿄에서 잰 곡선을 하타가 식으로 맞춘 것이다. 1G·2G
    셀 설계가 이 식 위에서 이뤄졌다. 적용 범위를 벗어나면 예외를
    던진다 — 범위 밖에서 쓰는 것이 이 식으로 저지르는 가장 흔한
    잘못이다.

    area: 'urban_large' · 'urban_small' · 'suburban' · 'open'
    """
    if not 150.0 <= f_mhz <= 1500.0:
        raise ValueError('하타는 150~1500 MHz 에서만 쓴다: %g' % f_mhz)
    if not 30.0 <= hb_m <= 200.0:
        raise ValueError('기지국 높이는 30~200 m 다: %g' % hb_m)
    if not 1.0 <= hm_m <= 10.0:
        raise ValueError('단말 높이는 1~10 m 다: %g' % hm_m)
    if not 1.0 <= d_km <= 20.0:
        raise ValueError('거리는 1~20 km 다: %g' % d_km)
    kind = 'urban_large' if area == 'urban_large' else 'urban_small'
    a = _hata_a(f_mhz, hm_m, kind)
    urban = (69.55 + 26.16 * math.log10(f_mhz)
             - 13.82 * math.log10(hb_m) - a
             + (44.9 - 6.55 * math.log10(hb_m)) * math.log10(d_km))
    if area in ('urban_large', 'urban_small'):
        return urban
    if area == 'suburban':
        return urban - 2.0 * (math.log10(f_mhz / 28.0)) ** 2 - 5.4
    if area == 'open':
        return (urban - 4.78 * (math.log10(f_mhz)) ** 2
                + 18.33 * math.log10(f_mhz) - 40.94)
    raise ValueError('모르는 지역 종류: %s' % area)


def cost231_db(f_mhz, hb_m, hm_m, d_km, area='urban_large'):
    """COST-231 하타 확장 (1500~2000 MHz).

    PCS·DCS1800·UMTS 대역을 다루려고 하타를 다시 맞춘 것이다. 거리
    기울기 (44.9 − 6.55 log h_b) 는 그대로 두고 상수항과 주파수 항만
    바꿨다 — 그래서 두 식의 '거리에 따른 모양' 이 같다.
    """
    if not 1500.0 <= f_mhz <= 2000.0:
        raise ValueError('COST-231 은 1500~2000 MHz 다: %g' % f_mhz)
    kind = 'urban_large' if area == 'urban_large' else 'urban_small'
    a = _hata_a(f_mhz, hm_m, kind)
    cm = 3.0 if area == 'urban_large' else 0.0
    return (46.3 + 33.9 * math.log10(f_mhz)
            - 13.82 * math.log10(hb_m) - a
            + (44.9 - 6.55 * math.log10(hb_m)) * math.log10(d_km) + cm)


# 3GPP TR 38.901 의 기본 안테나 높이 (표 7.2-1·7.2-2)
_TR_DEFAULT_HBS = {'uma': 25.0, 'umi': 10.0}
_TR_HE = 1.0     # 유효 지면 높이 h_E [m]


def tr38901_db(scen, d2d_m, fc_ghz, los=True, hbs=None, hut=1.5):
    """3GPP TR 38.901 의 UMa·UMi 경로손실 (0.5~100 GHz).

    LTE·NR 의 성능 평가가 전부 이 모형 위에서 이뤄진다. 특징 둘:

      · **3차원 거리** 를 쓴다. 안테나 높이 차가 거리에 들어간다.
      · **분기점(breakpoint)** 이 있다. 가까이서는 거리 지수가 2 에
        가깝고, 지면 반사파와 직접파가 상쇄되기 시작하는 분기점
        너머에서는 4 로 꺾인다.

    NLOS 는 LOS 보다 나쁠 수밖에 없으므로 둘 중 큰 값을 쓴다 —
    규격이 max() 로 적어 둔 까닭이 그것이다.
    """
    scen = scen.lower()
    if scen not in _TR_DEFAULT_HBS:
        raise ValueError('UMa·UMi 만 구현했다: %s' % scen)
    if hbs is None:
        hbs = _TR_DEFAULT_HBS[scen]
    d3d = math.sqrt(d2d_m ** 2 + (hbs - hut) ** 2)
    fc_hz = fc_ghz * 1e9
    dbp = (4.0 * (hbs - _TR_HE) * (hut - _TR_HE) * fc_hz / C)

    if scen == 'uma':
        if d2d_m <= dbp:
            pl_los = (28.0 + 22.0 * math.log10(d3d)
                      + 20.0 * math.log10(fc_ghz))
        else:
            pl_los = (28.0 + 40.0 * math.log10(d3d)
                      + 20.0 * math.log10(fc_ghz)
                      - 9.0 * math.log10(dbp ** 2 + (hbs - hut) ** 2))
        pl_nlos = (13.54 + 39.08 * math.log10(d3d)
                   + 20.0 * math.log10(fc_ghz) - 0.6 * (hut - 1.5))
    else:
        if d2d_m <= dbp:
            pl_los = (32.4 + 21.0 * math.log10(d3d)
                      + 20.0 * math.log10(fc_ghz))
        else:
            pl_los = (32.4 + 40.0 * math.log10(d3d)
                      + 20.0 * math.log10(fc_ghz)
                      - 9.5 * math.log10(dbp ** 2 + (hbs - hut) ** 2))
        pl_nlos = (35.3 * math.log10(d3d) + 22.4
                   + 21.3 * math.log10(fc_ghz) - 0.3 * (hut - 1.5))
    return pl_los if los else max(pl_los, pl_nlos)


def shadowing_db(n, sigma_db, seed=1):
    """로그정규 음영 — dB 영역에서 평균 0, 표준편차 σ 인 정규분포다.

    "로그정규" 라는 이름이 헷갈리지만, 재는 양(전력비)에 로그를
    취했을 때 정규분포라는 뜻이다. 그러니 dB 로는 그냥 정규분포다.
    """
    rnd = random.Random(seed)
    return [rnd.gauss(0.0, sigma_db) for _ in range(n)]


# ── 페이딩 ────────────────────────────────────────────────────────


def rayleigh(n, seed=1):
    """레일리 페이딩 계수. 평균 전력 1 인 복소 가우스.

    직접파가 없고 산란파만 아주 많을 때, 중심극한정리가 I 와 Q 를 각각
    정규분포로 만든다. 그 크기가 레일리 분포다 — pdf 2r·e^{−r²},
    CDF 1 − e^{−r²}. 시험이 이 CDF 를 확인한다.
    """
    rnd = random.Random(seed)
    s = math.sqrt(0.5)
    return [complex(rnd.gauss(0.0, s), rnd.gauss(0.0, s))
            for _ in range(n)]


def rician(n, k, seed=1):
    """라이시안 페이딩. K 는 직접파 전력 대 산란파 전력의 비다.

    총 전력을 1 로 두므로 직접파는 √(K/(K+1)), 산란파는 √(1/(K+1)) 을
    받는다. K=0 이면 정확히 레일리가 되어야 한다 — 시험이 같은 씨앗으로
    두 함수를 맞대어 그것을 확인한다.
    """
    if k < 0:
        raise ValueError('K 는 0 이상이어야 한다')
    rnd = random.Random(seed)
    s = math.sqrt(0.5 / (k + 1.0))
    los = math.sqrt(k / (k + 1.0))
    return [complex(los + rnd.gauss(0.0, s), rnd.gauss(0.0, s))
            for _ in range(n)]


def jakes(n, fd_hz, fs_hz, seed=1, nsin=32):
    """클라크 스펙트럼을 따르는 시간 상관 페이딩 (정현파 합).

    Zheng·Xiao(2003) 판을 쓴다. 각 정현파의 도착각을

        α_m = (2πm − π + θ) / (4M),  θ·φ_m·ψ_m ~ U(−π, π)

    로 두면 자기상관이 J₀(2π f_D τ) 로 모인다 — 클라크가 유도한 바로
    그 값이다. 원래의 제이크스 모형은 위상을 고정해서 여러 채널을
    만들면 서로 상관이 생기는데, 이 판은 그 결함이 없다.

    시간 O(n·M). M=32 면 이 책의 그림에 충분하다.
    """
    if fd_hz < 0 or fs_hz <= 0:
        raise ValueError('도플러는 0 이상, 표본율은 양수여야 한다')
    rnd = random.Random(seed)
    theta = rnd.uniform(-math.pi, math.pi)
    a = [(2.0 * math.pi * (m + 1) - math.pi + theta) / (4.0 * nsin)
         for m in range(nsin)]
    phi = [rnd.uniform(-math.pi, math.pi) for _ in range(nsin)]
    psi = [rnd.uniform(-math.pi, math.pi) for _ in range(nsin)]
    wr = [2.0 * math.pi * fd_hz * math.cos(v) / fs_hz for v in a]
    wi = [2.0 * math.pi * fd_hz * math.sin(v) / fs_hz for v in a]
    scale = 1.0 / math.sqrt(nsin)
    re = [0.0] * n
    im = [0.0] * n
    cos = math.cos
    for m in range(nsin):
        w1, p1, w2, p2 = wr[m], phi[m], wi[m], psi[m]
        for t in range(n):
            re[t] += cos(w1 * t + p1)
            im[t] += cos(w2 * t + p2)
    return [complex(re[t] * scale, im[t] * scale) for t in range(n)]


def level_crossing_rate(h, level, fs_hz):
    """포락선이 주어진 높이를 아래에서 위로 지나는 횟수 [회/초].

    이론값은 √(2π)·f_D·ρ·e^{−ρ²} 이고 ρ 는 실효값 대비 높이다.
    이 값이 '페이딩이 얼마나 빠른가' 를 말한다 — 부호 인터리버의
    깊이도, 전력 제어 주기도 결국 여기서 정해진다.
    """
    cnt = 0
    prev = abs(h[0])
    for v in h[1:]:
        cur = abs(v)
        if prev < level <= cur:
            cnt += 1
        prev = cur
    return cnt / (len(h) / fs_hz)


# ── 시간·주파수 상관 ──────────────────────────────────────────────


def doppler_hz(v_ms, fc_hz, theta_rad=0.0):
    """도플러 편이 — f_D = v·f_c·cos θ / c.

    θ 는 이동 방향과 전파가 오는 방향 사이의 각이다.
    """
    return v_ms * fc_hz * math.cos(theta_rad) / C


def coherence_time_s(fd_hz):
    """간섭성 시간 — 0.423 / f_D (상관 0.5 기준의 흔한 어림).

    이 값보다 짧은 동안에는 채널이 '그대로' 라고 봐도 된다. 파일럿
    간격도, 채널 추정 주기도 이 값을 넘지 않게 잡는다.
    """
    if fd_hz <= 0:
        raise ValueError('도플러가 0 이면 간섭성 시간은 무한이다')
    return 0.423 / fd_hz


def coherence_bw_hz(tau_rms_s):
    """간섭성 대역폭 — 1 / (5·σ_τ) (상관 0.5 기준의 흔한 어림).

    이 폭 안에서는 채널이 평탄하다. OFDM 의 부반송파 간격을 정할 때
    "부반송파 폭 ≪ 간섭성 대역폭" 이 바로 이 값과의 비교다.
    """
    if tau_rms_s <= 0:
        raise ValueError('지연 확산은 양수여야 한다')
    return 1.0 / (5.0 * tau_rms_s)


def rms_delay_spread(taps):
    """탭 [(지연 s, 전력)] 의 실효 지연 확산.

    전력으로 가중한 지연의 표준편차다.
    """
    p = sum(w for _t, w in taps)
    if p <= 0:
        raise ValueError('전력 합이 0 이다')
    m1 = sum(t * w for t, w in taps) / p
    m2 = sum(t * t * w for t, w in taps) / p
    return math.sqrt(max(0.0, m2 - m1 * m1))


def tdl_apply(x, taps, fs_hz, seed=1, fd=0.0):
    """탭 지연선 채널 — 각 탭이 제 나름의 페이딩을 겪는다.

        y[n] = Σ_k √p_k · g_k[n] · x[n − d_k]

    fd 가 0 이면 이득을 1 로 고정한다(정적 다중경로). 0 보다 크면
    탭마다 독립인 제이크스 과정을 쓴다 — 탭이 독립이라는 가정이
    곧 '산란체가 서로 멀리 떨어져 있다' 는 뜻이다.
    """
    n = len(x)
    y = [0j] * n
    for i, (delay, power) in enumerate(taps):
        d = int(round(delay * fs_hz))
        if d >= n:
            continue
        amp = math.sqrt(power)
        if fd > 0:
            g = jakes(n, fd, fs_hz, seed=seed * 1000 + i)
        else:
            g = [1 + 0j] * n
        for t in range(d, n):
            y[t] += amp * g[t] * x[t - d]
    return y
