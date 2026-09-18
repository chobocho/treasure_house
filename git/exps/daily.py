# -*- coding: utf-8 -*-
"""daily — 활용 가이드 I(15부): 날마다 쓰는 레시피.

  · 부분 스테이징 — add -p 에 답을 흘려 넣어 덩어리 하나만.
  · 커밋 나누기 — reset -p 로 스테이징의 일부를 되돌리기.
  · stash 레시피 — 파일 하나만(-- 경로), 메시지, branch 로 꺼내기.
  · log 레시피 — 누가·언제·무엇·어디를 조건으로.
  · grep — 커밋에서 찾기, 함수 문맥.
  · 별칭 모음.
"""
from exps.util import commit, tick

TWO = ''.join('line %02d\n' % i for i in range(1, 21))


def partial(ctx):
    r = ctx.repo('daily_addp')
    commit(r, 0, 'base', {'f.txt': TWO})
    changed = TWO.replace('line 02', 'LINE 02').replace('line 19',
                                                         'LINE 19')
    r.write('f.txt', changed)
    r.cap('git diff --stat')
    # ? 는 답의 뜻을 보여 준다 — q 로 아무것도 올리지 않고 나온다
    r.cap("printf '?\\nq\\n' | git add -p 2>&1 | sed -n 's/.*? y - /y - /; /^. - /p'",
          label='daily_addp.help')
    # 덩어리 둘 가운데 첫째만 올린다 — y(올림) n(건너뜀)
    r.cap("printf 'y\\nn\\n' | git add -p 2>&1 | grep -v '^$'")
    r.cap('git diff --cached --stat')
    r.cap('git diff --stat', label='daily_addp.after')
    r.cap("printf 'y\\n' | git reset -p 2>&1 | tail -2",
          label='daily_addp.reset')
    r.cap('git diff --cached --stat', label='daily_addp.reset')


def stashes(ctx):
    r = ctx.repo('daily_stash')
    commit(r, 0, 'base', {'a.txt': 'a\n', 'b.txt': 'b\n'})
    r.write('a.txt', 'a2\n')
    r.write('b.txt', 'b2\n')
    tick(r, 1)
    r.cap('git stash push -q -m "only a" -- a.txt && git status --short')
    r.cap('git stash list')
    r.cap('git stash branch try-a 2>&1 | head -4')
    r.cap('git branch --show-current && git status --short',
          label='daily_stash.after')


def logs(ctx):
    r = ctx.repo('daily_log')
    people = [('alice', 'feat: login form', {'login.c': 'l\n'}),
              ('bob', 'fix: typo in README', {'README': 'r\n'}),
              ('alice', 'feat: logout', {'login.c': 'l\nlo\n'}),
              ('carol', 'docs: usage', {'README': 'r\nu\n'}),
              ('bob', 'fix: null check in login', {'login.c': 'l\nlo\nn\n'})]
    for k, (who, msg, files) in enumerate(people):
        r.env['GIT_AUTHOR_NAME'] = who
        r.env['GIT_AUTHOR_EMAIL'] = '%s@example.com' % who
        commit(r, k * 60, msg, files)
    recipes = [
        'git log --oneline --author=alice',
        'git log --oneline --grep=fix',
        'git log --oneline -i --grep=LOGIN',
        'git log --oneline -- README',
        'git log --oneline --since=1700007200 --until=1700014400',
        'git log --oneline --reverse',
        'git log --oneline -2',
        'git log --format="%h %<(6)%an %s"',
        'git log --oneline --name-only -2',
        # 파이프·스크립트 안에서 리비전 없는 shortlog 는 표준 입력을
        # 읽는다 — 터미널이 아니면 HEAD 를 적어 줘야 한다
        'git shortlog -sn < /dev/null',
        'git shortlog -sn HEAD',
        'git shortlog --format="%s" HEAD -- login.c',
        'git log -1 --format="%H%n%an <%ae>%n%ad" --date=iso',
    ]
    for cmd in recipes:
        r.cap(cmd)
    r.cap('git log --oneline --no-merges --diff-filter=A --name-only')
    r.cap("git show :/typo --stat --format=%s")
    r.cap('git grep -n "lo" HEAD~2 -- login.c')


