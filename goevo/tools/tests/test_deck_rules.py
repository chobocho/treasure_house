# -*- coding: utf-8 -*-
"""조립기·검사기에 이 덱이 새로 더한 규칙의 시험 (PLAN.md §1, §6).

git/deck 에서 물려받은 검사(폭·커버리지·예산·slices)는 그 덱이 이미
시험했다. 여기서는 Go 덱에만 있는 것 — GOVER·REL 지시자, 인용 키 해석,
버전 배지, 산문의 '1.N' 근거 — 만 본다. 픽스처는 임시 디렉터리에 만든다.

    python3 -m unittest discover -s tools/tests
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))           # goevo
sys.path.insert(0, os.path.join(BASE, 'deck'))

import build_deck      # noqa: E402
import check_claims    # noqa: E402
import check_xref      # noqa: E402
import cites           # noqa: E402


def write(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


RELEASES = ('version\tdate\tkind\trelnotes-key\n'
            'go1\t2000-01-01\tmajor\trelnotes-1.0\n'
            'go1.0.1\t2000-01-02\tminor\t\n'
            'go1.20\t2000-02-01\tmajor\trelnotes-1.20\n'
            'go1.22.0\t2000-03-01\tmajor\trelnotes-1.22\n'
            'go1.22.3\t2000-03-09\tminor\t\n')
CITE_KEYS = ('key\tname\tfile\n'
             'godebug\tGo, Backwards Compatibility, and GODEBUG\tgodebug.txt\n'
             'relnotes-1.28\tGo 1.28 릴리스 노트(초안)\trelnotes/go1.28-draft.txt\n')


class Fixture(unittest.TestCase):
    """임시 goevo/ 하나 — data/·docs/·out/ 를 채워 두고 모듈 전역을 돌려 놓는다."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='goevo-test-')
        write(self.root, 'data/releases.tsv', RELEASES)
        write(self.root, 'data/cite_keys.tsv', CITE_KEYS)
        write(self.root, 'docs/relnotes/go1.22.txt',
              '§\tGo 1.22 Release Notes\n§\tChanges to the language\n'
              'Previously, the variables declared by a "for" loop ...\n')
        write(self.root, 'docs/relnotes/go1.txt', '§\tGo 1 Release Notes\n')
        write(self.root, 'docs/api/go1.22.txt',
              'pkg slices, func Concat[$0 interface{ ~[]$1 }, $1 interface{}](...$0) $0 #56353\n')
        write(self.root, 'docs/godebug.txt', '§\tGo 1.22\nx\n')
        self.saved = (build_deck.BASE, build_deck.OUTDIR, list(build_deck.errors))
        build_deck.BASE = self.root
        build_deck.OUTDIR = os.path.join(self.root, 'out')
        build_deck._REL.clear()
        build_deck._DOCS.clear()
        del build_deck.errors[:]

    def tearDown(self):
        build_deck.BASE, build_deck.OUTDIR, errs = self.saved
        build_deck.errors[:] = errs
        build_deck._REL.clear()
        build_deck._DOCS.clear()
        shutil.rmtree(self.root)


# ------------------------------------------------------------ 캡처 이름 규칙
class GoverSlug(unittest.TestCase):
    def test_lang_variant(self):
        self.assertEqual(build_deck.goverslug('ex/07/rangeint', v='1.22'),
                         '07-rangeint__go1.22')

    def test_godebug_variant(self):
        self.assertEqual(
            build_deck.goverslug('ex/07/timer', godebug='asynctimerchan=1'),
            '07-timer__godebug-asynctimerchan-1')

    def test_experiment_and_tag_join_in_order(self):
        self.assertEqual(
            build_deck.goverslug('ex/08/x', v='1.27', exp='jsonv2', tag='vet'),
            '08-x__go1.27-exp-jsonv2-vet')

    def test_uppercase_and_odd_chars_fold(self):
        self.assertEqual(build_deck.goverslug('ex/05/Embed_FS', v='1.16'),
                         '05-embed_fs__go1.16')

    def test_needs_a_variant(self):
        with self.assertRaises(ValueError):
            build_deck.goverslug('ex/07/rangeint')

    def test_needs_ex_prefix(self):
        with self.assertRaises(ValueError):
            build_deck.goverslug('out/07/rangeint', v='1.22')

    def test_cmdline_shows_env_prefixes(self):
        self.assertEqual(build_deck.gover_cmdline('go run .'), 'go run .')
        self.assertEqual(
            build_deck.gover_cmdline('go run .', godebug='x=0', exp='jsonv2'),
            'GODEBUG=x=0 GOEXPERIMENT=jsonv2 go run .')


