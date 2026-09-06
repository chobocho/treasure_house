# -*- coding: utf-8 -*-
"""16.16 고정소수점 — SPEC §2.

   여기 있는 함수들은 파이썬만 생각하면 전부 한 줄이면 끝난다.
   그런데도 이렇게 쪼개 놓은 이유는 루아와 타입스크립트 때문이다.
   두 언어에서 정수는 배정밀도 부동소수점(가수 53비트)에 얹혀 있고,
   `>>` 는 32비트로 잘린다. 그래서 이 모듈은
     · 시프트를 쓰지 않고 (floordiv 로만)
     · 곱셈 중간값이 2^53 을 넘지 않게 쪼개서
   계산한다. 파이썬에서 손해를 보더라도 세 언어가 같은 답을 내는 쪽을 골랐다.
"""

FP_BITS = 16
FP_ONE = 65536


def floordiv(a, b):
    """b > 0 일 때 -무한대 방향 내림. 파이썬의 // 가 이미 그렇다."""
    return a // b


def fmod(a, b):
    """항상 0 <= 결과 < b. 파이썬의 % 가 이미 그렇다."""
    return a % b


def ashr(a, k):
    """산술 우시프트 = 2^k 로 내림 나눗셈. 음수에서도 내림이다."""
    return a // (1 << k)


def fp(n):
    return n * FP_ONE


def fp_floor(x):
    return x // FP_ONE


def fp_round(x):
    return (x + FP_ONE // 2) // FP_ONE


def fp_frac(x):
    return x % FP_ONE


def fp_mul(a, b):
    """floor(a*b / 65536). a 를 상·하위 16비트로 쪼개 중간값을 2^53 아래로 묶는다.

       a = ah*2^16 + al 이므로 a*b = ah*b*2^16 + al*b 이고,
       2^16 으로 내림 나누면 ah*b 가 정수라 그대로 빠져나온다.
       |a| < 2^31, |b| < 2^37 이면 |ah*b| < 2^52, |al*b| < 2^53. (정리 2.1)
    """
    ah = a // FP_ONE
    al = a - ah * FP_ONE                      # 0 <= al < 65536
    return ah * b + (al * b) // FP_ONE


def fp_mulr(a, b):
    """반올림 곱. 광원 감쇠처럼 한쪽으로 쏠리면 곤란한 곳에만 쓴다."""
    ah = a // FP_ONE
    al = a - ah * FP_ONE
    return ah * b + (al * b + FP_ONE // 2) // FP_ONE


def fp_div(a, b):
    """floor(a*65536 / b). |a| < 2^37 이면 a*65536 이 2^53 미만이다."""
    return (a * FP_ONE) // b


def isqrt(n):
    """floor(sqrt(n)). 뉴턴 반복 — 단조 감소라 반드시 멈춘다. (정리 2.2)

       O(log log n) 반복, 나눗셈만 쓴다. math.isqrt 를 쓰지 않는 이유는
       루아·타입스크립트에 그런 함수가 없어서다. 세 언어가 같은 코드를 돈다.
    """
    if n < 2:
        return n
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


def fp_sqrt(x):
    return isqrt(x * FP_ONE)


# 알파 맥스 플러스 베타 민 — 최소최대오차 최적 계수를 1024배 해 반올림한 것.
# 도스 시절 거리 비교에 sqrt 를 부르지 않으려고 쓰던 근사다.
OCT_A = 983
OCT_B = 407


def oct_dist(dx, dy):
    """sqrt(dx^2+dy^2) 의 정수 근사. 곱셈 두 번과 나눗셈 한 번."""
    ax = dx if dx >= 0 else -dx
    ay = dy if dy >= 0 else -dy
    hi = ax if ax > ay else ay
    lo = ay if ax > ay else ax
    return (OCT_A * hi + OCT_B * lo) // 1024


# ---------------------------------------------------------------- CORDIC (SPEC §2.6)
N_ITER = 20
GUARD = 8
# atan(2^-i) 를 brad(한 바퀴=256) 로 환산해 16.16 으로 반올림한 값.
# 첫 항이 32*65536 인 것은 45도가 정확히 32 brad 라서다.
ATAN_BRAD = [2097152, 1238021, 654136, 332050, 166669, 83416, 41718, 20860,
             10430, 5215, 2608, 1304, 652, 326, 163, 81, 41, 20, 10, 5]
# round(65536 * 2^GUARD / prod sqrt(1 + 4^-i))
K_INV = 10188014


def cordic(theta):
    """16.16 brad 각도 -> (cos, sin) 16.16.

       가드 8비트를 안에서 들고 다니다가 끝에서 반올림해 버린다.
       그 여덟 비트가 없으면 스무 번의 내림이 쌓여 오차가 5까지 벌어진다.
    """
    t = theta % (256 * FP_ONE)
    quad = t // (64 * FP_ONE)
    t -= quad * 64 * FP_ONE
    x, y, z = K_INV, 0, t
    for i in range(N_ITER):
        d = 1 if z >= 0 else -1
        nx = x - d * (y // (1 << i))
        ny = y + d * (x // (1 << i))
        z -= d * ATAN_BRAD[i]
        x, y = nx, ny
    x = (x + 128) // 256
    y = (y + 128) // 256
    if quad == 0:
        return (x, y)
    if quad == 1:
        return (-y, x)
    if quad == 2:
        return (-x, -y)
    return (y, -x)


def _build_trig():
    c = [0] * 256
    s = [0] * 256
    for a in range(256):
        c[a], s[a] = cordic(a * FP_ONE)
    return c, s


COS, SIN = _build_trig()


def _nib_table():
    t = [0] * 256
    for a in range(16):
        for b in range(16):
            r = 0
            p = 1
            x, y = a, b
            for _ in range(4):
                if x % 2 != y % 2:
                    r += p
                x //= 2
                y //= 2
                p *= 2
            t[a * 16 + b] = r
    return t


NIB_XOR = _nib_table()


def xor8(a, b):
    """8비트 배타적 논리합. 니블 표 두 번이면 끝난다 — 256칸짜리 표 하나로 족하다."""
    return NIB_XOR[(a // 16) * 16 + (b // 16)] * 16 + NIB_XOR[(a % 16) * 16 + (b % 16)]


def xor16(a, b):
    """표 없이 만든 16비트 배타적 논리합.

       루아 5.1 에는 비트 연산자가 없다(luajit 의 bit 라이브러리는 love 밖에서
       늘 있는 것이 아니다). 나눗셈만으로 만들면 세 언어가 같은 코드를 쓴다.
       한 비트씩 16번 — O(16), 표를 만들 필요도 없다.
    """
    r = 0
    p = 1
    for _ in range(16):
        ba = a % 2
        bb = b % 2
        if ba != bb:
            r += p
        a = a // 2
        b = b // 2
        p *= 2
    return r
