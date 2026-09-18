# -*- coding: utf-8 -*-
"""doc_text.py 시험 — 위키·마크다운 문서를 인용할 수 있는 글로.

문서를 근거로 쓴 장(b 등급)은 "그 문서의 몇 절" 을 claims.md 에
적는다. 그래서 변환 결과의 제목 줄은 `절번호<TAB>제목` 꼴이어야 하고,
같은 입력이면 같은 번호가 나와야 한다.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import doc_text                                    # noqa: E402

WIKI = """Intro line with '''bold''' and ''it''.

= How does it work =
See [[Package Management|packages]] and [[FAQ]].
{{Note|a template}}
* first
** nested
== Details ==
Visit [https://example.org the site] now.<ref>cite</ref>
<syntaxhighlight lang="bash">
pkg install x
</syntaxhighlight>
= Second =
text
"""


class WikiTest(unittest.TestCase):
    def setUp(self):
        self.t = doc_text.wikitext(WIKI)
        self.lines = self.t.split('\n')

    def test_sections_numbered(self):
        self.assertIn('1\tHow does it work', self.lines)
        self.assertIn('1.1\tDetails', self.lines)
        self.assertIn('2\tSecond', self.lines)

    def test_links_and_markup(self):
        self.assertIn('Intro line with bold and it.', self.lines)
        self.assertIn('See packages and FAQ.', self.lines)
        self.assertIn('Visit the site (https://example.org) now.',
                      self.lines)

    def test_templates_and_refs_dropped(self):
        self.assertNotIn('{{', self.t)
        self.assertNotIn('cite', self.t)

    def test_lists(self):
        self.assertIn('- first', self.lines)
        self.assertIn('  - nested', self.lines)

    def test_code_kept_verbatim(self):
        self.assertIn('pkg install x', self.lines)
        self.assertNotIn('syntaxhighlight', self.t)

    def test_empty(self):
        self.assertEqual(doc_text.wikitext(''), '')


MD = """# Title

Para with **bold** and `code` and [link](https://x.invalid).

## Sub A
<!-- hidden -->
text
### Deep
more
## Sub B
```sh
# not a heading
```
"""


class MarkdownTest(unittest.TestCase):
    def setUp(self):
        self.lines = doc_text.markdown(MD).split('\n')

    def test_sections(self):
        self.assertIn('1\tTitle', self.lines)
        self.assertIn('1.1\tSub A', self.lines)
        self.assertIn('1.1.1\tDeep', self.lines)
        self.assertIn('1.2\tSub B', self.lines)

    def test_heading_inside_code_is_not_a_section(self):
        self.assertIn('# not a heading', self.lines)

    def test_inline_markup(self):
        self.assertIn('Para with bold and code and link '
                      '(https://x.invalid).', self.lines)

    def test_comment_dropped(self):
        self.assertNotIn('<!-- hidden -->', self.lines)

    def test_skipped_level_still_numbers(self):
        got = doc_text.markdown('## A\n#### B\n').split('\n')
        self.assertEqual(got[:2], ['1\tA', '1.1\tB'])


HTML = '''<html><head><title>T</title><style>p{}</style>
<script>var x = "<h2>no</h2>";</script></head><body>
<nav>menu</nav>
<h1>Platforms</h1><p>Intro &amp; more</p>
<h2 id="a">Android 10 (API level 29)</h2><p>Line <b>one</b>.</p>
<h3>Detail</h3><ul><li>x</li><li>y</li></ul>
<pre>code  line</pre>
<h2>Android 9</h2><p>z</p>
</body></html>'''


class HtmlTest(unittest.TestCase):
    def setUp(self):
        self.lines = doc_text.html_text(HTML).split('\n')

    def test_sections(self):
        self.assertIn('1\tPlatforms', self.lines)
        self.assertIn('1.1\tAndroid 10 (API level 29)', self.lines)
        self.assertIn('1.1.1\tDetail', self.lines)
        self.assertIn('1.2\tAndroid 9', self.lines)

    def test_script_style_nav_dropped(self):
        self.assertNotIn('menu', self.lines)
        self.assertNotIn('1.1\tno', self.lines)
        self.assertFalse(any('p{}' in l for l in self.lines))

    def test_text_and_entities(self):
        self.assertIn('Intro & more', self.lines)
        self.assertIn('Line one.', self.lines)
        self.assertIn('- x', self.lines)
        self.assertIn('code  line', self.lines)


class NumberTest(unittest.TestCase):
    def test_shallower_sibling_after_deeper_child(self):
        # 실제 위키(Build-environment.md)에서 난 일: ### 다음 ## 가
        # 같은 번호 1.1 을 두 번 받았다. 번호는 겹치면 안 된다.
        got = doc_text.markdown('# A\n### B\n## C\n## D\n')
        self.assertEqual(got.split('\n'),
                         ['1\tA', '1.1\tB', '1.2\tC', '1.3\tD'])

    def test_new_parent_restarts_children(self):
        got = doc_text.markdown('# A\n## B\n# C\n## D\n')
        self.assertEqual(got.split('\n'),
                         ['1\tA', '1.1\tB', '2\tC', '2.1\tD'])


class FetchTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_mediawiki_from_cache_with_revid(self):
        raw = {'parse': {'title': 'FAQ', 'revid': 42,
                         'wikitext': {'*': '= Q =\nA'}}}
        p = os.path.join(self.d, doc_text.raw_name('faq', 42))
        io.open(p, 'w').write(json.dumps(raw))
        text, rev = doc_text.mediawiki('FAQ', 42, self.d, offline=True)
        self.assertEqual(rev, 42)
        self.assertEqual(text.split('\n')[:2], ['1\tQ', 'A'])

    def test_latest_query_follows_redirects(self):
        # 위키의 문서 이름 여럿이 넘겨주기다(Installing → Installation).
        # page= 로 물을 때는 넘겨주기를 따라가야 본문이 온다.
        q = doc_text.query('Installing', None)
        self.assertEqual(q['redirects'], '1')
        self.assertEqual(q['page'], 'Installing')
        q = doc_text.query('X', 42)
        self.assertEqual(q['oldid'], '42')
        self.assertNotIn('page', q)

    def test_offline_miss(self):
        with self.assertRaises(LookupError):
            doc_text.mediawiki('Nope', 1, self.d, offline=True)

    def test_header(self):
        h = doc_text.header('https://w.invalid/x', 'revid 42',
                            '2026-09-18')
        self.assertEqual(h, '# source: https://w.invalid/x\n'
                            '# pin: revid 42\n# fetched: 2026-09-18\n')


if __name__ == '__main__':
    unittest.main()
