# -*- coding: utf-8 -*-
"""tools/data_check.py 의 시험 (PLAN.md §0.3–§0.5, §3.2).

손으로 쓴 표가 기억에서 나온 사실을 싣지 못하게 막는 검사다. 그래서
시험도 "막아야 할 것" 위주다 — 위키백과 주소만 적은 출처, 받은 날이
없는 2025년 이후 행, 받은 법령 글에 없는 조문 번호, 칸이 빈 행.
픽스처는 임시 디렉터리에 만든다.

    python3 -m unittest discover -s tools/tests
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))           # drone
sys.path.insert(0, os.path.join(BASE, 'tools'))

import data_check as dc    # noqa: E402

KEYS = ('key\tname\turl\tkind\tlicence\tfile\n'
        'kr-act\t항공안전법\thttps://x/a\tlaw\t-\tlaw/act.txt\n'
        'ecfr\tPart 107\thttps://x/b\tlaw\t-\tlaw/107.txt\n'
        'eu\tEU 2019/947\thttps://x/c\tlaw\t-\tlaw/eu.txt\n'
        'gone\t받지 않은 글\thttps://x/d\tlaw\t-\tlaw/none.txt\n'
        'sky\tSkybrush\thttps://x/e\tdoc\t-\tsky.txt\n')
ACT = ('§\t제10장 초경량비행장치\n§\t제125조\n'
       '§\t제125조(초경량비행장치 조종자 증명 등)\n'
       '① 초경량비행장치를 ...\n'
       '§\t제131조의2\n§\t제131조의2(무인비행장치의 적용 특례)\n')
P107 = ('§\t#107.29\n§\t§ 107.29 Operation at night.\n'
        '(a) No person may ...\n')
EU = ('Article 4\n‘Open’ category of UAS operations\n'
      'Article 40\nUAS.OPEN.020 UAS operations in subcategory A1\n'
      'PART 1\nRequirements for a class C0\n')

LAW_HEAD = ('jurisdiction\trule\tarticle\trequirement(ko)\tsource\t'
            'verified-how\n')
VH = 'fetched 2026-09-25'


def write(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def law_row(j='KR', rule='항공안전법', art='제125조',
            req='증명이 있어야', src='kr-act', vh=VH):
    return '\t'.join((j, rule, art, req, src, vh)) + '\n'


class Pure(unittest.TestCase):
    """칸 하나를 보는 작은 함수들."""

    def test_dates_accepted(self):
        for s in ('1849', '2024-03', '2024-02-29', '2026-09-25'):
            self.assertTrue(dc.valid_date(s), s)

    def test_dates_rejected(self):
        for s in ('', '24', '2024/03', '2024-13', '2023-02-29',
                  '2024-04-31', '2024-3', '미확인', '2024-03-05x'):
            self.assertFalse(dc.valid_date(s), s)

    def test_year_only(self):
        self.assertTrue(dc.valid_date('2013', year_only=True))
        self.assertFalse(dc.valid_date('2013-01', year_only=True))

    def test_wikipedia_is_never_a_source(self):
        for u in ('https://en.wikipedia.org/wiki/Drone',
                  'https://ko.m.wikipedia.org/wiki/무인_항공기',
                  'https://en.wikipedia.org/w/index.php?title=UAV'):
            self.assertTrue(dc.is_wikipedia(u), u)
        self.assertFalse(dc.is_wikipedia('https://www.faa.gov/uas'))
        self.assertFalse(dc.is_wikipedia(
            'https://example.org/wikipedia.org/wiki/x'))

    def test_source_key_or_https(self):
        keys = {'kr-act': {}, 'sky': {}}
        self.assertIsNone(dc.source_problem('kr-act', keys))
        self.assertIsNone(
            dc.source_problem('https://skybrush.io/', keys))
        self.assertIsNone(dc.source_problem('kr-act; sky', keys))

    def test_source_rejects(self):
        keys = {'kr-act': {}}
        for s in ('nokey', 'http://skybrush.io/',
                  'https://en.wikipedia.org/wiki/Drone',
                  'kr-act; https://de.wikipedia.org/wiki/X', ''):
            self.assertTrue(dc.source_problem(s, keys), s)

    def test_verified_how(self):
        for s in ('fetched 2026-09-25', 'websearch 2026-09-25',
                  'fetched 2026-09-25; docs §제129조(x)'):
            self.assertTrue(dc.verified_ok(s), s)
        for s in ('', 'fetched', 'Fetched 2026-09-25', 'fetched 2026',
                  'memory 2026-09-25', 'websearch 2026-9-25'):
            self.assertFalse(dc.verified_ok(s), s)

    def test_article_korean_heading(self):
        self.assertTrue(dc.article_in_text('제125조', ACT))
        self.assertTrue(dc.article_in_text('제131조의2', ACT))

    def test_article_korean_needs_exact_number(self):
        # 제131조의2 는 있지만 제131조 는 없다 — 앞머리만 맞으면 안 된다
        self.assertFalse(dc.article_in_text('제131조', ACT))
        self.assertFalse(dc.article_in_text('제12조', ACT))

    def test_article_cfr_section(self):
        self.assertTrue(dc.article_in_text('§107.29', P107))
        self.assertFalse(dc.article_in_text('§107.2', P107))
        self.assertFalse(dc.article_in_text('§107.31', P107))

    def test_article_free_text_with_boundary(self):
        self.assertTrue(dc.article_in_text('Article 4', EU))
        self.assertTrue(dc.article_in_text('UAS.OPEN.020', EU))
        self.assertTrue(dc.article_in_text('PART 1', EU))
        self.assertFalse(dc.article_in_text('Article 5', EU))
        self.assertFalse(dc.article_in_text('UAS.OPEN.02', EU))


class Fixture(unittest.TestCase):
    """임시 drone/ — cite_keys·docs 를 깔고 표를 하나씩 쓴다."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='drone-dc-')
        write(self.root, 'data/cite_keys.tsv', KEYS)
        write(self.root, 'docs/law/act.txt', ACT)
        write(self.root, 'docs/law/107.txt', P107)
        write(self.root, 'docs/law/eu.txt', EU)
        write(self.root, 'docs/sky.txt', '§\tOverview\n')

    def tearDown(self):
        shutil.rmtree(self.root)

    def law(self, *rows):
        write(self.root, 'data/law.tsv',
              '# 주석\n' + LAW_HEAD + ''.join(rows))
        return dc.check_table(self.root, 'law.tsv')

    def has(self, res, *words):
        hit = [e for e in res.errors if all(w in e for w in words)]
        self.assertTrue(hit, '%r 가 오류에 없다: %r'
                        % (words, res.errors))


