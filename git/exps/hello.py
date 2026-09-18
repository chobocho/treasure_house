# -*- coding: utf-8 -*-
"""hello — 저장소 하나가 태어나 첫 커밋을 갖기까지(2·3·6부).

git init 직후의 .git, 첫 add 가 만드는 blob, 첫 commit 이 만드는
tree·commit, 태그 하나, 그리고 네 형식의 객체를 cat-file 로 연다.
세 영역(작업 트리·인덱스·HEAD)이 명령마다 어떻게 움직이는지도
같은 저장소에서 차례로 찍는다.
"""


def run(ctx):
    r = ctx.repo('hello', init=False)
    r.cap('git init -b main')
    # -type f 가 아니라 ! -type d — 이 기계의 find(bfs)는 proot 위에서
    # git 이 읽기 전용으로 쓴 객체 파일을 '파일' 로 못 알아봐 목록이
    # 조용히 비었다. 뜻은 같고 GNU find 에서도 똑같이 돈다.
    r.cap('find .git ! -type d | sort')
    r.write('hello.txt', 'hello\n')
    r.cap('git status')
    r.cap('git add hello.txt')
    r.cap('git status --short', label='hello.added')
    r.cap('find .git/objects ! -type d | sort', label='hello.added')
    r.cap('git ls-files --stage')
    r.cap('git cat-file -t ce013625030ba8dba906f756967f9e9ca394464a')
    r.cap('git cat-file -p ce013625030ba8dba906f756967f9e9ca394464a')
    r.cap('git commit -m "first commit"')
    r.cap('find .git/objects ! -type d | sort',
          label='hello.committed')
    r.cap('git cat-file -p HEAD')
    r.cap('git cat-file -p HEAD^{tree}')
    r.cap('git log')
    r.cap('cat .git/HEAD')
    r.cap('cat .git/refs/heads/main')
    # 두 번째 커밋 — 부모가 생긴다
    r.env['GIT_AUTHOR_DATE'] = r.env['GIT_COMMITTER_DATE'] = \
        '1700000060 +0900'
    r.write('src/main.c', 'int main(void) { return 0; }\n')
    r.write('hello.txt', 'hello\nworld\n')
    r.cap('git status', label='hello.edited')
    r.cap('git diff')
    r.cap('git add .')
    r.cap('git diff --cached')
    r.cap('git commit -m "add main.c, extend hello"')
    r.cap('git cat-file -p HEAD', label='hello.second')
    r.cap('git log --oneline')
    r.cap('git tag -a v1.0 -m "release 1.0"')
    r.cap('git cat-file -p v1.0')
    r.cap('git count-objects -v')
    # 객체 그래프(도해 hello_objects)의 원료 — 그림은 이것만 읽는다
    r.cap('git cat-file --batch-all-objects --batch-check')
    r.cap('git log --format="%h tree=%t parents=%p %s"')
    r.cap('git ls-tree -r -t --abbrev HEAD~1')
    r.cap('git ls-tree -r -t --abbrev HEAD')
    r.cap('git rev-parse v1.0 v1.0^{commit}')
    # 세 영역: 작업 트리만 · 인덱스까지 · 되돌리기
    r.write('hello.txt', 'hello\nworld\nagain\n')
    r.cap('git status --short', label='hello.wt')
    r.cap('git restore hello.txt')
    r.cap('git status --short', label='hello.restored')
    r.cap('git mv hello.txt greeting.txt')
    r.cap('git status --short', label='hello.moved')
    r.cap('git rm --cached src/main.c')
    r.cap('git status --short', label='hello.rmcached')
    r.cap('git restore --staged src/main.c greeting.txt hello.txt')
    r.cap('git status --short', label='hello.unstaged')
