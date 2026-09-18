# -*- coding: utf-8 -*-
"""pack — 팩파일과 저장소 관리(10부).

조금씩 자라는 파일 하나의 역사 40개 커밋을 만든다. 느슨한 객체의
수·크기 → gc 뒤의 팩 → verify-pack 의 델타 사슬 → 델타 창·깊이를
바꿔 가며 잰 팩 크기 표 → commit-graph·multi-pack-index·비트맵 →
닿지 않는 객체와 prune. 팩 내용은 pack.threads=1·window=10·
depth=50 으로 고정한다(PLAN.md §0.9).
"""
import os
import re

from exps.util import commit, tick

BASE = ''.join('row %03d: %s\n' % (i, 'x' * (i % 37))
               for i in range(300))


def history(ctx, name, n=40):
    r = ctx.repo(name)
    for k in ('pack.threads 1', 'pack.window 10', 'pack.depth 50',
              'gc.auto 0'):
        r.sh('git config ' + k)
    text = BASE
    for i in range(n):
        text = text.replace('row %03d:' % (i * 7 % 300),
                            'ROW %03d:' % (i * 7 % 300))
        note = 'notes/%02d.txt' % (i % 5)
        commit(r, i, 'v%02d' % i, {'data.txt': text, note: 'n%d\n' % i})
    return r


def noname(t):
    """팩 파일 이름(내용의 SHA-1)을 줄인다 — 캡션에 적는다."""
    return re.sub(r'pack-[0-9a-f]{40}', 'pack-<이름>', t)


def pack_size(r):
    d = os.path.join(r.path, '.git', 'objects', 'pack')
    return sum(os.path.getsize(os.path.join(d, f))
               for f in os.listdir(d) if f.endswith('.pack'))


def run(ctx):
    r = history(ctx, 'pack')
    # size: 는 느슨한 객체의 디스크 사용량(블록 크기)이라 기계마다 다르다
    r.cap('git count-objects -v | grep -v "^size:"')
    r.cap('git gc --quiet && git count-objects -v', label='pack.gc')
    r.cap('ls .git/objects/pack')
    idx = '.git/objects/pack/*.idx'
    r.cap('git verify-pack -v %s | tail -9' % idx, edit=noname)
    r.cap("git verify-pack -v %s | awk '$6 != \"\"' | head -8" % idx,
          label='pack.chain', edit=noname)
    r.cap('git verify-pack -s %s' % idx)
    # 사슬 길이 분포 전부(도해 delta_chains 의 원료)
    r.cap('git verify-pack -v %s | grep -E "^(non delta|chain length)"'
          % idx)
    r.cap('od -A d -t x1 -N 32 .git/objects/pack/*.pack')
    # < 뒤의 * 는 dash 가 펼치지 않는다(처음 판은 "cannot open" 을
    # 캡처했다) — ls 로 이름을 먼저 얻는다
    r.cap('git show-index < $(ls %s) | head -5' % idx)
    # 델타 창과 깊이 — 같은 객체를 다시 싸며 크기를 잰다
    rows = []
    for window, depth in ((0, 0), (1, 50), (10, 1), (10, 10), (10, 50),
                          (50, 50), (250, 250)):
        r.sh('git repack -a -d -f -q --window=%d --depth=%d'
             % (window, depth))
        rows.append((window, depth, pack_size(r)))
    base = rows[0][2]
    ctx.table('pack_window', ['window', 'depth', '팩 크기(바이트)',
                              '델타 없음 대비'],
              [(w, d, s, '%.1f%%' % (100.0 * s / base))
               for w, d, s in rows],
              '같은 40커밋을 repack -a -d -f 로 다시 쌌을 때')
    r.sh('git repack -a -d -f -q')
    # 저장소 부속 색인들
    r.cap('git commit-graph write --reachable && '
          'ls .git/objects/info', label='pack.cg')
    r.cap('git commit-graph verify')
    r.cap('git multi-pack-index write && ls .git/objects/pack',
          label='pack.midx',
          edit=noname)
    r.cap('git repack -a -d -q --write-bitmap-index && '
          'ls .git/objects/pack', label='pack.bitmap',
          edit=noname)
    # 닿지 않는 객체 — 참조에서 떨어진 커밋, 그리고 prune
    tick(r, 100)
    r.sh('git switch -q -c scratch && '
         'git commit -q --allow-empty -m lost && '
         'git switch -q main && git branch -D -q scratch')
    r.cap('git fsck --unreachable --no-reflogs')
    r.cap('git fsck --lost-found --no-reflogs')
    r.cap('git reflog expire --expire=now --all && '
          'git prune --expire=now -v')
    r.cap('git fsck --unreachable --no-reflogs', label='pack.pruned')
    r.cap('git maintenance run --task=gc --quiet && '
          'git count-objects -v', label='pack.maint')
