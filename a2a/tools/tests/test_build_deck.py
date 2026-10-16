# -*- coding: utf-8 -*-
"""build_deck.py · verify_deck.py 시험 — 작은 가짜 덱 나무를 만들어 조립해 본다.

   ../rust/tools/tests/test_build_deck.py 를 옮겨 와 A2A 덱에 맞게 고쳤다:
   언어 셋(py·ts·go), 구역 표시(region), 캡처의 구역(part·server·wire·ex·grep), 장부 대조.
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'deck'))
import a2arun  # noqa: E402
import build_deck  # noqa: E402
import verify_deck  # noqa: E402

HEAD = ('<html><head><title>t</title></head><body>'
        '<select id="nav">\n<!--NAV-->\n</select>\n<main class="prose">\n')
TAIL = '</main>\n<!--DEMOS-->\n</body></html>\n'
CODE = 'def main():\n    v = [1, 2]\n    print(v)\n\n\nmain()\n'
CAP = '$ python 06/a.py\n[1, 2]\n'
COVER = ('<article class="card section" id="p06">\n<p class="chnum">6부</p>\n'
         '<h2>맨손 구현</h2>\n</article>\n')
SPEC = ('serve name=bus cmd="py:06/bus.py --port 10651" ready=tcp:10651\n'
        'tap   name=bus-wire listen=10601 target=10651\n'
        'run   cmd="sh:curl -s http://127.0.0.1:10601/a"\n'
        'run   cmd="sh:curl -s http://127.0.0.1:10601/b"\n')
SPEC_CAP = ('[터미널 1] $ python 06/bus.py --port 10651\n'           # 1
            '[터미널 2] $ python tools/wiretap.py 10601 10651\n'     # 2
            '[터미널 3] $ curl -s http://127.0.0.1:10601/a\n'        # 3
            'A\n'                                                    # 4
            '[터미널 3] $ curl -s http://127.0.0.1:10601/b\n'        # 5
            'B\n'                                                    # 6
            '── 터미널 1 (bus) 출력 ──\n'                            # 7
            'bus ready\n'                                            # 8
            'GET /a\n'                                               # 9
            'GET /b\n'                                               # 10
            '── 와이어 (bus-wire) ──\n'                              # 11
            '→ GET /a HTTP/1.1\n'                                    # 12
            '  Accept: */*\n'                                        # 13
            '← 200 OK\n'                                             # 14
            '  A\n'                                                  # 15
            '→ GET /b HTTP/1.1\n'                                    # 16
            '  Accept: */*\n'                                        # 17
            '← 200 OK\n'                                             # 18
            '  B\n')                                                 # 19


class Tree(unittest.TestCase):
    """deck/·ex/·out/·data/ 를 가진 임시 뿌리."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='deck-test-')
        self.addCleanup(shutil.rmtree, self.root, True)
        self.put('deck/base/head.html', HEAD)
        self.put('deck/base/tail.html', TAIL)
        self.put('deck/order.txt', '# 순서\n06_bare.html\n')
        self.put('deck/budget.txt', '# 부 목표\n6 10\n')
        self.put('data/releases.tsv', 'version\tdate\nv1.0.1\t2026-05-28\n')
        self.put('data/sources.tsv',
                 'key\turl\ttitle\nspec\thttps://a2a-protocol.org/x\tA2A Specification\n')
        self.example('ex/py/06/a.py', CODE, CAP)

    def put(self, rel, text):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8', newline='') as f:
            f.write(text)

    def example(self, rel, code, cap, main=None):
        self.put(main or rel, code)
        self.put(a2arun.capture_path(rel), cap)
        a2arun.manifest_update(self.root, rel, 'python 3.14')

    def spec(self):
        self.put('ex/py/06/bus.py', 'print("bus ready")\n#@ norun\n')
        self.example('ex/run/06/bus.run', SPEC, SPEC_CAP)

    def section(self, body, cover=COVER):
        self.put('deck/sections/06_bare.html', cover + body)

    def slide(self, body, sid='p06-x'):
        return '<article class="card" id="%s">\n%s\n</article>\n' % (sid, body)

    def ok_slide(self):
        return self.slide('<!--RUN file=ex/py/06/a.py-->', 'p06-a')

    def build(self, **kw):
        return build_deck.build(self.root, **kw)

    def errs(self, **kw):
        return '\n'.join(self.build(**kw).errors)


