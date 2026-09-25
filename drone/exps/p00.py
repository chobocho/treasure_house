# -*- coding: utf-8 -*-
"""0부 — 이 기계의 도구와 첫 쇼 한 편."""


def run(ctx):
    ctx.py('p00_python', '-c', 'import sys, platform; print("python", '
           'sys.version.split()[0], platform.machine())')
    ctx.cmd('p00_node', ['node', '--version'])
    env = {'PYTHONPATH': 'py'}
    ctx.py('p00_plan', '-m', 'droneshow', 'plan', 'ex/spec_hello.json',
           '-o', 'out/show_hello.json', env=env)
    ctx.adopt('show_hello.json')
    ctx.py('p00_info', '-m', 'droneshow', 'info', 'out/show_hello.json',
           env=env)
