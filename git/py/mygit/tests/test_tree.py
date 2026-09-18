# -*- coding: utf-8 -*-
"""tree 의 시험 — SPEC.md §4.3 · §8.2, 4단계 "정렬 규칙이 전부다".

오라클은 golden/trees/ — 경우마다 진짜 git 이 인덱스에 올린
(모드·blob·경로) 목록(<경우>.tsv)과 write-tree 의 이름(trees.tsv),
그리고 ls-tree -r -t 의 출력(<경우>.ls)이다.
"""
import os
import shutil
import tempfile
import unittest

from mygit import cli, objects, tree, worktree, zlib
from mygit.tests import golden

CASES = golden.tsv('trees', 'trees.tsv')
OBJS = golden.tsv('objects', 'objects.tsv')


def entries_of(case):
    """<경우>.tsv → [(모드, blob 이름, 경로 바이트)]."""
    out = []
    for line in golden.read('trees', case + '.tsv').split(b'\n'):
        if not line or line.startswith(b'#'):
            continue
        mode, oid, path = line.split(b'\t', 2)
        out.append((mode.decode(), oid.decode(), path))
    return out


def unquote(p):
    """ls-tree 가 따옴표로 감싼 경로를 바이트로 되돌린다(시험 전용)."""
    if not p.startswith('"'):
        return p.encode()
    return golden.unescape_c(p[1:-1])


class Git(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gitdir = os.path.join(self.tmp, '.git')
        os.makedirs(os.path.join(self.gitdir, 'objects', 'pack'))

    def tearDown(self):
        for root, _d, files in os.walk(self.tmp):
            for f in files:
                os.chmod(os.path.join(root, f), 0o644)
        shutil.rmtree(self.tmp)


class TestWriteTree(Git):
    def test_s4_3_twelve_trees_have_git_names(self):
        self.assertEqual(len(CASES), 12)
        for row in CASES:
            got = tree.write_tree(self.gitdir, entries_of(row['case']))
            self.assertEqual(got, row['tree'], row['case'])

    def test_s4_3_every_subtree_git_listed_was_written(self):
        for row in CASES:
            tree.write_tree(self.gitdir, entries_of(row['case']))
            ls = golden.read('trees', row['case'] + '.ls').decode()
            for line in ls.split('\n'):
                if not line:
                    continue
                meta = line.split('\t')[0].split(' ')
                if meta[1] == 'tree':
                    t, _ = objects.read_object(self.gitdir, meta[2])
                    self.assertEqual(t, 'tree', line)

    def test_s4_3_flatten_gives_back_the_input(self):
        for row in CASES:
            ents = entries_of(row['case'])
            oid = tree.write_tree(self.gitdir, ents)
            flat = tree.flatten_tree(self.gitdir, oid)
            self.assertEqual(flat, ents, row['case'])


class TestSortRule(unittest.TestCase):
    def test_s4_3_directory_sorts_as_if_it_ended_in_slash(self):
        z = '0' * 40
        ents = [('100644', b'ab', z), ('40000', b'a', z),
                ('100644', b'a=b', z), ('100644', b'a.b', z),
                ('100644', b'a-b', z)]
        body = tree.serialize_tree(ents)
        names = [n for _m, n, _o in tree.parse_tree(body)]
        self.assertEqual(names, [b'a-b', b'a.b', b'a', b'a=b', b'ab'])

    def test_s4_3_plain_name_sort_would_be_wrong(self):
        # 이름만으로 정렬하면 a 가 맨 앞 — 규칙이 왜 있는지 보여 준다
        self.assertLess(tree.tree_entry_key('100644', b'a-b'),
                        tree.tree_entry_key('40000', b'a'))
        self.assertLess(tree.tree_entry_key('100644', b'a'),
                        tree.tree_entry_key('100644', b'a-b'))

    def test_s4_3_mode_is_not_zero_padded_in_the_body(self):
        body = tree.serialize_tree([('40000', b'd', '1' * 40)])
        self.assertTrue(body.startswith(b'40000 d\0'))


class TestParse(unittest.TestCase):
    def test_s4_3_round_trip_on_git_trees(self):
        n = 0
        for row in OBJS:
            if row['type'] != 'tree':
                continue
            raw = zlib.decompress(golden.read('objects', row['id']))
            body = raw.partition(b'\0')[2]
            self.assertEqual(tree.serialize_tree(tree.parse_tree(body)),
                             body)
            n += 1
        self.assertGreaterEqual(n, 2)


class TestQuote(unittest.TestCase):
    def test_s8_2_quoting(self):
        q = worktree.quote_path
        self.assertEqual(q(b'plain.txt'), 'plain.txt')
        self.assertEqual(q(b'sp ace'), 'sp ace')
        self.assertEqual(q(b'sp ace', space=True), '"sp ace"')
        self.assertEqual(q(b'tab\tx'), '"tab\\tx"')
        self.assertEqual(q(b'q"uote'), '"q\\"uote"')
        self.assertEqual(q(b'back\\slash'), '"back\\\\slash"')
        self.assertEqual(q('한글.txt'.encode()),
                         '"\\355\\225\\234\\352\\270\\200.txt"')
        self.assertEqual(q(b'del\x7f'), '"del\\177"')


class TestCatFileTree(Git):
    def test_s9_cat_file_p_tree_matches_ls_tree_top_level(self):
        root = os.path.dirname(self.gitdir)
        env = dict(os.environ, GIT_CEILING_DIRECTORIES=self.tmp)
        for row in CASES:
            tree.write_tree(self.gitdir, entries_of(row['case']))
            ls = golden.read('trees', row['case'] + '.ls').decode()
            want = ''.join(line + '\n' for line in ls.split('\n')
                           if line and b'/' not in
                           unquote(line.split('\t', 1)[1]))
            code, out, _ = cli.run(['cat-file', '-p', row['tree']],
                                   cwd=root, env=env)
            self.assertEqual((code, out.decode()), (0, want),
                             row['case'])


if __name__ == '__main__':
    unittest.main()