class Expand(Tree):
    def test_run_gives_code_and_capture(self):
        self.section(self.slide('<h3>목록</h3>\n<!--RUN file=ex/py/06/a.py note=목록 찍기-->', 'p06-a'))
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertEqual(r.slides, 2)
        self.assertIn('<p class="fname">ex/py/06/a.py · 목록 찍기</p>', r.html)
        self.assertIn('<pre data-src="ex/py/06/a.py" data-lines="1-6">'
                      '<code data-lang="python">def main():\n    v = [1, 2]\n', r.html)
        self.assertIn('<pre class="term" data-src="out/06/a.py.txt" data-lines="1-2">'
                      '<span class="p">$ python 06/a.py</span>\n[1, 2]\n</pre>', r.html)

    def test_note_may_contain_angle_brackets_and_arrows(self):
        self.section(self.slide('<!--RUN file=ex/py/06/a.py note=-> dict[str, list<int>] => 둘 다-->', 'p06-a'))
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertIn('<p class="fname">ex/py/06/a.py · -&gt; dict[str, list&lt;int&gt;] =&gt; 둘 다</p>', r.html)

    def test_note_starting_with_a_quoted_word_is_kept_whole(self):
        self.section(self.slide('<!--RUN file=ex/py/06/a.py note="role" 을 세 가지로 본다-->', 'p06-a'))
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertIn('<p class="fname">ex/py/06/a.py · "role" 을 세 가지로 본다</p>', r.html)

    def test_lines_slice_and_escaping(self):
        self.example('ex/py/06/e.py', 'x = "<a&b>"\nprint(x)\n', '$ python 06/e.py\n<a&b>\n')
        self.section(self.ok_slide() + self.slide(
            '<!--CODE file=ex/py/06/e.py lines=2-2-->\n<!--OUT file=out/06/e.py.txt lines=2-2-->'))
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertIn('data-lines="2-2"><code data-lang="python">print(x)\n</code>', r.html)
        self.assertIn('data-src="out/06/e.py.txt" data-lines="2-2">&lt;a&amp;b&gt;\n</pre>', r.html)

    def test_trailing_directives_are_not_shown(self):
        self.example('ex/py/06/b.py', 'raise SystemExit(3)\n\n#@ exit: 3\n',
                     '$ python 06/b.py\n[종료 코드 3]\n')
        self.section(self.ok_slide() + self.slide('<!--RUN file=ex/py/06/b.py-->', 'p06-b'))
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertNotIn('#@', r.html)
        self.assertIn('data-src="ex/py/06/b.py" data-lines="1-1"', r.html)

    def test_ruff_formatted_directives_are_not_shown_either(self):
        self.example('ex/py/06/c.py', 'raise SystemExit(3)\n# @ exit: 3\n',
                     '$ python 06/c.py\n[종료 코드 3]\n')
        self.section(self.ok_slide() + self.slide('<!--RUN file=ex/py/06/c.py-->', 'p06-c'))
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertNotIn('# @', r.html)
        self.assertIn('data-src="ex/py/06/c.py" data-lines="1-1"', r.html)

    def test_region_markers_are_never_shown(self):
        src = ('import json\n'                      # 1
               '# region: build\n'                  # 2
               'req = {"jsonrpc": "2.0"}\n'         # 3
               '# region: inner\n'                  # 4
               'req["id"] = 1\n'                    # 5
               '# endregion\n'                      # 6
               '# endregion\n'                      # 7
               'print(json.dumps(req))\n')          # 8
        self.example('ex/py/06/r.py', src, '$ python 06/r.py\n{}\n')
        self.section(self.ok_slide() + self.slide(
            '<!--CODE file=ex/py/06/r.py region=build-->', 'p06-r1') +
            self.slide('<!--CODE file=ex/py/06/r.py region=inner-->', 'p06-r2') +
            self.slide('<!--RUN file=ex/py/06/r.py-->', 'p06-r3'))
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertIn('data-src="ex/py/06/r.py" data-lines="3-3,5-5"><code data-lang="python">'
                      'req = {"jsonrpc": "2.0"}\nreq["id"] = 1\n</code>', r.html)
        self.assertIn('data-lines="5-5"><code data-lang="python">req["id"] = 1\n</code>', r.html)
        self.assertIn('data-lines="1-1,3-3,5-5,8-8"><code', r.html)
        self.assertNotIn('region', r.html.split('<main')[1])

    def test_missing_or_unclosed_region(self):
        self.example('ex/py/06/r.py', '# region: a\nx = 1\nprint(x)\n', '$ python 06/r.py\n')
        self.section(self.ok_slide() + self.slide('<!--CODE file=ex/py/06/r.py region=b-->'))
        self.assertIn('region=b', self.errs())
        self.section(self.ok_slide() + self.slide('<!--CODE file=ex/py/06/r.py region=a-->'))
        self.assertIn('endregion', self.errs())

    def test_go_tabs_are_four_columns_and_main_go_is_shown(self):
        self.example('ex/go/06/hello', 'package main\n\nfunc main() {\n\tprintln("hi")\n}\n//@ args: x\n',
                     '$ go run ./06/hello x\nhi\n', main='ex/go/06/hello/main.go')
        self.section(self.ok_slide() + self.slide('<!--RUN file=ex/go/06/hello-->', 'p06-g'))
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertIn('<pre data-src="ex/go/06/hello/main.go" data-lines="1-5"><code data-lang="go">'
                      'package main\n\nfunc main() {\n    println("hi")\n}\n</code>', r.html)
        self.assertIn('data-src="out/06/hello.go.txt"', r.html)
        self.assertEqual(build_deck.display_width('\tx', '.go'), 5)

    def test_typescript_and_json_languages(self):
        # 픽스처는 모든 캡처의 입력이다 — 먼저 두고 나서 캡처를 장부에 올린다.
        self.put('ex/fixtures/lodging.json', '{"rooms": 15}\n')
        a2arun.manifest_update(self.root, 'ex/py/06/a.py', 'python 3.14')
        self.example('ex/ts/06/t.ts', 'const n: number = 1;\nconsole.log(n);\n', '$ node 06/t.ts\n1\n')
        self.section(self.ok_slide() + self.slide('<!--RUN file=ex/ts/06/t.ts-->\n'
                                                  '<!--CODE file=ex/fixtures/lodging.json-->'))
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertIn('<code data-lang="typescript">const n', r.html)
        self.assertIn('<code data-lang="json">{"rooms": 15}', r.html)

    def test_rel_and_src(self):
        self.section(self.slide('<!--RUN file=ex/py/06/a.py-->\n'
                                '<p>1.0 은 <!--REL v=v1.0.1--> <!--SRC key=spec--></p>', 'p06-a'))
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertIn('1.0 은 v1.0.1(2026-05-28) <a class="src" href="https://a2a-protocol.org/x" '
                      'title="A2A Specification">출처</a>', r.html)

    def test_nav_lists_parts_and_chapters(self):
        self.section('<article class="card" id="p06-ch1"><p class="chnum">1장</p>'
                     '<h2>HTTP &amp; JSON</h2></article>\n' + self.ok_slide())
        html = self.build().html
        self.assertIn('<option value="p06">6부 · 맨손 구현</option>', html)
        self.assertIn('<option value="p06-ch1">· HTTP &amp; JSON</option>', html)


