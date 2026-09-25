# -*- coding: utf-8 -*-
"""show — 장면 목록을 쇼 파일로, 쇼 파일을 시각별 위치·색으로 (SPEC §9).

쇼 파일의 약속: 한 전환 안에서 모든 드론은 **같은 β(u)** 로 직선을
간다(동기 직선 이동). 그래서 제곱 거리 최적 할당과 장면 간격만으로
충돌이 없음을 증명할 수 있다(T31).
"""
import json
import math

from . import assign as AS
from . import collide
from . import poly
from . import profile as PR
from . import vec3 as V

KIND = {'trapezoid': 'T', 'minsnap': 'S', 'minjerk': 'J', 'linear': 'L'}
_C = {'S': poly.rest_to_rest(4), 'J': poly.rest_to_rest(3)}
_D = {k: (poly.deriv(c, 1), poly.deriv(c, 2)) for k, c in _C.items()}


def r9(x):
    """출력용 반올림 (SPEC §1.7). −0.0 은 0.0 으로."""
    return round(x, 9) + 0.0


def rnd(x):
    """반올림 — 파이썬의 round 는 .5 를 짝수 쪽으로 보낸다(126.5 → 126).
    자바스크립트의 Math.round 와 같게 floor(x + ½) 를 쓴다."""
    return math.floor(x + 0.5)


def beta(kind, u, ramp):
    """(β, β', β'') at u ∈ [0, 1]."""
    u = min(1.0, max(0.0, u))
    if kind == 'L':
        return u, 1.0, 0.0
    if kind == 'T':
        vh = 1.0 / (1.0 - ramp)
        if u <= ramp:
            return vh * u * u / (2 * ramp), vh * u / ramp, vh / ramp
        if u < 1 - ramp:
            return vh * (u - ramp / 2), vh, 0.0
        w = 1 - u
        return 1 - vh * w * w / (2 * ramp), vh * w / ramp, -vh / ramp
    c, (d1, d2) = _C[kind], _D[kind]
    return poly.val(c, u), poly.val(d1, u), poly.val(d2, u)


def limits(kind, ramp):
    """(max β', max |β''|) — 전환 시간을 정하는 데 쓴다."""
    if kind == 'L':
        return 1.0, 0.0
    if kind == 'T':
        return PR.beta_trap_limits(ramp)
    return PR.poly_limits(_C[kind])


def _rgb(sc, slot):
    """장면의 색 — (r, g, b) 하나이거나, 자리마다의 색 목록."""
    c = sc['rgb']
    return list(c) if isinstance(c, tuple) else list(c[slot])


def plan(scenes, p, profile=None, fps=25, seed=7):
    """장면 [{name, points, hold, rgb}] → 쇼 dict.

    장면이 바뀔 때마다 지금 자리에서 새 자리로 제곱 거리 헝가리안
    할당을 하고, 가장 먼 드론이 속도·가속도 한계에 닿는 시간으로
    전환 시간을 정한 뒤 1/fps 로 올림한다. 드론 i 의 번호는 쇼
    내내 그대로이고, slot[i] 가 그 장면에서 선 자리 번호다."""
    profile = profile or {'kind': 'trapezoid', 'ramp': 0.25}
    k = KIND[profile['kind']]
    ramp = profile.get('ramp', 0.25)
    d1, d2 = limits(k, ramp)
    n = len(scenes[0]['points'])
    where = [list(q) for q in scenes[0]['points']]
    slot = list(range(n))
    rows = [[] for _ in range(n)]
    meta, t = [], 0.0

    def mark(tt, sc, kind):
        for i in range(n):
            row = ([r9(tt)] + [r9(x) for x in where[i]]
                   + _rgb(sc, slot[i]))
            rows[i].append(row + ([kind] if kind else []))

    for s_i, sc in enumerate(scenes):
        if s_i:
            c = AS.cost_matrix(where, sc['points'], True)
            perm, _tot, _ops = AS.hungarian(c)
            dmax = max(V.dist(where[i], sc['points'][perm[i]])
                       for i in range(n))
            big_t = max(dmax * d1 / p['vmax'],
                        math.sqrt(dmax * d2 / p['amax']))
            big_t = math.ceil(big_t * fps - 1e-9) / fps
            mark(t, scenes[s_i - 1], k)       # 전환 시작 — 앞 장면의 색
            where = [list(sc['points'][perm[i]]) for i in range(n)]
            slot = perm
            t += big_t
        meta.append({'name': sc['name'], 't0': r9(t)})
        mark(t, sc, 'L')                      # 멈춤 시작
        t += sc['hold']
        meta[-1]['t1'] = r9(t)
    mark(t, scenes[-1], None)                 # 끝
    return {'format': 'droneshow/1', 'fps': fps, 'dmin': p['dmin'],
            'seed': seed, 'profile': {'kind': profile['kind'],
                                      'ramp': ramp},
            'duration': r9(t), 'scenes': meta,
            'drones': [{'id': i, 'keyframes': rows[i]}
                       for i in range(n)]}


