# -*- coding: utf-8 -*-
"""merge — fast-forward, 3-way, 충돌, 그리고 전략 옵션들(7부).

같은 모양의 작은 역사를 경우마다 새로 만든다: base 커밋 하나에서
main 과 topic 이 갈라진다. 파일 내용만 바꿔 경우를 가른다.
"""
from exps.util import commit, tick

LINES = ''.join('line %d\n' % i for i in range(1, 9))


def fork(ctx, name, ours, theirs, extra_t=None):
    """base → topic(theirs) · main(ours) 로 갈라진 저장소."""
    r = ctx.repo(name)
    commit(r, 0, 'base', {'f.txt': LINES})
    r.sh('git switch -q -c topic')
    files = {'f.txt': theirs}
    files.update(extra_t or {})
    commit(r, 1, 'theirs', files)
    r.sh('git switch -q main')
    if ours is not None:
        commit(r, 2, 'ours', {'f.txt': ours})
    tick(r, 3)
    return r


def run(ctx):
    # fast-forward — main 이 topic 의 조상
    r = fork(ctx, 'merge_ff', None, LINES + 'line 9\n')
    r.cap('git log --oneline --all --graph')
    r.cap('git merge topic')
    r.cap('git log --oneline --graph', label='merge_ff.after')
    r.cap('cat .git/ORIG_HEAD')
    # --no-ff — 빨리 감을 수 있어도 머지 커밋을 만든다
    r = fork(ctx, 'merge_noff', None, LINES + 'line 9\n')
    r.cap('git merge --no-ff --no-edit topic')
    r.cap('git log --oneline --graph')
    # 3-way 깨끗한 경우 — 서로 먼 줄을 고쳤다
    both = LINES.replace('line 1\n', 'LINE 1\n')
    r = fork(ctx, 'merge_clean', both,
             LINES.replace('line 8\n', 'LINE 8\n'))
    r.cap('git merge --no-edit topic')
    r.cap('cat f.txt')
    r.cap('git log --oneline --graph')
    r.cap('git cat-file -p HEAD')
    # 충돌 — 같은 줄을 다르게
    r = fork(ctx, 'merge_conflict', LINES.replace('line 4', 'ours 4'),
             LINES.replace('line 4', 'theirs 4'))
    r.cap('git merge topic', ok=(1,))
    r.cap('git status')
    r.cap('cat f.txt')
    r.cap('git ls-files --stage')
    r.cap('git diff')
    r.cap('cat .git/MERGE_MSG')
    r.cap('git -c merge.conflictStyle=diff3 checkout --conflict=merge '
          'f.txt && cat f.txt', label='merge_conflict.redo')
    r.cap('git checkout --conflict=diff3 f.txt && cat f.txt')
    r.cap('git checkout --conflict=zdiff3 f.txt && cat f.txt')
    r.cap('git show :1:f.txt | sed -n 4p')
    r.cap('git show :2:f.txt | sed -n 4p')
    r.cap('git show :3:f.txt | sed -n 4p')
    r.cap('git merge --abort')
    r.cap('git status --short', label='merge_conflict.aborted')
    # -X ours / -X theirs — 충돌한 덩어리만 한쪽으로
    r.cap('git merge -X ours --no-edit topic')
    r.cap('sed -n 4p f.txt')
    r.sh('git reset -q --hard HEAD~1')
    r.cap('git merge -X theirs --no-edit topic')
    r.cap('sed -n 4p f.txt', label='merge_conflict.theirs')
    # 스쿼시 — 머지 커밋 없이 결과만
    r = fork(ctx, 'merge_squash', None, LINES + 'line 9\n',
             {'new.txt': 'new\n'})
    r.cap('git merge --squash topic')
    r.cap('git status --short')
    r.cap('git commit -q -m "squashed topic" && '
          'git log --oneline --graph')
    # 문어발(octopus) — 가지 셋을 한 번에
    r = ctx.repo('merge_octopus')
    commit(r, 0, 'base', {'f': 'base\n'})
    for k, b in enumerate(('a', 'b', 'c')):
        r.sh('git switch -q -c %s main' % b)
        commit(r, 1 + k, b, {b: b + '\n'})
    r.sh('git switch -q main')
    tick(r, 5)
    r.cap('git merge --no-edit a b c')
    r.cap('git log --oneline --graph')
    r.cap('git cat-file -p HEAD | head -5')
    # 이름 바꾸기 감지 — ort 는 옮긴 파일에 들어온 고침을 따라간다
    r = ctx.repo('merge_rename')
    commit(r, 0, 'base', {'old.txt': LINES})
    r.sh('git switch -q -c topic')
    commit(r, 1, 'edit', {'old.txt': LINES.replace('line 2', 'LINE 2')})
    r.sh('git switch -q main && git mv old.txt new.txt')
    tick(r, 2)
    r.sh('git commit -q -m rename')
    tick(r, 3)
    r.cap('git merge --no-edit topic')
    r.cap('git ls-files')
    r.cap('sed -n 2p new.txt')
    r.sh('git reset -q --hard HEAD~1')
    r.cap('git -c merge.renames=false merge --no-edit topic '
          '| fold -w 96')
    r.cap('git status --short', label='merge_rename.norename')
    # rerere — 같은 충돌을 두 번째엔 기억으로 푼다
    r = fork(ctx, 'merge_rerere', LINES.replace('line 4', 'ours 4'),
             LINES.replace('line 4', 'theirs 4'))
    r.sh('git config rerere.enabled true')
    r.cap('git merge topic', ok=(1,))
    r.sh("sed -i 's/^<<<<<<< .*//; s/^=======//; s/^>>>>>>> .*//' f.txt"
         " && sed -i '/^$/d' f.txt")
    r.cap('git rerere diff')
    r.sh('git add f.txt && git commit -q --no-edit')
    r.sh('git reset -q --hard HEAD~1')
    r.cap('git merge topic', label='merge_rerere.again', ok=(1,))
    r.cap('cat f.txt')
    r.cap('git rerere status')