class Sections(Tree):
    """명세 캡처의 구역 — part · server · wire(ex=) · lines · grep."""

    def setUp(self):
        super().setUp()
        self.spec()

    def out(self, args):
        self.section(self.ok_slide() + self.slide('<!--SPEC file=ex/run/06/bus.run-->\n'
                                                  '<!--CODE file=ex/py/06/bus.py-->\n'
                                                  '<!--OUT file=out/06/bus.txt %s-->' % args))
        r = self.build()
        self.assertEqual(r.errors, [])
        return r.html.split('data-src="out/06/bus.txt"')[1].split('</pre>')[0]

    def test_whole_capture(self):
        self.assertTrue(self.out('').startswith(' data-lines="1-19">'))

    def test_client_terminal(self):
        got = self.out('part=터미널 3')
        self.assertTrue(got.startswith(' data-lines="3-6">'))
        self.assertIn('<span class="p">[터미널 3] $ curl -s http://127.0.0.1:10601/a</span>\nA\n', got)

    def test_server_output(self):
        self.assertEqual(self.out('server=bus'), ' data-lines="8-10">bus ready\nGET /a\nGET /b\n')

    def test_wire_exchanges(self):
        self.assertTrue(self.out('wire=bus-wire').startswith(' data-lines="12-19">'))
        self.assertEqual(self.out('wire=bus-wire ex=2'),
                         ' data-lines="16-19">→ GET /b HTTP/1.1\n  Accept: */*\n← 200 OK\n  B\n')
        self.assertTrue(self.out('wire=bus-wire ex=1-2').startswith(' data-lines="12-19">'))

    def test_lines_are_relative_to_the_section(self):
        self.assertEqual(self.out('server=bus lines=2-3'), ' data-lines="9-10">GET /a\nGET /b\n')

    def test_grep_keeps_matching_lines(self):
        self.assertEqual(self.out('wire=bus-wire grep=^[→←]'),
                         ' data-lines="12-12,14-14,16-16,18-18">→ GET /a HTTP/1.1\n← 200 OK\n'
                         '→ GET /b HTTP/1.1\n← 200 OK\n')

    def test_label_becomes_the_caption(self):
        self.section(self.ok_slide() + self.slide('<!--SPEC file=ex/run/06/bus.run-->\n'
                                                  '<!--CODE file=ex/py/06/bus.py-->\n'
                                                  '<!--OUT file=out/06/bus.txt wire=bus-wire ex=1-->'))
        self.assertIn('<p class="cap">와이어 (bus-wire) · 주고받음 1</p>', self.build().html)

    def test_unknown_sections_are_errors(self):
        for args in ('server=nope', 'wire=nope', 'part=터미널 9', 'wire=bus-wire ex=3',
                     'server=bus grep=zzz', 'server=bus lines=2-9'):
            self.section(self.ok_slide() + self.slide('<!--SPEC file=ex/run/06/bus.run-->\n'
                                                      '<!--CODE file=ex/py/06/bus.py-->\n'
                                                      '<!--OUT file=out/06/bus.txt %s-->' % args))
            self.assertNotEqual(self.build().errors, [], args)

    def test_spec_shows_the_spec_file(self):
        self.section(self.ok_slide() + self.slide('<!--SPEC file=ex/run/06/bus.run-->\n'
                                                  '<!--CODE file=ex/py/06/bus.py-->'))
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertIn('<pre data-src="ex/run/06/bus.run" data-lines="1-4"><code data-lang="text">serve', r.html)


