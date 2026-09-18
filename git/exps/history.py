# -*- coding: utf-8 -*-
"""history — 1부(Git 의 역사)의 캡처.

git 자신의 저장소(make mirror 로 받은 부분 복제 mirror/git.git)를
GIT_DIR 로 두고 읽기만 한다. 커밋·태그는 바뀌지 않으니 몇 번을 떠도
같다. 부분 복제라 없는 blob 을 건드리면 네트워크로 받으러 가는데,
GIT_NO_LAZY_FETCH 로 그 길을 막아 두었다 — 받아 둔 것만 쓴다.

mirror 가 없으면(새로 clone 한 사람) 캡처하지 않고 알린다. 덱에 실린
캡처는 커밋되어 있으니 빌드는 그대로 된다.
"""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR = os.path.join(HERE, 'mirror', 'git.git')

FIRST = 'e83c5163'


def run(ctx):
    if not os.path.isdir(MIRROR):
        print('  history: mirror/git.git 이 없다 — make mirror 뒤에 다시')
        return
    r = ctx.repo('history', init=False)
    r.env['GIT_DIR'] = MIRROR
    r.env['GIT_NO_LAZY_FETCH'] = '1'
    # 첫 커밋 — 해시·시각·제목, 원래 객체 그대로, 파일 열한 개
    r.cap("git show -s --format='%H%n%an%n%ad%n%s' --date=iso " + FIRST)
    r.cap('git cat-file -p ' + FIRST)
    r.cap('git ls-tree --name-only ' + FIRST)
    r.cap('git show %s:README | head -21' % FIRST)
    r.cap("git show %s:README | sed -n '/^The object database/,/^$/p'"
          % FIRST)
    r.cap('git ls-tree -r -l %s | wc -l' % FIRST, label='history.count')
    # 첫 걸음들
    r.cap("git log --reverse --format='%h %ad %an %s' --date=short "
          'v1.0.0 | head -5')
    r.cap("git log --reverse --author=Junio --format='%h %ad %an' "
          '--date=short v1.0.0 | head -1')
    r.cap("git log --reverse --merges --format='%h %ad %s' "
          '--date=short v1.0.0 | head -1')
    # v0.99 는 서명된 태그인데 tagger 줄이 없다 — 날짜는 커밋에서
    r.cap('git cat-file -p v0.99 | head -6')
    r.cap('git cat-file -p v1.0.0 | head -6')
    r.cap("git log -1 --format='%h %ad' --date=short v0.99")
    # 판마다의 크기
    for v in ('v1.0.0', 'v2.0.0', 'v2.55.0'):
        r.cap('git rev-list --count %s' % v)
        r.cap('git shortlog -sn %s | wc -l' % v)
    r.cap("git tag -l --format='%(refname:short) %(creatordate:short)'"
          ' v1.0.0 v1.5.0 v2.0.0 v2.55.0 v2.56.0-rc1')
