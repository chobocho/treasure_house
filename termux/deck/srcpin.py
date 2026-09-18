# -*- coding: utf-8 -*-
"""핀 고정한 upstream 소스를 그 커밋에서 읽는다 (PLAN.md §1·§3.2).

덱의 원리 장은 termux-app·termux-exec·termux-packages 같은 upstream
저장소의 줄을 보여 준다. 그 줄은 "지금 sources/ 에 체크아웃된 작업
트리" 가 아니라 **data/repos.tsv 에 적은 커밋** 의 것이어야 한다.
작업 트리는 `make sources` 한 번에 움직이지만, 독자가 배지의
repo@sha 를 열었을 때 보는 것은 그 커밋이기 때문이다.
그래서 파일을 열지 않고 `git show <sha>:<path>` 로 읽는다.

조립기(build_deck.py)·역검증(verify_deck.py)·사실 검사(check_claims.py)
가 모두 이 모듈 하나로 읽는다 — 셋이 서로 다른 방법으로 읽으면
셋이 서로 다른 답을 낸다.

시간: 파일 하나에 git 프로세스 한 번, 그 뒤로는 캐시. 공간 O(읽은 파일).
"""
import io
import os
import re
import subprocess

# 짧은 SHA 는 이 길이부터 받는다. git 의 기본 약어 길이와 같다.
MIN_SHA = 7


def split(path):
    """'sources/<저장소>/<경로>' → (저장소, 경로). 아니면 None."""
    parts = path.split('/', 2)
    if len(parts) == 3 and parts[0] == 'sources' and parts[1] and parts[2]:
        return parts[1], parts[2]
    return None


class Pins(object):
    """data/repos.tsv 한 장과 sources/ 체크아웃들."""

    def __init__(self, base):
        self.base = base
        self._repos = None
        self._cache = {}

    def repos(self):
        """{저장소: 행}. 칸 차례는 첫 줄(칸 이름)에서 읽는다."""
        if self._repos is not None:
            return self._repos
        self._repos = {}
        p = os.path.join(self.base, 'data', 'repos.tsv')
        if not os.path.exists(p):
            return self._repos
        head = None
        for line in io.open(p, encoding='utf-8').read().split('\n'):
            if not line.strip() or line.startswith('#'):
                continue
            cols = [c.strip() for c in line.split('\t')]
            if head is None:
                head = cols
                continue
            row = dict(zip(head, cols))
            if row.get('repo'):
                self._repos[row['repo']] = row
        return self._repos

    def sha(self, repo):
        row = self.repos().get(repo)
        return row.get('pinned-sha') if row else None

    def check(self, repo, sha):
        """지시자의 sha= 가 핀과 같은가. 같으면 None, 다르면 까닭."""
        pinned = self.sha(repo)
        if not pinned:
            return '저장소 %r 가 data/repos.tsv 에 없다' % repo
        if not sha or len(sha) < MIN_SHA:
            return '%s: sha= 가 없거나 %d자보다 짧다' % (repo, MIN_SHA)
        if not pinned.startswith(sha):
            return ('%s: sha=%s 가 핀(%s)과 다르다 — 핀을 옮겼으면 '
                    '인용 줄도 다시 볼 것' % (repo, sha, pinned[:12]))
        return None

    def lines(self, path):
        """핀 커밋에서 그 파일의 줄 목록. 없으면 None."""
        if path in self._cache:
            return self._cache[path]
        got = None
        sp = split(path)
        if sp:
            repo, rel = sp
            sha = self.sha(repo)
            where = os.path.join(self.base, 'sources', repo)
            if sha and os.path.isdir(where):
                r = subprocess.run(['git', '-C', where, 'show',
                                    '%s:%s' % (sha, rel)],
                                   capture_output=True)
                if r.returncode == 0:
                    got = r.stdout.decode('utf-8', 'replace').split('\n')
                    if got and got[-1] == '':
                        got.pop()
        self._cache[path] = got
        return got

    def exists(self, path):
        return self.lines(path) is not None

    def grep(self, where, pattern):
        """'저장소:경로' 의 핀 커밋 파일에서 pattern 과 맞는 조각을
        '줄번호:조각' 으로. 줄이 72칸을 넘어 코드 블록에 못 싣는
        파일(XML 따위)을 캡처로 보여 줄 때 쓴다. O(파일 줄 수)."""
        repo, _, path = where.partition(':')
        if '*' in path:
            path = self._glob(repo, path)
        lines = self.lines('sources/%s/%s' % (repo, path))
        if lines is None:
            raise LookupError('핀 커밋에 없다: %s' % where)
        rx = re.compile(pattern)
        return ['%d:%s' % (i, m.group(0))
                for i, line in enumerate(lines, 1)
                for m in rx.finditer(line)]

    def _glob(self, repo, pattern):
        """핀 커밋의 파일 목록에서 pattern 과 맞는 경로 **하나**.
        둘 이상이거나 없으면 LookupError — 어느 파일인지 모호한 캡처는
        싣지 않는다."""
        import fnmatch
        r = subprocess.run(['git', '-C', os.path.join(self.base, 'sources',
                                                      repo),
                            'ls-tree', '-r', '--name-only',
                            self.sha(repo) or 'HEAD'],
                           capture_output=True, text=True)
        hits = [f for f in r.stdout.split('\n')
                if f and fnmatch.fnmatch(f, pattern)]
        if len(hits) != 1:
            raise LookupError('%s:%s 에 맞는 파일이 %d개' % (repo, pattern,
                                                        len(hits)))
        return hits[0]

    def missing(self):
        """핀 커밋이 체크아웃에 없는 저장소들 — make sources-check.

        sources/ 는 커밋하지 않는 캐시다. 지웠거나 얕게 받아 핀 커밋이
        빠졌으면 조립기가 "파일이 없다" 로 수십 번 넘어진다. 그 전에
        한 줄로 알려 준다. O(저장소 수) 번의 git 호출.
        """
        out = []
        for repo, row in sorted(self.repos().items()):
            where = os.path.join(self.base, 'sources', repo)
            sha = row.get('pinned-sha', '')
            if not os.path.isdir(where):
                out.append('%s: sources/%s 가 없다 (make sources)'
                           % (repo, repo))
                continue
            r = subprocess.run(['git', '-C', where, 'cat-file', '-e',
                                '%s^{commit}' % sha], capture_output=True)
            if r.returncode != 0:
                out.append('%s: 핀 커밋 %s 가 체크아웃에 없다 (make sources)'
                           % (repo, sha[:12]))
        return out


def main(argv):
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pins = Pins(base)
    if len(argv) == 3 and argv[0] == 'grep':
        try:
            for line in pins.grep(argv[1], argv[2]):
                print(line)
        except LookupError as err:
            print(err)
            return 1
        return 0
    if '--check' in argv:
        bad = pins.missing()
        for line in bad:
            print('  ✗ ' + line)
        print('핀 고정 저장소 %d개 — 빠진 커밋 %d건'
              % (len(pins.repos()), len(bad)))
        return 1 if bad else 0
    print('사용법: srcpin.py --check | grep 저장소:경로 패턴')
    return 2


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]))
