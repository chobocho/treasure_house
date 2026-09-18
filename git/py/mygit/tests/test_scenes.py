# -*- coding: utf-8 -*-
"""장면 시험 — golden/scen/*.scn 을 mygit 으로 다시 돌린다
(SPEC.md §16.4).

장면의 기대 출력은 진짜 git 2.55.0 이 채웠다. 이 실행기는 같은 명령을
빈 임시 디렉터리에서 mygit 으로 돌리고, 명령마다 표준 출력·표준 오류·
종료 코드를 한 글자씩 견준다. 장면은 자기에게 필요한 명령이 다
생기는 단계(STEP)부터 켜진다 — 그 전에는 이유를 달고 건너뛴다.
12단계를 마치면 건너뛰는 장면이 하나도 없어야 한다.
"""
import os
import shutil
import tempfile
import unittest

import mygit
from mygit import cli, index, refs, worktree
from mygit.tests import golden

# 장면 → 켜지는 단계 (그 장면이 쓰는 명령이 모두 생기는 단계)
NEEDS = {'plumbing': 6, 'status': 6, 'hello': 7, 'checkout': 9,
         'errors': 10, 'clone': 12}
ENV = {'GIT_AUTHOR_NAME': 'A U Thor',
       'GIT_AUTHOR_EMAIL': 'author@example.com',
       'GIT_COMMITTER_NAME': 'C O Mitter',
       'GIT_COMMITTER_EMAIL': 'committer@example.com'}


def step_of(name):
    return 10 if name.startswith('merge-') else NEEDS[name]


def split_args(line):
    """SPEC.md §16.4 — 공백으로 가르고 "…" 는 한 덩어리."""
    args, cur, i, quoted = [], None, 0, False
    while i < len(line):
        c = line[i]
        if quoted:
            if c == '\\' and i + 1 < len(line):
                n = line[i + 1]
                cur += {'n': '\n', 't': '\t'}.get(n, n)
                i += 2
                continue
            if c == '"':
                quoted = False
            else:
                cur += c
        elif c == '"':
            quoted, cur = True, cur or ''
        elif c.isspace():
            if cur is not None:
                args.append(cur)
                cur = None
        else:
            cur = (cur or '') + c
        i += 1
    if cur is not None:
        args.append(cur)
    return args


def parse(text):
    """.scn → [(명령 줄, [기대 줄 …])].

    기대 줄은 '> ' · '! ' · '= ' 로 시작하거나 '%noeol' 이다.
    """
    steps = []
    for line in text.split('\n'):
        if not line or line.startswith('#'):
            continue
        if line[:2] in ('> ', '! ', '= ') or line == '%noeol':
            steps[-1][1].append(line)
        else:
            steps.append((line, []))
    return steps


def render(out, err, code):
    """실제 결과를 .scn 의 기대 줄 꼴로 — 같은 규칙으로 견주려고."""
    rows = []
    for prefix, data in (('> ', out), ('! ', err)):
        text = data.decode('utf-8', 'surrogateescape')
        if not text:
            continue
        body = text[:-1] if text.endswith('\n') else text
        rows += [prefix + l for l in body.split('\n')]
        if not text.endswith('\n'):
            rows.append('%noeol')
    if code:
        rows.append('= %d' % code)
    return rows


class Scene(object):
    def __init__(self, case, root):
        self.case = case
        self.root = root
        self.cwd = root
        self.env = dict(os.environ, **ENV)
        self.env['GIT_CEILING_DIRECTORIES'] = os.path.dirname(root)
        self.date(1700000000)

    def date(self, secs):
        for who in ('AUTHOR', 'COMMITTER'):
            self.env['GIT_%s_DATE' % who] = '%d +0900' % secs

    def gitdir(self):
        return cli.Ctx(self.cwd, self.env, b'').gitdir()

    def do(self, line):
        """한 줄을 돌려 (표준 출력, 표준 오류, 코드). 손질 줄은 None."""
        a = split_args(line)
        path = os.path.join(self.cwd, a[1]) if len(a) > 1 else None
        if a[0] == '@date':
            self.date(int(a[1]))
        elif a[0] == '@cd':
            self.cwd = os.path.normpath(os.path.join(self.root, a[1]))
        elif a[0] in ('write', 'append'):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'ab' if a[0] == 'append' else 'wb') as f:
                f.write(golden.make(a[2]))
        elif a[0] == 'chmod':
            os.chmod(path, int(a[2], 8))
        elif a[0] == 'rm':
            os.remove(path)
        elif a[0] == 'mkdir':
            os.makedirs(path, exist_ok=True)
        elif a[0] == 'mygit':
            args = [x.replace('<ROOT>', self.root) for x in a[1:]]
            code, out, err = cli.run(args, cwd=self.cwd, env=self.env,
                                     stdin=b'')
            return out, err, code
        elif a[0] == 'cat':
            with open(path, 'rb') as f:
                return f.read(), b'', 0
        elif a[0] == 'stage':
            rows = ''.join('%06o %s %d\t%s\n'
                           % (e.mode, e.oid, e.stage,
                              worktree.quote_path(e.path))
                           for e in index.read_index(self.gitdir()))
            return rows.encode(), b'', 0
        elif a[0] == 'ref':
            oid = refs.rev_parse(self.gitdir(), a[1])
            return (oid + '\n').encode(), b'', 0
        else:
            raise ValueError('모르는 장면 줄: %s' % line)
        return None


class TestScenes(unittest.TestCase):
    pass


def make_test(name):
    def test(self):
        if mygit.STEP < step_of(name):
            self.skipTest('%d단계에서 켜진다' % step_of(name))
        tmp = tempfile.mkdtemp()
        try:
            root = os.path.join(tmp, 'scene')
            os.makedirs(root)
            sc = Scene(name, root)
            text = golden.read('scen', name + '.scn').decode('utf-8')
            for k, (line, want) in enumerate(parse(text)):
                got = sc.do(line)
                if got is None:
                    self.assertEqual(want, [], line)
                    continue
                want = [w.replace('<ROOT>', root) for w in want]
                where = '%s 장면 %d번째 줄: %s' % (name, k, line)
                self.assertEqual(render(*got), want, where)
        finally:
            for r, _d, files in os.walk(tmp):
                for f in files:
                    os.chmod(os.path.join(r, f), 0o644)
            shutil.rmtree(tmp)
    return test


for _f in sorted(os.listdir(golden.path('scen'))):
    _n = _f[:-4]
    setattr(TestScenes, 'test_s16_4_' + _n.replace('-', '_'),
            make_test(_n))


if __name__ == '__main__':
    unittest.main()
