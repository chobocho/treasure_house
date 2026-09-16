# -*- coding: utf-8 -*-
"""5부 — 말뭉치 통계. corpus/stats.py 를 그대로 부른다."""
import importlib.util
import os

BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def main():
    path = os.path.join(BASE, 'corpus', 'stats.py')
    spec = importlib.util.spec_from_file_location('corpus_stats', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    text = mod.report()
    out = os.path.join(BASE, 'out', 'corpus_stats.txt')
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    return out


if __name__ == '__main__':
    print(main())
