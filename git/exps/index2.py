# -*- coding: utf-8 -*-
"""index2 — 인덱스(5부)의 나머지.

  · 끝 20바이트 = 앞부분 전체의 SHA-1.
  · 확장 — TREE(캐시 트리)·REUC(충돌 해소 전의 판)·UNTR(추적 안 하는
    파일 캐시)·link(분할 인덱스)·sdir(희소 인덱스). 확장 이름과 크기를
    뽑는 작은 도구로 본다.
  · 판 2·3·4 — 같은 파일 목록을 판마다 적은 크기.
  · add -N(의도만 추가), 충돌 때의 단계 1·2·3.
  · index.lock — 다른 git 이 인덱스를 쓰는 중이면.
"""
from exps.util import commit, tick

# 인덱스의 확장 이름과 크기를 뽑는다(판 2·3 만 — 판 4 는 경로가 눌려
# 항목 길이를 이 식으로 셀 수 없다).
IDXEXT = r'''import struct, sys
d = open(sys.argv[1] if len(sys.argv) > 1 else ".git/index", "rb").read()
ver, n = struct.unpack(">II", d[4:12])
pos = 12
for _ in range(n):
    flags = struct.unpack(">H", d[pos + 60:pos + 62])[0]
    extra = 2 if flags & 0x4000 else 0
    name_end = d.index(b"\0", pos + 62 + extra)
    pos += (name_end - pos + 8) // 8 * 8      # NUL 1~8 개로 8의 배수
print("판 %d, 항목 %d" % (ver, n))
while pos < len(d) - 20:
    sig, size = d[pos:pos + 4], struct.unpack(">I", d[pos + 4:pos + 8])[0]
    print("확장 %s  %d바이트" % (sig.decode("latin-1"), size))
    pos += 8 + size
print("끝 SHA-1 %d바이트" % (len(d) - pos))
'''


# 끝 20바이트가 앞부분의 SHA-1 인지 — 값 자체는 싣지 않는다. 인덱스에는
# ctime·inode 처럼 실행마다 다른 칸이 있어 해시도 매번 달라진다.
SUMCHK = """body=$(head -c -20 .git/index | sha1sum | cut -c1-40)
tail=$(tail -c 20 .git/index | od -A n -t x1 | tr -d ' \\n')
if [ "$body" = "$tail" ]; then echo "끝 20바이트 = 앞부분의 SHA-1"
else echo "다르다"; fi
"""


def files(n):
    return {'dir%02d/file%04d.txt' % (k % 10, k): '%d\n' % k
            for k in range(n)}


def checksum(ctx):
    r = ctx.repo('idxsum')
    commit(r, 0, 'base', {'a.txt': 'a\n', 'b.txt': 'b\n'})
    # 파일 시각을 과거로 — 인덱스와 같은 초에 걸린 "racy" 항목이 있으면
    # status 가 내용을 다시 읽고 인덱스를 새로 쓰기도 해서 캡처가
    # 실행마다 달라진다(5부 racy git 의 장이 바로 그 이야기다)
    r.sh('touch -d @1700000000 a.txt b.txt && git update-index --refresh')
    r.write('../idx-tools/sumchk.sh', SUMCHK)
    r.cap('cat ../idx-tools/sumchk.sh')
    r.cap('sh ../idx-tools/sumchk.sh')
    r.cap('git ls-files --stage')
    # 한 바이트를 바꾸면
    r.sh("python3 -c \"p='.git/index'; b=bytearray(open(p,'rb').read());"
         " b[70]^=1; open(p,'wb').write(b)\"")
    r.cap('sh ../idx-tools/sumchk.sh', label='idxsum.broken')
    r.cap('git fsck 2>&1 | head -3', ok=None, label='idxsum.broken')
    # status 는 끝 SHA-1 을 검사하지 않는다 — 깨진 채로 읽고 넘어간다
    r.cap('git status 2>&1', ok=None, label='idxsum.broken')
    r.cap('sh ../idx-tools/sumchk.sh', label='idxsum.after')
    r.cap('git fsck 2>&1 | head -3', ok=None, label='idxsum.after')
    r.cap('rm .git/index && git reset -q && git status --short',
          label='idxsum.rebuilt')


