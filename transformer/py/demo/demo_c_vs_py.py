# -*- coding: utf-8 -*-
"""9부 — 파이썬 참조와 C 를 나란히 (tfs parity 의 출력 그대로)."""
from demo import crun, report


def main():
    text = crun.tfs('parity', crun.THREADS)
    sections, title, body = [], None, []
    for line in text.rstrip('\n').split('\n'):
        if line.startswith('== '):
            if title:
                sections.append((title, '\n'.join(body)))
            title = line.strip('= ').split('. ', 1)[1]
            body = []
        else:
            body.append(line)
    sections.append((title, '\n'.join(body)))
    return report.write('c_vs_py.txt', sections)


if __name__ == '__main__':
    print(main())
