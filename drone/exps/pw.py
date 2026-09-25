# -*- coding: utf-8 -*-
"""증인 시험 — 정리마다 그 증인 하나를 돌린 캡처 out/w_<id>.txt."""
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, '..', 'deck'))
import cites  # noqa: E402


def run(ctx):
    base = os.path.join(HERE, '..')
    for r in cites.rows(base, 'theorems.tsv'):
        w = r.get('witness-test', '')
        if '::' in w:
            ctx.py('w_' + r['id'], 'tools/witness.py', r['id'])
