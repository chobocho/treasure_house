# -*- coding: utf-8 -*-
"""원 마스크 — 시야·스플래시·자원 스탬프가 전부 이것을 쓴다 (SPEC §6).

   고전 미드포인트 원 알고리즘은 여기에 쓰지 않는다. 그것은 *외곽선*을 그리는
   알고리즘이라 참원에 가장 가까운 점을 고르고, 그 점이 원 안이라는 보장이 없다.
   r=2 에서 (2,1) 을 찍는데 2²+1² = 5 > 4 다. 시야 마스크로 쓰면 격자점 개수가
   가우스 원 문제의 값과 어긋난다 — 골든을 처음 만들 때 그 검사가 잡았다.
"""

_span_cache = {}
_off_cache = {}


def spans(r):
    """span[j] = 행 j 에서 원 안에 드는 최대 |i|. 덧셈과 뺄셈만 쓴다.

       불변식은 t = r² − j² − x² >= 0 이고 x 가 그 조건을 만족하는 최대값이다.
       x 는 결코 늘지 않으므로 전체 비용이 O(r) 이다 (SPEC 정리 6.2).
    """
    if r in _span_cache:
        return _span_cache[r]
    out = [0] * (r + 1)
    out[0] = r
    x, t = r, 0
    for j in range(1, r + 1):
        t -= 2 * (j - 1) + 1
        while t < 0:
            t += 2 * x - 1
            x -= 1
        out[j] = x
    _span_cache[r] = out
    return out


def offsets(r):
    """(dx, dy) 목록. dy 오름차순, 같은 dy 안에서 dx 오름차순으로 **고정**한다.

       순서가 다르면 참조 카운트 결과는 같지만 이벤트 로그의 순서가 달라지고,
       그 차이가 상태 해시를 가른다(SPEC §6.3).
    """
    if r in _off_cache:
        return _off_cache[r]
    sp = spans(r)
    out = []
    for j in range(-r, r + 1):
        w = sp[j if j >= 0 else -j]
        for i in range(-w, w + 1):
            out.append((i, j))
    _off_cache[r] = out
    return out


def count(r):
    return len(offsets(r))


def in_disc(dx, dy, r):
    return dx * dx + dy * dy <= r * r


def midpoint_outline(r):
    """고전 미드포인트 '외곽선' — 엔진은 쓰지 않는다. 6부의 대조용으로만 있다."""
    pts = set()
    x, y, d = r, 0, 1 - r
    while y <= x:
        for a, b in ((x, y), (y, x), (-x, y), (-y, x),
                     (x, -y), (y, -x), (-x, -y), (-y, -x)):
            pts.add((a, b))
        y += 1
        if d < 0:
            d += 2 * y + 1
        else:
            x -= 1
            d += 2 * (y - x) + 1
    return pts
