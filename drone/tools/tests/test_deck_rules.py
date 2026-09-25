# -*- coding: utf-8 -*-
"""조립기·검사기에 이 덱이 새로 더한 규칙의 시험 (PLAN.md §0.6, §1, §6).

git/goevo 에서 물려받은 검사(폭·커버리지·예산·slices)는 그 덱들이 이미
시험했다. 여기서는 드론 덱에만 있는 것 — THM·WITNESS·SHOW 지시자, 인용
키 해석, 정리 표(theorems.tsv) 규칙, 산문의 드론 대수·조문 번호 근거,
상한 3000장 — 만 본다. 픽스처는 임시 디렉터리에 만든다.

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
sys.path.insert(0, os.path.join(BASE, 'deck'))

import build_deck      # noqa: E402
import check_claims    # noqa: E402
import check_thm       # noqa: E402
import cites           # noqa: E402


def write(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


CITE_KEYS = ('key\tname\turl\tkind\tlicence\tfile\n'
             'px4-att\tPX4 AttitudeControl.cpp\thttps://x/a.cpp\tcode\tBSD-3\t'
             'px4_att.txt\n'
             'nofile\t파일 없는 키\thttps://x/b\tweb\t-\t\n')

THM_HEAD = ('id\tstatement\tlevel\tproof-kind\tprerequisites\t'
            'witness-test\tcite-key\n')
THMS = (THM_HEAD +
        'M1\t벡터의 내적은 교환법칙을 만족한다\t1학년\tfull\t-\t'
        'py/tests/test_vec3.py::test_dot_commutes\t-\n'
        'T14\t2차 계의 초과량은 <span class="mi">e</span> 로 쓴다\t1학년\t'
        'full\tM1\tpy/tests/test_pid.py::test_overshoot\t-\n'
        'T20\tSE(3) 추종 제어는 거의 전역적으로 수렴한다\t심화\tcited\t-\t-\t'
        'px4-att\n')
TEST_VEC = 'def test_dot_commutes():\n    pass\n'
TEST_PID = 'class T:\n    def test_overshoot(self):\n        pass\n'


class Fixture(unittest.TestCase):
    """임시 drone/ 하나 — data/·docs/·py/ 를 채워 두고 모듈 전역을 돌려 놓는다."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='drone-test-')
        write(self.root, 'data/cite_keys.tsv', CITE_KEYS)
        write(self.root, 'data/theorems.tsv', THMS)
        write(self.root, 'docs/px4_att.txt',
              '§\tAttitudeControl.cpp\n§\tupdate\nquaternion error ...\n')
        write(self.root, 'py/tests/test_vec3.py', TEST_VEC)
        write(self.root, 'py/tests/test_pid.py', TEST_PID)
        self.saved = (build_deck.BASE, build_deck.OUTDIR, list(build_deck.errors))
        build_deck.BASE = self.root
        build_deck.OUTDIR = os.path.join(self.root, 'out')
        build_deck._DOCS.clear()
        build_deck._THM.clear()
        del build_deck.errors[:]

    def tearDown(self):
        build_deck.BASE, build_deck.OUTDIR, errs = self.saved
        build_deck.errors[:] = errs
        build_deck._DOCS.clear()
        build_deck._THM.clear()
        sys.modules.pop('droneshow.render', None)
        sys.modules.pop('droneshow', None)
        shutil.rmtree(self.root)


# ------------------------------------------------------------ 인용 키
class Cites(Fixture):
    def test_index_reads_table(self):
        idx = cites.index(self.root)
        self.assertEqual(idx['px4-att']['name'], 'PX4 AttitudeControl.cpp')
        self.assertEqual(idx['px4-att']['licence'], 'BSD-3')

    def test_resolve_exact_heading(self):
        self.assertIsNone(cites.resolve(self.root, 'px4-att', 'update'))

    def test_resolve_prefix_is_not_enough(self):
        self.assertIn('절 제목', cites.resolve(self.root, 'px4-att', 'upd'))

    def test_resolve_unknown_key(self):
        self.assertIn('cite_keys.tsv', cites.resolve(self.root, 'zz', ''))

    def test_resolve_key_without_file(self):
        self.assertIn('file 칸', cites.resolve(self.root, 'nofile', 'x'))

    def test_cite_badge(self):
        out = build_deck.expand(
            'a <!--CITE key=px4-att sec=update--> b')
        self.assertIn('data-cite="px4-att"', out)
        self.assertEqual(build_deck.errors, [])