def pickaxe(ctx):
    # 픽액스 — -S 는 그 문자열의 "개수" 가 바뀐 커밋, -G 는 그 정규식이
    # 걸린 줄이 바뀐 커밋. 줄을 고치기만 하면 -S 에는 안 걸린다
    r = ctx.repo('daily_pick')
    commit(r, 0, 'add call', {'m.c': 'frotz(a);\n'})
    commit(r, 1, 'keep result', {'m.c': 'x = frotz(a);\n'})
    commit(r, 2, 'drop call', {'m.c': 'x = 0;\n'})
    r.cap('git log --oneline -S "frotz(a)"')
    r.cap('git log --oneline -G "frotz"')


def aliases(ctx):
    r = ctx.repo('daily_alias')
    commit(r, 0, 'base', {'a.txt': 'a\n'})
    commit(r, 1, 'second', {'a.txt': 'a\nb\n'})
    for k, v in (('st', 'status -sb'),
                 ('lg', 'log --oneline --graph --decorate'),
                 ('last', 'log -1 --stat'),
                 ('unstage', 'restore --staged'),
                 ('amend', 'commit --amend --no-edit'),
                 ('who', '!git shortlog -sn --no-merges HEAD')):
        r.sh("git config alias.%s '%s'" % (k, v))
    r.cap('git config --get-regexp "^alias\\."')
    r.cap('git st')
    r.cap('git lg')
    r.cap('git who')
    r.write('a.txt', 'a\nb\nc\n')
    r.sh('git add a.txt')
    r.cap('git unstage a.txt && git st', label='daily_alias.unstage')


def tidy(ctx):
    r = ctx.repo('daily_tidy')
    commit(r, 0, 'base', {'app.c': 'int main;\n'})
    r.sh('git switch -q -c feat')
    commit(r, 1, 'add parser', {'parse.c': 'parse\n'})
    commit(r, 2, 'add printer', {'print.c': 'print\n'})
    # 리뷰에서 parser 의 오타를 지적받았다 — 고친 것을 그 커밋에 붙이기로
    r.write('parse.c', 'parse();\n')
    tick(r, 3)
    r.cap('git add parse.c && git commit -q --fixup=":/add parser" '
          '&& git log --oneline main..')
    r.cap('git config rebase.autoSquash true')
    r.cap('GIT_SEQUENCE_EDITOR=true git rebase -q -i main && '
          'git log --oneline main..', label='daily_tidy.squashed')
    r.cap('git show HEAD~:parse.c', label='daily_tidy.squashed')
    # 메시지만 고치는 amend! (reword) 커밋
    tick(r, 4)
    r.write('../reword.sh', "#!/bin/sh\n"
            "sed -i 's/^add printer$/add printer (stdout)/' \"$1\"\n", 0o755)
    r.cap('GIT_EDITOR=../reword.sh git commit -q --fixup=reword:HEAD && '
          'git log --format=%B -1', label='daily_tidy.reword')
    r.cap('GIT_SEQUENCE_EDITOR=true git rebase -q -i main && '
          'git log --oneline main..', label='daily_tidy.reword')


# git 은 프롬프트·완성 스크립트를 같이 싣는다 — 경로는 배포판마다
# 다르지만 이 git 에선 exec-path 에서 두 칸 위 etc/bash_completion.d
PS1 = '''#!/bin/bash
. "$(git --exec-path)/../../etc/bash_completion.d/git-prompt.sh"
GIT_PS1_SHOWDIRTYSTATE=1
GIT_PS1_SHOWUNTRACKEDFILES=1
__git_ps1 '(%s)'; echo
'''


def prompt(ctx):
    r = ctx.repo('daily_ps1')
    commit(r, 0, 'base', {'a.txt': 'a\n'})
    r.write('../ps1.sh', PS1, 0o755)
    r.cap('cat ../ps1.sh')
    r.cap('ls "$(git --exec-path)/../../etc/bash_completion.d" | grep git')
    r.cap('../ps1.sh', label='daily_ps1.clean')
    r.write('a.txt', 'a2\n')
    r.cap('../ps1.sh', label='daily_ps1.dirty')
    r.sh('git add a.txt')
    r.write('new.txt', 'n\n')
    r.cap('../ps1.sh', label='daily_ps1.staged')
    tick(r, 1)
    r.sh('git commit -q -m main2 && rm new.txt && git switch -q -c t HEAD~ '
         '&& echo t > a.txt && git commit -qam t')
    r.cap('git merge -q main >/dev/null 2>&1; ../ps1.sh',
          label='daily_ps1.merge')


def run(ctx):
    partial(ctx)
    stashes(ctx)
    logs(ctx)
    pickaxe(ctx)
    tidy(ctx)
    aliases(ctx)
    prompt(ctx)