# ------------------------------------------------------------ GOVER 지시자
class GoverDirective(Fixture):
    def expand(self, args):
        return build_deck.expand(
            '<!--GOVER %s-->\n' % args)

    def test_missing_capture_is_error(self):
        self.expand('v=1.22 file=ex/07/rangeint')
        self.assertTrue(any('07-rangeint__go1.22.txt' in e
                            for e in build_deck.errors), build_deck.errors)

    def test_first_line_must_match_command(self):
        write(self.root, 'out/07-rangeint__go1.22.txt',
              '$ go vet .\nok\n')
        self.expand('v=1.22 file=ex/07/rangeint')
        self.assertTrue(any('첫 줄' in e for e in build_deck.errors),
                        build_deck.errors)

    def test_hit_renders_capture_with_version_label(self):
        write(self.root, 'out/07-rangeint__go1.22.txt',
              '$ go run .\n0\n1\n2\n')
        out = self.expand('v=1.22 file=ex/07/rangeint')
        self.assertEqual(build_deck.errors, [])
        self.assertIn('<pre class="term" data-out="07-rangeint__go1.22.txt"', out)
        self.assertIn('go 1.22', out)          # go.mod 의 go 줄을 화면에 보인다
        self.assertIn('$ go run .', out)

    def test_long_compiler_line_gets_wrap_class(self):
        # go 의 컴파일 오류는 한 줄이 120칸을 넘는다 — 고쳐 싣지 않고
        # 화면에서만 접는다(바이트는 그대로, verify_deck 가 대조한다)
        msg = './main.go:7:17: ' + 'x' * 110
        write(self.root, 'out/07-r__go1.21.txt', '$ go run .\n' + msg + '\n')
        out = self.expand('v=1.21 file=ex/07/r')
        self.assertEqual(build_deck.errors, [])
        self.assertIn('<pre class="term wrap"', out)
        self.assertIn(msg, out)

    def test_short_capture_has_no_wrap(self):
        write(self.root, 'out/07-r__go1.22.txt', '$ go run .\n012\n')
        self.assertIn('<pre class="term" ', self.expand('v=1.22 file=ex/07/r'))

    def test_godebug_prefix_must_be_in_capture(self):
        write(self.root, 'out/07-t__godebug-x-0.txt', '$ go run .\n')
        self.expand('godebug=x=0 file=ex/07/t')
        self.assertTrue(any('첫 줄' in e for e in build_deck.errors))


# ------------------------------------------------------------ REL 지시자
class RelDirective(Fixture):
    def test_major_with_dot_zero(self):
        out = build_deck.expand('나온 날 <!--REL v=1.22-->.')
        self.assertIn('2000-03-01', out)
        self.assertNotIn('<!--REL', out)
        self.assertEqual(build_deck.errors, [])

    def test_major_without_dot_zero(self):
        self.assertIn('2000-02-01', build_deck.expand('<!--REL v=1.20-->'))

    def test_go1_is_version_1_0(self):
        self.assertIn('2000-01-01', build_deck.expand('<!--REL v=1.0-->'))

    def test_minor_release(self):
        self.assertIn('2000-03-09', build_deck.expand('<!--REL v=1.22.3-->'))

    def test_unknown_is_error(self):
        build_deck.expand('<!--REL v=1.99-->')
        self.assertTrue(any('1.99' in e for e in build_deck.errors))