# ------------------------------------------------------------ THM · WITNESS
class Thm(Fixture):
    def test_statement_box_with_level_badge(self):
        out = build_deck.expand('<!--THM id=T14-->\n')
        self.assertIn('class="thm"', out)
        self.assertIn('data-thm="T14"', out)
        self.assertIn('<span class="lv l1">1학년</span>', out)
        self.assertIn('<span class="mi">e</span>', out)     # 표의 HTML 은 그대로
        self.assertEqual(build_deck.errors, [])

    def test_advanced_badge_and_kind(self):
        out = build_deck.expand('<!--THM id=T20-->\n')
        self.assertIn('<span class="lv adv">심화</span>', out)
        self.assertIn('인용', out)

    def test_continuation_header(self):
        out = build_deck.expand('<!--THM id=T14 cont-->\n')
        self.assertIn('증명 계속', out)
        self.assertIn('<span class="lv l1">1학년</span>', out)
        self.assertNotIn('class="thm"', out)

    def test_unknown_id_is_error(self):
        build_deck.expand('<!--THM id=T99-->\n')
        self.assertTrue(any('T99' in e for e in build_deck.errors))

    def test_witness_line(self):
        out = build_deck.expand('<!--WITNESS id=T14-->\n')
        self.assertIn('py/tests/test_pid.py::test_overshoot', out)
        self.assertIn('class="witness"', out)

    def test_witness_missing_is_error(self):
        build_deck.expand('<!--WITNESS id=T20-->\n')
        self.assertTrue(any('증인' in e for e in build_deck.errors))


# ------------------------------------------------------------ SHOW
RENDER_STUB = '''
def snapshot_svg(show, frame, view):
    return '<svg class="show" viewBox="0 0 340 200"><circle r="%d"/>%s</svg>' % (
        len(show["drones"]), view)
'''


class Show(Fixture):
    def test_missing_show_file(self):
        build_deck.expand('<!--SHOW file=out/show_x.json frame=3-->\n')
        self.assertTrue(any('show_x.json' in e for e in build_deck.errors))

    def test_missing_renderer(self):
        write(self.root, 'out/show_a.json', '{"fps": 25, "drones": []}')
        build_deck.expand('<!--SHOW file=out/show_a.json frame=3-->\n')
        self.assertTrue(any('render' in e for e in build_deck.errors))

    def test_renders_with_simulator(self):
        write(self.root, 'py/droneshow/__init__.py', '')
        write(self.root, 'py/droneshow/render.py', RENDER_STUB)
        write(self.root, 'out/show_a.json',
              '{"fps": 25, "drones": [{"id": 1}, {"id": 2}]}')
        out = build_deck.expand(
            '<!--SHOW file=out/show_a.json frame=3 view=top cap=하트-->\n')
        self.assertEqual(build_deck.errors, [])
        self.assertIn('data-show="out/show_a.json"', out)
        self.assertIn('data-frame="3"', out)
        self.assertIn('<circle r="2"/>top', out)
        self.assertIn('<p class="cap">하트</p>', out)


