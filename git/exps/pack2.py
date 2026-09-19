# -*- coding: utf-8 -*-
"""pack2 — 팩파일과 저장소 관리(10부)의 나머지.

  · 팩 안의 객체 — verify-pack 의 칸, cat-file 이 알려 주는 디스크 크기와
    델타 바탕.
  · .idx 의 머리 — 마법 수와 판, 첫 fanout 칸.
  · 크러프트 팩 — 닿지 않는 객체를 지우지 않고 한 팩에 모아 두기.
  · 느슨한 객체가 몇 개면 gc 가 저절로 도나(gc.auto).
  · repack -a -d 와 -A, .keep 팩.
"""
import hashlib
import os

from exps.util import commit, tick

# 델타로 들어간 객체 셋과 그 바탕 — 명령이 길어 스크립트로
DISK = """f='%(objectname) %(objecttype) %(objectsize) %(objectsize:disk)'
git cat-file --batch-all-objects --batch-check="$f %(deltabase)" |
  grep -v ' 0\\{40\\}$' | head -3
b=$(git cat-file --batch-all-objects --batch-check='%(deltabase)' |
  grep -v '^0\\{40\\}$' | head -1)
echo "바탕:"; echo "$b" | git cat-file --batch-check="$f"
"""
BASE = ''.join('row %03d: %s\n' % (i, 'x' * (i % 37)) for i in range(300))


def history(ctx, name, n=12):
    r = ctx.repo(name)
    for k in ('pack.threads 1', 'pack.window 10', 'pack.depth 50',
              'gc.auto 0'):
        r.sh('git config ' + k)
    text = BASE
    for i in range(n):
        text = text.replace('row %03d:' % (i * 7 % 300),
                            'ROW %03d:' % (i * 7 % 300))
        commit(r, i, 'v%02d' % i, {'data.txt': text})
    return r


def inside(ctx):
    r = history(ctx, 'pack_inside')
    r.sh('git gc -q')
    idx = '$(ls .git/objects/pack/*.idx)'
    r.cap('git verify-pack -v %s | head -6' % idx)
    r.write('../pack-tools/disk.sh', DISK)
    r.cap('cat ../pack-tools/disk.sh')
    r.cap('sh ../pack-tools/disk.sh')
    r.cap('od -A d -t x1 -N 16 %s' % idx)
    r.cap('git show-index < %s | head -3' % idx)


def cruft(ctx):
    r = history(ctx, 'pack_cruft', n=4)
    tick(r, 50)
    r.sh('git switch -q -c tmp && git commit -q --allow-empty -m lost && '
         'git switch -q main && git branch -D -q tmp')
    r.sh('git reflog expire --expire=now --all')
    r.cap('git gc -q --cruft --prune=1.week.ago && '
          'ls .git/objects/pack | sed "s/pack-[0-9a-f]*/pack-<이름>/"')
    r.cap('git fsck --unreachable --no-reflogs')
    r.cap('git gc -q --prune=now && ls .git/objects/pack | '
          'sed "s/pack-[0-9a-f]*/pack-<이름>/"', label='pack_cruft.now')
    r.cap('git fsck --unreachable --no-reflogs', label='pack_cruft.now')


def auto(ctx):
    """gc.auto=20 이면 20개를 넘길 때 도는가 — 아니다. v2.55.0 은
    문턱을 256 의 배수로 올리고(builtin/gc.c), 느슨한 객체 수를
    objects/17 디렉터리 하나의 수 × 256 으로 어림한다
    (odb/source-loose.c)."""
    r = ctx.repo('pack_auto')
    r.sh('git config gc.auto 20')
    # 기본은 뒤에서 돈다(gc.autoDetach) — 바로 뒤의 캡처가 끝나기 전의
    # 상태를 찍지 않게 앞에서 돌린다
    r.sh('git config gc.autoDetach false')
    for k in range(10):
        commit(r, k, 'c%d' % k, {'f%d' % k: '%d\n' % k})
    r.cap('git config --get gc.auto')
    r.cap('git count-objects | cut -d, -f1')
    r.cap('git gc --auto && git count-objects | cut -d, -f1')
    r.cap('ls .git/objects/17 2>/dev/null | wc -l')
    # 이름이 17 로 시작하는 blob 둘을 골라 넣는다(내용이 정해져 있어
    # 어느 둘인지도 늘 같다)
    picked = []
    k = 0
    while len(picked) < 2:
        data = ('seventeen %d\n' % k).encode()
        oid = hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()
        if oid.startswith('17'):
            picked.append(k)
        k += 1
    for k in picked:
        r.sh("printf 'seventeen %d\\n' | git hash-object -w --stdin" % k)
    r.cap('ls .git/objects/17 | wc -l', label='pack_auto.more')
    r.cap('git count-objects | cut -d, -f1', label='pack_auto.more')
    r.cap('git gc --auto --quiet && git count-objects -v | '
          'grep -E "^(count|packs)"', label='pack_auto.more')


def trigger(ctx):
    """커밋이 끝에 부르는 것은 무엇인가. 2.54 부터 gc --auto 가 아니라
    maintenance run --auto 이고 기본 전략은 geometric 이다 — 첫 판의
    본문은 "커밋이 gc --auto 를 부른다" 고 적었다(3차 리뷰에서 정정)."""
    r = ctx.repo('pack_trigger')
    r.sh('git config maintenance.autoDetach false')
    r.write('f', '1\n')
    r.sh('git add f')
    r.cap('GIT_TRACE=1 git commit -q -m seed 2>&1 | '
          'grep -o "run_command: .*"')


def keep(ctx):
    r = history(ctx, 'pack_keep', n=3)
    r.sh('git gc -q')
    r.sh('for p in .git/objects/pack/*.pack; do '
         'touch "${p%.pack}.keep"; done')
    commit(r, 10, 'after keep', {'new.txt': 'n\n'})
    r.cap('git repack -a -d -q && ls .git/objects/pack | '
          'sed "s/pack-[0-9a-f]*/pack-<이름>/" | sort | uniq -c')


def run(ctx):
    inside(ctx)
    cruft(ctx)
    auto(ctx)
    trigger(ctx)
    keep(ctx)
