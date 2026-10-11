# -*- coding: utf-8 -*-
"""build_deck.py · verify_deck.py 시험 — 작은 가짜 덱 나무를 만들어 조립해 본다."""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'deck'))
import build_deck  # noqa: E402
import rsrun  # noqa: E402
import verify_deck  # noqa: E402

HEAD = ('<html><head><title>t</title></head><body>'
        '<select id="nav">\n<!--NAV-->\n</select>\n<main class="prose">\n')
TAIL = '</main>\n<!--DEMOS-->\n</body></html>\n'
CODE = 'fn main() {\n    let v = vec![1, 2];\n    println!("{:?}", &v);\n}\n'
CAP = '$ rustc --edition 2024 a.rs && ./a\n[1, 2]\n'
COVER = ('<article class="card section" id="p06">\n<p class="chnum">6부</p>\n'
         '<h2>소유권</h2>\n</article>\n')


class Tree(unittest.TestCase):
    """deck/·ex/·out/·data/ 를 가진 임시 뿌리."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='deck-test-')
        self.addCleanup(shutil.rmtree, self.root, True)
        self.put('deck/base/head.html', HEAD)
        self.put('deck/base/tail.html', TAIL)
        self.put('deck/order.txt', '# 순서\n06_own.html\n')
        self.put('deck/budget.txt', '# 부 목표\n6 10\n')
        self.put('data/releases.tsv', 'version\tdate\n1.0\t2015-05-15\n1.65\t2022-11-03\n')
        self.put('data/features.tsv',
                 'key\tversion\tlabel\tevidence\nlet-else\t1.65\tlet-else\tlet-else\n')
        self.put('data/sources.tsv',
                 'key\turl\ttitle\nrust-1.0\thttps://blog.rust-lang.org/x\tAnnouncing Rust 1.0\n')
        self.example('ex/06/a.rs', CODE, CAP)

    def put(self, rel, text):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8', newline='') as f:
            f.write(text)

    def example(self, rel, code, cap):
        self.put(rel, code)
        out = rsrun.capture_path(rel)
        self.put(out, cap)
        rsrun.manifest_update(self.root, rel, 'rustc 1.99.0')

    def section(self, body, cover=COVER):
        self.put('deck/sections/06_own.html', cover + body)

    def build(self, **kw):
        return build_deck.build(self.root, **kw)

    def errs(self, **kw):
        return '\n'.join(self.build(**kw).errors)


class Expand(Tree):
    def test_run_gives_code_and_capture(self):
        self.section('<article class="card" id="p06-a">\n<h3>이동</h3>\n'
                     '<!--RUN file=ex/06/a.rs note=벡터 찍기-->\n</article>\n')
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertEqual(r.slides, 2)
        self.assertIn('<p class="fname">ex/06/a.rs · 벡터 찍기</p>', r.html)
        self.assertIn('<pre data-src="ex/06/a.rs" data-lines="1-4">'
                      '<code data-lang="rust">fn main() {', r.html)
        self.assertIn('println!("{:?}", &amp;v);', r.html)          # 이스케이프
        self.assertIn('<pre class="term" data-src="out/06/a.txt" data-lines="1-2">'
                      '<span class="p">$ rustc --edition 2024 a.rs &amp;&amp; ./a</span>\n'
                      '[1, 2]\n</pre>', r.html)

    def test_code_lines_slice(self):
        self.section('<article class="card" id="p06-a">\n'
                     '<!--CODE file=ex/06/a.rs lines=2-3-->\n'
                     '<!--OUT file=out/06/a.txt lines=2-2-->\n</article>\n')
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertIn('data-lines="2-3"><code data-lang="rust">    let v = vec![1, 2];\n'
                      '    println!', r.html)
        self.assertIn('data-lines="2-2">[1, 2]\n</pre>', r.html)

    def test_trailing_directives_are_not_shown(self):
        self.example('ex/06/b.rs', 'fn main() {\n    panic!("x");\n}\n//@ exit: 101\n',
                     '$ rustc --edition 2024 b.rs && ./b\nboom\n[종료 코드 101]\n')
        self.section('<article class="card" id="p06-a"><!--RUN file=ex/06/a.rs--></article>\n'
                     '<article class="card" id="p06-b">\n<!--RUN file=ex/06/b.rs-->\n</article>\n')
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertNotIn('//@', r.html)
        self.assertIn('data-src="ex/06/b.rs" data-lines="1-3"', r.html)

    def test_rel_since_src(self):
        self.section('<article class="card" id="p06-a"><!--RUN file=ex/06/a.rs-->\n'
                     '<p>1.0 은 <!--REL v=1.0--> 에 나왔고 <!--SINCE key=let-else-->'
                     ' <!--SRC key=rust-1.0--></p>\n</article>\n')
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertIn('1.0 은 1.0(2015-05-15) 에', r.html)
        self.assertIn('<span class="vt" title="let-else">1.65</span>', r.html)
        self.assertIn('<a class="src" href="https://blog.rust-lang.org/x" '
                      'title="Announcing Rust 1.0">출처</a>', r.html)

    def test_nav_lists_parts_and_chapters(self):
        self.section('<article class="card" id="p06-ch1"><p class="chnum">1장</p>'
                     '<h2>이동 &amp; 복사</h2></article>\n'
                     '<article class="card" id="p06-a"><!--RUN file=ex/06/a.rs--></article>\n')
        html = self.build().html
        self.assertIn('<option value="p06">6부 · 소유권</option>', html)
        self.assertIn('<option value="p06-ch1">· 이동 &amp; 복사</option>', html)
        self.assertNotIn('<!--NAV-->', html)


class Rules(Tree):
    def ok_slide(self):
        return '<article class="card" id="p06-a"><!--RUN file=ex/06/a.rs--></article>\n'

    def test_missing_file(self):
        self.section('<article class="card" id="p06-a"><!--RUN file=ex/06/none.rs--></article>\n')
        self.assertIn('ex/06/none.rs', self.errs())

    def test_stale_capture(self):
        self.section(self.ok_slide())
        self.put('ex/06/a.rs', CODE.replace('1, 2', '1, 3'))     # 캡처 뒤에 소스를 고쳤다
        self.assertIn('낡았', self.errs())

    def test_edited_capture(self):
        self.section(self.ok_slide())
        self.put('out/06/a.txt', CAP.replace('[1, 2]', '[1, 3]'))  # 캡처를 손으로 고쳤다
        self.assertIn('낡았', self.errs())

    def test_handwritten_pre_is_rejected(self):
        self.section(self.ok_slide() + '<article class="card" id="p06-b">\n'
                     '<pre><code data-lang="rust">let x = 1;</code></pre>\n</article>\n')
        self.assertIn('손으로 쓴 <pre>', self.errs())

    def test_fig_pre_is_allowed_but_measured(self):
        self.section(self.ok_slide() + '<article class="card" id="p06-b">\n'
                     '<pre class="fig">스택 | 힙\n</pre>\n</article>\n')
        self.assertEqual(self.build().errors, [])
        self.section(self.ok_slide() + '<article class="card" id="p06-b">\n'
                     '<pre class="fig">' + '가' * 37 + '\n</pre>\n</article>\n')
        self.assertIn('72칸', self.errs())

    def test_code_width_counts_korean_as_two(self):
        self.example('ex/06/w.rs', 'fn main() {\n    // ' + '가' * 34 + '\n}\n', CAP)
        self.section(self.ok_slide() +
                     '<article class="card" id="p06-w"><!--CODE file=ex/06/w.rs--></article>\n')
        self.assertIn('72칸', self.errs())

    def test_code_too_long(self):
        self.example('ex/06/l.rs', 'fn main() {\n' + '    let _x = 1;\n' * 45 + '}\n', CAP)
        self.section(self.ok_slide() +
                     '<article class="card" id="p06-l"><!--CODE file=ex/06/l.rs--></article>\n')
        self.assertIn('45줄', self.errs())

    def test_duplicate_and_missing_id(self):
        self.section(self.ok_slide() + self.ok_slide())
        self.assertIn('id 가 겹친다', self.errs())
        self.section(self.ok_slide() + '<article class="card"><p>x</p></article>\n')
        self.assertIn('id 가 없다', self.errs())

    def test_id_must_carry_part_prefix(self):
        self.section(self.ok_slide().replace('p06-a', 'p07-a'))
        self.assertIn('p06', self.errs())

    def test_dead_internal_link(self):
        self.section(self.ok_slide() + '<article class="card" id="p06-b">'
                     '<a href="#p99-x">저기</a></article>\n')
        self.assertIn('#p99-x', self.errs())

    def test_unknown_release_feature_source(self):
        for d in ('<!--REL v=9.9-->', '<!--SINCE key=nope-->', '<!--SRC key=nope-->'):
            self.section(self.ok_slide() + '<article class="card" id="p06-b"><p>%s</p></article>\n' % d)
            self.assertNotEqual(self.build().errors, [], d)

    def test_unknown_directive(self):
        self.section(self.ok_slide() + '<article class="card" id="p06-b">\n<!--RUNN file=x-->\n</article>\n')
        self.assertIn('RUNN', self.errs())

    def test_placeholder_is_an_error_unless_skeleton(self):
        self.section(self.ok_slide(), cover=COVER.replace('</article>', '<p class="chsub">준비 중입니다</p></article>'))
        self.assertIn('준비 중', self.errs())
        self.assertEqual(self.build(skel=True).errors, [])

    def test_part_budget_over_ten_percent(self):
        self.put('deck/budget.txt', '6 2\n')
        self.section(self.ok_slide() + ''.join(
            '<article class="card" id="p06-x%d"><p>x</p></article>\n' % i for i in range(2)))
        self.assertIn('예산', self.errs())

    def test_hard_cap(self):
        self.put('deck/budget.txt', '6 2000\n')
        self.section(self.ok_slide() + ''.join(
            '<article class="card" id="p06-x%d"><p>x</p></article>\n' % i for i in range(1000)))
        self.assertIn('1000장', self.errs())

    def test_unused_example_is_an_error_when_finished(self):
        self.example('ex/06/unused.rs', CODE, CAP)
        self.section(self.ok_slide())
        self.assertIn('ex/06/unused.rs', self.errs())
        self.assertEqual(self.build(skel=True).errors, [])

    def test_box_drawing_outside_pre(self):
        self.section(self.ok_slide() + '<article class="card" id="p06-b"><p>┌─┐</p></article>\n')
        self.assertIn('박스 그리기', self.errs())

    def test_long_capture_line_wraps_then_fails(self):
        self.example('ex/06/long.rs', CODE, '$ x\n' + 'e' * 120 + '\n')
        self.section(self.ok_slide() +
                     '<article class="card" id="p06-l"><!--RUN file=ex/06/long.rs--></article>\n')
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertIn('<pre class="term wrap" data-src="out/06/long.txt"', r.html)
        self.example('ex/06/long.rs', CODE, '$ x\n' + 'e' * 201 + '\n')
        self.assertIn('200칸', self.errs())


class History(Tree):
    """역사 부(1부)의 규칙 — 연도는 근거가 있어야 한다."""

    def setUp(self):
        super().setUp()
        self.put('deck/order.txt', '01_history.html\n06_own.html\n')
        self.put('deck/budget.txt', '1 10\n6 10\n')
        self.put('data/sources.tsv', 'key\turl\ttitle\tdate\n'
                 'rust-1.0\thttps://blog.rust-lang.org/x\tAnnouncing Rust 1.0\t2015-05-15\n'
                 'releases\thttps://example.org/RELEASES.md\tRust Release Notes\t\n')
        self.put('data/evidence.tsv', 'id\tsource\tmatched\n'
                 'first-release\treleases\tVersion 0.1 (2012-01-20)\n'
                 'one-oh\trust-1.0\tToday we are very proud to announce the 1.0 release\n')
        self.section('<article class="card" id="p06-a"><!--RUN file=ex/06/a.rs--></article>\n')

    def history(self, body):
        self.put('deck/sections/01_history.html',
                 '<article class="card section" id="p01"><p class="chnum">1부</p><h2>역사</h2></article>\n'
                 '<article class="card" id="p01-a">' + body + '</article>\n')

    def test_fact_renders_a_source_link(self):
        self.history('<p>첫 공개판은 2012년입니다. <!--FACT id=first-release--></p>')
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertIn('<a class="src" href="https://example.org/RELEASES.md" '
                      'title="Rust Release Notes — Version 0.1 (2012-01-20)">출처</a>', r.html)

    def test_year_from_source_date_and_rel(self):
        self.history('<p>2015년에 1.0 이 나왔습니다. <!--FACT id=one-oh--> '
                     '그 뒤 <!--REL v=1.65--> 에… 2022년.</p>')
        self.assertEqual(self.build().errors, [])

    def test_year_without_evidence_is_an_error(self):
        self.history('<p>2006년에 시작했습니다. <!--FACT id=first-release--></p>')
        self.assertIn('2006', self.errs())

    def test_unknown_fact(self):
        self.history('<p>x <!--FACT id=nope--></p>')
        self.assertIn('nope', self.errs())

    def test_history_slide_without_any_source_is_an_error(self):
        self.history('<p>그냥 주장만 있습니다.</p>')
        self.assertIn('근거', self.errs())

    def test_other_parts_are_not_year_checked(self):
        self.history('<p>x <!--FACT id=first-release--></p>')
        self.section('<article class="card" id="p06-a"><!--RUN file=ex/06/a.rs-->'
                     '<p>1999년 이야기</p></article>\n')
        self.assertEqual(self.build().errors, [])


class Width(unittest.TestCase):
    def test_width(self):
        self.assertEqual(build_deck.width('abc'), 3)
        self.assertEqual(build_deck.width('가나'), 4)
        self.assertEqual(build_deck.width('a\tb'), 9)      # 탭은 8칸 자리까지
        self.assertEqual(build_deck.width('→'), 1)


class Verify(Tree):
    def built(self):
        self.section('<article class="card" id="p06-a">\n<!--RUN file=ex/06/a.rs-->\n</article>\n')
        r = self.build()
        self.assertEqual(r.errors, [])
        return r.html

    def test_clean_deck_verifies(self):
        self.assertEqual(verify_deck.verify(self.root, self.built()), [])

    def test_edited_code_in_deck_is_caught(self):
        html = self.built().replace('vec![1, 2]', 'vec![1, 9]')
        self.assertNotEqual(verify_deck.verify(self.root, html), [])

    def test_edited_capture_in_deck_is_caught(self):
        html = self.built().replace('[1, 2]\n</pre>', '[7]\n</pre>')
        self.assertNotEqual(verify_deck.verify(self.root, html), [])

    def test_pre_without_source_is_caught(self):
        html = self.built().replace('</main>', '<pre><code>let x;</code></pre></main>')
        self.assertNotEqual(verify_deck.verify(self.root, html), [])

    def test_source_changed_after_build_is_caught(self):
        html = self.built()
        self.put('ex/06/a.rs', CODE + '// 나중에 덧붙임\n')
        self.assertNotEqual(verify_deck.verify(self.root, html), [])


if __name__ == '__main__':
    unittest.main()
