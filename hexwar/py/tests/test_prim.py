# -*- coding: utf-8 -*-
"""골든 프리미티브 대조 — golden/prim.txt 의 모든 줄을 구현과 맞춰 본다.

   벡터는 tools/gen_prim.py 가 '다른 알고리즘'으로 만든 것이다(거리는 BFS,
   픽킹은 점-포함 판정, 라인은 부동소수). 여기서 맞으면 구현과 오라클이
   서로 독립적으로 같은 답에 도달했다는 뜻이다.

   루아·타입스크립트 테스트도 같은 파일을 같은 순서로 읽는다.
"""
import io
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(BASE, 'py'))

from hexwar import hexcoord as H          # noqa: E402
from hexwar import hexmap as M            # noqa: E402
from hexwar import picker as PK           # noqa: E402
from hexwar import rng as R               # noqa: E402

fails = []


def eq(name, got, want):
    if got != want:
        fails.append('%s: got %r want %r' % (name, got, want))


def main():
    path = os.path.join(BASE, 'golden', 'prim.txt')
    nline = 0
    for raw in io.open(path, encoding='utf-8'):
        raw = raw.strip()
        if not raw or raw.startswith(';'):
            continue
        nline += 1
        parts = raw.split()
        key = parts[0]
        if key == 'fnv':
            data = b'' if parts[1] == '-' else bytes.fromhex(parts[1])
            eq('fnv %s' % parts[1], R.fnv1a(data), int(parts[2]))
            continue
        v = [int(x) for x in parts[1:]]

        if key == 'dirs':
            eq('dirs', [c for d in H.DIRS for c in d], v)
        elif key == 'oddr':
            eq('axial_to_oddr%s' % v[:2], list(H.axial_to_oddr(v[0], v[1])), v[2:])
            eq('oddr_to_axial%s' % v[2:], list(H.oddr_to_axial(v[2], v[3])), v[:2])
        elif key == 'oddq':
            eq('axial_to_oddq%s' % v[:2], list(H.axial_to_oddq(v[0], v[1])), v[2:])
            eq('oddq_to_axial%s' % v[2:], list(H.oddq_to_axial(v[2], v[3])), v[:2])
        elif key == 'dist':
            eq('distance%s' % v[:4], H.distance(v[0], v[1], v[2], v[3]), v[4])
        elif key == 'neighbors':
            got = [c for (nq, nr) in H.neighbors(v[0], v[1]) for c in (nq, nr)]
            eq('neighbors%s' % v[:2], got, v[2:])
        elif key == 'ring':
            got = [c for h in H.ring(0, 0, v[0]) for c in h]
            eq('ring%d' % v[0], got, v[1:])
        elif key == 'spiral':
            eq('spiral%d' % v[0], len(H.spiral(0, 0, v[0])), v[1])
        elif key == 'line':
            got = [c for h in H.line(v[0], v[1], v[2], v[3]) for c in h]
            eq('line%s' % v[:4], [len(got) // 2] + got, v[4:])
        elif key == 'pick':
            got = PK.pick(v[0], v[1], v[2], v[3])
            eq('pick%s' % v[:4], list(got) if got else [-1, -1], v[4:])
        elif key == 'lcg':
            st = R.Rng(v[0])
            eq('lcg', [st.next() for _ in range(len(v) - 1)], v[1:])
        elif key == 'd6':
            st = R.Rng(0x1BADB002)
            eq('d6', [st.d6() for _ in range(len(v))], v)
        elif key == 'cell':
            eq('pack%s' % v[:3], M.pack_cell(v[0], v[1], v[2]), v[3])
            eq('unpack%d' % v[3],
               [M.cell_terrain(v[3]), M.cell_elev(v[3]), M.cell_road(v[3])], v[:3])
        else:
            fails.append('알 수 없는 키: %s' % key)

    # 마스크 표가 golden/pick_mask.txt 와 같은지도 본다 — 코드가 만든 표와
    # 파일로 굳힌 표가 어긋나면 세 언어가 서로 다른 칸을 고르게 된다.
    mask_path = os.path.join(BASE, 'golden', 'pick_mask.txt')
    rows = [l.strip() for l in io.open(mask_path, encoding='utf-8') if l.strip()]
    eq('mask 행 수', len(rows), PK.ROW_STEP)
    for oy, row in enumerate(rows):
        eq('mask[%d]' % oy,
           ''.join(str(PK.PICK_MASK[oy * PK.HEX_W + ox]) for ox in range(PK.HEX_W)), row)

    if fails:
        print('FAIL %d / %d줄' % (len(fails), nline))
        for f in fails[:20]:
            print('  ' + f)
        return 1
    print('prim OK — %d줄 + 마스크 768칸 전부 일치' % nline)
    return 0


if __name__ == '__main__':
    sys.exit(main())
