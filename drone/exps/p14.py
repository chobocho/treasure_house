# -*- coding: utf-8 -*-
"""14부 — 파이썬 시뮬레이터를 모듈마다: RED → GREEN, 그리고 CLI."""

# 시험 파일 하나가 모듈 하나를 맡는다(test_<이름>.py ↔ droneshow/<이름>.py).
# sim·collide·font5x7 은 따로 시험 파일이 없다 — cascade·assign·
# formation 시험이 그것을 쓰며 함께 본다.
MODULES = ['rng', 'vec3', 'quat', 'params', 'linalg', 'rigidbody', 'motor',
           'mixer', 'quadrotor', 'pid', 'attitude', 'cascade', 'sensors',
           'estimator', 'poly', 'profile', 'formation', 'assign', 'show',
           'tricks', 'render', 'cli']
ENV = {'PYTHONPATH': 'py'}


def modules(ctx):
    """모듈마다 줄 수와 시험 수 — 파일에서 센다(표를 손으로 적지
    않는다). 시험 수는 tests/test_<모듈>.py 의 def test_ 줄 수."""
    import os
    names = sorted(f[:-3] for f in os.listdir('py/droneshow')
                   if f.endswith('.py'))
    cells = []
    for n in names:
        with open('py/droneshow/%s.py' % n, encoding='utf-8') as f:
            lines = sum(1 for _ in f)
        t = 'py/tests/test_%s.py' % n
        tests = '—'
        if os.path.exists(t):
            with open(t, encoding='utf-8') as f:
                got = [l for l in f if l.lstrip().startswith('def test_')]
            tests = '%d' % len(got)
        cells.append([n, '%d' % lines, tests])
    half = (len(cells) + 1) // 2
    rows = [a + (cells[half + k] if half + k < len(cells) else
                 ['', '', ''])
            for k, a in enumerate(cells[:half])]
    ctx.table('p14_modules', ['모듈', '줄', '시험'] * 2, rows,
              num=(1, 2, 4, 5))


def run(ctx):
    modules(ctx)
    for m in MODULES:
        ctx.red(m)
        ctx.green(m)
    ctx.green('golden')
    ctx.py('p14_cli_help', '-m', 'droneshow', '--help', env=ENV)
    ctx.py('p14_plan', '-m', 'droneshow', 'plan', 'ex/spec_small.json',
           '-o', 'out/show_p14.json', env=ENV)
    ctx.adopt('show_p14.json')
    ctx.py('p14_info', '-m', 'droneshow', 'info', 'out/show_p14.json',
           env=ENV)
    ctx.py('p14_fly_k', '-m', 'droneshow', 'fly', 'out/show_p14.json',
           '--mode', 'kinematic', env=ENV)
    ctx.py('p14_fly_p', '-m', 'droneshow', 'fly', 'out/show_p14.json',
           '--mode', 'physics', '--ids', '0,1,2,3', env=ENV)
    ctx.cmd('p14_csv', ['sh', '-c', 'PYTHONPATH=py python3 -m droneshow '
                        'csv out/show_p14.json scratch/csv >/dev/null && '
                        'head -5 scratch/csv/drone_0.csv'])
