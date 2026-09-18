# -*- coding: utf-8 -*-
"""recovery — 사고 40 장면: 사고 → 진단 → 복구(16부).

장면마다 새 저장소 rec_NN 을 만든다. 대본의 줄은 두 가지다:
'$ ' 로 시작하면 돌리고 캡처한다(out/rec_NN__<slug>.txt), 아니면
준비로만 돌린다. '!' 로 끝나는 캡처 줄은 0 이 아닌 종료 코드를
기대한다(사고 그 자체를 보이는 줄). 같은 명령을 한 장면에서 두 번
찍을 때는 '# 2' 처럼 꼬리를 달아 label 을 가른다.

'@이름=명령' 줄은 명령의 출력을 기억해 뒤 줄의 {이름} 자리에 넣는다
— 되살릴 커밋의 실제 이름을 명령에 그대로 적기 위해서다.

준비 줄에서 쓰는 c NAME 은 파일 NAME 에 NAME 을 써서 커밋하는
셸 함수다 — 대본을 짧게 하려는 것일 뿐, 캡처에는 나오지 않는다.
"""
PRELUDE = ('c() { echo "$1" > "$1" && git add "$1" && '
           'git commit -q -m "$1"; }; ')

SCENES = [
    ('01', '커밋 메시지 오타', [
        'c a', 'echo b > b && git add b && git commit -q -m "fixx b"',
        '$ git log --oneline',
        '$ git commit --amend -q -m "fix b" && git log --oneline']),
    ('02', '파일 하나를 빠뜨린 커밋', [
        'echo a > a && echo b > b && git add a && git commit'
        ' -q -m "a+b"',
        '$ git show --stat --oneline HEAD',
        '$ git add b && git commit -q --amend --no-edit '
        '&& git show --stat --oneline HEAD']),
    ('03', '엉뚱한 브랜치에 커밋', [
        'c base', 'c oops',
        '$ git log --oneline --all --graph --decorate',
        '$ git branch feature && git reset -q --hard HEAD~1 '
        '&& git log --oneline --all --graph --decorate']),
    ('04', '마지막 커밋을 무르기(아직 안 보냄)', [
        'c a', 'c b',
        '$ git reset --soft HEAD~1 && git status --short',
        '$ git log --oneline']),
    ('05', '이미 보낸 커밋을 되돌리기', [
        'c a', 'c bad',
        '$ git revert --no-edit HEAD && git log --oneline',
        '$ ls']),
    ('06', '잘못 스테이지함', [
        'c a', 'echo x >> a && echo y > y && git add .',
        '$ git status --short',
        '$ git restore --staged y && git status --short']),
    ('07', '작업 트리의 변경을 버리기', [
        'c a', 'echo junk >> a',
        '$ git diff --stat',
        '$ git restore a && git status --short && cat a']),
    ('08', 'reset --hard 로 커밋을 날림', [
        'c a', 'c b', 'c c', 'git reset -q --hard HEAD~2',
        '$ git log --oneline',
        '$ git reflog -4',
        '$ git reset -q --hard HEAD@{1} && git log --oneline']),
    ('09', '지운 브랜치 되살리기', [
        'c a', 'git switch -q -c topic', 'c t1', 'c t2',
        'git switch -q main',
        '$ git branch -D topic',
        '$ git reflog | grep "topic" | head -3',
        '$ git branch topic HEAD@{1} && git log --oneline topic']),
    ('10', '분리 HEAD 에서 만든 커밋', [
        'c a', 'c b', 'git switch -q --detach HEAD~1', 'c lost',
        '$ git switch main',
        '$ git branch rescue HEAD@{1} && git log --oneline rescue']),
    ('11', '머지 충돌에서 빠져나오기', [
        'c base', 'git switch -q -c t', 'echo t > base && git'
        ' commit -qam t',
        'git switch -q main', 'echo m > base && git commit -qam m',
        '$ git merge t !',
        '$ git merge --abort && git status --short && git log'
        ' --oneline']),
    ('12', '끝낸 머지를 없던 일로(아직 안 보냄)', [
        'c base', 'git switch -q -c t', 'c t', 'git switch -q'
        ' main', 'c m',
        'git merge -q --no-edit t',
        '$ git log --oneline --graph',
        '$ git reset -q --hard ORIG_HEAD && git log --oneline'
        ' --graph']),
    ('13', '망친 리베이스 되돌리기', [
        'c base', 'git switch -q -c t', 'c t1', 'c t2',
        'git switch -q main', 'c m', 'git switch -q t',
        'git rebase -q main',
        '$ git log --oneline --graph',
        '$ git reset -q --hard ORIG_HEAD && git log --oneline'
        ' --graph']),
    ('14', '리베이스 도중 충돌', [
        'c base', 'git switch -q -c t', 'echo t > base && git'
        ' commit -qam t',
        'git switch -q main', 'echo m > base && git commit -qam m',
        'git switch -q t',
        '$ git rebase main !',
        '$ git rebase --abort && git log --oneline']),
    ('15', '지워 버린 stash 찾기', [
        'c a', 'echo wip >> a && git stash -q', 'git stash drop -q',
        '$ git stash list',
        '$ git fsck --no-reflogs --unreachable | grep commit',
        '$ git fsck --no-reflogs --unreachable | grep commit '
        '| cut -d" " -f3 | xargs git log --no-walk --merges',
        '@WIP=git fsck --no-reflogs --unreachable | grep commit '
        '| cut -d" " -f3 | xargs git rev-list --no-walk --merges '
        '--abbrev-commit',
        '$ git stash apply -q {WIP} && git diff']),
    ('16', '작성자를 잘못 적었다', [
        'GIT_AUTHOR_NAME=Wrong GIT_AUTHOR_EMAIL=wrong@x c a',
        '$ git log --format="%an <%ae> %s"',
        '$ git commit --amend -q --no-edit --reset-author '
        '&& git log --format="%an <%ae> %s"']),
    ('17', '비밀 파일을 커밋했다(마지막 커밋)', [
        'c a', 'echo "token=not-a-real-secret" > .env',
        'git add .env && git commit -q -m "add env"',
        '$ git show --stat --oneline HEAD',
        '$ git rm -q --cached .env && echo .env > .gitignore',
        '$ git add .gitignore && git commit -q --amend --no-edit',
        '$ git show --stat --oneline HEAD',
        '$ git log --all --oneline -- .env',
        # 가지에서는 사라졌지만 옛 커밋은 reflog 가 아직 쥐고 있다
        '$ git show HEAD@{1}:.env']),
    ('18', '비밀이 역사 깊이 들어갔다', [
        'c a', 'echo "token=not-a-real-secret" > .env',
        'git add .env && git commit -q -m env', 'c b', 'c c',
        '$ git log --oneline -- .env',
        '$ FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch '
        '--tree-filter "rm -f .env" HEAD 2>&1 | tail -1',
        '$ git log --oneline -- .env',
        '$ git log --oneline',
        # filter-branch 는 옛 역사를 refs/original 에 백업해 둔다
        '$ git for-each-ref --format="%(refname)" refs/original',
        '$ git log --oneline refs/original/refs/heads/main -- .env']),
    ('19', '큰 파일을 커밋했다', [
        # 0 으로 채우면 zlib 이 수 KB 로 눌러 버린다 — 압축되지 않는
        # (그러나 실행마다 같은) 바이트로
        'c a', 'echo n > note && python3 -c "import random, sys; '
        'random.seed(1); sys.stdout.buffer.write(random.randbytes('
        '3000000))" > big.bin',
        'git add note big.bin && git commit -q -m "note and big"',
        'git gc -q',
        '$ git count-objects -vH | grep size-pack',
        '$ git rm -q --cached big.bin && '
        'git commit -q --amend --no-edit',
        '$ git reflog expire --expire=now --all && '
        'git gc -q --prune=now',
        '$ git count-objects -vH | grep size-pack']),
    ('20', '보내기가 거절됐다(되감기 아님)', [
        'c a', 'git clone -q --bare . ../rec_20.git',
        'git remote add origin ../rec_20.git && git fetch -q',
        'git branch -q -u origin/main',
        'git clone -q ../rec_20.git ../rec_20_other '
        '&& (cd ../rec_20_other && c theirs && git push -q)',
        'c ours',
        '$ git push origin main 2>&1 !',
        '$ git pull -q --rebase && git log --oneline --graph',
        '$ git push -q origin main && git status -sb']),
    ('21', '추적하면 안 될 파일을 추적 중', [
        'c a', 'mkdir build && echo o > build/x.o',
        'git add build && git commit -q -m build',
        '$ git ls-files',
        '$ echo build/ > .gitignore && git rm -r -q --cached build',
        '$ git add .gitignore && git commit -q -m untrack',
        '$ git ls-files',
        '$ git status --short --ignored']),
    ('22', '파일 하나만 옛 판으로', [
        'c a', 'echo v2 > a && git commit -qam v2',
        'echo v3 > a && git commit -qam v3',
        '$ git restore --source=HEAD~2 a && cat a && git'
        ' status --short']),
    ('23', '다른 브랜치의 파일 하나만 가져오기', [
        'c a', 'git switch -q -c t', 'c want', 'c skip', 'git'
        ' switch -q main',
        '$ git restore --source=t --staged --worktree want '
        '&& git status --short']),
    ('24', '커밋 둘을 하나로', [
        'c a', 'c b', 'c b2',
        '$ git reset --soft HEAD~2 && git commit -q -m "b and b2" '
        '&& git log --oneline']),
    ('25', '커밋 하나를 둘로 쪼개기', [
        'c a', 'echo x > x && echo y > y',
        'git add . && git commit -q -m "x and y"',
        '$ git reset -q HEAD~1 && git status --short',
        '$ git add x && git commit -q -m x',
        '$ git add y && git commit -q -m y && git log --oneline']),
    ('26', '커밋 순서 바꾸기', [
        'c a', 'c b', 'c c',
        '$ GIT_SEQUENCE_EDITOR="sed -i \'1{h;d};2G\'" git rebase -q -i '
        'HEAD~2 && git log --oneline']),
    ('27', '브랜치 이름 오타', [
        'c a', 'git branch featrue',
        '$ git branch -m featrue feature && git branch']),
    ('28', '태그를 엉뚱한 커밋에 붙였다', [
        'c a', 'c b', 'git tag v1 HEAD~1',
        '$ git tag -f v1 HEAD && git log --oneline --decorate',
        '$ git tag -d v1']),
    ('29', '커밋 전에 지운 파일', [
        'c a', 'rm a',
        '$ git status --short',
        '$ git restore a && ls']),
    ('30', '오래전에 지운 파일 찾기', [
        'c a', 'c old', 'git rm -q old && git commit -q -m'
        ' "remove old"',
        'c b',
        '$ git log --oneline --diff-filter=D -- old',
        '$ git restore --source=$(git log -1 --format=%h '
        '--diff-filter=D -- old)~1 old && cat old']),
    ('31', '원격에서 지운 브랜치가 남아 있다', [
        'c a', 'git clone -q --bare . ../rec_31.git',
        'git remote add origin ../rec_31.git',
        'git push -q origin HEAD:refs/heads/gone && git fetch -q',
        # 내가 지우면 origin/gone 도 같이 지워진다 — 다른 사람이 지운다
        'git clone -q ../rec_31.git ../rec_31_other '
        '&& git -C ../rec_31_other push -q origin :gone',
        '$ git branch -r',
        '$ git fetch --prune 2>&1 && git branch -r']),
    ('32', '원격과 갈라졌다', [
        'c a', 'git clone -q --bare . ../rec_32.git',
        'git remote add origin ../rec_32.git && git fetch -q',
        'git branch -q -u origin/main',
        'git clone -q ../rec_32.git ../rec_32_other '
        '&& (cd ../rec_32_other && c theirs && git push -q)',
        'c ours', 'git fetch -q',
        '$ git status -sb',
        '$ git log --oneline --graph --all',
        '$ git rebase -q origin/main && git status -sb']),
    ('33', '줄 끝이 전부 바뀐 것처럼 보인다', [
        "printf 'a\\r\\nb\\r\\n' > t.txt && git add t.txt "
        "&& git commit -q -m crlf",
        'echo "*.txt text eol=lf" > .gitattributes && git add'
        ' .gitattributes '
        '&& git commit -q -m attrs',
        '$ git add --renormalize . && git status --short',
        '$ git commit -q -m renormalize && git ls-files --eol t.txt']),
    ('34', '실행 비트만 바뀐 파일이 쏟아진다', [
        'c a', 'c b', 'chmod 755 a b',
        '$ git status --short',
        '$ git config core.fileMode false && git status --short']),
    ('35', 'index.lock 이 남았다', [
        'c a', 'touch .git/index.lock', 'echo x >> a',
        '$ git add a !',
        '$ rm .git/index.lock && git add a && git status --short']),
    ('36', '체리픽 충돌에서 빠져나오기', [
        'c base', 'git switch -q -c t', 'echo t > base && git'
        ' commit -qam t',
        'git switch -q main', 'echo m > base && git commit -qam m',
        '$ git cherry-pick t !',
        '$ git cherry-pick --abort && git status --short && '
        'git log --oneline']),
    ('37', '브랜치를 다른 커밋으로 옮기기', [
        'c a', 'c b', 'c c', 'git branch release HEAD~2',
        '$ git branch -f release HEAD~1 && git log --oneline'
        ' --decorate']),
    ('38', '다 날린 것 같을 때 — 매달린 커밋 찾기', [
        'c a', 'git switch -q -c t', 'c t', 'git switch -q main',
        'git branch -q -D t', 'git reflog expire --expire=now --all',
        '$ git fsck --lost-found',
        '$ ls .git/lost-found/commit',
        '$ git show --stat --oneline $(ls .git/lost-found/commit)']),
    ('39', '.gitignore 가 먹지 않는다', [
        'c a', 'echo log > app.log && git add app.log '
        '&& git commit -q -m log',
        'echo "*.log" > .gitignore && echo more >> app.log',
        '$ git status --short',
        '$ git rm -q --cached app.log && git add .gitignore '
        '&& git status --short']),
    ('40', '오래된 커밋의 메시지 고치기', [
        'c a', 'c tpyo', 'c c',
        '$ git log --oneline',
        '$ GIT_SEQUENCE_EDITOR="sed -i 1s/pick/reword/" '
        'GIT_EDITOR="sed -i s/tpyo/typo/" git rebase -q -i HEAD~2',
        '$ git log --oneline']),
]


def run(ctx):
    rows = []
    for sid, title, script in SCENES:
        r = ctx.repo('rec_' + sid)
        for d in ('../rec_%s.git' % sid, '../rec_%s_other' % sid):
            r.sh('rm -rf ' + d)
        seen, var = {}, {}
        for line in script:
            for k, v in var.items():
                line = line.replace('{%s}' % k, v)
            if line.startswith('@'):
                k, cmd = line[1:].split('=', 1)
                var[k] = r.sh(cmd).strip()
                continue
            if not line.startswith('$ '):
                r.sh(PRELUDE + line)
                continue
            cmd = line[2:]
            ok = (0,)
            if cmd.endswith(' !'):
                cmd, ok = cmd[:-2], None
            n = seen[cmd] = seen.get(cmd, 0) + 1
            label = 'rec_%s%s' % (sid, '' if n == 1 else '.%d' % n)
            r.cap(cmd, label=label, ok=ok)
        rows.append((sid, title))
    ctx.table('recovery', ['장면', '사고'], rows)