class Rules(Tree):
    def test_missing_file(self):
        self.section(self.ok_slide() + self.slide('<!--RUN file=ex/py/06/none.py-->'))
        self.assertIn('ex/py/06/none.py', self.errs())

    def test_stale_capture(self):
        self.section(self.ok_slide())
        self.put('ex/py/06/a.py', CODE.replace('1, 2', '1, 3'))     # 캡처 뒤에 소스를 고쳤다
        self.assertIn('낡았', self.errs())

    def test_fixture_change_makes_capture_stale(self):
        self.section(self.ok_slide())
        self.put('ex/fixtures/bus.json', '{}\n')
        self.assertIn('ex/fixtures', self.errs())

    def test_edited_capture(self):
        self.section(self.ok_slide())
        self.put('out/06/a.py.txt', CAP.replace('[1, 2]', '[1, 3]'))
        self.assertIn('낡았', self.errs())

    def test_run_on_a_norun_example(self):
        self.put('ex/py/06/s.py', 'print(1)\n#@ norun\n')
        self.section(self.ok_slide() + self.slide('<!--RUN file=ex/py/06/s.py-->'))
        self.assertIn('norun', self.errs())

    def test_handwritten_pre_is_rejected(self):
        self.section(self.ok_slide() + self.slide('<pre><code data-lang="json">{"id": 1}</code></pre>'))
        self.assertIn('손으로 쓴 <pre>', self.errs())

    def test_fig_pre_is_allowed_but_measured_and_must_not_hold_code(self):
        self.section(self.ok_slide() + self.slide('<pre class="fig">클라이언트 → 서버\n</pre>'))
        self.assertEqual(self.build().errors, [])
        self.section(self.ok_slide() + self.slide('<pre class="fig">' + '가' * 37 + '\n</pre>'))
        self.assertIn('72칸', self.errs())
        self.section(self.ok_slide() + self.slide('<pre class="fig">{"jsonrpc": "2.0", "id": 1}\n</pre>'))
        self.assertIn('그림', self.errs())

    def test_code_width_counts_korean_as_two(self):
        self.example('ex/py/06/w.py', '# ' + '가' * 36 + '\nprint(1)\n', CAP)
        self.section(self.ok_slide() + self.slide('<!--CODE file=ex/py/06/w.py-->'))
        self.assertIn('72칸', self.errs())

    def test_code_too_long(self):
        self.example('ex/py/06/l.py', 'x = 1\n' * 46, CAP)
        self.section(self.ok_slide() + self.slide('<!--CODE file=ex/py/06/l.py-->'))
        self.assertIn('45줄', self.errs())

    def test_slice_must_end_on_a_block_boundary_for_braces(self):
        src = 'function f(): void {\n  console.log("}");  // {\n}\nf();\n'
        self.example('ex/ts/06/f.ts', src, '$ node 06/f.ts\n}\n')
        self.section(self.ok_slide() + self.slide('<!--RUN file=ex/ts/06/f.ts-->\n'
                                                  '<!--CODE file=ex/ts/06/f.ts lines=1-2-->'))
        self.assertIn('중괄호', self.errs())
        self.section(self.ok_slide() + self.slide('<!--RUN file=ex/ts/06/f.ts-->\n'
                                                  '<!--CODE file=ex/ts/06/f.ts lines=1-3-->'))
        self.assertEqual(self.build().errors, [])

    def test_duplicate_and_missing_id(self):
        self.section(self.ok_slide() + self.ok_slide())
        self.assertIn('id 가 겹친다', self.errs())
        self.section(self.ok_slide() + '<article class="card"><p>x</p></article>\n')
        self.assertIn('id 가 없다', self.errs())

    def test_id_must_carry_part_prefix(self):
        self.section(self.ok_slide().replace('p06-a', 'p07-a'))
        self.assertIn('p06', self.errs())

    def test_dead_internal_link(self):
        self.section(self.ok_slide() + self.slide('<a href="#p99-x">저기</a>'))
        self.assertIn('#p99-x', self.errs())

    def test_unknown_release_or_source(self):
        for d in ('<!--REL v=v9-->', '<!--SRC key=nope-->', '<!--FACT id=nope-->'):
            self.section(self.ok_slide() + self.slide('<p>%s</p>' % d))
            self.assertNotEqual(self.build().errors, [], d)

    def test_unknown_and_unexpanded_directives(self):
        self.section(self.ok_slide() + self.slide('<!--RUNN file=x-->'))
        self.assertIn('RUNN', self.errs())
        self.section(self.ok_slide() + self.slide('<!--RUN file = ex/py/06/a.py-->'))
        self.assertIn('펴지지 않은 지시자', self.errs())

    def test_placeholder_is_an_error_unless_skeleton_and_is_counted(self):
        self.section(self.ok_slide() + self.slide('<p>준비 중입니다</p>'))
        self.assertIn('준비 중', self.errs())
        r = self.build(skel=True)
        self.assertEqual(r.errors, [])
        self.assertEqual(r.placeholders, 1)

    def test_part_budget_over_ten_percent(self):
        self.put('deck/budget.txt', '6 2\n')
        self.section(self.ok_slide() + ''.join(self.slide('<p>x</p>', 'p06-x%d' % i) for i in range(2)))
        self.assertIn('예산', self.errs())

    def test_hard_cap(self):
        self.put('deck/budget.txt', '6 4000\n')
        self.section(self.ok_slide() + ''.join(self.slide('<p>x</p>', 'p06-x%d' % i) for i in range(2000)))
        self.assertIn('상한은 2000장', self.errs())

    def test_unused_example_is_an_error_when_finished(self):
        self.example('ex/py/06/unused.py', CODE, CAP)
        self.put('ex/py/06/srv.py', 'print(1)\n#@ norun\n')
        self.section(self.ok_slide())
        self.assertIn('ex/py/06/unused.py', self.errs())
        self.assertIn('ex/py/06/srv.py', self.errs())          # norun 도 어딘가에는 실려야 한다
        self.assertEqual(self.build(skel=True).errors, [])

    def test_box_drawing_outside_pre(self):
        self.section(self.ok_slide() + self.slide('<p>┌─┐</p>'))
        self.assertIn('박스 그리기', self.errs())

    def test_long_capture_line_wraps_then_fails(self):
        self.example('ex/py/06/long.py', CODE, '$ x\n' + 'e' * 120 + '\n')
        self.section(self.ok_slide() + self.slide('<!--RUN file=ex/py/06/long.py-->'))
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertIn('<pre class="term wrap" data-src="out/06/long.py.txt"', r.html)
        self.example('ex/py/06/long.py', CODE, '$ x\n' + 'e' * 201 + '\n')
        self.assertIn('200칸', self.errs())


