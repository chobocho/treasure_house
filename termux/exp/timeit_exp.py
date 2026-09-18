# -*- coding: utf-8 -*-
"""timeit_exp.py — 명령을 N번 돌려 걸린 시간의 가운뎃값 (실험 5).

    python3 exp/timeit_exp.py -n 3 -- CMD ARGS…

이름이 timeit.py 가 아닌 까닭: 표준 라이브러리 timeit 을 가린다.
시계는 time.monotonic_ns() — 벽시계는 NTP 가 뒤로 돌릴 수 있다.
가운뎃값을 쓰는 까닭은 폰이 가끔 한 번씩 크게 늦기 때문이다
(백그라운드 앱·열 제한). 이 숫자는 이 기기·그날의 것이라 덱에서는
스냅샷 캡처로만 싣는다(PLAN.md §0.9). O(N × 명령 시간).
"""
import subprocess
import sys
import time


def median(xs):
    s = sorted(xs)
    m = len(s) // 2
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def main(argv):
    if len(argv) < 4 or argv[0] != '-n' or argv[2] != '--':
        print('사용법: timeit_exp.py -n N -- CMD …')
        return 2
    n, cmd = int(argv[1]), argv[3:]
    took = []
    for _ in range(n):
        t0 = time.monotonic_ns()
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        took.append(time.monotonic_ns() - t0)
    print('runs=%d median_ms=%.3f' % (n, median(took) / 1e6))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