def extensions(ctx):
    r = ctx.repo('idxext')
    r.write('../idx-tools/idxext.py', IDXEXT)
    tool = 'python3 ../idx-tools/idxext.py'
    r.cap('cat ../idx-tools/idxext.py')
    commit(r, 0, 'base', {'a.txt': 'a\n', 'src/m.c': 'int m;\n',
                          'src/n.c': 'int n;\n'})
    r.cap(tool, label='idxext.commit')
    # 파일 하나를 add 하면 그 경로의 캐시 트리가 무효가 된다
    r.write('src/m.c', 'int m2;\n')
    r.sh('git add src/m.c')
    r.cap('git ls-files --stage --abbrev src && ' + tool,
          label='idxext.added')
    r.cap('git write-tree && ' + tool, label='idxext.written')
    # 추적 안 하는 파일 캐시
    r.sh('git commit -q -m m2')
    # racy 항목을 없앤다(checksum() 의 주석) — 이것 없이는 분할 인덱스
    # 캡처가 네 번 중 한 번 다르게 나왔다. 넣은 뒤 여섯 번 돌려 같았다
    r.sh('touch -d @1700000000 a.txt src/m.c src/n.c && '
         'git update-index --refresh')
    r.cap('git update-index --untracked-cache && git status -s && '
          + tool, label='idxext.untr')
    r.sh('git update-index --no-untracked-cache')
    # 분할 인덱스 — 큰 인덱스의 대부분을 shared 파일로
    r.cap('git update-index --split-index && ' + tool,
          label='idxext.split')
    r.cap("ls .git | grep index | sed 's/[0-9a-f]\\{40\\}$/<이름>/'")
    r.sh('git update-index --no-split-index')


def resolve_undo(ctx):
    r = ctx.repo('idxreuc')
    r.write('../idx-tools/idxext.py', IDXEXT)
    commit(r, 0, 'base', {'f.txt': 'base\n'})
    r.sh('git switch -q -c topic')
    commit(r, 1, 'theirs', {'f.txt': 'theirs\n'})
    r.sh('git switch -q main')
    commit(r, 2, 'ours', {'f.txt': 'ours\n'})
    tick(r, 3)
    r.cap('git merge -q topic 2>&1', ok=None)
    r.cap('git ls-files --stage --abbrev')
    r.cap('git ls-files -u --abbrev')
    r.cap('for s in 1 2 3; do git cat-file -p :$s:f.txt; done')
    r.sh("printf 'merged\\n' > f.txt")
    r.cap('git add f.txt && git ls-files --stage --abbrev')
    r.cap('python3 ../idx-tools/idxext.py', label='idxreuc.after')
    # 해소를 되돌리면 — REUC 가 기억한 세 판이 돌아온다
    r.cap('git checkout -m f.txt && git ls-files -u --abbrev')


def versions(ctx):
    r = ctx.repo('idxver')
    commit(r, 0, 'many', files(2000))
    for v in (2, 3, 4):
        r.cap('git update-index --index-version %d && '
              'wc -c < .git/index' % v, label='idxver.%d' % v)


def intent(ctx):
    r = ctx.repo('idxintent')
    commit(r, 0, 'base', {'a.txt': 'a\n'})
    r.write('new.txt', 'new\n')
    r.cap('git add -N new.txt && git ls-files --stage')
    r.cap('git status --short')
    r.cap('git diff')
    r.cap('git commit -q -m try 2>&1; git log --oneline', ok=None)


def sparse_index(ctx):
    r = ctx.repo('idxsparse')
    r.write('../idx-tools/idxext.py', IDXEXT)
    commit(r, 0, 'base', files(40))
    tool = 'python3 ../idx-tools/idxext.py'
    r.cap(tool, label='idxsparse.full')
    r.cap('git sparse-checkout set --cone --sparse-index dir03 && '
          + tool, label='idxsparse.on')
    r.cap('git ls-files --sparse | tail -4')
    r.cap('git ls-files | wc -l')
    r.cap('ls')


def skip_version(ctx):
    """skip-worktree 비트는 판 3 의 확장 플래그에만 산다."""
    r = ctx.repo('idxskipver')
    commit(r, 0, 'base', {'a.txt': 'a\n', 'b.txt': 'b\n'})
    ver = 'od -A d -t x1 -j 4 -N 4 .git/index | head -1'
    r.cap(ver)
    r.cap('git update-index --skip-worktree a.txt && ' + ver)
    r.cap('git update-index --no-skip-worktree a.txt && ' + ver)


def locked(ctx):
    r = ctx.repo('idxlock')
    commit(r, 0, 'base', {'a.txt': 'a\n'})
    r.sh('touch .git/index.lock')
    r.write('a.txt', 'b\n')
    r.cap('git add a.txt 2>&1', ok=None)


def run(ctx):
    checksum(ctx)
    extensions(ctx)
    resolve_undo(ctx)
    versions(ctx)
    intent(ctx)
    sparse_index(ctx)
    skip_version(ctx)
    locked(ctx)
