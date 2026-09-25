# -*- coding: utf-8 -*-
"""cli — 명령 줄에서 쇼를 짜고, 보고, 날린다 (SPEC §9.6).

    python3 -m droneshow plan spec.json -o show.json
    python3 -m droneshow info show.json
    python3 -m droneshow csv  show.json 폴더
    python3 -m droneshow svg  show.json 프레임 [--view
    front|top|audience]
    python3 -m droneshow fly  show.json --mode physics --ids 0,1

장면 설명(spec.json)은 모양 이름과 인자만 적는다 — 점을 손으로 적지
않는다. 모든 장면의 점 수가 같아야 한다(드론은 사라지지 않는다).
"""
import argparse
import json
import os

from . import formation as F
from . import params
from . import show as SH

SHAPES = {'grid': F.grid, 'circle': F.circle, 'rings': F.rings,
          'sphere': F.sphere, 'heart': F.heart, 'globe': F.globe}


def points(sc):
    z0 = sc.get('z0', 0.0)
    if sc['shape'] == 'text':
        return F.text(sc['s'], sc['d'], z0)
    if sc['shape'] == 'digit':
        return F.digit(sc['k'], sc['d'], z0)
    return SHAPES[sc['shape']](sc['n'], sc['d'], z0=z0)


def cmd_plan(a):
    spec = json.load(open(a.spec, encoding='utf-8'))
    scenes = [{'name': sc['name'], 'points': points(sc),
               'hold': sc['hold'], 'rgb': tuple(sc['rgb'])}
              for sc in spec['scenes']]
    counts = {len(sc['points']) for sc in scenes}
    if len(counts) != 1:
        print('장면마다 점의 수가 다르다: %s'
              % [len(sc['points']) for sc in scenes])
        return 2
    s = SH.plan(scenes, params.load(), spec.get('profile'),
                spec.get('fps', 25), spec.get('seed', 7))
    with open(a.o, 'w', encoding='utf-8', newline='\n') as f:
        f.write(SH.dumps(s))
    print('%s — 드론 %d대 · %.2f초' % (a.o, len(s['drones']),
                                      s['duration']))
    return 0


def cmd_info(a):
    s = SH.loads(open(a.show, encoding='utf-8').read())
    print('드론 %d대 · 길이 %.2f초 · %d fps · 모양 %s'
          % (len(s['drones']), s['duration'], s['fps'],
             s['profile']['kind']))
    for sc in s['scenes']:
        print('  %-10s %7.2f – %7.2f초' % (sc['name'], sc['t0'],
                                            sc['t1']))
    d, t, i, j = SH.min_distance(s)
    print('최소 간격 %.3f m (%.2f초, 드론 %d–%d)' % (d, t, i, j))
    return 0


def cmd_csv(a):
    s = SH.loads(open(a.show, encoding='utf-8').read())
    for d in s['drones']:
        p = os.path.join(a.dir, 'drone_%d.csv' % d['id'])
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(SH.csv_rows(s, d)) + '\n')
    print('%d개 파일 → %s' % (len(s['drones']), a.dir))
    return 0


def cmd_svg(a):
    from . import render
    s = SH.loads(open(a.show, encoding='utf-8').read())
    print(render.snapshot_svg(s, int(a.frame), a.view))
    return 0


def cmd_fly(a):
    s = SH.loads(open(a.show, encoding='utf-8').read())
    if a.mode == 'kinematic':
        d, t, i, j = SH.min_distance(s)
        print('kinematic — 계획 그대로. 최소 간격 %.3f m' % d)
        return 0
    ids = [int(x) for x in a.ids.split(',')]
    print('physics — 6자유도 모델 %d대, 제어기가 계획을 따라 난다'
          % len(ids))
    print('  id   최대 오차[m]  평균 오차[m]')
    for r in SH.fly_physics(s, params.load(), ids):
        print('  %2d   %11.4f  %11.4f' % (r['id'], r['max_err'],
                                         r['mean_err']))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog='droneshow')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('plan')
    p.add_argument('spec')
    p.add_argument('-o', required=True)
    p = sub.add_parser('info')
    p.add_argument('show')
    p = sub.add_parser('csv')
    p.add_argument('show')
    p.add_argument('dir')
    p = sub.add_parser('svg')
    p.add_argument('show')
    p.add_argument('frame')
    p.add_argument('--view', default='front')
    p = sub.add_parser('fly')
    p.add_argument('show')
    p.add_argument('--mode', default='kinematic')
    p.add_argument('--ids', default='0')
    a = ap.parse_args(argv)
    return {'plan': cmd_plan, 'info': cmd_info, 'csv': cmd_csv,
            'svg': cmd_svg, 'fly': cmd_fly}[a.cmd](a)
