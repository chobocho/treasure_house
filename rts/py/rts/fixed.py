# -*- coding: utf-8 -*-
"""16.16 고정소수점 · 정수 기하 · 거리 척도 — SPEC §1, §2.

   여기 있는 함수 대부분은 파이썬만 생각하면 한 줄이면 끝난다. 그런데도
   이렇게 쪼개 놓은 이유는 루아 5.1 과 타입스크립트 때문이다. 두 언어에서
   정수는 배정밀도 부동소수점(가수 53비트)에 얹혀 있고, 자바스크립트의 `>>` 는
   32비트로 잘린다. 그래서 이 모듈은
     · 시프트를 쓰지 않고 (floordiv 로만)
     · 곱셈 중간값이 2^53 을 넘지 않게 쪼개서
     · 비트 연산자 대신 산술로
   계산한다. 파이썬에서 손해를 보더라도 세 언어가 같은 답을 내는 쪽을 골랐다.

   이 파일은 다른 모듈을 하나도 참조하지 않는다. 나머지 전부가 여기에 기댄다.
"""

FP_BITS = 16
FP_ONE = 65536
FP_HALF = 32768
FP_DIAG = 46341                      # 1/√2 의 16.16 반올림 (46340.950…)
FP_SQRT2M1 = 27146                   # √2−1 의 16.16 반올림 (27145.951…)

D_STRAIGHT = 10
D_DIAG = 14

# SPEC §2.7 — 화면 좌표이므로 y 는 아래로 증가한다.
DX = [0, 1, 1, 1, 0, -1, -1, -1]
DY = [-1, -1, 0, 1, 1, 1, 0, -1]
DNAME = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
DCOST = [D_STRAIGHT, D_DIAG, D_STRAIGHT, D_DIAG,
         D_STRAIGHT, D_DIAG, D_STRAIGHT, D_DIAG]


# ── SPEC §1 정수 연산 규약 ──────────────────────────────────────────────────
def floordiv(a, b):
    """b > 0 일 때 -무한대 방향 내림. 파이썬의 // 가 이미 그렇다."""
    return a // b


def fmod(a, b):
    """항상 0 <= 결과 < b. 파이썬의 % 가 이미 그렇다."""
    return a % b


def ashr(a, k):
    """산술 우시프트 = 2^k 로 내림 나눗셈. 음수에서도 내림이다."""
    return a // (1 << k)


def ashl(a, k):
    return a * (1 << k)


