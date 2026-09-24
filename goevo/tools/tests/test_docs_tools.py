# -*- coding: utf-8 -*-
"""tools/html_text.py 와 tools/fetch_docs.py 의 시험 (PLAN.md §3.1).

픽스처는 2026-09-24 에 go.dev 와 golang/go 에서 받은 진짜 문서의 발췌다
(tools/tests/fixtures/). 기대값은 그 원문에서 눈으로 읽어 적었다.

    python3 -m unittest discover -s tools/tests
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, 'fixtures')
sys.path.insert(0, os.path.dirname(HERE))

import fetch_docs  # noqa: E402
import html_text   # noqa: E402


def fixture(name):
    with io.open(os.path.join(FIX, name), encoding='utf-8') as f:
        return f.read()


def heads(text):
    return [l[2:] for l in text.split('\n') if l.startswith('§\t')]


class RelnotesText(unittest.TestCase):
    def setUp(self):
        self.t = html_text.convert(fixture('relnotes_go122.html'))

    def test_headings_become_section_lines(self):
        self.assertEqual(heads(self.t)[:3], ['Go 1.22 Release Notes',
                                            'Introduction to Go 1.22',
                                            'Changes to the language'])

    def test_package_dt_is_a_heading(self):
        # 부 라이브러리 변경은 <dt> 가 패키지 이름이다 — CITE 의 절이 된다
        h = heads(self.t)
        self.assertIn('Minor changes to the library', h)
        self.assertIn('archive/tar', h)
        self.assertIn('archive/zip', h)

    def test_paragraph_is_one_normalised_line(self):
        self.assertIn('Go 1.22 makes two changes to “for” loops.',
                      self.t.split('\n'))

    def test_list_item_prefix_and_entities(self):
        self.assertTrue(any(l.startswith('- Previously, the variables '
                                         'declared by a “for” loop')
                            for l in self.t.split('\n')), self.t)

    def test_comments_style_nav_footer_dropped(self):
        for junk in ('NOTE: In this document', 'margin: 0.5em',
                     'Footer', 'CL 513316'):
            self.assertNotIn(junk, self.t)

    def test_inline_code_kept_as_text(self):
        self.assertIn('The new method Writer.AddFS adds all of the files '
                      'from an fs.FS to the archive.', self.t)


class PreBlocks(unittest.TestCase):
    def test_pre_kept_verbatim(self):
        t = html_text.convert(fixture('relnotes_go15.html'))
        self.assertIn('m := map[Point]string{\n'
                      '    {29.935523, 52.891566}:   "Persepolis",\n', t)
        self.assertEqual(heads(t), ['Changes to the language', 'Map literals',
                                    'The Implementation'])


class ReleasePage(unittest.TestCase):
    def setUp(self):
        self.lines = html_text.convert(fixture('release.html')).split('\n')

    def test_major_headings(self):
        h = [l for l in self.lines if l.startswith('§\t')]
        self.assertIn('§\tgo1.22.0 (released 2024-02-06)', h)
        self.assertIn('§\tgo1 (released 2012-03-28)', h)

    def test_minor_paragraph_joined(self):
        self.assertTrue(any(l.startswith('go1.22.1 (released 2024-03-05) '
                                         'includes security fixes to the '
                                         'crypto/x509')
                            for l in self.lines))
        self.assertTrue(any(l.startswith('go1.0.1 (released 2012-04-25) was')
                            for l in self.lines))


class GodebugPage(unittest.TestCase):
    def test_version_sections_and_text(self):
        t = html_text.convert(fixture('godebug.html'))
        self.assertEqual(heads(t), ['Go, Backwards Compatibility, and GODEBUG',
                                    'Go 1.22'])
        self.assertIn('This behavior is controlled by the '
                      'httplaxcontentlength setting.', t)
        self.assertNotIn('\nx\n', t)          # footer


class SpecHeader(unittest.TestCase):
    def test_json_header_title_and_subtitle(self):
        t = html_text.convert(fixture('spec_head.html'))
        lines = t.split('\n')
        self.assertEqual(lines[0], '§\tThe Go Programming Language Specification')
        self.assertEqual(lines[1], 'Language version go1.27 (May 26, 2026)')
        self.assertIn('Introduction', heads(t))


class MarkdownText(unittest.TestCase):
    def test_hash_headings(self):
        t = html_text.convert_md(fixture('proposal_readme.md'))
        self.assertEqual(heads(t)[:3], ['Proposing Changes to Go',
                                        'Introduction',
                                        'The Proposal Process'])


# ---------------------------------------------------------------- fetch_docs
RELEASE_TXT = ('§\tRelease History\n'
               '§\tgo1.27.0 (released 2026-08-19)\n'
               'go1.27.1 (released 2026-09-02) includes x\n'
               '§\tgo1.26.0 (released 2026-02-10)\n'
               '§\tgo1.20 (released 2023-02-01)\n'
               '§\tgo1.1 (released 2013-05-13)\n'
               '§\tgo1 (released 2012-03-28)\n')


class FetchPlan(unittest.TestCase):
    def setUp(self):
        self.items = fetch_docs.plan(RELEASE_TXT)
        self.by_path = dict((i['path'], i) for i in self.items)

    def test_majors_from_release_page(self):
        self.assertEqual(fetch_docs.majors(RELEASE_TXT),
                         ['1', '1.1', '1.20', '1.26', '1.27'])

    def test_relnotes_urls_and_paths(self):
        self.assertEqual(self.by_path['relnotes/go1.txt']['url'],
                         'https://go.dev/doc/go1')
        self.assertEqual(self.by_path['relnotes/go1.20.txt']['url'],
                         'https://go.dev/doc/go1.20')
        self.assertEqual(self.by_path['relnotes/go1.20.txt']['kind'], 'html')

    def test_next_version_is_the_draft(self):
        # go.dev/doc/go1.28 는 2026-09-24 에 "No next release note fragments
        # available." 한 줄뿐이었다. 초안 조각은 tip 사이트에만 보인다.
        d = self.by_path['relnotes/go1.28-draft.txt']
        self.assertEqual(d['url'], 'https://tip.golang.org/doc/go1.28')

    def test_api_files_pinned_to_installed_tag(self):
        a = self.by_path['api/go1.20.txt']
        self.assertEqual(a['url'], 'https://raw.githubusercontent.com/golang/'
                                   'go/%s/api/go1.20.txt' % fetch_docs.TAG)
        self.assertEqual(a['kind'], 'raw')
        self.assertIn('api/go1.txt', self.by_path)
        self.assertNotIn('api/go1.28.txt', self.by_path)   # 아직 없다

    def test_fixed_documents_present(self):
        for p in ('release.txt', 'spec.txt', 'go1compat.txt', 'godebug.txt',
                  'toolchain.txt', 'faq.txt', 'proposal-README.txt',
                  'blog/go1.txt', 'blog/index.txt', 'pre_go1.txt',
                  'weekly.txt'):
            self.assertIn(p, self.by_path)

    def test_paths_unique(self):
        paths = [i['path'] for i in self.items]
        self.assertEqual(len(paths), len(set(paths)))


class FetchedLog(unittest.TestCase):
    def test_first_heading(self):
        self.assertEqual(fetch_docs.first_heading('\n\n§\tGo 1.22 Release Notes\n'
                                                  'x\n'), 'Go 1.22 Release Notes')
        self.assertEqual(fetch_docs.first_heading('pkg bytes, func X\n'),
                         'pkg bytes, func X')
        self.assertEqual(fetch_docs.first_heading(''), '')

    def test_fetched_line(self):
        line = fetch_docs.fetched_line('api/go1.txt', 'https://x/y', '2026-09-24',
                                       b'abc', 'pkg a')
        self.assertEqual(line.split('\t'), [
            'api/go1.txt', 'https://x/y', '2026-09-24',
            'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
            'pkg a'])


if __name__ == '__main__':
    unittest.main()