class Law(Fixture):
    def test_good_rows(self):
        r = self.law(law_row(),
                     law_row('US', '14 CFR 107', '§107.29', '야간',
                             'ecfr'),
                     law_row('EU', '2019/947', 'Article 4', '개방',
                             'eu'))
        self.assertEqual(r.errors, [])
        self.assertEqual(r.rows, 3)

    def test_header_must_match(self):
        write(self.root, 'data/law.tsv',
              'jurisdiction\trule\tarticle\trequirement\tsource\n')
        r = dc.check_table(self.root, 'law.tsv')
        self.has(r, '칸')

    def test_empty_required_cell_names_line(self):
        r = self.law(law_row(req=''))
        self.has(r, 'requirement(ko)', ':3')

    def test_wrong_cell_count(self):
        r = self.law(law_row().rstrip('\n') + '\t남는 칸\n')
        self.has(r, '칸 수')

    def test_jurisdiction_set(self):
        r = self.law(law_row(j='JP'))
        self.has(r, 'jurisdiction', 'JP')

    def test_article_missing_from_docs(self):
        r = self.law(law_row(art='제999조'))
        self.has(r, '제999조')

    def test_article_prefix_is_not_enough(self):
        r = self.law(law_row(art='제131조'))
        self.has(r, '제131조')

    def test_docs_file_not_fetched(self):
        r = self.law(law_row(src='gone'))
        self.has(r, 'make docs')

    def test_law_rows_need_fetch_date(self):
        r = self.law(law_row(vh=''))
        self.has(r, 'verified-how')
        r = self.law(law_row(vh='기억'))
        self.has(r, 'verified-how')

    def test_quoted_heading_must_exist(self):
        ok = VH + '; docs §제125조(초경량비행장치 조종자 증명 등)'
        self.assertEqual(self.law(law_row(vh=ok)).errors, [])
        bad = VH + '; docs §제125조(조종자 증명)'
        self.has(self.law(law_row(vh=bad)), '제125조(조종자 증명)')

    def test_wikipedia_source(self):
        wiki = 'https://en.wikipedia.org/wiki/Part_107'
        r = self.law(law_row(src=wiki))
        self.has(r, 'source')

    def test_below_minimum_is_warning_only(self):
        r = self.law(law_row())
        self.assertEqual(r.errors, [])
        self.assertTrue(any('(미달)' in w for w in r.warnings),
                        r.warnings)


TL_HEAD = 'date\tevent(ko)\tkind\tsource\tverified-how\n'
SH_HEAD = ('date\tplace\torganiser\tdrone-count\trecord\tsource\t'
           'verified-how\n')
FW_HEAD = ('project\tfirst-release\tlicence\tlanguage\t'
           'attitude-representation\tsource\tverified-how\n')
TS_HEAD = ('tool\tvendor\tkind\topen-source\tfile-formats\tnotes(ko)\t'
           'source\tverified-how\n')
PR_HEAD = ('year\tmaker\tproduct\tclass\tnotable-for(ko)\tsource\t'
           'verified-how\n')
