# -*- coding: utf-8 -*-
"""cellular — 셀을 쪼개고, 주파수를 되쓰고, 회선을 몇 개 둘지 정하기.

   1947년 벨 연구소의 메모 한 장이 이 모듈 전체다. **송신 전력을 줄여
   서비스 구역을 작게 만들면, 충분히 떨어진 곳에서 같은 주파수를 다시
   쓸 수 있다.** 그러면 주파수를 더 받지 않고도 가입자를 늘릴 수 있다.

   그 착상을 숫자로 만들면 셋이 나온다.

     · **재사용 패턴** — 육각 격자에서 같은 주파수를 쓰는 셀 사이의
       거리는 √(3N)·R 이다. N 은 클러스터 크기이고 i²+ij+j² 꼴만 된다.
     · **SIR** — 재사용 거리가 정해지면 같은 채널 간섭이 정해진다.
       N 을 키우면 깨끗해지지만 셀마다 쓸 채널이 준다. 이 맞바꿈이
       셀 설계의 전부다.
     · **얼랑** — 회선을 몇 개 둘지. 가입자가 늘 다 쓰는 것이 아니므로
       회선은 가입자보다 훨씬 적어도 된다. 그 '훨씬' 을 세는 식이다.
"""
import math
import random


# ── 재사용 ────────────────────────────────────────────────────────


def cluster_sizes(maxi):
    """쓸 수 있는 클러스터 크기 N = i² + ij + j².

    아무 수나 되는 것이 아니다 — 육각 격자를 빈틈없이 덮으려면 이 꼴
    이어야 한다. 그래서 4 는 되고 5 는 안 된다.
    """
    out = set()
    for i in range(maxi + 1):
        for j in range(maxi + 1):
            n = i * i + i * j + j * j
            if n > 0:
                out.add(n)
    return sorted(out)


def _check_cluster(n):
    if n not in cluster_sizes(12):
        raise ValueError('N = i²+ij+j² 꼴이 아니다: %s' % n)


def reuse_ratio(n):
    """재사용 거리비 D/R = √(3N). 육각 기하에서 바로 나온다."""
    _check_cluster(n)
    return math.sqrt(3.0 * n)


def sir_db(n, gamma, interferers=6):
    """같은 채널 간섭 대비 신호비.

        SIR = (D/R)^γ / i₀ = (√(3N))^γ / i₀

    첫 고리의 같은 채널 셀이 여섯이므로 i₀ = 6 이 기본이다. 섹터
    안테나를 쓰면 그중 일부만 보이므로 i₀ 가 준다(3섹터에서 2).
    N=7·γ=4·i₀=6 이 18.7 dB — 아날로그 AMPS 가 요구하던 18 dB 를
    막 넘는 값이고, 그래서 N=7 이 표준이 되었다.
    """
    if interferers < 1:
        raise ValueError('간섭원 수는 1 이상이어야 한다')
    return 10.0 * math.log10(reuse_ratio(n) ** gamma / interferers)


def channels_per_cell(total, n):
    """전체 채널을 클러스터로 나눈 몫. 깨끗함의 값이 여기서 빠진다."""
    _check_cluster(n)
    return total // n


# ── 얼랑 ──────────────────────────────────────────────────────────


def erlang_b(a, n):
    """얼랑 B — 기다릴 수 없는 호가 막힐 확률.

        B(0) = 1,  B(k) = A·B(k−1) / (k + A·B(k−1))

    되부름 대신 이 점화식을 쓰는 까닭: 원래 식에는 A^N/N! 이 들어 있어
    N 이 조금만 커져도 넘침이 난다. 점화식은 0~1 사이 값만 오간다.
    시간 O(N).
    """
    if a < 0 or n < 0:
        raise ValueError('부하와 회선 수는 음수일 수 없다')
    b = 1.0
    for k in range(1, n + 1):
        b = a * b / (k + a * b)
    return b


def erlang_c(a, n):
    """얼랑 C — 기다릴 수 있는 호가 '기다리게 될' 확률.

        C = B / (1 − ρ(1 − B)),  ρ = A/N

    큐가 안정되려면 A < N 이어야 한다. 같은 A·N 에서 C > B 인데,
    막힌 호를 버리지 않고 쌓아 두면 그만큼 대기가 늘기 때문이다.
    """
    if a >= n:
        raise ValueError('A < N 이어야 큐가 안정된다: A=%g N=%d'
                         % (a, n))
    b = erlang_b(a, n)
    rho = a / float(n)
    return b / (1.0 - rho * (1.0 - b))


def offered_load(n, gos, hi=1e6, tol=1e-12):
    """차단률을 gos 로 맞추는 최대 부하 [얼랑]. 이분법으로 푼다.

    얼랑 B 는 A 에 대해 단조 증가하므로 이분법이 언제나 모인다.
    회선을 한 통에 모을수록 회선당 실어 나르는 양이 는다 —
    그 '트렁킹 이득' 을 이 함수로 잰다.
    """
    if not 0 < gos < 1:
        raise ValueError('차단률은 0 과 1 사이여야 한다')
    lo = 0.0
    while hi - lo > tol * max(1.0, hi):
        mid = (lo + hi) / 2.0
        if erlang_b(mid, n) < gos:
            lo = mid
        else:
            hi = mid
    return lo


# ── 핸드오프 ──────────────────────────────────────────────────────


def ping_pong_count(hysteresis_db, seed=1, steps=2000, bias_db=0.0,
                    sigma_db=4.0):
    """히스테리시스를 걸었을 때 남는 핑퐁 핸드오프의 수.

    두 셀의 수신 세기가 비슷한 곳에서는 음영과 페이딩 때문에 순위가
    쉴 새 없이 바뀐다. 그때마다 넘기면 통화가 끊긴다. 그래서
    "지금 셀보다 H dB 이상 좋아야 넘긴다" 는 문턱을 둔다.

    bias_db 는 한쪽이 평균적으로 얼마나 센가다. 크게 주면 경계가
    아니라 셀 한가운데라는 뜻이라 핸드오프가 아예 일어나지 않는다.
    """
    rnd = random.Random(seed)
    cur = 0
    cnt = 0
    a = b = 0.0
    for _ in range(steps):
        a = 0.8 * a + rnd.gauss(0.0, sigma_db * 0.6) + 0.2 * bias_db
        b = 0.8 * b + rnd.gauss(0.0, sigma_db * 0.6)
        lv = [a, b]
        other = 1 - cur
        if lv[other] > lv[cur] + hysteresis_db:
            cur = other
            cnt += 1
    return cnt


# ── 셀 호흡 ───────────────────────────────────────────────────────


def breathing_radius(load, gamma):
    """CDMA 셀의 상대 반지름. 부하가 차면 셀이 줄어든다.

    역방향 잡음 상승은 1/(1−η) 이고(η 는 극한 용량 대비 부하), 그만큼
    경로손실 여유가 준다. 손실이 거리의 γ 제곱이므로 반지름은
    (1−η)^{1/γ} 로 줄어든다.

    FDMA·TDMA 셀은 크기가 고정이지만 CDMA 셀은 숨을 쉰다. 이것이
    셀 설계를 어렵게 만들었고, 동시에 '부드러운 용량' 의 다른 얼굴이다.
    """
    if not 0.0 <= load <= 1.0:
        raise ValueError('부하는 0 과 1 사이여야 한다')
    if gamma <= 0:
        raise ValueError('경로손실 지수는 양수여야 한다')
    return (1.0 - load) ** (1.0 / gamma)
