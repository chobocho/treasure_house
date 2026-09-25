# -*- coding: utf-8 -*-
"""params — 기준 쿼드로터의 값(data/params.tsv)을 읽는다 (SPEC §3).

숫자는 표 한 곳에만 있다. 코드와 슬라이드는 이 표를 읽을 뿐 값을 다시
적지 않는다 — 두 곳에 적으면 한쪽만 고쳐지는 날이 온다.
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TSV = os.path.join(HERE, '..', '..', 'data', 'params.tsv')


def load(path=TSV):
    """{이름: float}. 첫 줄(칸 이름)과 # 주석 줄은 건너뛴다."""
    out = {}
    with open(path, encoding='utf-8') as f:
        rows = [ln.rstrip('\n').split('\t') for ln in f
                if ln.strip() and not ln.startswith('#')]
    for name, value, *_rest in rows[1:]:
        out[name] = float(value)
    return out


def derived(p):
    """표에서 계산으로 얻는 값 — 슬라이드는 이것도 캡처로만 보인다."""
    t_h = p['m'] * p['g'] / 4
    return {'a': p['L'] / math.sqrt(2),
            'c': p['kQ'] / p['kT'],
            'T_hover': t_h,
            'omega_hover': math.sqrt(t_h / p['kT']),
            'T_max': p['kT'] * p['omega_max'] ** 2,
            'T_min': p['kT'] * p['omega_min'] ** 2,
            'twr': (4 * p['kT'] * p['omega_max'] ** 2
                    / (p['m'] * p['g'])),
            'area': math.pi * p['r_prop'] ** 2}
