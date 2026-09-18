# -*- coding: utf-8 -*-
"""build_deck.tier_report 시험 — a 등급의 증거.

부록의 소스 전문(FULLSRC) 장은 파일 그 자체가 증거다: 역검증이
원본과 한 글자씩 대조하고, 그 파일들은 make test 가 돌린다. 그래서
전문 장(id 가 src- 로 시작하고 data-src 가 달린 코드)은 캡처 없이도
a 를 받는다. 본문의 코드만 있는 장은 여전히 캡처가 있어야 한다.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import build_deck                                  # noqa: E402

CODE = ('<pre><code data-lang="py" data-src="tools/x.py" '
        'data-lines="1-3">x</code></pre>')


def card(aid, inner):
    return ('<article class="card" id="%s">\n%s\n'
            '<span class="tier a">실행 검증</span>\n</article>' % (aid, inner))


class TierTest(unittest.TestCase):
    def run_it(self, doc):
        del build_deck.errors[:]
        build_deck.tier_report(doc)
        return list(build_deck.errors)

    def test_fullsrc_slide_needs_no_capture(self):
        self.assertEqual(self.run_it(card('src-tools-x-py-1', CODE)), [])

    def test_body_code_only_slide_still_fails(self):
        errs = self.run_it(card('p5-code', CODE))
        self.assertEqual(len(errs), 1)
        self.assertIn('p5-code', errs[0])

    def test_src_id_without_code_fails(self):
        self.assertEqual(len(self.run_it(card('src-empty-1', '<p>x</p>'))),
                         1)


if __name__ == '__main__':
    unittest.main()