class History(Tree):
    """역사 부(1부) — 연도는 근거가 있어야 한다."""

    def setUp(self):
        super().setUp()
        self.put('deck/order.txt', '01_why.html\n06_bare.html\n')
        self.put('deck/budget.txt', '1 10\n6 10\n')
        self.put('data/sources.tsv', 'key\turl\ttitle\tdate\n'
                 'announce\thttps://example.org/a\tAnnouncing A2A\t2025-04-09\n')
        self.put('data/evidence.tsv', 'id\tsource\tmatched\n'
                 'launch\tannounce\tToday we are launching a new, open protocol called Agent2Agent\n')
        self.section(self.ok_slide())

    def history(self, body):
        self.put('deck/sections/01_why.html',
                 '<article class="card section" id="p01"><p class="chnum">1부</p><h2>왜</h2></article>\n'
                 '<article class="card" id="p01-a">' + body + '</article>\n')

    def test_fact_renders_a_source_link_and_allows_its_year(self):
        self.history('<p>2025년에 공개됐습니다. <!--FACT id=launch--></p>')
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertIn('<a class="src" href="https://example.org/a" title="Announcing A2A — Today we are '
                      'launching a new, open protocol called Agent2Agent">출처</a>', r.html)

    def test_year_without_evidence_is_an_error(self):
        self.history('<p>2019년에 시작했습니다. <!--FACT id=launch--></p>')
        self.assertIn('2019', self.errs())

    def test_history_slide_without_any_source_is_an_error(self):
        self.history('<p>그냥 주장만 있습니다.</p>')
        self.assertIn('근거', self.errs())

    def test_placeholder_slide_is_not_history_checked(self):
        self.history('<p>준비 중입니다</p>')
        self.assertEqual(self.build(skel=True).errors, [])


