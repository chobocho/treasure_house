# -*- coding: utf-8 -*-
"""말뭉치의 약속 — PLAN.md §0.10·§5 4단계.

  · 합성 과제는 씨앗에서 똑같이 다시 만들어지고, 훈련과 시험이 겹치지
    않으며, 답이 맞다.
  · 한국어 작품은 전부 1956년 이전에 세상을 떠난 작가의 것이고,
    출처 표의 줄과 파일이 하나씩 맞으며, 위키 문법이 남아 있지 않다.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
CORPUS = os.path.join(BASE, 'corpus')
sys.path.insert(0, CORPUS)

import fetch_ko                                       # noqa: E402
import gen_tasks                                      # noqa: E402


def lines(name):
    p = os.path.join(CORPUS, 'tasks', name)
    return io.open(p, encoding='utf-8').read().split('\n')[:-1]


class TestTasks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = gen_tasks.build()

    def test_files_match_seed(self):
        for name, text in self.files.items():
            p = os.path.join(CORPUS, 'tasks', name)
            got = io.open(p, encoding='utf-8', newline='').read()
            self.assertEqual(got, text, name)

    def test_train_and_test_never_overlap(self):
        for task, sep in (('add', '='), ('addplain', '='),
                          ('sort', '>'), ('reverse', '<'),
                          ('parity', '=')):
            q = lambda l: l.split(sep)[0]
            train = set(q(l) for l in lines(task + '_train.txt'))
            test = [q(l) for l in lines(task + '_test.txt')]
            self.assertEqual(len(set(test)), len(test), task)
            self.assertFalse(train & set(test), task)

    def test_addition_answers(self):
        for l in lines('add_test.txt') + lines('add_train.txt')[:500]:
            m = re.match(r'^(\d{3})\+(\d{3})=(\d{4})$', l)
            self.assertIsNotNone(m, l)
            want = '%04d' % (int(m.group(1)) + int(m.group(2)))
            self.assertEqual(m.group(3), want[::-1], l)

    def test_plain_addition_is_same_problems(self):
        a = [l.split('=')[0] for l in lines('add_test.txt')]
        b = [l.split('=')[0] for l in lines('addplain_test.txt')]
        self.assertEqual(a, b)

    def test_sort_reverse_parity_answers(self):
        for l in lines('sort_test.txt'):
            x, y = l.split('>')
            self.assertEqual(y, ''.join(sorted(x)))
        for l in lines('reverse_test.txt'):
            x, y = l.split('<')
            self.assertEqual(y, x[::-1])
        for l in lines('parity_test.txt'):
            x, y = l.split('=')
            self.assertEqual(int(y), x.count('1') % 2)
            self.assertEqual(len(x), 16)

    def test_every_line_has_fixed_length(self):
        """줄 머리에 맞춰 자르는 배치(SPEC §6.1)가 이 길이에 기댄다."""
        for task, n in (('add', 12), ('sort', 13), ('reverse', 13),
                        ('parity', 18)):
            got = set(len(l) for l in lines(task + '_train.txt'))
            self.assertEqual(got, {n}, task)


class TestKorean(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = fetch_ko.read_sources()

    def test_every_work_fetched_and_listed(self):
        names = set(fetch_ko.fname(a, t) for a, t in fetch_ko.WORKS)
        self.assertEqual(set(self.rows), names)
        for n in names:
            self.assertTrue(os.path.exists(os.path.join(CORPUS, n)), n)

    def test_authors_died_before_1956(self):
        for r in self.rows.values():
            self.assertLess(int(r['died']), 1956, r['file'])

    def test_license_template_is_public_domain(self):
        for r in self.rows.values():
            self.assertTrue(r['license-basis'].startswith('PD-'),
                            r['file'])

    def test_no_wiki_markup_left(self):
        for n in self.rows:
            p = os.path.join(CORPUS, n)
            t = io.open(p, encoding='utf-8').read()
            for mark in ('{{', '}}', '[[', ']]', '<', "''"):
                self.assertNotIn(mark, t, '%s %r' % (n, mark))
            self.assertTrue(t.endswith('\n') and not t.startswith('\n'))

    def test_strip_rules(self):
        w = ("{{머리말\n|제목 = 가 {{틀|안}}\n}}\n"
             "<center>🙝🙟</center>\n\n"
             "[[저자:현진건|현진건]]의 신조(信條)는 '''굳다'''.\n\n\n\n"
             "[[분류:소설]]둘째 줄<ref>각주</ref>  \n"
             "== 라이선스 ==\n{{PD-old-70}}")
        self.assertEqual(fetch_ko.strip(w),
                         '현진건의 신조는 굳다.\n\n둘째 줄\n')
        self.assertEqual(fetch_ko.license_of(w), 'PD-old-70')


if __name__ == '__main__':
    unittest.main()
