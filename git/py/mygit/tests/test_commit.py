# -*- coding: utf-8 -*-
"""commit·tag·신원 줄과 참조의 시험 — SPEC.md §4.4 · §4.5 · §6, 5단계.

가장 강한 오라클은 "같은 입력에서 같은 이름" 이다. golden/objects 의
커밋(b23b7a5…)과 태그(5702a43…)는 tools/gitenv.sh 의 고정 환경에서
진짜 git 이 만들었다 — mygit 이 같은 트리·같은 환경으로 만든 커밋과
태그는 바이트까지 같아야 하고, 그러면 이름도 같다.
"""
import datetime
import os
import shutil
import tempfile
import unittest

from mygit import cli, commit, objects, refs, zlib
from mygit.tests import golden

OBJS = {r['id']: r for r in golden.tsv('objects', 'objects.tsv')}
ERRORS = {r['command']: r for r in golden.tsv('errors.tsv')}
COMMIT = 'b23b7a5fefc32902eb83feac2800cf158140dcb1'
TAG = '5702a431dba432bfe47c3b3fdda3835a8f542f5c'
ENV = {'GIT_AUTHOR_NAME': 'A U Thor',
       'GIT_AUTHOR_EMAIL': 'author@example.com',
       'GIT_AUTHOR_DATE': '1700000000 +0900',
       'GIT_COMMITTER_NAME': 'C O Mitter',
       'GIT_COMMITTER_EMAIL': 'committer@example.com',
       'GIT_COMMITTER_DATE': '1700000000 +0900'}


def body_of(oid):
    raw = zlib.decompress(golden.read('objects', oid))
    return raw.partition(b'\0')[2]


class TestIdentAndDate(unittest.TestCase):
    def test_s4_4_parse_ident(self):
        self.assertEqual(
            commit.parse_ident('A U Thor <author@example.com> '
                               '1700000000 +0900'),
            ('A U Thor', 'author@example.com', 1700000000, '+0900'))

    def test_s9_1_date_matches_git_log(self):
        # golden/scen/hello.scn: git log 이 찍은 두 날짜
        self.assertEqual(commit.format_date(1700000000, '+0900'),
                         'Wed Nov 15 07:13:20 2023 +0900')
        self.assertEqual(commit.format_date(1700000060, '+0900'),
                         'Wed Nov 15 07:14:20 2023 +0900')

    def test_s9_1_date_other_zones_agree_with_datetime(self):
        # 달력 계산은 손으로 한다 — 표준 datetime 은 증인으로만
        for secs in (0, 86399, 951782400, 1700000000, 2000000000,
                     1709251199, 4102444800):
            for tz in ('+0000', '-0700', '+0530', '-1200', '+1400'):
                sign = -1 if tz[0] == '-' else 1
                off = sign * (int(tz[1:3]) * 3600 + int(tz[3:]) * 60)
                d = datetime.datetime.fromtimestamp(
                    secs, datetime.timezone(
                        datetime.timedelta(seconds=off)))
                want = '%s %s %d %s %s' % (
                    d.strftime('%a'), d.strftime('%b'), d.day,
                    d.strftime('%H:%M:%S %Y'), tz)
                self.assertEqual(commit.format_date(secs, tz), want)

    def test_s1_3_missing_env_is_an_error(self):
        env = dict(ENV)
        del env['GIT_AUTHOR_DATE']
        e = golden.assert_git_error(self, commit.ident_from_env, env,
                                    'AUTHOR')
        self.assertEqual(e.message,
                         'fatal: mygit: GIT_AUTHOR_DATE is not set')
        env['GIT_AUTHOR_DATE'] = 'yesterday'
        e = golden.assert_git_error(self, commit.ident_from_env, env,
                                    'AUTHOR')
        self.assertEqual(e.message, "fatal: mygit: GIT_AUTHOR_DATE is "
                                    "not '<seconds> <+hhmm>'")


class TestMessages(unittest.TestCase):
    def test_s4_4_cleanup_matches_git(self):
        # SPEC.md §4.4 의 예 — 진짜 git commit -m 으로 확인한 것
        self.assertEqual(
            commit.cleanup_message('\n\n  lead  \n\nx   \n '
                                   '\n\n\ny\n\n'),
            '  lead\n\nx\n\ny\n')
        self.assertEqual(commit.cleanup_message('one'), 'one\n')
        self.assertEqual(commit.cleanup_message(' \n \n'), '')

    def test_s4_4_subject_joins_the_first_paragraph(self):
        self.assertEqual(commit.subject_of('second\n\nbody line\n'),
                         'second')
        self.assertEqual(
            commit.subject_of('second\nbody line\n\npara2\n'),
            'second body line')