class Appendix(Tree):
    def setUp(self):
        super().setUp()
        self.put('deck/order.txt', '06_bare.html\n18_appendix.html\n')
        self.put('deck/budget.txt', '6 10\n18 20\n')
        self.section(self.ok_slide())

    def appendix(self, body):
        self.put('deck/sections/18_appendix.html',
                 '<article class="card section" id="p18"><p class="chnum">부록</p><h2>부록</h2></article>\n' + body)

    def test_glossary_is_paged_sorted_and_link_checked(self):
        self.put('deck/glossary.tsv', 'ko\ten\tdesc\twhere\n'
                 '작업\tTask\t상태를 가진 일\tp06-a\n'
                 '메시지\tMessage\t한 번 주고받는 말\tp06-a\n')
        self.appendix('<!--GLOSSARY per=1-->\n')
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertLess(r.html.index('>메시지</a>'), r.html.index('>작업</a>'))
        self.assertEqual(r.per_part[18], 3)
        self.put('deck/glossary.tsv', 'ko\ten\tdesc\twhere\n작업\tTask\t설명\tp99-x\n')
        self.assertIn('p99-x', self.errs())

    def test_sources_lists_every_source(self):
        self.appendix('<!--SOURCES per=10-->\n')
        r = self.build()
        self.assertEqual(r.errors, [])
        self.assertIn('<a href="https://a2a-protocol.org/x">A2A Specification</a>', r.html)

    def test_generated_slides_must_be_outside_an_article(self):
        self.appendix('<article class="card" id="p18-x"><!--GLOSSARY per=2--></article>\n')
        self.assertIn('GLOSSARY', self.errs())


