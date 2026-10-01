# -*- coding: utf-8 -*-
"""조립기·검사기에 이 덱이 새로 더한 규칙의 시험 (PLAN.md §1, §6).

goevo/deck 에서 물려받은 검사(폭·커버리지·예산·slices)는 그 덱이 이미
시험했다. 여기서는 C# 덱에 맞춰 바꾼 것 — CSVER·REL 지시자, 인용 키 해석
(문서 절 · 소스 한 줄), 버전 배지, 산문의 'C# N' 근거, C# 이름 찾기 — 만
본다. 픽스처는 임시 디렉터리에 만든다.

    python3 -m unittest discover -s tools/tests
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))           # csevo
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


RELEASES = ('version\tdate\tvs\tframework\tsource\n'
            '1.0\t2002-02-13\tVS .NET 2002\t.NET Framework 1.0\tx\n'
            '1.2\t2003-04-24\tVS .NET 2003\t.NET Framework 1.1\tx\n'
            '7.3\t2018-05-07\tVS 2017 15.7\t.NET Framework 4.7.2\tx\n'
            '8.0\t2019-09-23\tVS 2019 16.3\t.NET Core 3.0\tx\n'
            '12.0\t2023-11-14\tVS 2022 17.8\t.NET 8\tx\n')
CITE_KEYS = ('key\tname\tfile\n'
             'whatsnew-12\tWhat\'s new in C# 12\twhatsnew/csharp-12.txt\n'
             'history\tThe history of C#\twhatsnew/csharp-version-history.txt\n'
             'msgid\tRoslyn MessageID.cs\troslyn/MessageID.cs\n')


class Fixture(unittest.TestCase):
    """임시 csevo/ 하나 — data/·docs/·out/ 를 채워 두고 모듈 전역을 돌려 놓는다."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='csevo-test-')
        write(self.root, 'data/releases.tsv', RELEASES)
        write(self.root, 'data/cite_keys.tsv', CITE_KEYS)
        write(self.root, 'docs/whatsnew/csharp-12.txt',
              '§\tWhat\'s new in C# 12\n§\tPrimary constructors\n'
              'You can now create primary constructors in any class ...\n')
        write(self.root, 'docs/whatsnew/csharp-version-history.txt',
              '§\tThe history of C#\n§\tC# version 1.0\n')
        write(self.root, 'docs/roslyn/MessageID.cs',
              '            switch (feature)\n'
              '                case MessageID.IDS_FeatureRecords:\n'
              '                    return LanguageVersion.CSharp9;\n')
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


# ------------------------------------------------------------ 버전 표기
class Versions(unittest.TestCase):
    def test_norm_drops_trailing_dot_zero(self):
        n = build_deck.vnorm
        self.assertEqual(n('8.0'), '8')
        self.assertEqual(n('12.0'), '12')
        self.assertEqual(n('12'), '12')
        self.assertEqual(n('1.0'), '1')
        self.assertEqual(n('1.2'), '1.2')
        self.assertEqual(n('7.3'), '7.3')

    def test_langversion_flag_value(self):
        # csc 가 받는 값 — 1·2 는 ISO-1·ISO-2 라는 이름이 따로 있지만
        # 숫자도 받는다(2026-10-01 확인). 지시자에 적은 그대로 넘긴다.
        self.assertEqual(build_deck.csver_cmdline('csrun', v='7.3'),
                         'csrun -langversion:7.3')
        self.assertEqual(build_deck.csver_cmdline('csrun', v='12'),
                         'csrun -langversion:12')