QU_HEAD = 'quote(en)\twho\twhere\tdate\tsource\n'


class Others(Fixture):
    def table(self, name, text):
        write(self.root, 'data/' + name, text)
        return dc.check_table(self.root, name)

    def test_timeline_header_only_is_warning(self):
        r = self.table('timeline.tsv', TL_HEAD)
        self.assertEqual(r.errors, [])
        self.assertEqual(r.rows, 0)
        self.assertTrue(any('(미달)' in w for w in r.warnings))

    def test_timeline_kind_and_date(self):
        r = self.table('timeline.tsv', TL_HEAD +
                       '1849-07\t풍선\tballoon\tsky\t-\n')
        self.has(r, 'kind', 'balloon')
        r = self.table('timeline.tsv', TL_HEAD +
                       '1849/07\t풍선\tmilitary\tsky\t-\n')
        self.has(r, 'date', '1849/07')

    def test_recent_rows_need_verification(self):
        r = self.table('timeline.tsv', TL_HEAD +
                       '2025-05\t기록\tshow\tsky\t\n')
        self.has(r, '2025', 'verified-how')
        r = self.table('timeline.tsv', TL_HEAD +
                       '2025-05\t기록\tshow\tsky\t'
                       'websearch 2026-09-25\n')
        self.assertEqual(r.errors, [])
        r = self.table('timeline.tsv', TL_HEAD +
                       '2024-12\t기록\tshow\tsky\t\n')
        self.assertEqual(r.errors, [])

    def test_shows_count_and_record(self):
        r = self.table('shows.tsv', SH_HEAD +
                       '2018-02\t평창\tIntel\t1,218\tGuinness\t'
                       'sky\t-\n')
        self.has(r, 'drone-count')
        r = self.table('shows.tsv', SH_HEAD +
                       '2018-02\t평창\tIntel\t1218\tyes\tsky\t-\n')
        self.has(r, 'record', 'yes')

    def test_products_year_only(self):
        r = self.table('products.tsv', PR_HEAD +
                       '2013-01\tDJI\tPhantom\tconsumer\t처음\t'
                       'sky\t-\n')
        self.has(r, 'year')

    def test_firmware_unknown_needs_explanation(self):
        row = 'MultiWii\t미확인\tGPL-3.0\tC++\t미확인\tsky\t%s\n'
        r = self.table('firmware.tsv', FW_HEAD + row % VH)
        self.has(r, '미확인')
        r = self.table('firmware.tsv', FW_HEAD +
                       row % (VH + '; 첫 배포 연도 1차 출처 미확인'))
        self.assertEqual(r.errors, [])

    def test_tools_kind_and_open_source(self):
        good = ('Skybrush Live\tCollMot\tlive\tyes\t.skyc\t'
                '지상국\tsky\t' + VH + '\n')
        self.assertEqual(self.table('tools_show.tsv',
                                    TS_HEAD + good).errors, [])
        r = self.table('tools_show.tsv',
                       TS_HEAD + good.replace('\tlive\t', '\tgame\t'))
        self.has(r, 'kind', 'game')
        r = self.table('tools_show.tsv',
                       TS_HEAD + good.replace('\tyes\t', '\tmaybe\t'))
        self.has(r, 'open-source', 'maybe')

    def test_quotes_have_no_verified_column(self):
        r = self.table('quotes.tsv', QU_HEAD +
                       'Hello.\tSomeone\tTalk\t2019-05\tsky\n')
        self.assertEqual(r.errors, [])

    def test_missing_table_is_error(self):
        r = dc.check_table(self.root, 'shows.tsv')
        self.has(r, 'shows.tsv')


class Main(Fixture):
    def all_tables(self, law_rows):
        write(self.root, 'data/law.tsv', LAW_HEAD + law_rows)
        write(self.root, 'data/timeline.tsv', TL_HEAD)
        write(self.root, 'data/shows.tsv', SH_HEAD)
        write(self.root, 'data/products.tsv', PR_HEAD)
        write(self.root, 'data/firmware.tsv', FW_HEAD)
        write(self.root, 'data/tools_show.tsv', TS_HEAD)
        write(self.root, 'data/quotes.tsv', QU_HEAD)

    def run_main(self):
        out = io.StringIO()
        code = dc.main([], base=self.root, out=out)
        return code, out.getvalue()

    def test_warnings_only_exit_zero(self):
        self.all_tables(law_row())
        code, text = self.run_main()
        self.assertEqual(code, 0, text)
        self.assertIn('(미달)', text)
        self.assertIn('law.tsv', text)
        self.assertIn('timeline.tsv', text)

    def test_errors_exit_one(self):
        self.all_tables(law_row(art='제999조'))
        code, text = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn('제999조', text)


if __name__ == '__main__':
    unittest.main()