# ------------------------------------------------------------ 인용 키
class Cites(Fixture):
    def test_keys_from_releases_and_table(self):
        idx = cites.index(self.root)
        self.assertEqual(idx['relnotes-1.22']['file'], 'relnotes/go1.22.txt')
        self.assertEqual(idx['relnotes-1.0']['file'], 'relnotes/go1.txt')
        self.assertEqual(idx['api-1.22']['file'], 'api/go1.22.txt')
        self.assertEqual(idx['godebug']['file'], 'godebug.txt')
        self.assertIn('relnotes-1.28', idx)
        self.assertNotIn('relnotes-1.22.3', idx)     # 부 릴리스는 노트가 없다

    def test_heading_resolves(self):
        self.assertIsNone(cites.resolve(self.root, 'relnotes-1.22',
                                        'Changes to the language'))

    def test_body_text_is_not_a_heading(self):
        self.assertIsNotNone(cites.resolve(self.root, 'relnotes-1.22',
                                           'Previously, the variables'))

    def test_api_key_needs_whole_line(self):
        line = ('pkg slices, func Concat[$0 interface{ ~[]$1 }, '
                '$1 interface{}](...$0) $0 #56353')
        self.assertIsNone(cites.resolve(self.root, 'api-1.22', line))
        self.assertIsNotNone(cites.resolve(self.root, 'api-1.22',
                                           'pkg slices, func Concat'))

    def test_unknown_key_and_missing_doc(self):
        self.assertIn('키', cites.resolve(self.root, 'relnotes-1.99', 'x'))
        self.assertIn('make docs', cites.resolve(self.root, 'relnotes-1.20', 'x'))

    def test_cite_directive_uses_names(self):
        out = build_deck.expand('<!--CITE key=relnotes-1.22 sec="Changes to the language"-->')
        self.assertEqual(build_deck.errors, [])
        self.assertIn('Go 1.22 릴리스 노트', out)
        build_deck.expand('<!--CITE key=nope-->')
        self.assertTrue(build_deck.errors)


# ------------------------------------------------------------ 산문의 1.N
class ProseVersions(unittest.TestCase):
    def test_finds_go_versions(self):
        got = check_claims.versions_in('Go 1.22 에서, 그리고 1.21.0 과 1.9.')
        self.assertEqual([v for v, _ in got], ['1.22', '1.21.0', '1.9'])

    def test_korean_particle_glued_to_version(self):
        # 조사가 붙어도 버전이다 — '1.22에서' 를 놓치면 검사에 구멍이 난다
        got = check_claims.versions_in('1.22에서 바뀌었고 1.23부터는')
        self.assertEqual([v for v, _ in got], ['1.22', '1.23'])

    def test_skips_non_versions(self):
        got = check_claims.versions_in(
            'HTTP/1.1 과 v1.2.3, 1.5배 빨라짐, 0.1.2, 11.3, x1.4, 1.25%')
        self.assertEqual(got, [])

    def test_known_prefix_words_are_skipped(self):
        got = check_claims.versions_in('TLS 1.3 과 Unicode 15.0',
                                       skip_words={'TLS'})
        self.assertEqual(got, [])

    def test_evidence_lookup(self):
        ev = 'go1\t...\ngo1.22.0\t...\n| go1.28 초안 | …'
        ok = check_claims.version_known
        self.assertTrue(ok('1.22', ev))
        self.assertTrue(ok('1.0', ev))
        self.assertTrue(ok('1.28', ev))
        self.assertFalse(ok('1.2', ev))            # go1.22 의 앞머리가 아니다
        self.assertFalse(ok('1.22.3', ev))


# ------------------------------------------------------------ 버전 배지
SEC = '''<article class="card" id="p7-rangeint">
<h3>정수 range <span class="vt v122">1.22</span></h3>
</article>
<article class="card" id="p7-two">
<h3>둘 <span class="vt v122">1.22</span> <span class="vt v121">1.21</span></h3>
</article>
<article class="card" id="p7-wrong">
<h3>틀린 짝 <span class="vt v121">1.22</span></h3>
</article>
<article class="card" id="p7-nobadge"><h3>배지 없음</h3></article>
<article class="card" id="p7-future"><h3>x <span class="vt v199">1.99</span></h3></article>
<article class="card" id="p7-stray"><h3>y <span class="vt v120">1.20</span></h3></article>
'''


