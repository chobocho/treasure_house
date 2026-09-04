# -*- coding: utf-8 -*-
"""전투 판정 — SPEC §7.

   보드 워게임의 CRT(Combat Results Table) 를 그대로 옮긴 것이다. 도스
   워게임의 전투식이 하나같이 '공격력 - 방어력 + 주사위' 꼴인 이유는
   원본이 종이 표였기 때문이다. 표를 코드로 옮기면 곱셈 없이 비교 몇 번이면
   끝나서, 8086 에서도 한 프레임 안에 수십 번 돌릴 수 있었다.
"""

from .hexmap import T_DEF, TERRAIN_MASK
from .units import K_ATK, K_DEF, K_RNG


def defense_of(m, pool, d):
    """방어 측 유효 방어력 = 병종 방어 * 체력비 + 지형 + 참호."""
    i = m.axial_idx(d.q, d.r)
    terr = T_DEF[m.cells[i] & TERRAIN_MASK] if i >= 0 else 0
    return K_DEF[d.kind] * d.hp // 10 + terr + d.ent


def attack_of(a):
    return K_ATK[a.kind] * a.hp // 10


def resolve(m, pool, rng, a, d):
    """공격 한 번. (공격측 손실, 방어측 손실, 주사위, 점수) 를 돌려준다.

       주사위는 2d6 이라 7 을 중심으로 삼각분포가 된다 — 극단값이 드물어서
       '전력 차가 결과를 대체로 결정하되 가끔 뒤집힌다' 는 워게임의 맛이 난다.
       난수 상태는 언두를 위해 바깥에서 미리 저장한다.
    """
    atk = attack_of(a)
    dfn = defense_of(m, pool, d)
    roll = rng.d6() + rng.d6()
    score = atk - dfn + roll - 7

    if score >= 4:
        dl, al = 3, 0
    elif score >= 1:
        dl, al = 2, 1
    elif score >= -2:
        dl, al = 1, 1
    else:
        dl, al = 0, 2

    a.ammo -= 1
    a.mp = 0
    d.hp -= dl
    a.hp -= al

    # 반격: 인접해 있고 탄약이 남았으면 절반 피해로 되돌려준다
    from . import hexcoord as H
    counter = 0
    if d.hp > 0 and d.ammo > 0 and K_RNG[d.kind] >= 1 and \
            H.distance(a.q, a.r, d.q, d.r) == 1:
        counter = dl // 2
        if counter > 0:
            a.hp -= counter
            d.ammo -= 1

    return (al + counter, dl, roll, score)


def can_attack(m, pool, a, d):
    from . import hexcoord as H
    if a.side == d.side or a.ammo <= 0 or a.mp <= 0:
        return False
    return H.distance(a.q, a.r, d.q, d.r) <= K_RNG[a.kind]
