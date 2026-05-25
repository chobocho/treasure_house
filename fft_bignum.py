"""
============================================================
FFT 기반 큰 수 곱셈 (Big Integer Multiplication via FFT)
============================================================

표준 라이브러리만 사용한 순수 파이썬 구현.
복잡도: O(n log n), n = 두 입력의 자릿수 합.

알고리즘 개요:
    1) 두 큰 수를 자리수 배열(다항식의 계수)로 변환
    2) FFT로 주파수 도메인으로 이동
    3) 점별 곱셈 (이 부분이 핵심 — 합성곱이 단순 곱셈으로!)
    4) 역 FFT로 시간 도메인 복귀 → 합성곱 결과
    5) 자리올림 처리하여 최종 자리 배열 완성

주의:
    부동소수점 연산이므로 매우 큰 수(수만 자리 이상)에서는
    오차가 누적될 수 있음. 실전에서는 NTT(정수 변환)를 고려.
"""

from cmath import exp, pi
from typing import List

Complex = complex


def fft(a: List[Complex], invert: bool = False) -> None:
    """
    제자리(in-place) 반복형 Cooley-Tukey FFT.

    Args:
        a:      길이가 2의 거듭제곱인 복소수 배열. 직접 수정됨.
        invert: True면 역 FFT 수행 (계산 후 N으로 나눠줌).

    동작 원리:
        1) 비트 반전 순열로 자리를 재배치
           (분할정복의 leaf 노드 순서로 미리 정렬해두는 것)
        2) 길이 2 → 4 → 8 → ... 로 짝지어 'butterfly' 연산을 수행

    재귀형보다 빠르고 메모리도 절약됨 (스택 사용 없음).
    """
    n = len(a)
    if n <= 1:
        return

    # ── 1단계: 비트 반전 순열 ──────────────────────────────
    # 예: n=8일 때 인덱스 1(001) ↔ 4(100), 3(011) ↔ 6(110) ...
    # 이렇게 섞어두면 이후 butterfly가 자연스러운 순서로 적용됨.
    j = 0
    for i in range(1, n):
        bit = n >> 1
        # j의 최상위 비트부터 내려가며 적절한 위치를 찾음
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            a[i], a[j] = a[j], a[i]

    # ── 2단계: 길이 length = 2, 4, 8, ..., n 의 butterfly 반복 ──
    length = 2
    while length <= n:
        # 회전인자 ω = e^(±2πi/length). invert면 부호 반대.
        angle = (2 * pi / length) * (1 if invert else -1)
        wlen = exp(1j * angle)

        # 길이 length 짜리 블록을 n/length 개 만큼 순회
        for i in range(0, n, length):
            w = 1 + 0j  # 블록 시작 시 ω⁰ = 1
            half = length >> 1
            for k in range(half):
                # butterfly: 두 점에서 합/차를 동시에 만들기
                u = a[i + k]
                v = a[i + k + half] * w
                a[i + k] = u + v
                a[i + k + half] = u - v
                w *= wlen  # ω를 한 칸 회전 (다음 주파수)
        length <<= 1  # 다음 라운드는 두 배 길이

    # ── 3단계: 역변환이면 N으로 나눔 ─────────────────────
    if invert:
        for i in range(n):
            a[i] /= n


