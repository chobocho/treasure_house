# -*- coding: utf-8 -*-
"""md_text.py · fetch_docs.py 의 시험 (PLAN.md §0.7, §4 2단계).

픽스처는 2026-10-01 에 받은 진짜 문서의 발췌다(tools/tests/fixtures/).
md_text 는 '§<TAB>제목' 줄을 만드는 것이 일의 전부다 — 이 줄이 CITE
sec= 의 과녁이라, 제목 하나를 잘못 읽으면 인용이 통째로 엉뚱해진다.

    python3 -m unittest discover -s tools/tests
"""
import io
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
FIX = os.path.join(HERE, 'fixtures')

import fetch_docs   # noqa: E402
import md_text      # noqa: E402


def fixture(name):
    with io.open(os.path.join(FIX, name), encoding='utf-8') as f:
        return f.read()


def heads(text):
    return [l[2:] for l in text.split('\n') if l.startswith('§\t')]


class MdText(unittest.TestCase):
    def test_version_history_headings(self):
        out = md_text.convert(fixture('version-history.md'))
        h = heads(out)
        # '\#' 는 마크다운 이스케이프다 — 제목 글자에는 '#' 로 남는다
        self.assertEqual(h[:2], ['The history of C#', 'C# version 14'])
        self.assertIn('*Released November 2025*', out.split('\n'))

    def test_front_matter_is_not_a_setext_heading(self):
        # 머리말의 닫는 '---' 앞줄(ms.custom: …)을 setext h2 로 읽으면 안 된다
        out = md_text.convert(fixture('version-history.md'))
        self.assertFalse(any(x.startswith('ms.') or x.startswith('title:')
                             for x in heads(out)), heads(out))
        self.assertIn('title: The history of C#', out)

    def test_setext_title_and_atx_version_headings(self):
        out = md_text.convert(fixture('language-version-history.md'))
        h = heads(out)
        self.assertEqual(h[0], 'Features Added in C# Language Versions')
        self.assertIn('C# 15.0 - .NET 11 and Visual Studio 2026 version 18.8',
                      h)
        self.assertNotIn('====================', out)

    def test_inline_code_in_heading(self):
        out = md_text.convert(fixture('csharp-14.md'))
        self.assertEqual(heads(out), ['The field keyword'])

    def test_fenced_code_is_verbatim_and_never_a_heading(self):
        out = md_text.convert(fixture('ignored-directives.md'))
        self.assertEqual(heads(out), ['Ignored directives for file-based apps',
                                      'Summary'])
        self.assertIn('\n#!/usr/bin/dotnet run\n', out)
        self.assertIn('\n#:sdk      Microsoft.NET.Sdk.Web\n', out)

    def test_byte_order_mark_does_not_hide_the_first_heading(self):
        # Roslyn 의 깨지는 변경 문서 몇 개는 BOM 으로 시작한다
        out = md_text.convert(fixture('bom-heading.md'))
        self.assertTrue(heads(out)[0].startswith(
            'This document lists known breaking changes in Roslyn in C# 10.0'),
            heads(out))

    def test_clean_heading_markup(self):
        c = md_text.clean
        self.assertEqual(c('[`params` collections](https://x/y.md)'),
                         'params collections')
        self.assertEqual(c('**Bold** and *em* {#anchor}'), 'Bold and em')
        self.assertEqual(c('Title ##'), 'Title')
        # Language-Version-History.md 의 진짜 제목 — 주소 안에 괄호가 있다
        self.assertEqual(c('[C# 2](https://msdn.microsoft.com/library/'
                           '7cz8t42e(v=vs.80).aspx) - Visual Studio 2005'),
                         'C# 2 - Visual Studio 2005')
        self.assertEqual(c('C\\# and <sup>1</sup>'), 'C# and 1')


