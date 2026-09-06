# -*- coding: utf-8 -*-
"""split_ranges.py — 너무 긴 코드 블록을 자동으로 쪼갠다.

한 <pre> 가 45줄을 넘으면 폴드(374 px)에서 슬라이드 하나에 안 들어간다.
손으로 쪼개면 반드시 어딘가를 빠뜨리거나 겹치므로 도구에게 맡긴다.

    python3 deck/split_ranges.py            # 제자리에서 고친다
"""
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
SECD = os.path.join(HERE, 'sections')

LIMIT = 42   # 45 보다 조금 여유를 둔다
HARD = re.compile(r'^(?:func |type |var |const |import |package |// ──|\t*//go:|'
                  r'[A-Za-z_][\w./$()-]*:)')
DIR = re.compile(r'<!--CODE\s+file=(\S+)\s+lines=(\d+)-(\d+)(.*?)-->')


def lines_of(name):
    p = os.path.join(SRC, name)
    return io.open(p, encoding='utf-8').read().split('\n')


def split(lo, hi, lines):
    out, start = [], lo
    while start <= hi:
        end = min(start + LIMIT - 1, hi)
        if end < hi:
            best = None
            for i in range(end, start + LIMIT // 2, -1):
                if i < len(lines) and HARD.match(lines[i]):
                    best = i
                    break
            if best is None:
                for i in range(end, start + LIMIT // 2, -1):
                    if i - 1 < len(lines) and lines[i - 1].strip() == '':
                        best = i - 1
                        break
            if best:
                end = best
        out.append((start, end))
        start = end + 1
    return out


def main():
    total = 0
    for fn in sorted(os.listdir(SECD)):
        if not fn.endswith('.html') or fn.startswith('10_'):
            continue
        p = os.path.join(SECD, fn)
        s = io.open(p, encoding='utf-8').read()

        def sub(m):
            global_total = 0
            name, lo, hi, rest = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
            if hi - lo + 1 <= 45:
                return m.group(0)
            parts = split(lo, hi, lines_of(name))
            cap = re.search(r'cap="([^"]*)"', rest)
            base = cap.group(1) if cap else name
            out = []
            for i, (a, b) in enumerate(parts):
                c = base if len(parts) == 1 else '%s (%d/%d)' % (base, i + 1, len(parts))
                out.append('<!--CODE file=%s lines=%d-%d cap="%s"-->' % (name, a, b, c))
            return '\n'.join(out)

        new = DIR.sub(sub, s)
        if new != s:
            n = new.count('<!--CODE') - s.count('<!--CODE')
            total += n
            io.open(p, 'w', encoding='utf-8', newline='').write(new)
            print('  %s — 블록 %d개 추가' % (fn, n))
    print('총 %d개 블록으로 쪼갬' % total)


if __name__ == '__main__':
    main()
