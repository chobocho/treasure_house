# -*- coding: utf-8 -*-
"""cmdref — 명령어 사전(17부)의 캡처.

data/commands.tsv 의 git-* 명령마다 `git <명령> -h` 의 앞 여섯 줄을
찍는다(사용법 요약). 이 기계에 깔리지 않은 명령(gitk·git gui 같은
Tk 도구, git svn 처럼 펄 모듈이 필요한 것)은 캡처 대신 표에 "이
기계에 없음" 으로 적는다 — 없는 출력을 지어내지 않는다.

자주 쓰는 명령에는 표본 저장소에서의 실제 한 번 실행(EXAMPLES)을
더한다. 표본 저장소는 main 과 topic, 태그 하나, 커밋 넷이다.
"""
import io
import os
import subprocess

from exps.util import commit, tick

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ABSENT = ('is not a git command', "Can't locate", 'unknown command -h',
          'not found', 'No such file or directory')
LIBS = ('sh-i18n', 'sh-setup')  # 셸 스크립트가 . 으로 읽는 것
# -h 를 모르는 명령 — 설치는 돼 있으니 대신 이렇게 사용법을 찍는다
# (git p4 는 파이썬 스크립트라 -h 에 "unknown command" 라고 답한다)
HELP = {'p4': 'git p4 sync --help',
        # -h 앞에 경고문이 여섯 줄 넘게 나온다 — 경고를 끄면 사용법
        'filter-branch': 'env FILTER_BRANCH_SQUELCH_WARNING=1 '
                         'git filter-branch -h'}
# 저장소를 바꾸지 않는 예 — 표본 하나를 같이 쓴다(나머지는 매번 새로).
# 표본은 깨끗해서 작업 트리를 보는 명령은 빈 출력이 된다. 그런 예는
# 준비(파일 고치기)를 명령줄 앞에 드러내 적고 여기서 뺀다.
READONLY = {'annotate', 'archive', 'blame', 'branch', 'cat-file',
            'check-ignore', 'check-ref-format', 'cherry',
            'column', 'count-objects', 'describe',
            'diff', 'diff-tree',
            'fast-export', 'for-each-ref', 'format-patch', 'fsck',
            'grep', 'hash-object', 'interpret-trailers', 'log',
            'ls-files', 'ls-remote', 'ls-tree', 'merge-base',
            'name-rev',
            'patch-id', 'range-diff', 'reflog',
            'rev-list', 'rev-parse', 'shortlog', 'show', 'show-branch',
            'show-ref', 'status', 'stripspace', 'symbolic-ref', 'tag',
            'var', 'whatchanged', 'worktree'}

EXAMPLES = {
    'add': 'echo more >> notes.txt && git add -v notes.txt',
    'annotate': 'git annotate -s app.py',
    'apply': 'git diff HEAD~1 > ../p.diff && '
             'git apply --stat ../p.diff',
    'archive': 'git archive --format=tar HEAD | tar t',
    # main 은 커밋 셋이라 HEAD~2 가 뿌리다 — HEAD~3 은 없는 커밋이라
    # bisect 가 그것을 경로로 받아 이분 탐색을 시작하지 않았다(리뷰 2차)
    'bisect': 'git bisect start HEAD HEAD~2 && git bisect reset',
    'blame': 'git blame -s app.py',
    'branch': 'git branch -v',
    'bundle': 'git bundle create -q ../all.bundle --all && '
              'git bundle list-heads ../all.bundle',
    'cat-file': 'git cat-file -p HEAD',
    'check-attr': 'echo "*.py diff=python" > .gitattributes && '
                  'git check-attr -a app.py',
    'check-ignore': 'git check-ignore -v build/x.o',
    'check-ref-format': 'git check-ref-format --branch topic',
    'cherry': 'git cherry -v main topic',
    'cherry-pick': 'git cherry-pick --no-commit topic && git status -s',
    'clean': 'touch scratch.tmp && git clean -n -d',
    'clone': 'git clone -q . ../cmdref-clone && ls ../cmdref-clone',
    'column': 'printf "a\\nb\\nc\\nd\\n" | git column --mode=column '
              '--width=20',
    'commit': 'echo more >> notes.txt && '
              'git commit -a --dry-run --short',
    'commit-tree': 'git commit-tree HEAD^{tree} -m demo',
    'count-objects': 'git count-objects -v',
    'describe': 'git describe --tags',
    'diff': 'git diff HEAD~1 --stat',
    'diff-files': 'echo more >> notes.txt && git diff-files --abbrev',
    'diff-index': 'echo more >> notes.txt && git diff-index --abbrev HEAD',
    'diff-tree': 'git diff-tree -r HEAD~1 HEAD',
    'fast-export': 'git fast-export HEAD~1..HEAD | head -12',
    'fetch': 'git clone -q . ../cmdref-clone && '
             'git fetch -v ../cmdref-clone 2>&1',
    'for-each-ref': 'git for-each-ref',
    'format-patch': 'git format-patch -1 --stdout | head -12',
    'fsck': 'git fsck --strict; echo "exit $?"',
    'gc': 'git gc -q && git count-objects -v',
    'grep': 'git grep -n return',
    'hash-object': 'git hash-object app.py',
    'interpret-trailers': 'printf "msg\\n\\nSigned-off-by: A <a@x>\\n" '
                          '| git interpret-trailers --parse',
    'log': 'git log --oneline --graph --all',
    'ls-files': 'git ls-files -s',
    'ls-remote': 'git ls-remote .',
    'ls-tree': 'git ls-tree HEAD',
    'merge-base': 'git merge-base main topic',
    'merge-tree': 'git merge-tree --write-tree main topic',
    'mktree': 'git ls-tree HEAD | git mktree',
    'mv': 'git mv notes.txt NOTES.txt && git status -s',
    'name-rev': 'git name-rev HEAD~1',
    'notes': 'git notes add -m "reviewed" HEAD && git notes show HEAD',
    'patch-id': 'git show HEAD | git patch-id',
    'range-diff': 'git range-diff main~1..main topic~1..topic',
    'read-tree': 'git read-tree --empty && git ls-files | wc -l',
    'reflog': 'git reflog -3',
    'remote': 'git remote add up ../cmdref-clone && git remote -v',
    'repack': 'git repack -a -d -q && ls .git/objects/pack | cut -c1-5,46-',
    'replace': 'git replace HEAD~1 topic && git replace --list',
    'reset': 'git reset --soft HEAD~1 && git status -s',
    'restore': 'echo more >> app.py && git add app.py && '
               'git restore --staged app.py && git status -s',
    'rev-list': 'git rev-list --count --all',
    'rev-parse': 'git rev-parse --show-toplevel HEAD --abbrev-ref HEAD',
    'rm': 'git rm --cached -q notes.txt && git status -s',
    'shortlog': 'git shortlog -sn --all',
    'show': 'git show --stat HEAD',
    'show-branch': 'git show-branch main topic',
    'show-ref': 'git show-ref',
    'sparse-checkout': 'git sparse-checkout set --no-cone /app.py && '
                       'git sparse-checkout list && ls',
    'stash': 'echo more >> notes.txt && '
             'git stash push -q -m wip && git stash list',
    'status': 'git status',
    'stripspace': 'printf "a  \\n\\n\\n\\nb\\n" | git stripspace',
    'switch': 'git switch topic 2>&1',
    'symbolic-ref': 'git symbolic-ref HEAD',
    'tag': 'git tag -n',
    'update-index': 'git update-index --chmod=+x app.py && '
                    'git ls-files -s app.py',
    'update-ref': 'git update-ref refs/heads/copy HEAD && '
                  'git branch --list copy',
    'var': 'git var GIT_COMMITTER_IDENT',
    'verify-pack': 'git gc -q && '
                   'git verify-pack -s .git/objects/pack/*.idx',
    'whatchanged': 'git whatchanged --oneline -1 '
                   '--i-still-use-this 2>&1 | head -5',
    'worktree': 'git worktree list',
    'write-tree': 'git write-tree',
}