def multiply_bignum(num1: str, num2: str) -> str:
    """
    두 큰 수를 문자열로 받아 곱한 결과를 문자열로 반환.

    예제:
        >>> multiply_bignum("123", "456")
        '56088'
        >>> multiply_bignum("12345678901234567890", "98765432109876543210")
        '1219326311370217952237463801111263526900'
        >>> multiply_bignum("-12345", "678")
        '-8370110'
    """
    # ── 음수 부호 처리 ──────────────────────────────────
    sign = 1
    if num1.startswith('-'):
        sign = -sign
        num1 = num1[1:]
    if num2.startswith('-'):
        sign = -sign
        num2 = num2[1:]

    # 앞자리 0 제거 (선택적 - 결과의 정확성에는 영향 없음)
    num1 = num1.lstrip('0') or '0'
    num2 = num2.lstrip('0') or '0'

    # 어느 한쪽이라도 0이면 결과는 0
    if num1 == '0' or num2 == '0':
        return '0'

    # ── 1단계: 자리수 → 계수 배열 (LSB 먼저: a[0]이 1의 자리) ──
    # 문자열 "1234" → [4, 3, 2, 1]
    a = [int(c) for c in reversed(num1)]
    b = [int(c) for c in reversed(num2)]

    # ── 결과의 최대 길이 = len(a) + len(b). ──
    # FFT는 2의 거듭제곱 길이가 필요하므로 그 이상으로 패딩.
    result_len = len(a) + len(b)
    n = 1
    while n < result_len:
        n <<= 1  # 가장 가까운 2의 거듭제곱

    # 복소수 배열로 변환하고 0으로 패딩
    fa: List[Complex] = [complex(x, 0) for x in a] + [0j] * (n - len(a))
    fb: List[Complex] = [complex(x, 0) for x in b] + [0j] * (n - len(b))

    # ── 2단계: 두 배열을 FFT로 주파수 도메인으로 ──
    fft(fa, invert=False)
    fft(fb, invert=False)

    # ── 3단계: 점별 곱셈 ──
    # 주파수 도메인에서의 곱셈 = 시간 도메인에서의 합성곱
    # (이것이 합성곱 정리의 마법)
    for i in range(n):
        fa[i] *= fb[i]

    # ── 4단계: 역 FFT로 시간 도메인 복귀 (= 합성곱 결과) ──
    fft(fa, invert=True)

    # ── 5단계: 실수부를 반올림하여 정수 자릿값으로 ──
    # 부동소수점 오차로 인해 약간의 허수부가 남을 수 있지만 무시
    digits = [round(x.real) for x in fa]

    # ── 자리올림 처리: 각 자리에서 10 이상이면 위로 올림 ──
    carry = 0
    for i in range(len(digits)):
        digits[i] += carry
        carry, digits[i] = divmod(digits[i], 10)
    # 남은 올림이 있다면 끝에 붙임
    while carry > 0:
        digits.append(carry % 10)
        carry //= 10

    # 앞쪽(상위 자리)의 0 제거
    while len(digits) > 1 and digits[-1] == 0:
        digits.pop()

    # 출력: 상위 자리부터 거꾸로 모음
    result = ''.join(str(d) for d in reversed(digits))
    return ('-' if sign == -1 else '') + result


# ════════════════════════════════════════════════════════
#  테스트
# ════════════════════════════════════════════════════════
if __name__ == "__main__":
    import time
    import random

    print("=" * 60)
    print(" FFT 큰 수 곱셈 — 정확성 테스트")
    print("=" * 60)
    tests = [
        ("0", "12345", "0"),
        ("1", "1", "1"),
        ("7", "8", "56"),
        ("9", "9", "81"),
        ("123", "456", "56088"),
        ("9999", "9999", "99980001"),
        ("99999999", "99999999", "9999999800000001"),
        ("12345678901234567890",
         "98765432109876543210",
         "1219326311370217952237463801111263526900"),
        ("-12345", "678", "-8369910"),
        ("-7", "-8", "56"),
    ]
    for a, b, expected in tests:
        got = multiply_bignum(a, b)
        flag = "✓" if got == expected else "✗"
        # 결과가 너무 길면 양 끝만 표시
        disp = got if len(got) <= 50 else f"{got[:20]}...{got[-20:]}"
        print(f"  {flag} {a[:15]} × {b[:15]} = {disp}")
        if got != expected:
            print(f"     기대값: {expected}")

    print("\n" + "=" * 60)
    print(" 성능 비교 (FFT vs 파이썬 내장 int 곱셈)")
    print("=" * 60)
    random.seed(42)
    for length in [50, 100, 500, 1000]:
        big_a = ''.join(random.choices('123456789', k=1)) + \
                ''.join(random.choices('0123456789', k=length - 1))
        big_b = ''.join(random.choices('123456789', k=1)) + \
                ''.join(random.choices('0123456789', k=length - 1))

        t0 = time.perf_counter()
        c_fft = multiply_bignum(big_a, big_b)
        t1 = time.perf_counter()
        c_native = str(int(big_a) * int(big_b))
        t2 = time.perf_counter()

        ok = "✓" if c_fft == c_native else "✗"
        print(f"  {length:>4}자리 × {length:>4}자리:  "
              f"FFT {(t1-t0)*1000:>7.2f} ms  |  "
              f"내장 {(t2-t1)*1000:>7.2f} ms  {ok}")

    print("\n[참고] 파이썬 내장 int는 C로 구현된 카라츠바/PGM이라 매우 빠릅니다.")
    print("       위 FFT는 순수 파이썬이라 더 느리지만, 알고리즘 자체는 더 적은")
    print("       '연산 횟수'를 사용합니다. C/Rust로 작성하면 큰 수에서 역전됩니다.")