class Width(unittest.TestCase):
    def test_width(self):
        w = build_deck.display_width
        self.assertEqual(w('abc', '.py'), 3)
        self.assertEqual(w('가나', '.py'), 4)
        self.assertEqual(w('a\tb', '.txt'), 9)       # 탭은 8칸 자리까지
        self.assertEqual(w('\t\tb', '.go'), 9)       # Go 는 4칸
        self.assertEqual(w('→', '.py'), 1)


class Verify(Tree):
    def built(self, body=None):
        self.section(body or self.ok_slide())
        r = self.build()
        self.assertEqual(r.errors, [])
        return r.html

    def test_clean_deck_verifies(self):
        self.assertEqual(verify_deck.verify(self.root, self.built()), [])

    def test_regions_go_tabs_and_grep_verify(self):
        self.example('ex/go/06/hello', 'package main\n\n// region: m\nfunc main() {\n\tprintln("hi")\n}\n'
                     '// endregion\n', '$ go run ./06/hello\nhi\n', main='ex/go/06/hello/main.go')
        self.spec()
        html = self.built(self.ok_slide() + self.slide(
            '<!--RUN file=ex/go/06/hello-->\n<!--CODE file=ex/go/06/hello/main.go region=m-->\n'
            '<!--SPEC file=ex/run/06/bus.run-->\n<!--CODE file=ex/py/06/bus.py-->\n'
            '<!--OUT file=out/06/bus.txt wire=bus-wire grep=^→-->'))
        self.assertEqual(verify_deck.verify(self.root, html), [])

    def test_edited_code_in_deck_is_caught(self):
        html = self.built().replace('v = [1, 2]', 'v = [1, 9]')
        self.assertNotEqual(verify_deck.verify(self.root, html), [])

    def test_edited_capture_in_deck_is_caught(self):
        html = self.built().replace('[1, 2]\n</pre>', '[7]\n</pre>')
        self.assertNotEqual(verify_deck.verify(self.root, html), [])

    def test_pre_without_source_is_caught(self):
        html = self.built().replace('</main>', '<pre><code>x = 1</code></pre></main>')
        self.assertNotEqual(verify_deck.verify(self.root, html), [])

    def test_source_changed_after_build_is_caught(self):
        html = self.built()
        self.put('ex/py/06/a.py', CODE + '# 나중에 덧붙임\n')
        self.assertNotEqual(verify_deck.verify(self.root, html), [])


if __name__ == '__main__':
    unittest.main()
