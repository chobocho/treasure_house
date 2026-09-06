# -*- coding: utf-8 -*-
"""주사위와 전투 — SPEC §10.

   분포는 합성곱으로 정확히 센다. 몬테카를로가 아니라 경우의 수다 —
   그래야 기대값과 분산을 정수 항등식으로 검사할 수 있다.
"""


def dist(n, m):
    """n개의 m면 주사위 합 분포. dist(n,m)[s] = 합이 s 인 경우의 수.

       c_{k} = c_{k-1} * (1면부터 m면까지) 의 합성곱을 n번. O(n^2 * m) 시간.
       총합은 정확히 m^n 이어야 한다.
    """
    c = [1]
    for _ in range(n):
        c2 = [0] * (len(c) + m)
        for s in range(len(c)):
            v = c[s]
            if v:
                for f in range(1, m + 1):
                    c2[s + f] += v
        c = c2
    return c


def roll(r, n, m):
    """실제 굴림. 난수 소비 순서가 명세의 일부다."""
    t = 0
    for _ in range(n):
        t += r.next() % m + 1
    return t


def to_hit(atk, dfn):
    """1d20 이 이 값 이상이면 명중."""
    return 11 + dfn - atk


def p_hit(atk, dfn):
    """20면 중 명중하는 눈의 수. 1은 언제나 실패, 20은 언제나 성공."""
    v = 21 - to_hit(atk, dfn)
    if v < 1:
        return 1
    if v > 19:
        return 19
    return v


def attack(r, atk, dfn, dn, dm, dbonus, armor):
    """(명중 여부, 피해, 굴림). 빗나가면 피해 0.

       난수는 명중 굴림 한 번, 그리고 명중했을 때만 피해 굴림 dn번을 쓴다.
       빗나갔을 때 피해 굴림을 건너뛰는 것까지 명세다 — 안 그러면 난수 흐름이 갈린다.
    """
    d20 = r.next() % 20 + 1
    if d20 == 1:
        return (False, 0, d20)
    if d20 != 20 and d20 < to_hit(atk, dfn):
        return (False, 0, d20)
    dmg = roll(r, dn, dm) + dbonus - armor
    if dmg < 1:
        dmg = 1
    return (True, dmg, d20)


def xp_to_next(lv):
    """다음 레벨까지 필요한 경험치. 2차식이라 후반이 완만하게 무거워진다."""
    return 20 * lv * lv + 30 * lv