class Plan(unittest.TestCase):
    def setUp(self):
        self.tree = json.loads(fixture('csharplang-tree.json'))
        self.index = json.loads(fixture('releases-index.json'))

    def test_proposals_only_shipped_or_planned_versions(self):
        items = fetch_docs.proposal_items(self.tree)
        paths = [i['path'] for i in items]
        self.assertEqual(paths, [
            'csharplang/proposals/csharp-14.0/field-keyword.txt',
            'csharplang/proposals/csharp-15.0/unions.txt',
            'csharplang/proposals/csharp-7.3/tuple-equality.txt'])
        self.assertTrue(all(i['kind'] == 'md' for i in items))
        self.assertIn(fetch_docs.CSLANG_SHA, items[0]['url'])

    def test_channels_from_index(self):
        items = fetch_docs.channel_items(self.index)
        self.assertEqual([i['path'] for i in items],
                         ['releases/1.0.json', 'releases/10.0.json'])
        self.assertTrue(items[1]['url'].endswith(
            '/release-notes/10.0/releases.json'))
        self.assertIn(fetch_docs.CORE_SHA, items[1]['url'])

    def test_every_github_source_is_pinned(self):
        # main 은 받는 날마다 바뀐다 — 인용한 줄이 다음 주에 사라지면 안 된다
        items = fetch_docs.plan(self.tree, self.index)
        gh = [i['url'] for i in items if 'githubusercontent.com' in i['url']]
        self.assertTrue(gh)
        for u in gh:
            self.assertRegex(u, r'githubusercontent\.com/[^/]+/[^/]+/'
                                r'[0-9a-f]{10,40}/', u)

    def test_removed_whatsnew_pages_come_from_the_parent_commit(self):
        items = dict((i['path'], i['url'])
                     for i in fetch_docs.plan(self.tree, self.index))
        self.assertIn('655ed4584ee2a847e878579f39c7e9aecc7607fb',
                      items['whatsnew/csharp-11.txt'])
        self.assertIn('d3acaab7be1b9ddd4d9038bedf49869a0ff88106',
                      items['whatsnew/csharp-6.txt'])
        self.assertIn(fetch_docs.DOCS_SHA, items['whatsnew/csharp-14.txt'])

    def test_gate_oracle_is_the_installed_compiler_commit(self):
        items = dict((i['path'], i) for i in
                     fetch_docs.plan(self.tree, self.index))
        it = items['roslyn/MessageID.cs']
        self.assertEqual(it['kind'], 'raw')
        self.assertIn('/dotnet/dotnet/95017c711e', it['url'])

    def test_standard_chapters_pinned(self):
        items = dict((i['path'], i['url'])
                     for i in fetch_docs.plan(self.tree, self.index))
        self.assertIn('standard/classes.txt', items)
        self.assertIn('standard/foreword.txt', items)
        self.assertIn(fetch_docs.STD_SHA, items['standard/classes.txt'])

    def test_history_pages(self):
        items = dict((i['path'], i) for i in
                     fetch_docs.plan(self.tree, self.index))
        self.assertIn('history/artima-the-c-design-process.txt', items)
        self.assertIn('history/artima-clr-design-choices.txt', items)
        self.assertEqual(items['history/pdc-2000.txt']['kind'], 'html')
        # news.microsoft.com 은 브라우저가 아닌 UA 를 403 으로 막는다
        self.assertTrue(fetch_docs.ua_for(
            items['history/ms-sun-settlement-2001.txt']['url'])
            .startswith('Mozilla/5.0 (Windows'))

    def test_part1_sources(self):
        # 1부(탄생 이전)의 1차 자료 — 사라진 페이지는 웨이백의 원본(id_)
        items = dict((i['path'], i) for i in
                     fetch_docs.plan(self.tree, self.index))
        for n in range(1, 8):
            it = items['history/cw-hejlsberg-2008-%d.txt' % n]
            self.assertEqual(it['kind'], 'html')
            self.assertRegex(it['url'], r'^https://web\.archive\.org/web/'
                             r'\d{14}id_/http://www\.computerworld\.com\.au/')
        self.assertTrue(items['history/cw-hejlsberg-2008-1.txt']['url']
                        .endswith('a-z_programming_languages_c_/'))
        self.assertTrue(items['history/cw-hejlsberg-2008-7.txt']['url']
                        .endswith('?pp=7'))
        for name in ('sun-about-delegates', 'ms-truth-about-delegates',
                     'ms-csharp-announce-2000', 'ms-ecma-2001'):
            self.assertIn('history/%s.txt' % name, items)
        self.assertTrue(fetch_docs.ua_for(
            items['history/ms-ecma-2001.txt']['url'])
            .startswith('Mozilla/5.0 (Windows'))

    def test_paths_are_unique(self):
        paths = [i['path'] for i in fetch_docs.plan(self.tree, self.index)]
        self.assertEqual(len(paths), len(set(paths)))


class Ledger(unittest.TestCase):
    def test_first_heading(self):
        self.assertEqual(fetch_docs.first_heading('x\n§\tTitle\n'), 'Title')
        self.assertEqual(fetch_docs.first_heading('\n  plain\n'), 'plain')

    def test_fetched_line(self):
        line = fetch_docs.fetched_line('a.txt', 'http://u', '2026-10-01',
                                       b'abc', 'T')
        cols = line.split('\t')
        self.assertEqual(cols[:3], ['a.txt', 'http://u', '2026-10-01'])
        self.assertTrue(re.match(r'^[0-9a-f]{64}$', cols[3]))
        self.assertEqual(cols[4], 'T')

    def test_old_dates(self):
        # --missing 로 새 문서만 받을 때, 다시 받지 않은 문서의 줄은 처음
        # 받은 날을 지킨다 — 장부의 날짜가 "그날 무엇을 봤는가" 다
        text = ('# 머리 줄\n'
                'a.txt\thttp://a\t2026-10-01\t' + '0' * 64 + '\tA\n'
                'b/c.txt\thttp://c\t2026-10-03\t' + '1' * 64 + '\tC\n')
        self.assertEqual(fetch_docs.old_dates(text),
                         {'a.txt': '2026-10-01', 'b/c.txt': '2026-10-03'})
        self.assertEqual(fetch_docs.old_dates(''), {})


if __name__ == '__main__':
    unittest.main()
