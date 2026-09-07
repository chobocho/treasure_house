# -*- coding: utf-8 -*-
"""untab.py — tmux capture-pane 이 넣은 탭을 공백으로 되돌린다.

tmux 는 기본 스타일의 공백이 길게 이어지면 그 자리를 탭 하나로 줄여서 내보낸다.
터미널에서는 결과가 같지만, 덱의 <pre> 안에서는 탭 폭이 브라우저·폰트마다 달라서
판이 어긋난다. 그래서 저장 직후에 탭을 원래의 공백으로 펼쳐 둔다.

핵심은 "탭 스톱은 화면 칸(cell) 기준"이라는 점이다. 한글 한 글자는 두 칸을 먹으므로
글자 수로 세면 한글이 섞인 줄에서 어긋난다. ANSI 이스케이프는 폭이 0 이라 빼고 센다.

    python3 deck/untab.py out/tmux_*.txt        # 제자리에서 고친다
"""
import io, re, sys, unicodedata

TABSTOP = 8
ANSI = re.compile(r'\x1b\[[0-9;:?]*[ -/]*[@-~]')


def cells(s):
    """ANSI 를 뺀 실제 화면 칸 수. 동아시아 넓은 글자는 2칸으로 센다."""
    n = 0
    for ch in ANSI.sub('', s):
        n += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return n


def untab(line):
    out = []
    for part in line.split('\t'):
        out.append(part)
        col = cells(''.join(out))
        pad = TABSTOP - (col % TABSTOP)
        out.append(' ' * pad)
    out.pop()                      # 마지막 조각 뒤에는 탭이 없었다
    return ''.join(out)


def main(paths):
    for p in paths:
        raw = io.open(p, encoding='utf-8', newline='').read()
        if '\t' not in raw:
            continue
        fixed = '\n'.join(untab(l) for l in raw.split('\n'))
        io.open(p, 'w', encoding='utf-8', newline='').write(fixed)
        print('  탭 제거: %s' % p)


if __name__ == '__main__':
    main(sys.argv[1:])