def _seg(show, d, t):
    kf = d['keyframes']
    if t <= kf[0][0]:
        return kf[0], kf[0], 0.0, 1.0
    for a, b in zip(kf, kf[1:]):
        if t <= b[0]:
            span = b[0] - a[0]
            return a, b, (t - a[0]) / span if span else 1.0, span
    return kf[-1], kf[-1], 1.0, 1.0


def _kind(show, a):
    return a[7] if len(a) > 7 else KIND[show['profile']['kind']]


def position(show, d, t):
    a, b, u, _s = _seg(show, d, t)
    s = beta(_kind(show, a), u, show['profile']['ramp'])[0]
    return [a[1 + k] + s * (b[1 + k] - a[1 + k]) for k in range(3)]


def velocity(show, d, t):
    a, b, u, span = _seg(show, d, t)
    s1 = beta(_kind(show, a), u, show['profile']['ramp'])[1]
    return [s1 / span * (b[1 + k] - a[1 + k]) for k in range(3)]


def acceleration(show, d, t):
    a, b, u, span = _seg(show, d, t)
    s2 = beta(_kind(show, a), u, show['profile']['ramp'])[2]
    return [s2 / span ** 2 * (b[1 + k] - a[1 + k]) for k in range(3)]


def colour(show, d, t):
    """시각 t 의 색 — lights 가 있으면 그것을, 없으면 키프레임을
    잇는다."""
    track = d.get('lights') or [[k[0]] + k[4:7] for k in d['keyframes']]
    if t <= track[0][0]:
        return [int(x) for x in track[0][1:4]]
    for a, b in zip(track, track[1:]):
        if t <= b[0]:
            u = (t - a[0]) / (b[0] - a[0]) if b[0] > a[0] else 1.0
            return [rnd(a[1 + k] + u * (b[1 + k] - a[1 + k]))
                    for k in range(3)]
    return [int(x) for x in track[-1][1:4]]


def frame(show, f):
    """f 번째 프레임의 [(위치, 색)] — 드론 id 순."""
    t = f / show['fps']
    return [(position(show, d, t), colour(show, d, t))
            for d in show['drones']]


def min_distance(show, step=0.04):
    """쇼 전체를 step 초마다 재어 (최소 거리, 시각, i, j)."""
    best = (math.inf, 0.0, -1, -1)
    n = round(show['duration'] / step)
    for k in range(n + 1):
        t = k * step
        pts = [position(show, d, t) for d in show['drones']]
        dd, i, j = collide.min_distance(pts)
        if dd < best[0]:
            best = (dd, t, i, j)
    return best


def csv_rows(show, d):
    """드론 한 대의 CSV (SPEC §9.2). fps 마다 한 줄."""
    rows = ['Time [msec],x [m],y [m],z [m],Red,Green,Blue']
    for f in range(round(show['duration'] * show['fps']) + 1):
        t = f / show['fps']
        x = position(show, d, t)
        c = colour(show, d, t)
        rows.append('%d,%.3f,%.3f,%.3f,%d,%d,%d'
                    % (rnd(t * 1000), x[0], x[1], x[2],
                       c[0], c[1], c[2]))
    return rows


def dumps(show):
    return json.dumps(show, ensure_ascii=False, indent=1,
                      sort_keys=False) + '\n'


def loads(text):
    return json.loads(text)


def fly_physics(show, p, ids, cfg=None):
    """물리 모드 — 고른 드론마다 6자유도 모델 + 제어기로 계획을 따라
    난다.

    앞먹임으로 계획의 속도·가속도를 준다. 드론끼리는 서로 모른다(공기
    흐름의 간섭은 모델에 없다). [{'id', 'max_err', 'mean_err'}]."""
    from . import sim
    out = []
    for i in ids:
        d = show['drones'][i]
        ref = lambda t, d=d: {'p': position(show, d, t),
                              'v': velocity(show, d, t),
                              'a': acceleration(show, d, t)}
        rows = sim.fly(p, ref, show['duration'],
                       start=position(show, d, 0.0), cfg=cfg)
        errs = [V.dist(r['s'][0:3], position(show, d, r['t']))
                for r in rows]
        out.append({'id': i, 'max_err': max(errs),
                    'mean_err': V.total(errs) / len(errs)})
    return out