class Badges(unittest.TestCase):
    def test_all_rules(self):
        bad = check_xref.badge_errors(
            {'07_s.html': SEC}, {'1.20', '1.21', '1.22'},
            {'p7-rangeint', 'p7-two', 'p7-wrong', 'p7-nobadge', 'p7-future',
             'p7-missing'})
        text = '\n'.join(bad)
        self.assertNotIn('p7-rangeint', text)
        self.assertIn('p7-two', text)          # 배지는 정확히 하나
        self.assertIn('p7-wrong', text)        # class 와 글자가 다르다
        self.assertIn('p7-nobadge', text)      # 기능 장인데 배지가 없다
        self.assertIn('p7-future', text)       # releases.tsv 에 없는 버전
        self.assertIn('p7-stray', text)        # features.tsv 에 없는 장
        self.assertIn('p7-missing', text)      # 표에는 있는데 덱에 없다
        self.assertEqual(len(bad), 6)

    def test_part0_legend_is_exempt(self):
        # 0부 '배지 읽기' 는 배지 견본을 보인다 — 기능 장이 아니다
        texts = {'00_start.html': '<article class="card" id="p0-badges">'
                 '<span class="vt v122">1.22</span></article>'}
        self.assertEqual(check_xref.badge_errors(texts, set(), set()), [])

    def test_unwritten_part_is_pending(self):
        # 표지 한 장뿐인 부의 기능 장은 아직 안 쓴 것이다 — 빨간불로 세지 않는다.
        # 그 부에 한 장이라도 더 쓰기 시작하면 그때부터 빠진 장을 센다.
        cover = '<article class="card section" id="p9"><h2>9</h2></article>\n'
        texts = {'09_x.html': cover}
        self.assertEqual(check_xref.badge_errors(texts, {'1.22'},
                                                 {'p9-draft'}), [])
        texts = {'09_x.html': cover + '<article class="card" id="p9-a">'
                                      '<h3>a</h3></article>\n'}
        bad = check_xref.badge_errors(texts, {'1.22'}, {'p9-draft'})
        self.assertEqual(len(bad), 1, bad)

    def test_class_name_rule(self):
        self.assertEqual(check_xref.badge_class('1.22'), 'v122')
        self.assertEqual(check_xref.badge_class('1.0'), 'v10')
        self.assertEqual(check_xref.badge_class('1.10'), 'v110')


class SplitPart(unittest.TestCase):
    # 한 부를 서브에이전트 둘이 나눠 쓰면 조각 파일이 둘이 된다(08_·08b_·08c_).
    # 앞 두 자리가 같은 파일의 장수는 한 부로 더해야 예산 검사가 맞다.
    def test_files_with_same_prefix_add_up(self):
        body = ('<!-- ===== 08_a.html ===== -->\n<article></article>\n'
                '<!-- ===== 08b_b.html ===== -->\n<article></article>'
                '<article></article>\n'
                '<!-- ===== 09_c.html ===== -->\n<article></article>\n')
        self.assertEqual(build_deck.budget_report(body), {8: 3, 9: 1})


class SplitPartChapters(unittest.TestCase):
    # 8부처럼 한 부를 여러 파일(08_·08b_·08c_)로 나누면 뒤 파일에는 부 표지가
    # 없다. 앞 두 자리가 같으면 앞 파일의 부를 이어받아야 장 수가 맞다.
    def test_chapters_in_continuation_files_count(self):
        files = [
            ('08_a.html', '<article class="card section" id="p8">'
                          '<p class="chnum">8부</p></article>\n'
                          '<article class="card" id="p8-c1">'
                          '<p class="chnum">1장</p></article>\n'),
            ('08b_b.html', '<article class="card" id="p8-c2">'
                           '<p class="chnum">2장</p></article>\n'
                           '<article class="card" id="p8-x"><h3>x</h3></article>\n'),
            ('09_c.html', '<article class="card" id="p9-y"><h3>y</h3></article>\n'),
        ]
        where, chaps = check_xref.scan_texts(files)
        self.assertEqual(chaps['8'], 2)
        self.assertEqual(where['p8-x'], ('8', '2'))
        self.assertEqual(where['p9-y'], (None, None))   # 다른 부는 잇지 않는다


if __name__ == '__main__':
    unittest.main()
