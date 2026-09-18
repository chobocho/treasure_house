# -*- coding: utf-8 -*-
"""diff 의 시험 — SPEC.md §11, 8단계 "diff — Myers 알고리즘".

golden/diff/ 는 진짜 `git -c diff.indentHeuristic=false diff --no-index`
의 출력이다. agree 30쌍은 바이트까지 같아야 하고, tie 3쌍은 git 이
같은 길이의 **다른** 편집 스크립트를 고르는 쌍이다 — 거기서는 지운 줄·
끼운 줄의 수가 같고 출력은 달라야 한다(SPEC.md §11.2). 세 영역 사이의
diff 는 golden/scen/diff.scn 이 장면 시험으로 본다.
"""
import os
import shutil
import tempfile
import unittest

from mygit import cli, diff
from mygit.tests import golden

AGREE = golden.tsv('diff', 'agree.tsv')
TIE = golden.tsv('diff', 'tie.tsv')


class Pairs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.env = dict(os.environ, GIT_CEILING_DIRECTORIES=self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_pair(self, stem):
        for ext in ('a', 'b'):
            name = stem + '.' + ext
            with open(os.path.join(self.tmp, name), 'wb') as f:
                f.write(golden.read('diff', name))
        return cli.run(['diff', '--no-index', stem + '.a', stem + '.b'],
                       cwd=self.tmp, env=self.env)


class TestAgainstGit(Pairs):
    def test_s11_agree_pairs_are_byte_identical(self):
        self.assertEqual(len(AGREE), 30)
        for row in AGREE:
            code, out, err = self.run_pair(row['name'])
            want = golden.read('diff', row['name'] + '.diff')
            self.assertEqual((code, out, err),
                             (int(row['exit']), want, b''), row['name'])

    def test_s11_2_tie_pairs_same_size_different_choice(self):
        self.assertEqual(len(TIE), 3)
        for row in TIE:
            code, out, _ = self.run_pair(row['name'])
            body = [l for l in out.split(b'\n')
                    if not l.startswith((b'---', b'+++'))]
            minus = sum(1 for l in body if l.startswith(b'-'))
            plus = sum(1 for l in body if l.startswith(b'+'))
            self.assertEqual((minus, plus),
                             (int(row['minus']), int(row['plus'])),
                             row['name'])
            gits = golden.read('diff', row['name'] + '.diff')
            self.assertNotEqual(out, gits,
                                row['name'] + ' — 분류가 틀렸다')


class TestLinearVariant(unittest.TestCase):
    """PLAN.md §9 결정 7 — Python 만 가진 선형 공간 변형(middle snake).

    같은 길이의 스크립트가 여럿일 때 두 방법은 다른 것을 고를 수 있다.
    그래서 이 시험은 agree 쌍에서만 둘이 같다고 단언한다 — 모든 입력에
    대해 같다는 주장이 아니다.
    """

    def test_decision7_linear_equals_forward_on_agree_pairs(self):
        for row in AGREE:
            stem = row['name']
            a = diff.split_lines(golden.read('diff', stem + '.a'))
            b = diff.split_lines(golden.read('diff', stem + '.b'))
            self.assertEqual(diff.edit_flags(a, b, linear=True),
                             diff.edit_flags(a, b), row['name'])


class TestPieces(unittest.TestCase):
    def test_s11_1_lines_keep_their_newline(self):
        self.assertEqual(diff.split_lines(b'a\nb\nc'),
                         [b'a\n', b'b\n', b'c'])
        self.assertEqual(diff.split_lines(b''), [])
        self.assertEqual(diff.split_lines(b'\n'), [b'\n'])

    def test_s11_2_minimal_edit_count(self):
        a = diff.split_lines(b'a\nb\nc\na\nb\nb\na\n')
        b = diff.split_lines(b'c\nb\na\nb\na\nc\n')
        ra, rb = diff.myers(a, b)
        # Myers 논문 그림 1 의 예 — 가장 짧은 편집 스크립트는 5
        self.assertEqual(sum(ra) + sum(rb), 5)

    def test_s11_3_hunk_header_counts(self):
        text = diff.unified_diff(diff.split_lines(b'x\n'), [])
        self.assertTrue(text.startswith(b'@@ -1 +0,0 @@\n'), text)
        text = diff.unified_diff([], diff.split_lines(b'x\ny\n'))
        self.assertTrue(text.startswith(b'@@ -0,0 +1,2 @@\n'), text)

    def test_s11_3_identical_inputs_have_no_hunks(self):
        a = diff.split_lines(b'same\n')
        self.assertEqual(diff.unified_diff(a, a), b'')


if __name__ == '__main__':
    unittest.main()
