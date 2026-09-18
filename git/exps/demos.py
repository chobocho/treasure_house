# -*- coding: utf-8 -*-
"""demos — 덱 데모(deck/demos.js)의 정답을 진짜 git 에게서 받는다.

check_deck.js 는 데모마다 "이 값을 넣으면 화면에 이것이 있어야 한다"
를 적어 두고 돌려 본다(PLAN.md §5 11단계). 그 기댓값이 자바스크립트
데모 스스로 낸 값이면 아무것도 검사하지 않는 셈이라, 여기서 진짜 git
으로 뜬 캡처를 기댓값의 출처로 삼는다. golden/ 에 이미 있는 것(SHA-1
벡터·diff 쌍·merge 장면·pkt 대화)은 그것을 쓰고, 없는 것만 여기서 뜬다.
"""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# golden/pack/ofs.pack 의 첫 델타 항목을 mygit.pack 으로 꺼내 16진으로
# 찍는다. 바탕과 결과의 크기는 아래에서 진짜 git 에게 따로 묻는다.
DELTA_PY = '''import sys, zlib
sys.path.insert(0, 'py')
from mygit import pack as P
data = open('golden/pack/ofs.pack', 'rb').read()
ver = [l.split() for l in open('golden/pack/ofs.verify')]
oid, _t, _s, _p, off, _d, base = [r for r in ver if len(r) == 7][0]
typ, dsize, p1 = P._entry_header(data, int(off))
dist, p2 = P._ofs(data, p1)
delta = zlib.decompressobj().decompress(data[p2:])
print('base', base)
print('target', oid)
h = delta.hex()
for k in range(0, len(h), 64):
    print(h[k:k + 64])
'''


def run(ctx):
    # 트리 정렬 — 3부 tree_sort 와 다른 이름들
    r = ctx.repo('demo_sort')
    for name in ('foo.c', 'foo-bar', 'foo0', 'foo=1'):
        r.write(name, name + '\n')
    r.write('foo/x', 'x\n')
    r.sh('git add -A')
    r.cap('git ls-tree --name-only $(git write-tree)')
    # .gitignore 판정 — 규칙 몇 개와 경로들
    g = ctx.repo('demo_ignore')
    g.write('.gitignore', '*.log\n!keep.log\nbuild/\n/root.txt\ndoc/**/*.tmp\n')
    for p in ('a.log', 'keep.log', 'sub/b.log', 'build/x.o', 'src/build',
              'root.txt', 'sub/root.txt', 'doc/a/b/c.tmp', 'doc/c.tmp',
              'readme.md'):
        g.write(p, 'x\n')
    g.cap('cat .gitignore')
    g.write('../paths.txt', '\n'.join(
        ('a.log', 'keep.log', 'sub/b.log', 'build/x.o', 'src/build',
         'root.txt', 'sub/root.txt', 'doc/a/b/c.tmp', 'doc/c.tmp',
         'readme.md')) + '\n')
    g.cap('cat ../paths.txt')
    # -n 은 맞지 않은 경로도 "::<TAB>경로" 로 찍는다 — 무시 안 됨의 증거
    g.cap('git check-ignore -v -n --no-index --stdin < ../paths.txt')
    # 델타 해석 — golden 의 진짜 델타와 그 바탕·결과의 크기
    d = ctx.repo('demo_delta', bare=True)
    d.sh('mkdir -p objects/pack && cp %s/golden/pack/ofs.pack '
         '%s/golden/pack/ofs.idx objects/pack/' % (HERE, HERE))
    d.sh('ln -s %s/py py && ln -s %s/golden golden' % (HERE, HERE))
    d.write('delta.py', DELTA_PY)
    d.cap('python3 delta.py')
    base, target = [l.split()[1] for l in
                    d.sh('python3 delta.py').split('\n')[:2]]
    d.cap('git cat-file -s %s' % base)
    d.cap('git cat-file -s %s' % target)
