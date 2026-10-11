# -*- coding: utf-8 -*-
"""make_data.py · fetch_docs.py 시험 — 픽스처는 받아 둔 진짜 RELEASES.md 의 작은 발췌다."""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import fetch_docs  # noqa: E402
import make_data  # noqa: E402

with open(os.path.join(HERE, 'fixtures', 'releases_excerpt.md'), encoding='utf-8') as _f:
    REL = _f.read()


class Releases(unittest.TestCase):
    def test_versions_and_dates_in_file_order(self):
        self.assertEqual(make_data.parse_releases(REL), [
            ('1.65', '2022-11-03'), ('1.62.1', '2022-07-19'), ('1.0', '2015-05-15'),
            ('0.2', '2012-03-29'), ('0.1', '2012-01-20')])

    def test_short_names(self):
        self.assertEqual(make_data.short('1.65.0'), '1.65')
        self.assertEqual(make_data.short('1.62.1'), '1.62.1')
        self.assertEqual(make_data.short('1.0.0'), '1.0')
        self.assertEqual(make_data.short('0.12.0'), '0.12')
        self.assertEqual(make_data.short('0.10'), '0.10')
        self.assertEqual(make_data.short('1.0.0-alpha.2'), '1.0.0-alpha.2')

    def test_sections_hold_their_own_text_only(self):
        s = make_data.sections(REL)
        self.assertIn('Stabilize `let else`', s['1.65'])
        self.assertNotIn('Stabilize `let else`', s['1.62.1'])
        self.assertNotIn('Version 1.62.1', s['1.65'])

    def test_empty_text_gives_nothing(self):
        self.assertEqual(make_data.parse_releases(''), [])
        self.assertEqual(make_data.sections(''), {})

    def test_releases_tsv(self):
        tsv = make_data.releases_tsv(REL)
        self.assertTrue(tsv.startswith('version\tdate\n1.65\t2022-11-03\n'))
        self.assertTrue(tsv.endswith('0.1\t2012-01-20\n'))


class Features(unittest.TestCase):
    def rows(self, *r):
        return [dict(zip(('key', 'version', 'label', 'evidence'), x)) for x in r]

    def test_evidence_found_in_its_version(self):
        rows = self.rows(('let-else', '1.65', 'let-else', r'Stabilize `let else`'))
        self.assertEqual(make_data.check_features(rows, make_data.sections(REL)), [])

    def test_wrong_version_is_caught(self):
        # 기억으로 "1.62 쯤" 이라고 적은 버전이 여기서 걸려야 한다.
        rows = self.rows(('let-else', '1.62.1', 'let-else', r'Stabilize `let else`'))
        self.assertEqual(len(make_data.check_features(rows, make_data.sections(REL))), 1)

    def test_unknown_version_and_bad_regex_and_empty_evidence(self):
        s = make_data.sections(REL)
        self.assertEqual(len(make_data.check_features(self.rows(('a', '9.9', 'a', 'x')), s)), 1)
        self.assertEqual(len(make_data.check_features(self.rows(('a', '1.65', 'a', '(')), s)), 1)
        self.assertEqual(len(make_data.check_features(self.rows(('a', '1.65', 'a', '')), s)), 1)

    def test_duplicate_key(self):
        rows = self.rows(('k', '1.65', 'a', 'GATs'), ('k', '1.65', 'b', 'GATs'))
        self.assertEqual(len(make_data.check_features(rows, make_data.sections(REL))), 1)


class Facts(unittest.TestCase):
    def setUp(self):
        self.docs = tempfile.mkdtemp(prefix='docs-test-')
        self.addCleanup(shutil.rmtree, self.docs, True)
        with open(os.path.join(self.docs, 'releases.txt'), 'w', encoding='utf-8') as f:
            f.write(REL)

    def facts(self, *r):
        return [dict(zip(('id', 'source', 'evidence'), x)) for x in r]

    def test_matched_text_is_recorded(self):
        ev, errs = make_data.match_facts(
            self.facts(('first', 'releases', r'Version 0\.1\s+\(2012-01-20\)')), self.docs)
        self.assertEqual(errs, [])
        self.assertEqual(ev, [('first', 'releases', 'Version 0.1 (2012-01-20)')])   # 공백은 하나로

    def test_a_space_in_evidence_matches_any_run_of_whitespace(self):
        # 받아 둔 글은 문장 가운데서 줄이 바뀐다 — 근거를 한 줄로 적어도 맞아야 한다.
        with open(os.path.join(self.docs, 'post.txt'), 'w', encoding='utf-8') as f:
            f.write('Today we are very proud to announce the\n1.0 release of Rust\n')
        ev, errs = make_data.match_facts(
            self.facts(('one', 'post', r'proud to announce the 1\.0 release')), self.docs)
        self.assertEqual(errs, [])
        self.assertEqual(ev[0][2], 'proud to announce the 1.0 release')

    def test_missing_evidence_and_missing_source(self):
        _, errs = make_data.match_facts(self.facts(('x', 'releases', r'Version 7\.7')), self.docs)
        self.assertEqual(len(errs), 1)
        _, errs = make_data.match_facts(self.facts(('x', 'nowhere', r'Version')), self.docs)
        self.assertEqual(len(errs), 1)

    def test_evidence_is_cut_at_300_chars(self):
        ev, _ = make_data.match_facts(self.facts(('long', 'releases', r'Version 1\.65.*')), self.docs)
        self.assertLessEqual(len(ev[0][2]), 300)


class HtmlText(unittest.TestCase):
    def test_tags_scripts_entities(self):
        h = ('<html><head><title>T</title><style>p{}</style><script>var a="<p>";</script></head>'
             '<body><h1>Announcing&nbsp;Rust 1.0</h1><p>Today we are <em>very</em> proud&hellip;</p>'
             '<ul><li>one</li><li>two &amp; three</li></ul></body></html>')
        t = fetch_docs.html_text(h)
        self.assertIn('Announcing Rust 1.0', t)
        self.assertIn('Today we are very proud…', t)
        self.assertIn('two & three', t)
        self.assertNotIn('var a', t)
        self.assertNotIn('p{}', t)

    def test_block_tags_break_lines(self):
        t = fetch_docs.html_text('<p>a</p><p>b</p><div>c<br>d</div>')
        self.assertEqual([x for x in t.split('\n') if x], ['a', 'b', 'c', 'd'])

    def test_empty(self):
        self.assertEqual(fetch_docs.html_text(''), '')


if __name__ == '__main__':
    unittest.main()