# ------------------------------------------------------------ 정리 표 검사
class ThmTable(Fixture):
    def rows(self, extra=''):
        write(self.root, 'data/theorems.tsv', THMS + extra)
        return cites.rows(self.root, 'theorems.tsv')

    def test_clean_table(self):
        self.assertEqual(check_thm.tsv_errors(self.rows(), self.root), [])

    def test_bad_level_and_kind(self):
        bad = check_thm.tsv_errors(self.rows(
            'X1\t가\t2학년\tproof\t-\t-\t-\n'), self.root)
        self.assertTrue(any('level' in b for b in bad))
        self.assertTrue(any('proof-kind' in b for b in bad))

    def test_unknown_prerequisite(self):
        bad = check_thm.tsv_errors(self.rows(
            'X2\t가\t1학년\tsketch\tM9\t-\t-\n'), self.root)
        self.assertTrue(any('M9' in b for b in bad))

    def test_advanced_prereq_under_freshman_proof(self):
        bad = check_thm.tsv_errors(self.rows(
            'X3\t가\t1학년\tfull\tT20\tpy/tests/test_vec3.py::'
            'test_dot_commutes\t-\n'), self.root)
        self.assertTrue(any('심화' in b and 'X3' in b for b in bad))

    def test_full_needs_witness(self):
        bad = check_thm.tsv_errors(self.rows(
            'X4\t가\t1학년\tfull\t-\t-\t-\n'), self.root)
        self.assertTrue(any('X4' in b and '증인' in b for b in bad))

    def test_witness_must_exist(self):
        bad = check_thm.tsv_errors(self.rows(
            'X5\t가\t1학년\tfull\t-\tpy/tests/test_vec3.py::test_nope\t-\n'
            'X6\t가\t1학년\tfull\t-\tpy/tests/test_none.py::test_a\t-\n'),
            self.root)
        self.assertTrue(any('X5' in b for b in bad))
        self.assertTrue(any('X6' in b for b in bad))

    def test_cited_needs_cite_key(self):
        bad = check_thm.tsv_errors(self.rows(
            'X7\t가\t심화\tcited\t-\t-\t-\n'
            'X8\t가\t심화\tcited\t-\t-\tzz\n'), self.root)
        self.assertTrue(any('X7' in b for b in bad))
        self.assertTrue(any('X8' in b and 'zz' in b for b in bad))

    def test_duplicate_id(self):
        bad = check_thm.tsv_errors(self.rows(
            'M1\t다시\t1학년\tsketch\t-\t-\t-\n'), self.root)
        self.assertTrue(any('M1' in b and '두 번' in b for b in bad))


class ThmSections(Fixture):
    def texts(self, body):
        return {'09_control.html': body}

    def test_unknown_thm_in_section(self):
        rows = cites.rows(self.root, 'theorems.tsv')
        bad = check_thm.section_errors(self.texts(
            '<article class="card" id="p9-a"><!--THM id=T77--></article>'),
            rows, skeleton=True)
        self.assertTrue(any('T77' in b for b in bad))

    def test_unreferenced_only_outside_skeleton(self):
        rows = cites.rows(self.root, 'theorems.tsv')
        t = self.texts('<article class="card" id="p9-a">'
                       '<!--THM id=T14--></article>')
        self.assertEqual(check_thm.section_errors(t, rows, skeleton=True), [])
        bad = check_thm.section_errors(t, rows, skeleton=False)
        self.assertTrue(any('M1' in b for b in bad))
        self.assertFalse(any('T14' in b for b in bad))

    def test_proof_slide_needs_one_badge(self):
        rows = cites.rows(self.root, 'theorems.tsv')
        none = ('<article class="card" id="p9-b"><div class="proof">'
                '<ol class="pf"><li>가</li></ol></div></article>')
        two = ('<article class="card" id="p9-c"><!--THM id=T14-->'
               '<!--THM id=M1--><div class="proof"><p>x</p></div>'
               '</article>')
        one = ('<article class="card" id="p9-d"><!--THM id=T14 cont-->'
               '<div class="proof"><p>x</p></div></article>')
        bad = check_thm.section_errors(self.texts(none + two + one), rows,
                                       skeleton=True)
        self.assertTrue(any('p9-b' in b for b in bad))
        self.assertTrue(any('p9-c' in b for b in bad))
        self.assertFalse(any('p9-d' in b for b in bad))


# ------------------------------------------------------------ 사실 검사
class Claims(unittest.TestCase):
    def test_counts_found(self):
        got = [c for c, _ in check_claims.counts_in(
            '평창에서 1,218대가 떴고 12대 시험, 500 대 쇼')]
        self.assertEqual(got, ['1,218', '500'])

    def test_count_known(self):
        self.assertTrue(check_claims.count_known('1,218', 'x\t1218\ty'))
        self.assertTrue(check_claims.count_known('1,218', '| 1,218 |'))
        self.assertFalse(check_claims.count_known('1,218', '11218'))

    def test_articles_found(self):
        got = [a for a, _ in check_claims.articles_in(
            '항공안전법 제129조와 제124조의2, § 107.29 와 §107.35')]
        self.assertEqual(got, ['제129조', '제124조의2', '§107.29', '§107.35'])


# ------------------------------------------------------------ 상한·부록
class Limits(unittest.TestCase):
    def test_hard_cap(self):
        self.assertEqual(build_deck.HARD_CAP, 3000)

    def test_appendix_label(self):
        self.assertEqual(build_deck.part_label(18), '부록')
        self.assertEqual(build_deck.part_label(9), '9부')


if __name__ == '__main__':
    unittest.main()
