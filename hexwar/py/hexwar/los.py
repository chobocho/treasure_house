# -*- coding: utf-8 -*-
"""시야와 안개 — SPEC §9.

   헥스에서 시야선은 사각 격자보다 오히려 쉽다. 대각선이 없어서 '모서리를
   스치는' 애매한 경우가 한 종류뿐이고, 그 한 종류를 넛지로 없애면 선이
   유일하게 정해진다.

   고도 판정은 정수로만 한다. '중간 헥스가 관측자 눈과 목표를 잇는 직선보다
   위로 솟았는가' 를 비교할 때, 분수를 만들지 않고 양변에 N 을 곱한다.
"""

from . import hexcoord as H
from .hexmap import T_BLOCK, T_LOSH, TERRAIN_MASK, ELEV_SHIFT, ELEV_MASK
from .hexmap import FOG_HIDDEN, FOG_EXPLORED, FOG_VISIBLE


def hex_height(m, i):
    """헥스의 시야 높이 = 고도 + 지형이 얹는 높이. 숲·도시는 1, 산은 2."""
    c = m.cells[i]
    return ((c >> ELEV_SHIFT) & ELEV_MASK) + T_LOSH[c & TERRAIN_MASK]


def blocks_sight(m, i):
    """지형 자체가 시야를 막는가 — 높이와 별개로 숲·도시·산은 관통을 막는다."""
    return T_BLOCK[m.cells[i] & TERRAIN_MASK] == 1


def los_clear(m, aq, ar, bq, br):
    """A 에서 B 가 보이는가. SPEC §9.2 — O(거리).

       관측자 눈높이는 자기 칸 높이 + 1 이다(사람 키). 목표는 지면 높이.
       중간 칸의 높이가 눈과 목표를 잇는 직선 위로 솟으면 막힌다.

           H(m_i) * N  >  H(a) * (N - i) + H(b) * i
    """
    n = H.distance(aq, ar, bq, br)
    if n <= 1:
        return True
    ia = m.axial_idx(aq, ar)
    ib = m.axial_idx(bq, br)
    if ia < 0 or ib < 0:
        return False
    ha = hex_height(m, ia) + 1
    hb = hex_height(m, ib)
    pts = H.line(aq, ar, bq, br)
    for i in range(1, n):
        q, r = pts[i]
        im = m.axial_idx(q, r)
        if im < 0:
            return False
        hm = hex_height(m, im)
        line_h = ha * (n - i) + hb * i
        # 시야를 막는 지형(숲·도시·산)은 '같은 높이여도' 관통을 막는다.
        # 트인 지형(언덕)은 직선보다 확실히 높을 때만 막는다 — 이 부등호 하나가
        # 능선 너머를 보느냐 마느냐를 가른다.
        if hm * n > line_h or (blocks_sight(m, im) and hm * n >= line_h):
            return False
    return True


def visible_hexes(m, u, vis):
    """유닛 하나가 보는 칸 인덱스 집합. 반경 vis 나선을 돌며 LOS 를 건다."""
    out = []
    for q, r in H.spiral(u.q, u.r, vis):
        i = m.axial_idx(q, r)
        if i < 0:
            continue
        if los_clear(m, u.q, u.r, q, r):
            out.append(i)
    return out


def update_fog(m, pool, side):
    """SPEC §9.3 — 보이던 칸을 '탐색됨'으로 내리고, 다시 보이는 칸만 올린다.

       세 상태를 쓰는 이유: 한 번 본 지형은 기억하되 그 위의 적은 잊게 하려면
       '지형은 기억, 유닛은 현재' 라는 구분이 필요하다. 도스 게임들은 이걸
       칸마다 2비트로 저장했고, 여기서도 값 0/1/2 하나로 쓴다.
    """
    from .units import K_VIS
    fog = m.fog
    for i in range(len(fog)):
        if fog[i] == FOG_VISIBLE:
            fog[i] = FOG_EXPLORED
    for u in pool.iter_alive(side):
        for i in visible_hexes(m, u, K_VIS[u.kind]):
            fog[i] = FOG_VISIBLE


def enemy_visible(m, pool, side, u):
    """상대 유닛 u 가 이쪽 시야에 들어와 있는가 — 화면에 그릴지 정한다."""
    i = m.axial_idx(u.q, u.r)
    return i >= 0 and m.fog[i] == FOG_VISIBLE
