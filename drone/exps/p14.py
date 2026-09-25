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


def run(ctx):
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