# ── SPEC §1.1 비트 연산의 산술 대체 ─────────────────────────────────────────
def bit(v, k):
    """k번째 비트 — 시프트도 AND 도 쓰지 않는다."""
    return (v // (1 << k)) % 2


def setbit(v, k):
    return v + (1 - bit(v, k)) * (1 << k)


def clrbit(v, k):
    return v - bit(v, k) * (1 << k)


def xor8(x, y):
    """바이트 두 개의 XOR — 여덟 번 도는 것이 전부다.

       루아 5.1 에는 비트 연산자가 없다. LuaJIT 의 bit 모듈은 LÖVE 에서도
       쓸 수 있지만 Lua 5.1 표준이 아니므로 쓰지 않기로 했다(SPEC §1.1).
    """
    r = 0
    p = 1
    for _ in range(8):
        if (x % 2) != (y % 2):
            r += p
        x //= 2
        y //= 2
        p *= 2
    return r


def xor_low8(h, b):
    """32비트 값의 하위 8비트에만 XOR — FNV-1a(SPEC §18.4)가 쓴다."""
    return h - h % 256 + xor8(h % 256, b)


# ── SPEC §2.1 변환 ──────────────────────────────────────────────────────────
def fp(n):
    return n * FP_ONE


def fp_floor(x):
    return x // FP_ONE


def fp_round(x):
    return (x + FP_HALF) // FP_ONE


def fp_frac(x):
    return x % FP_ONE


# ── SPEC §2.3 곱셈 (분할 곱) ────────────────────────────────────────────────
def fp_mul(a, b):
    """floor(a*b / 65536). a 를 상·하위로 쪼개 중간값을 2^53 아래로 붙든다.

       a = ah·2^16 + al 이므로 a·b/2^16 = ah·b + al·b/2^16 이고,
       첫 항이 정수라 바닥함수 밖으로 나온다 (SPEC 정리 2.1).
    """
    ah = a // FP_ONE
    al = a % FP_ONE
    return ah * b + (al * b) // FP_ONE


def fp_div(a, b):
    """floor(a*65536 / b). b == 0 은 호출자의 버그이므로 그냥 터진다."""
    if b == 0:
        raise ZeroDivisionError('fp_div: b == 0')
    return (a * FP_ONE) // b


# ── SPEC §2.5 정수 제곱근 ───────────────────────────────────────────────────
def isqrt(n):
    """뉴턴 반복. 초기값과 종료 조건까지 명세다 — 세 언어가 같은 횟수를 돈다."""
    if n < 2:
        return n
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x


def fp_sqrt(x):
    """고정소수점 제곱근. x < 2^31 이므로 x*65536 < 2^47 — 안전하다."""
    return isqrt(x * FP_ONE)


# ── SPEC §2.6 거리 척도 ─────────────────────────────────────────────────────
def _mxmn(dx, dy):
    ax = dx if dx >= 0 else -dx
    ay = dy if dy >= 0 else -dy
    return (ax, ay) if ax >= ay else (ay, ax)


def d1(dx, dy):
    """L1 (맨해튼) — 4방향 이동의 정확한 걸음 수."""
    return (dx if dx >= 0 else -dx) + (dy if dy >= 0 else -dy)


def dinf(dx, dy):
    """L∞ (체비셰프) — 8방향 이동의 정확한 걸음 수. 사거리 판정은 전부 이것."""
    mx, _mn = _mxmn(dx, dy)
    return mx


def d83(dx, dy):
    """옥타일 8분의 3 근사. √2−1 = 0.41421 을 3/8 로 바꾼 도스식 값."""
    mx, mn = _mxmn(dx, dy)
    return mx + (3 * mn) // 8


def doct(dx, dy):
    """경로 비용 단위의 옥타일 거리. 직선 10, 대각 14 — A* 휴리스틱이 이것이다."""
    mx, mn = _mxmn(dx, dy)
    return D_STRAIGHT * mx + (D_DIAG - D_STRAIGHT) * mn


def dab(dx, dy):
    """alpha-max-beta-min. 마지막 반올림(+32768)이 없으면 dab(1,0) = 0 이 된다.

       거리 1 이 0 으로 나오면 사거리 판정과 타깃 선택이 통째로 무너진다.
       골든 벡터를 처음 만들 때 오차 −100 % 로 드러난 자리다(SPEC §2.6).
    """
    mx, mn = _mxmn(dx, dy)
    return (62943 * mx + 26072 * mn + FP_HALF) // FP_ONE


# ── SPEC §2.7 8방향 판별 ────────────────────────────────────────────────────
def atan8(dx, dy):
    """비교만으로 8방향을 고른다. 나눗셈도 삼각함수도 없다.

       경계는 22.5°이고 tan 22.5° = √2−1 = 0.414214 다. 5/12 = 0.416667 로
       바꾸면 경계각이 22.62° — 0.12° 넓어질 뿐이다. √2−1 의 연분수 수렴분수가
       1/2, 2/5, 5/12, 12/29 … (펠 수의 비)이므로 5/12 는 우연이 아니다.
    """
    if dx == 0 and dy == 0:
        return 2                                   # 규약: 정지 상태는 E 를 본다
    ax = dx if dx >= 0 else -dx
    ay = dy if dy >= 0 else -dy
    mx, mn = (ax, ay) if ax >= ay else (ay, ax)
    diag = 12 * mn > 5 * mx
    if ax >= ay:                                   # 동서가 주축
        if dx > 0:
            if diag:
                return 1 if dy < 0 else 3
            return 2
        if diag:
            return 7 if dy < 0 else 5
        return 6
    if dy < 0:                                     # 남북이 주축
        if diag:
            return 1 if dx > 0 else 7
        return 0
    if diag:
        return 3 if dx > 0 else 5
    return 4
