# -*- coding: utf-8 -*-
"""write_golden — 파이썬 판이 낸 값을 golden/*.json 으로 (SPEC §10).

자바스크립트 판의 시험은 이 파일들과 1e-9 안에서 같아야 한다. 이
파일을 만드는 것은 파이썬 판의 공식 증인 시험이 모두 초록이 된
**뒤**다(PLAN.md §0.7) — 틀린 값을 기준으로 삼지 않기 위해서다.

    python3 tests/write_golden.py          # golden/ 을 다시 쓴다
    python3 tests/write_golden.py --check  # 다르면 1 (make test-py)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from droneshow import (assign, formation, mixer, params, pid,  # noqa
                       poly, profile, quat, rng, show, sim)

OUT = os.path.join(HERE, '..', '..', 'golden')


def r9(x):
    """재귀적으로 실수를 round(·, 9). −0.0 → 0.0."""
    if isinstance(x, float):
        return round(x, 9) + 0.0
    if isinstance(x, (list, tuple)):
        return [r9(v) for v in x]
    if isinstance(x, dict):
        return {k: r9(v) for k, v in x.items()}
    return x


def g_rng():
    out = {}
    for s in (0, 1, 7, 2026):
        g = rng.Rng(s)
        out['next_%d' % s] = [g.next() for _ in range(20)]
    g = rng.Rng(7)
    out['normal_7'] = [g.normal() for _ in range(10)]
    return out


def g_quat():
    g = rng.Rng(101)
    cases = []
    for _ in range(20):
        a = quat.normalize([g.normal() for _ in range(4)])
        b = quat.normalize([g.normal() for _ in range(4)])
        v = [g.uniform() * 2 - 1 for _ in range(3)]
        ax = [g.normal() for _ in range(3)]
        ang = g.uniform() * 6.0 - 3.0
        cases.append({'a': a, 'b': b, 'v': v, 'axis': ax, 'angle': ang,
                      'mul': quat.mul(a, b),
                      'rotate': quat.rotate(a, v),
                      'matrix': quat.to_matrix(a),
                      'from_matrix': quat.canonical(
                          quat.from_matrix(quat.to_matrix(a))),
                      'axis_angle': quat.from_axis_angle(ax, ang),
                      'euler': quat.to_euler(a)})
    return {'cases': cases}


def g_mixer():
    p = params.load()
    d = params.derived(p)
    g = rng.Rng(102)
    cases = []
    for _ in range(10):
        u = [g.uniform() * 25, g.normal() * 0.5, g.normal() * 0.5,
             g.normal() * 0.1]
        t, flags = mixer.allocate(p, u, d['T_min'], d['T_max'])
        cases.append({'u': u, 'T': t, 'flags': flags})
    return {'M': mixer.matrix(p), 'Minv': mixer.inverse(p),
            'cases': cases}


def g_hover():
    return params.derived(params.load())


def g_pid():
    seqs = []
    for kp, ki, kd, imax, tau in ((2.0, 0.5, 0.1, 1.0, 0.0),
                                  (1.0, 3.0, 0.0, 0.3, 0.0),
                                  (0.5, 0.2, 0.8, 5.0, 0.05)):
        c = pid.PID(kp, ki, kd, imax, tau)
        y, out = 0.0, []
        for k in range(50):
            u = c.update(1.0, y, 0.02)
            y += 0.02 * (u - 0.3 * y)
            out.append(u)
        seqs.append({'gains': [kp, ki, kd, imax, tau], 'u': out})
    return {'dt': 0.02, 'seqs': seqs}


def g_physics():
    p = params.load()
    refs = {'hold': lambda t: {'p': [0.0, 0.0, 5.0]},
            'step': lambda t: {'p': [1.0, 0.5, 6.0], 'yaw': 0.5},
            'circle': lambda t: {
                'p': [2 * math.cos(0.8 * t), 2 * math.sin(0.8 * t),
                      5.0],
                'v': [-1.6 * math.sin(0.8 * t), 1.6 * math.cos(0.8 * t),
                      0.0],
                'a': [-1.28 * math.cos(0.8 * t),
                      -1.28 * math.sin(0.8 * t), 0.0]}}
    starts = {'hold': [0.0, 0.0, 5.0], 'step': [0.0, 0.0, 5.0],
              'circle': [2.0, 0.0, 5.0]}
    out = {}
    for name in ('hold', 'step', 'circle'):
        rows = sim.fly(p, refs[name], 5.0, start=starts[name], every=1)
        pick = {}
        for tt in (0.5, 1.0, 2.0, 5.0):
            k = round(tt * 500) - 1
            pick['%.1f' % tt] = rows[k]['s']
        out[name] = pick
    return out


def g_poly():
    sets = [([0.0, 2.0, 1.0, 4.0], [1.5, 1.0, 2.0]),
            ([1.0, 4.0], [2.0]),
            ([0.0, 1.0, 3.0, 2.0, 0.0], [1.0, 1.0, 1.5, 1.0])]
    beta = {k: [show.beta(k, u / 20, 0.25) for u in range(21)]
            for k in ('T', 'S', 'J', 'L')}
    snaps = [{'wp': w, 'times': t, 'coef': poly.min_snap(w, t)}
             for w, t in sets]
    return {'min_snap': snaps,
            'rest3': poly.rest_to_rest(3),
            'rest4': poly.rest_to_rest(4),
            'beta': beta}


def g_assign():
    g = rng.Rng(103)
    out = []
    for n in (5, 10, 20, 30, 40, 50):
        a = [[g.uniform() * 30, 0.0, g.uniform() * 30]
             for _ in range(n)]
        b = [[g.uniform() * 30, 0.0, g.uniform() * 30]
             for _ in range(n)]
        perm, total, _ops = assign.hungarian(assign.cost_matrix(a, b))
        out.append({'a': a, 'b': b, 'perm': perm, 'total': total})
    return {'cases': out}


def g_profile():
    out = []
    for d in (0.5, 4.5, 12.0):
        pr = profile.trapezoid(d, 3.0, 2.0)
        out.append({'d': d, 'T': pr['T'], 'samples': [
            profile.sample(pr, pr['T'] * k / 20) for k in range(21)]})
    return {'cases': out}


def g_formation():
    d = 1.5
    return {'grid': formation.grid(10, d, z0=5.0),
            'grid_xy': formation.grid(7, d, plane='xy'),
            'circle': formation.circle(16, d, z0=5.0),
            'rings': formation.rings(20, d, layers=3, z0=5.0),
            'sphere': formation.sphere(40, d, z0=5.0),
            'heart': formation.heart(30, d, z0=5.0),
            'globe': formation.globe(48, d, z0=5.0),
            'text': formation.text('DRONE', d, z0=5.0),
            'digit': formation.digit(7, d, z0=5.0)}


def show12():
    p = params.load()
    d = 3.0
    scenes = [{'name': 'grid', 'points': formation.grid(12, d, z0=10.0),
               'hold': 2.0, 'rgb': (255, 255, 255)},
              {'name': 'heart',
               'points': formation.heart(12, d, z0=10.0),
               'hold': 3.0, 'rgb': (255, 0, 64)},
              {'name': 'circle', 'points': formation.circle(12, d,
                                                            z0=10.0),
               'hold': 2.0, 'rgb': (0, 200, 255)}]
    return show.plan(scenes, p)


def g_show12():
    s = show12()
    samples = []
    for f in range(0, round(s['duration'] * s['fps']) + 1, 10):
        samples.append(show.frame(s, f))
    return {'show': s, 'frames_every10': samples}


GOLDEN = {'rng': g_rng, 'quat': g_quat, 'mixer': g_mixer,
          'hover': g_hover, 'pid': g_pid, 'physics': g_physics,
          'poly': g_poly, 'assign': g_assign, 'profile': g_profile,
          'formation': g_formation, 'show12': g_show12}


def text_of(name):
    return json.dumps(r9(GOLDEN[name]()), ensure_ascii=False,
                      separators=(',', ':')) + '\n'


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    bad = 0
    for name in GOLDEN:
        p = os.path.join(OUT, name + '.json')
        text = text_of(name)
        if '--check' in argv:
            old = open(p, encoding='utf-8').read() if os.path.exists(
                p) else ''
            if old != text:
                print('golden/%s.json 이 지금 판과 다르다' % name)
                bad = 1
            continue
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        print('golden/%s.json %d바이트' % (name, len(text)))
    return bad


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
