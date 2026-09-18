# -*- coding: utf-8 -*-
"""3-way 파일 합치기의 시험 — SPEC.md §12.3, 10단계.

큰 오라클은 golden/scen/merge-*.scn 13장면(진짜 git merge 의 작업 트리
파일·인덱스·MERGE_MSG·머지 커밋 이름)이다. 여기서는 merge3 하나를
따로 부른다 — 장면의 세 판을 그대로 넣고, 장면에서 git 이 남긴 파일
내용과 같은지 본다. 규칙마다 한 장면이 증거다.
"""
import unittest

from mygit import merge
from mygit.tests import golden


def case(base, ours, theirs):
    return merge.merge3(golden.make(base), golden.make(ours),
                        golden.make(theirs), 't')


class TestMerge3(unittest.TestCase):
    def test_s12_3_adjacent_lines_conflict(self):
        # merge-adjacent.scn — 둘째 줄과 셋째 줄을 따로 고쳐도 충돌
        text, conflicts = case('text:a\\nb\\nc\\nd\\n',
                               'text:a\\nB\\nc\\nd\\n',
                               'text:a\\nb\\nC\\nd\\n')
        self.assertEqual(conflicts, 1)
        self.assertEqual(text, b'a\n<<<<<<< HEAD\nB\nc\n=======\nb\nC\n'
                               b'>>>>>>> t\nd\n')

    def test_s12_3_one_line_apart_is_clean(self):
        text, conflicts = case('text:a\\nb\\nc\\nd\\ne\\n',
                               'text:a\\nB\\nc\\nd\\ne\\n',
                               'text:a\\nb\\nc\\nD\\ne\\n')
        self.assertEqual((text, conflicts), (b'a\nB\nc\nD\ne\n', 0))

    def test_s12_3_refine_keeps_common_lines_outside(self):
        text, conflicts = case('text:a\\nb\\nz\\n',
                               'text:a\\nq\\nw\\ne\\nz\\n',
                               'text:a\\nq\\nr\\ne\\nz\\n')
        self.assertEqual(text, b'a\nq\n<<<<<<< HEAD\nw\n=======\nr\n'
                               b'>>>>>>> t\ne\nz\n')

    def test_s12_3_three_lines_apart_join_four_split(self):
        text, n = case('text:a\\nb\\nm1\\nm2\\nm3\\nd\\ne\\n',
                       'text:a\\n1\\nm1\\nm2\\nm3\\n2\\ne\\n',
                       'text:a\\n3\\nm1\\nm2\\nm3\\n4\\ne\\n')
        self.assertEqual(n, 1)
        text, n = case('text:a\\nb\\nm1\\nm2\\nm3\\nm4\\nd\\ne\\n',
                       'text:a\\n1\\nm1\\nm2\\nm3\\nm4\\n2\\ne\\n',
                       'text:a\\n3\\nm1\\nm2\\nm3\\nm4\\n4\\ne\\n')
        self.assertEqual(n, 2)

    def test_s12_3_identical_change_taken_once(self):
        text, n = case('seq:1:5', 'text:1\\nX\\n3\\n4\\n5\\n',
                       'text:1\\nX\\n3\\n4\\nY\\n')
        self.assertEqual((text, n), (b'1\nX\n3\n4\nY\n', 0))


if __name__ == '__main__':
    unittest.main()