class TestObjects(unittest.TestCase):
    def test_s4_4_parse_and_rebuild_git_commit(self):
        body = body_of(COMMIT)
        c = commit.parse_commit(body)
        self.assertEqual(c['parents'], [])
        self.assertEqual(commit.serialize_commit(
            c['tree'], c['parents'], c['author'], c['committer'],
            c['message']), body)

    def test_s4_5_tag_bytes_match_git(self):
        body = body_of(TAG)
        tagger = 'C O Mitter <committer@example.com> 1700000000 +0900'
        self.assertEqual(commit.serialize_tag(COMMIT, 'commit', 'v1',
                                              tagger, 'tag message\n'),
                         body)


class Repo(unittest.TestCase):
    """.git 을 mygit init 으로 만든 임시 저장소."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, 'w')
        os.makedirs(self.root)
        self.env = dict(ENV, GIT_CEILING_DIRECTORIES=self.tmp)
        self.gitdir = os.path.join(self.root, '.git')

    def tearDown(self):
        for root, _d, files in os.walk(self.tmp):
            for f in files:
                os.chmod(os.path.join(root, f), 0o644)
        shutil.rmtree(self.tmp)

    def mygit(self, *args):
        return cli.run(list(args), cwd=self.root, env=self.env)

    def plant_all(self):
        for oid in OBJS:
            p = os.path.join(self.gitdir, 'objects', oid[:2], oid[2:])
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'wb') as f:
                f.write(golden.read('objects', oid))

    def first_line(self, result):
        return (result[0], result[2].decode().split('\n')[0])


class TestInit(Repo):
    def test_s5_1_layout_and_message(self):
        code, out, err = self.mygit('init')
        self.assertEqual((code, err), (0, b''))
        self.assertEqual(out.decode(), 'Initialized empty Git '
                         'repository in %s/.git/\n' % self.root)
        with open(os.path.join(self.gitdir, 'HEAD')) as f:
            self.assertEqual(f.read(), 'ref: refs/heads/main\n')
        with open(os.path.join(self.gitdir, 'config')) as f:
            self.assertEqual(f.read(), '[core]\n'
                             '\trepositoryformatversion = 0\n'
                             '\tfilemode = true\n\tbare = false\n'
                             '\tlogallrefupdates = true\n')
        for d in ('objects/pack', 'refs/heads', 'refs/tags'):
            self.assertTrue(os.path.isdir(os.path.join(self.gitdir, d)))

    def test_s5_1_reinit_touches_nothing(self):
        self.mygit('init')
        with open(os.path.join(self.gitdir, 'HEAD'), 'w') as f:
            f.write('ref: refs/heads/dev\n')
        _, out, _ = self.mygit('init')
        self.assertEqual(out.decode(), 'Reinitialized existing Git '
                         'repository in %s/.git/\n' % self.root)
        with open(os.path.join(self.gitdir, 'HEAD')) as f:
            self.assertEqual(f.read(), 'ref: refs/heads/dev\n')

    def test_s5_1_init_into_a_new_directory(self):
        code, out, _ = self.mygit('init', 'sub')
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isdir(os.path.join(self.root, 'sub',
                                                   '.git')))


class TestCommitTreeAndTag(Repo):
    def test_s4_4_commit_tree_reproduces_git_commit(self):
        self.mygit('init')
        self.plant_all()
        tree = commit.parse_commit(body_of(COMMIT))['tree']
        code, out, err = self.mygit('commit-tree', tree, '-m',
                                    'objects')
        self.assertEqual((code, out, err),
                         (0, COMMIT.encode() + b'\n', b''))

    def test_s4_4_parents_and_messages(self):
        self.mygit('init')
        self.plant_all()
        tree = commit.parse_commit(body_of(COMMIT))['tree']
        _, out, _ = self.mygit('commit-tree', tree, '-p', COMMIT,
                               '-m', 'a', '-m', 'b')
        t, body = objects.read_object(self.gitdir, out.strip().decode())
        c = commit.parse_commit(body)
        self.assertEqual((c['parents'], c['message']),
                         ([COMMIT], 'a\n\nb\n'))
        _, out, _ = self.mygit('commit-tree', tree, '-m', '  m1  ')
        _, body = objects.read_object(self.gitdir, out.strip().decode())
        self.assertEqual(commit.parse_commit(body)['message'],
                         '  m1  \n')

    def test_s4_5_annotated_tag_reproduces_git_tag(self):
        self.mygit('init')
        self.plant_all()
        self.mygit('branch', 'main', COMMIT)
        code, out, err = self.mygit('tag', '-a', 'v1', '-m',
                                    'tag message')
        self.assertEqual((code, out, err), (0, b'', b''))
        self.assertEqual(refs.resolve_ref(self.gitdir, 'refs/tags/v1'),
                         TAG)

    def test_s1_4_errors(self):
        self.mygit('init')
        self.plant_all()
        self.mygit('branch', 'main', COMMIT)
        for cmd in ('commit-tree nope -m x', 'branch x nope',
                    'tag t nope', 'branch main', 'branch a..b'):
            row = ERRORS[cmd]
            want = (int(row['exit']), row['stderr-first-line'])
            self.assertEqual(self.first_line(self.mygit(*cmd.split())),
                             want, cmd)
        self.mygit('tag', 't')
        row = ERRORS['tag t']
        self.assertEqual(self.first_line(self.mygit('tag', 't')),
                         (int(row['exit']), row['stderr-first-line']))


class TestBranchAndReflog(Repo):
    def test_s9_2_list_and_create(self):
        self.mygit('init')
        self.plant_all()
        self.assertEqual(self.mygit('branch', 'main', COMMIT)[0], 0)
        self.mygit('branch', 'topic')
        self.assertEqual(self.mygit('branch')[1], b'* main\n  topic\n')
        self.assertEqual(refs.resolve_ref(self.gitdir,
                                          'refs/heads/topic'), COMMIT)

    def test_s6_3_branch_reflog(self):
        self.mygit('init')
        self.plant_all()
        self.mygit('branch', 'main', COMMIT)
        self.mygit('branch', 'topic', 'main')
        log = refs.read_reflog(self.gitdir, 'refs/heads/topic')
        self.assertEqual(log, [('0' * 40, COMMIT,
                                'C O Mitter <committer@example.com> '
                                '1700000000 +0900',
                                'branch: Created from main')])
        code, out, _ = self.mygit('reflog', 'topic')
        want = '%s topic@{0}: branch: Created from main\n' % COMMIT[:7]
        self.assertEqual(out, want.encode())

    def test_s6_3_reflog_line_bytes(self):
        self.mygit('init')
        refs.append_reflog(self.gitdir, 'HEAD', '0' * 40, COMMIT,
                           'X <x@y> 1 +0000', 'commit (initial): t')
        with open(os.path.join(self.gitdir, 'logs', 'HEAD')) as f:
            self.assertEqual(f.read(), '0' * 40 + ' ' + COMMIT +
                             ' X <x@y> 1 +0000\tcommit (initial): t\n')


class TestRevParse(unittest.TestCase):
    """golden/dag/equal — 진짜 git 이 만든 역사. 이름과 7글자는 그
    저장소에서 git log --oneline 이 찍은 것(expect.txt)이다."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.gitdir = os.path.join(cls.tmp, '.git')
        shutil.copytree(golden.path('dag', 'equal', 'git'), cls.gitdir)
        os.makedirs(os.path.join(cls.gitdir, 'objects', 'pack'),
                    exist_ok=True)
        cls.ids = {}
        text = golden.read('dag', 'equal', 'expect.txt').decode()
        block = text.split('$ git log --oneline\n')[1].split('= 0')[0]
        for k, line in enumerate(block.strip().split('\n')):
            abbrev, subject = line.split(' ', 1)
            cls.ids['%d:%s' % (k, subject)] = abbrev

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def rp(self, spec):
        oid = refs.rev_parse(self.gitdir, spec)
        return oid[:7] if oid else None

    def test_s6_2_names_and_suffixes(self):
        i = self.ids
        self.assertEqual(self.rp('HEAD'), i['0:I'])
        self.assertEqual(self.rp('main'), i['0:I'])
        self.assertEqual(self.rp('refs/heads/main'), i['0:I'])
        self.assertEqual(self.rp('main~1'), i["1:Merge branch 't'"])
        self.assertEqual(self.rp('HEAD~2'), i['2:G'])       # 첫 부모
        self.assertEqual(self.rp('HEAD~1^2'), i['3:H'])     # 둘째 부모
        self.assertEqual(self.rp('HEAD^^'), i['2:G'])
        self.assertEqual(self.rp('t'), i['3:H'])
        self.assertEqual(self.rp(i['2:G']), i['2:G'])       # 앞부분
        self.assertEqual(self.rp('HEAD^0'), i['0:I'])
        self.assertIsNone(self.rp('nope'))
        self.assertIsNone(self.rp('HEAD~99'))

    def test_s6_2_tree_suffix(self):
        oid = refs.rev_parse(self.gitdir, 'HEAD^{tree}')
        t, _ = objects.read_object(self.gitdir, oid)
        self.assertEqual(t, 'tree')


if __name__ == '__main__':
    unittest.main()