# ------------------------------------------------------------ 캡처 이름 규칙
class CsverSlug(unittest.TestCase):
    def test_lang_variant(self):
        self.assertEqual(build_deck.csverslug('ex/08/tuples', v='7.3'),
                         '08-tuples__cs7.3')

    def test_env_variant(self):
        self.assertEqual(
            build_deck.csverslug('ex/06/sync', env='DOTNET_TieredPGO=0'),
            '06-sync__env-dotnet_tieredpgo-0')

    def test_version_env_and_tag_join_in_order(self):
        self.assertEqual(
            build_deck.csverslug('ex/09/nrt', v='8.0', env='A=1', tag='warn'),
            '09-nrt__cs8.0-env-a-1-warn')

    def test_uppercase_and_odd_chars_fold(self):
        self.assertEqual(build_deck.csverslug('ex/10/Top_Level', v='9.0'),
                         '10-top_level__cs9.0')

    def test_needs_a_variant(self):
        with self.assertRaises(ValueError):
            build_deck.csverslug('ex/08/tuples')

    def test_needs_ex_prefix(self):
        with self.assertRaises(ValueError):
            build_deck.csverslug('out/08/tuples', v='7.3')

    def test_version_only_for_csrun(self):
        # dotnet --version 같은 명령에 -langversion 을 끼우면 안 된다 —
        # 버전은 이름(slug)에만 남는다
        self.assertEqual(build_deck.csver_cmdline('dotnet --version',
                                                  v='14.0'),
                         'dotnet --version')

    def test_cmdline_shows_env_and_flags(self):
        self.assertEqual(build_deck.csver_cmdline('csrun'), 'csrun')
        self.assertEqual(
            build_deck.csver_cmdline('csrun -- a b', v='8.0',
                                     flags='-nullable:enable',
                                     env='DOTNET_gcServer=1'),
            'DOTNET_gcServer=1 csrun -langversion:8.0 -nullable:enable -- a b')


# ------------------------------------------------------------ CSVER 지시자
class CsverDirective(Fixture):
    def expand(self, args):
        return build_deck.expand('<!--CSVER %s-->\n' % args)

    def test_missing_capture_is_error(self):
        self.expand('v=7.3 file=ex/08/tuples')
        self.assertTrue(any('08-tuples__cs7.3.txt' in e
                            for e in build_deck.errors), build_deck.errors)

    def test_first_line_must_match_command(self):
        write(self.root, 'out/08-tuples__cs7.3.txt',
              '$ csrun -langversion:7.2\nok\n')
        self.expand('v=7.3 file=ex/08/tuples')
        self.assertTrue(any('첫 줄' in e for e in build_deck.errors),
                        build_deck.errors)

    def test_hit_renders_capture_with_version_label(self):
        write(self.root, 'out/08-tuples__cs7.3.txt',
              '$ csrun -langversion:7.3\n(1, 2)\n')
        out = self.expand('v=7.3 file=ex/08/tuples')
        self.assertEqual(build_deck.errors, [])
        self.assertIn('<pre class="term" data-out="08-tuples__cs7.3.txt"', out)
        self.assertIn('ex/08/tuples · C# 7.3', out)
        self.assertIn('$ csrun -langversion:7.3', out)

    def test_long_compiler_line_gets_wrap_class(self):
        # Roslyn 의 버전 거절은 위치까지 한 줄이 120칸을 넘는다 — 고쳐
        # 싣지 않고 화면에서만 접는다(바이트는 그대로, verify_deck 가 대조)
        msg = ('Program.cs(3,1): error CS8400: Feature \'records\' is not '
               'available in C# 8.0. Please use language version 9.0 or '
               'greater.')
        write(self.root, 'out/10-rec__cs8.0.txt',
              '$ csrun -langversion:8.0\n' + msg + '\n')
        out = self.expand('v=8.0 file=ex/10/rec')
        self.assertEqual(build_deck.errors, [])
        self.assertIn('<pre class="term wrap"', out)
        self.assertIn(html_escape(msg), out)

    def test_short_capture_has_no_wrap(self):
        write(self.root, 'out/10-rec__cs9.0.txt',
              '$ csrun -langversion:9.0\nok\n')
        self.assertIn('<pre class="term" ', self.expand('v=9.0 file=ex/10/rec'))

    def test_flags_and_env_must_be_in_capture(self):
        write(self.root, 'out/09-n__cs8.0.txt', '$ csrun -langversion:8.0\n')
        self.expand('v=8.0 file=ex/09/n flags="-nullable:enable"')
        self.assertTrue(any('첫 줄' in e for e in build_deck.errors))


def html_escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


# ------------------------------------------------------------ REL 지시자
class RelDirective(Fixture):
    def test_version_as_written_in_table(self):
        out = build_deck.expand('나온 날 <!--REL v=7.3-->.')
        self.assertIn('2018-05-07', out)
        self.assertNotIn('<!--REL', out)
        self.assertEqual(build_deck.errors, [])

    def test_dot_zero_is_optional_both_ways(self):
        self.assertIn('2019-09-23', build_deck.expand('<!--REL v=8-->'))
        self.assertIn('2023-11-14', build_deck.expand('<!--REL v=12-->'))
        self.assertIn('2023-11-14', build_deck.expand('<!--REL v=12.0-->'))
        self.assertIn('2002-02-13', build_deck.expand('<!--REL v=1-->'))
        self.assertEqual(build_deck.errors, [])

    def test_unknown_is_error(self):
        build_deck.expand('<!--REL v=15-->')
        self.assertTrue(any('15' in e for e in build_deck.errors))


