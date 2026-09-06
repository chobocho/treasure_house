# -*- coding: utf-8 -*-
"""시야·스플래시용 원 마스크를 만든다 — golden/circle.txt

   SPEC §6. 두 가지 방법으로 같은 집합을 만들고 그 둘이 같은지 여기서 먼저 확인한다.
     (가) 정의 그대로:  x² + y² <= r²
     (나) 미드포인트 래스터라이저의 span 표
   엔진은 (나)만 구현하고, 이 파일이 (가)로 검산한 결과와 대조한다.

   실행:  python3 tools/gen_circle.py
"""
import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN = os.path.join(BASE, 'golden')
RMAX = 8


def by_definition(r):
    return set((x, y) for y in range(-r, r + 1) for x in range(-r, r + 1)
               if x * x + y * y <= r * r)


def disc_spans(r):
    """SPEC §6.2 — span[j] = 행 j 의 최대 |i|. 덧셈·뺄셈만 쓴다."""
    span = [0] * (r + 1)
    span[0] = r
    x, t = r, 0                                # 불변식: t = r² − j² − x²
    for j in range(1, r + 1):
        t -= 2 * (j - 1) + 1
        while t < 0:
            t += 2 * x - 1
            x -= 1
        span[j] = x
    return span


def midpoint_outline(r):
    """고전 미드포인트 '외곽선' 알고리즘 — 원 밖의 점을 찍는다. 대조용."""
    pts = set()
    x, y, d = r, 0, 1 - r
    while y <= x:
        for (a, b) in ((x, y), (y, x), (-x, y), (-y, x),
                       (x, -y), (y, -x), (-x, -y), (-y, -x)):
            pts.add((a, b))
        y += 1
        if d < 0:
            d += 2 * y + 1
        else:
            x -= 1
            d += 2 * (y - x) + 1
    return pts


def by_span(r):
    span = disc_spans(r)
    out = set()
    for j in range(-r, r + 1):
        for i in range(-span[abs(j)], span[abs(j)] + 1):
            out.add((i, j))
    return out


def main():
    out = []
    out.append('== 1. 격자점 개수 (가우스 원 문제) ==')
    out.append(' r   개수  span')
    counts = []
    for r in range(1, RMAX + 1):
        a, b = by_definition(r), by_span(r)
        assert a == b, 'r=%d 에서 정의와 미드포인트가 다르다' % r
        counts.append(len(a))
        out.append('%2d %6d  %s' % (r, len(a),
                                    ' '.join(str(v) for v in disc_spans(r))))
    out.append('')
    out.append('N(r) = %s' % ' '.join(str(c) for c in counts))

    out.append('')
    out.append('== 2. 오프셋 목록 (dy 오름차순, 같은 dy 안에서 dx 오름차순) ==')
    for r in range(1, RMAX + 1):
        offs = sorted(by_definition(r), key=lambda p: (p[1], p[0]))
        out.append('r=%d n=%d' % (r, len(offs)))
        line = []
        for (dx, dy) in offs:
            line.append('(%d,%d)' % (dx, dy))
            if len(line) == 10:
                out.append('  ' + ' '.join(line))
                line = []
        if line:
            out.append('  ' + ' '.join(line))

    out.append('')
    out.append('== 3. 고전 미드포인트 외곽선과의 차이 ==')
    out.append('고전 알고리즘은 참원에 가장 가까운 점을 찍는다 — 원 안이라는 보장이 없다.')
    out.append(' r  원 밖으로 찍힌 점')
    for r in range(1, RMAX + 1):
        bad = sorted(p for p in midpoint_outline(r)
                     if p[0] * p[0] + p[1] * p[1] > r * r)
        out.append('%2d  %s' % (r, ' '.join('(%d,%d)' % q for q in bad) or '없음'))

    out.append('')
    out.append('== 4. 그림 ==')
    for r in range(1, RMAX + 1):
        s = by_definition(r)
        out.append('r=%d' % r)
        for y in range(-r, r + 1):
            out.append('  ' + ''.join('#' if (x, y) in s else '.'
                                      for x in range(-r, r + 1)))

    p = os.path.join(GOLDEN, 'circle.txt')
    io.open(p, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('circle.txt  r=1..%d · N(r) = %s' % (RMAX, ' '.join(str(c) for c in counts)))


if __name__ == '__main__':
    main()
