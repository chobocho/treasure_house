# -*- coding: utf-8 -*-
"""make_data.py · fetch_sources.py 시험 — 역사 주장은 받아 둔 출처 글에서
근거 정규식이 맞아야만 덱에 들어간다(1부)."""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import fetch_sources  # noqa: E402
import make_data  # noqa: E402

POST = ('Today, we are launching a new, open protocol called\n'
        'Agent2Agent (A2A), with support and contributions from more\n'
        'than 50 technology partners\n')


class Facts(unittest.TestCase):
    def setUp(self):
        self.docs = tempfile.mkdtemp(prefix='docs-test-')
        self.addCleanup(shutil.rmtree, self.docs, True)
        with open(os.path.join(self.docs, 'google-launch.txt'), 'w',
                  encoding='utf-8') as f:
            f.write(POST)

    def facts(self, *r):
        return [dict(zip(('id', 'source', 'evidence'), x)) for x in r]

    def test_matched_text_is_recorded_with_single_spaces(self):
        ev, errs = make_data.match_facts(self.facts(
            ('launch', 'google-launch', r'called Agent2Agent \(A2A\)')), self.docs)
        self.assertEqual(errs, [])
        self.assertEqual(ev, [('launch', 'google-launch', 'called Agent2Agent (A2A)')])

    def test_a_space_in_evidence_matches_a_line_break(self):
        ev, errs = make_data.match_facts(self.facts(
            ('n', 'google-launch', r'more than 50 technology partners')), self.docs)
        self.assertEqual(errs, [])
        self.assertEqual(ev[0][2], 'more than 50 technology partners')

    def test_missing_evidence_missing_source_bad_regex(self):
        for row in (('x', 'google-launch', r'100 partners'),
                    ('y', 'nowhere', r'A2A'),
                    ('z', 'google-launch', r'(unclosed'),
                    ('w', 'google-launch', '')):
            _, errs = make_data.match_facts(self.facts(row), self.docs)
            self.assertEqual(len(errs), 1, row)

    def test_evidence_is_cut_at_300_chars(self):
        ev, _ = make_data.match_facts(
            self.facts(('long', 'google-launch', r'Today.*')), self.docs)
        self.assertLessEqual(len(ev[0][2]), 300)

    def test_duplicate_fact_id_is_an_error(self):
        _, errs = make_data.match_facts(self.facts(
            ('d', 'google-launch', r'Today'), ('d', 'google-launch', r'open')),
            self.docs)
        self.assertEqual(len(errs), 1)

    def test_fact_source_must_be_listed(self):
        rows = self.facts(('a', 'google-launch', 'Today'), ('b', 'other', 'x'))
        errs = make_data.check_sources(rows, [{'key': 'google-launch'}])
        self.assertEqual(len(errs), 1)
        self.assertIn('other', errs[0])


class HtmlText(unittest.TestCase):
    def test_tags_scripts_entities(self):
        h = ('<html><head><title>T</title><style>p{}</style>'
             '<script>var a="<p>";</script></head><body>'
             '<h1>Announcing&nbsp;A2A</h1><p>A <em>new</em> era&hellip;</p>'
             '<ul><li>one</li><li>two &amp; three</li></ul></body></html>')
        t = fetch_sources.html_text(h)
        self.assertIn('Announcing A2A', t)
        self.assertIn('A new era…', t)
        self.assertIn('two & three', t)
        self.assertNotIn('var a', t)
        self.assertNotIn('p{}', t)

    def test_block_tags_break_lines(self):
        t = fetch_sources.html_text('<p>a</p><p>b</p><div>c<br>d</div>')
        self.assertEqual([x for x in t.split('\n') if x], ['a', 'b', 'c', 'd'])

    def test_empty(self):
        self.assertEqual(fetch_sources.html_text(''), '')


if __name__ == '__main__':
    unittest.main()