# ------------------------------------------------------------ 인용 키
class Cites(Fixture):
    def test_keys_come_from_table(self):
        idx = cites.index(self.root)
        self.assertEqual(idx['whatsnew-12']['file'], 'whatsnew/csharp-12.txt')
        self.assertEqual(idx['msgid']['file'], 'roslyn/MessageID.cs')

    def test_heading_resolves(self):
        self.assertIsNone(cites.resolve(self.root, 'whatsnew-12',
                                        'Primary constructors'))

    def test_body_text_is_not_a_heading(self):
        self.assertIsNotNone(cites.resolve(self.root, 'whatsnew-12',
                                           'You can now create primary'))

    def test_source_key_needs_whole_stripped_line(self):
        # 소스 파일(.cs)에는 제목이 없다 — 한 줄을 통째로(앞뒤 공백 뺀 것)
        # 가리켜야 한다. "records 는 C# 9" 의 증거가 바로 그 case 줄이다.
        self.assertIsNone(cites.resolve(
            self.root, 'msgid', 'case MessageID.IDS_FeatureRecords:'))
        self.assertIsNotNone(cites.resolve(self.root, 'msgid',
                                           'IDS_FeatureRecords'))

    def test_unknown_key_and_missing_doc(self):
        self.assertIn('키', cites.resolve(self.root, 'whatsnew-99', 'x'))
        write(self.root, 'data/cite_keys.tsv',
              CITE_KEYS + 'gone\tGone\tnowhere.txt\n')
        self.assertIn('make docs', cites.resolve(self.root, 'gone', 'x'))

    def test_cite_directive_uses_names(self):
        out = build_deck.expand(
            '<!--CITE key=whatsnew-12 sec="Primary constructors"-->')
        self.assertEqual(build_deck.errors, [])
        self.assertIn('What\'s new in C# 12', html_unescape(out))
        build_deck.expand('<!--CITE key=nope-->')
        self.assertTrue(build_deck.errors)


def html_unescape(s):
    import html
    return html.unescape(s)


# ------------------------------------------------------------ 산문의 C# N
class ProseVersions(unittest.TestCase):
    def test_finds_csharp_versions(self):
        got = check_claims.versions_in('C# 7.3 에서, 그리고 C# 12 와 C#8.0.')
        self.assertEqual([v for v, _ in got], ['7.3', '12', '8.0'])

    def test_korean_particle_glued_to_version(self):
        got = check_claims.versions_in('C# 9에서 바뀌었고 C# 10부터는')
        self.assertEqual([v for v, _ in got], ['9', '10'])

    def test_skips_non_versions(self):
        got = check_claims.versions_in(
            'C# 코드, C#은, F# 6, C# 언어 7.3, C# 3배, C# 1.5.2')
        self.assertEqual(got, [])

    def test_evidence_lookup(self):
        known = {'1', '1.2', '7.3', '8', '12'}
        ok = check_claims.version_known
        self.assertTrue(ok('7.3', known))
        self.assertTrue(ok('8.0', known))
        self.assertTrue(ok('8', known))
        self.assertTrue(ok('12.0', known))
        self.assertTrue(ok('1.0', known))
        self.assertFalse(ok('7.2', known))
        self.assertFalse(ok('15', known))

    def test_known_versions_from_releases_and_claims(self):
        rel = [{'version': '7.3'}, {'version': '12.0'}]
        got = check_claims.known_versions(rel, '| C# 15 은 제안 단계 | …')
        self.assertEqual(got, {'7.3', '12', '15'})


# ------------------------------------------------------------ 버전 배지
SEC = """<article class="card" id="p8-tuples">
<h3>튜플 <span class="vt v7">C# 7.0</span></h3>
</article>
<article class="card" id="p8-two">
<h3>둘 <span class="vt v7">C# 7.0</span> <span class="vt v7_3">C# 7.3</span></h3>
</article>
<article class="card" id="p8-wrong">
<h3>틀린 짝 <span class="vt v7_2">C# 7.3</span></h3>
</article>
<article class="card" id="p8-nobadge"><h3>배지 없음</h3></article>
<article class="card" id="p8-future"><h3>x <span class="vt v15">C# 15</span></h3></article>
<article class="card" id="p8-stray"><h3>y <span class="vt v7_3">C# 7.3</span></h3></article>
<article class="card" id="p8-bare"><h3>z <span class="vt v7_3">7.3</span></h3></article>
"""