def names():
    out = []
    path = os.path.join(HERE, 'data', 'commands.tsv')
    for line in io.open(path, encoding='utf-8'):
        cols = line.rstrip('\n').split('\t')
        if cols[0].startswith('git-'):
            out.append(cols[0][4:])
        elif cols[0] in ('gitk', 'gitweb', 'scalar'):
            out.append(cols[0])
    return out


def sample(ctx, name):
    r = ctx.repo(name)
    r.sh('rm -rf ../cmdref-clone ../all.bundle ../p.diff')
    commit(r, 0, 'init', {'app.py': 'def f():\n    return 1\n',
                          'notes.txt': 'n\n', '.gitignore': 'build/\n'})
    r.sh('git tag -a v1 -m v1')
    commit(r, 1, 'second', {'app.py': 'def f():\n    return 2\n'})
    r.sh('git switch -q -c topic')
    commit(r, 2, 'topic', {'t.txt': 't\n'})
    r.sh('git switch -q main')
    commit(r, 3, 'third', {'app.py': 'def f():\n    return 3\n'})
    r.write('build/x.o', 'o\n')
    tick(r, 4)
    return r


def run(ctx):
    r = sample(ctx, 'cmdref')
    rows = []
    for name in names():
        cmd = HELP.get(name) or ('git %s -h' % name
                                 if not name.startswith(('git', 'scalar'))
                                 else '%s -h' % name)
        p = subprocess.run(['sh', '-c', 'timeout 10 %s 2>&1 | head -6'
                            % cmd], cwd=r.path, env=r.env,
                           stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE)
        text = p.stdout.decode('utf-8', 'replace')
        if name in LIBS:
            rows.append((name, '셸 라이브러리 — 직접 부르지 않는다'))
            continue
        if not text.strip() or any(a in text for a in ABSENT):
            rows.append((name, '이 기계에 없음'))
            continue
        wide = any(len(l) > 100 for l in text.split('\n'))
        r.cap('%s 2>&1 | head -6%s' % (cmd, ' | cut -c1-100' if wide
                                         else ''), ok=None)
        rows.append((name, '-h · 실행' if name in EXAMPLES else '-h'))
    # 실행 예 — 명령마다 표본 저장소를 새로 만든다(서로 섞이지 않게)
    shared = sample(ctx, 'cmdref_ro')
    for name, cmd in sorted(EXAMPLES.items()):
        r = shared if name in READONLY else sample(ctx, 'cmdref_ex')
        r.cap(cmd, label='cmdref_ex', ok=None)
    ctx.table('cmdref', ['명령', '캡처'], rows,
              'data/commands.tsv 의 명령 %d개' % len(rows))
