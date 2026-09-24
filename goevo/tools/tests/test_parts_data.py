# -*- coding: utf-8 -*-
"""부마다 나눈 자료 파일과 릴리스 개관 표의 시험.

서브에이전트 둘이 서로 다른 부를 동시에 쓰므로, 사람이 쓰는 자료는 부마다
파일 하나다: data/features/pNN.tsv · deck/claims/pNN.md · deck/glossary/pNN.txt.
읽는 쪽(검사기·표 생성기)은 그것을 모두 합쳐 읽어야 한다.

    python3 -m unittest discover -s tools/tests
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(BASE, 'deck'))

import check_claims  # noqa: E402
import cites         # noqa: E402
import gen_glossary  # noqa: E402
import gen_tables    # noqa: E402

HEAD = 'id\tversion\tkind\ttitle\tcite-key\tcite-sec\tslide-id\n'


def w(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


class Parts(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='parts-')
        w(self.root, 'data/features/p07.tsv', '# 7부\n' + HEAD +
          'loopvar\t1.22\tlang\t루프 변수\trelnotes-1.22\tX\tp7-v122-loopvar\n')
        w(self.root, 'data/features/p03.tsv', HEAD +
          'race\t1.1\ttoolchain\t경쟁 검출기\trelnotes-1.1\tY\tp3-v11-race\n')

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_feature_rows_from_all_parts_in_order(self):
        rows = cites.feature_rows(self.root)
        self.assertEqual([r['id'] for r in rows], ['race', 'loopvar'])
        self.assertEqual(rows[1]['_file'], 'data/features/p07.tsv')

    def test_claims_evidence_reads_part_files(self):
        saved = (check_claims.HERE, check_claims.DATA)
        try:
            check_claims.HERE = os.path.join(self.root, 'deck')
            check_claims.DATA = os.path.join(self.root, 'data')
            w(self.root, 'deck/claims.md', '| go1 은 2012-03-28 |\n')
            w(self.root, 'deck/claims/p03.md', '| go1.1 은 2013-05-13 |\n')
            ev = check_claims.evidence_text()
            self.assertIn('go1.1 은 2013-05-13', ev)
            self.assertIn('go1 은 2012-03-28', ev)
            self.assertIn('p3-v11-race', ev)          # 부별 features 도
        finally:
            check_claims.HERE, check_claims.DATA = saved

    def test_glossary_reads_part_files(self):
        saved = (gen_glossary.SRC, gen_glossary.PARTS)
        try:
            gen_glossary.SRC = os.path.join(self.root, 'deck', 'glossary.txt')
            gen_glossary.PARTS = os.path.join(self.root, 'deck', 'glossary')
            w(self.root, 'deck/glossary.txt', '# x\n고루틴 | 가벼운 실행 흐름 | p0-a\n')
            w(self.root, 'deck/glossary/p03.txt', '경쟁 검출기 | -race | p3-b\n')
            self.assertEqual([e[0] for e in gen_glossary.entries()],
                             ['고루틴', '경쟁 검출기'])
        finally:
            gen_glossary.SRC, gen_glossary.PARTS = saved


class Overview(unittest.TestCase):
    def test_release_table(self):
        rel = [{'version': 'go1.21.0', 'date': '2023-08-08', 'kind': 'major'},
               {'version': 'go1.22.0', 'date': '2024-02-06', 'kind': 'major'},
               {'version': 'go1.22.1', 'date': '2024-03-05', 'kind': 'minor'}]
        feats = [
            {'version': '1.22', 'kind': 'lang', 'title': '루프 변수 <새로>',
             'slide-id': 'p7-v122-loopvar'},
            {'version': '1.22', 'kind': 'lang', 'title': '정수 range',
             'slide-id': ''},
            {'version': '1.22', 'kind': 'stdlib', 'title': 'math/rand/v2',
             'slide-id': 'p7-v122-randv2'},
            {'version': '1.21', 'kind': 'lang', 'title': 'min·max',
             'slide-id': 'p7-v121-minmax'},
        ]
        api = [{'version': '1.22', 'new-packages': '2', 'new-symbols': '130',
                'sample-packages': 'go/version, math/rand/v2'}]
        out = gen_tables.release_tables(rel, feats, api)
        t = out['tbl_rel_1.22.html']
        self.assertIn('<th>날짜</th><td>2024-02-06</td>', t)
        self.assertIn('<th>언어</th><td><a href="#p7-v122-loopvar">'
                      '루프 변수 &lt;새로&gt;</a> · 정수 range</td>', t)
        self.assertIn('<th>표준 라이브러리</th><td><a href="#p7-v122-randv2">'
                      'math/rand/v2</a></td>', t)
        self.assertIn('<th>런타임</th><td>—</td>', t)
        self.assertIn('새 패키지 2개(go/version, math/rand/v2) · '
                      '새 기호 130개', t)
        self.assertIn('tbl_rel_1.21.html', out)
        self.assertNotIn('tbl_rel_1.22.1.html', out)


if __name__ == '__main__':
    unittest.main()