class Badges(unittest.TestCase):
    def test_all_rules(self):
        bad = check_xref.badge_errors(
            {'08_s.html': SEC}, {'7', '7.3'},
            {'p8-tuples', 'p8-two', 'p8-wrong', 'p8-nobadge', 'p8-future',
             'p8-missing', 'p8-bare'})
        text = '\n'.join(bad)
        self.assertNotIn('p8-tuples', text)
        self.assertIn('p8-two', text)          # 배지는 정확히 하나
        self.assertIn('p8-wrong', text)        # class 와 글자가 다르다
        self.assertIn('p8-nobadge', text)      # 기능 장인데 배지가 없다
        self.assertIn('p8-future', text)       # releases.tsv 에 없는 버전
        self.assertIn('p8-stray', text)        # features 에 없는 장
        self.assertIn('p8-missing', text)      # 표에는 있는데 덱에 없다
        self.assertIn('p8-bare', text)         # 글자는 'C# N' 꼴이어야 한다
        self.assertEqual(len(bad), 7, bad)

    def test_part0_legend_is_exempt(self):
        texts = {'00_start.html': '<article class="card" id="p0-badges">'
                 '<span class="vt v7_3">C# 7.3</span></article>'}
        self.assertEqual(check_xref.badge_errors(texts, set(), set()), [])

    def test_unwritten_part_is_pending(self):
        cover = '<article class="card section" id="p9"><h2>9</h2></article>\n'
        texts = {'09_x.html': cover}
        self.assertEqual(check_xref.badge_errors(texts, {'8'},
                                                 {'p9-nrt'}), [])
        texts = {'09_x.html': cover + '<article class="card" id="p9-a">'
                                      '<h3>a</h3></article>\n'}
        bad = check_xref.badge_errors(texts, {'8'}, {'p9-nrt'})
        self.assertEqual(len(bad), 1, bad)

    def test_class_name_rule(self):
        # 점은 '_' 로, 끝의 .0 은 뺀다 — C# 1.2(v1_2)와 C# 12(v12)가 겹치지 않는다
        c = check_xref.badge_class
        self.assertEqual(c('1.2'), 'v1_2')
        self.assertEqual(c('12'), 'v12')
        self.assertEqual(c('12.0'), 'v12')
        self.assertEqual(c('1.0'), 'v1')
        self.assertEqual(c('7.3'), 'v7_3')
        self.assertEqual(c('8.0'), 'v8')


# ------------------------------------------------------------ C# 이름 찾기
CS = """// 슬라이드 p8-x — 튜플, C# 7.0
using System;

/// <summary>점 하나.</summary>
[Serializable]
public readonly record struct Point(int X, int Y);

internal static class Program
{
    // 진입점
    static void Main(string[] args)
    {
        var p = new Point(1, 2);
        Console.WriteLine(Swap(p));
    }

    static Point Swap(Point p) => new(p.Y, p.X);

    public async Task<int> RunAsync(
        int a,
        int b)
    {
        await Task.Yield();
        return a + b;
    }
}

enum Color { Red, Green }
"""


class CsSymbols(Fixture):
    def setUp(self):
        super().setUp()
        write(self.root, 'ex/08/x/Program.cs', CS)

    def sym(self, name):
        return build_deck.find_symbol('ex/08/x/Program.cs', name)

    def test_one_line_record_with_doc_and_attribute(self):
        # /// 문서 주석과 [특성] 도 정의에 붙어 따라온다. 한 줄 record 는
        # 다음 형의 { 를 집어 오면 안 된다.
        self.assertEqual(self.sym('Point'), (4, 6))

    def test_allman_class_body(self):
        self.assertEqual(self.sym('Program'), (8, 26))

    def test_method_with_comment(self):
        self.assertEqual(self.sym('Main'), (10, 15))

    def test_expression_bodied_member(self):
        self.assertEqual(self.sym('Swap'), (17, 17))

    def test_wrapped_signature(self):
        self.assertEqual(self.sym('RunAsync'), (19, 25))

    def test_enum_on_one_line(self):
        self.assertEqual(self.sym('Color'), (28, 28))
        self.assertEqual(build_deck.errors, [])


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
