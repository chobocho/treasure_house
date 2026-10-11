# -*- coding: utf-8 -*-
"""rsrun.py 시험 — 지시자 해석·명령 줄·정규화·캡처 형식, 그리고 진짜 rustc 로 한 번씩."""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import rsrun  # noqa: E402


class Directives(unittest.TestCase):
    def test_no_directive_gives_defaults(self):
        code, d = rsrun.parse_directives('fn main() {}\n')
        self.assertEqual(code, 'fn main() {}\n')
        self.assertEqual(d['edition'], '2024')
        self.assertEqual(d['exit'], 0)
        self.assertEqual(d['expect'], [])

    def test_trailing_directives_are_stripped(self):
        src = 'fn main() {}\n//@ edition: 2021\n//@ exit: 101\n'
        code, d = rsrun.parse_directives(src)
        self.assertEqual(code, 'fn main() {}\n')
        self.assertEqual(d['edition'], '2021')
        self.assertEqual(d['exit'], 101)

    def test_blank_line_before_directives_is_stripped_too(self):
        code, _ = rsrun.parse_directives('fn main() {}\n\n//@ test\n')
        self.assertEqual(code, 'fn main() {}\n')

    def test_expect_list(self):
        _, d = rsrun.parse_directives('x\n//@ expect: E0382, E0499\n')
        self.assertEqual(d['expect'], ['E0382', 'E0499'])

    def test_flag_directives(self):
        _, d = rsrun.parse_directives(
            'x\n//@ test\n//@ norun\n//@ warnings: show\n//@ flags: -O\n')
        self.assertTrue(d['test'])
        self.assertTrue(d['norun'])
        self.assertTrue(d['warnings'])
        self.assertEqual(d['flags'], ['-O'])

    def test_stdin_unescapes_newlines(self):
        _, d = rsrun.parse_directives('x\n//@ stdin: 3\\n4\\n\n')
        self.assertEqual(d['stdin'], '3\n4\n')

    def test_directive_in_the_middle_is_an_error(self):
        # 가운데에 두면 화면의 줄 번호와 컴파일러가 말하는 줄 번호가 어긋난다.
        with self.assertRaises(rsrun.RsrunError):
            rsrun.parse_directives('//@ exit: 1\nfn main() {}\n')

    def test_unknown_key_is_an_error(self):
        with self.assertRaises(rsrun.RsrunError):
            rsrun.parse_directives('x\n//@ editon: 2021\n')

    def test_bad_edition_is_an_error(self):
        with self.assertRaises(rsrun.RsrunError):
            rsrun.parse_directives('x\n//@ edition: 2019\n')

    def test_empty_file_is_an_error(self):
        with self.assertRaises(rsrun.RsrunError):
            rsrun.parse_directives('')


class Commands(unittest.TestCase):
    def d(self, text='x\n'):
        return rsrun.parse_directives(text)[1]

    def test_plain(self):
        self.assertEqual(rsrun.shown_commands('move', self.d()),
                         ['rustc --edition 2024 move.rs', './move'])

    def test_flags_test_args(self):
        d = self.d('x\n//@ flags: -O\n//@ test\n//@ args: a b\n')
        self.assertEqual(rsrun.shown_commands('t', d),
                         ['rustc --edition 2024 -O --test t.rs', './t a b'])

    def test_stdin_is_shown_as_printf(self):
        d = self.d('x\n//@ stdin: 3\\n4\\n\n')
        self.assertEqual(rsrun.shown_commands('add', d)[1],
                         "printf '3\\n4\\n' | ./add")

    def test_expect_or_norun_has_no_run_step(self):
        self.assertEqual(
            rsrun.shown_commands('bad', self.d('x\n//@ expect: E0382\n')),
            ['rustc --edition 2024 bad.rs'])
        self.assertEqual(
            rsrun.shown_commands('w', self.d('x\n//@ norun\n')),
            ['rustc --edition 2024 w.rs'])


class Normalize(unittest.TestCase):
    def test_thread_id(self):
        s = "thread 'main' (15382) panicked at p.rs:1:56:\n"
        self.assertEqual(rsrun.normalize(s, '/s'),
                         "thread 'main' (tid) panicked at p.rs:1:56:\n")

    def test_unnamed_thread_id(self):
        s = "thread '<unnamed>' (7) panicked at a.rs:2:5:\n"
        self.assertIn("'<unnamed>' (tid) panicked", rsrun.normalize(s, '/s'))

    def test_timings(self):
        s = ('test result: ok. 1 passed; 0 failed; finished in 1.23s\n'
             '    Finished `dev` profile [unoptimized] target(s) in 12.34s\n')
        out = rsrun.normalize(s, '/s')
        self.assertIn('finished in 0.00s', out)
        self.assertIn('target(s) in 0.00s', out)

    def test_doctest_timings(self):
        s = 'all doctests ran in 1.35s; merged doctests compilation took 1.26s\n'
        self.assertEqual(rsrun.normalize(s, '/s'),
                         'all doctests ran in 0.00s; merged doctests compilation took 0.00s\n')

    def test_sandbox_path(self):
        s = 'Compiling demo v0.1.0 (/a/b/scratch/run/x)\n'
        self.assertEqual(rsrun.normalize(s, '/a/b/scratch/run/x'),
                         'Compiling demo v0.1.0 (/work)\n')

    def test_ordinary_numbers_are_untouched(self):
        s = 'sum (15382) = 3 in 4.5s total\n'
        self.assertEqual(rsrun.normalize(s, '/s'), s)


class Capture(unittest.TestCase):
    def test_silent_compile_is_folded_into_one_line(self):
        cap = rsrun.format_capture([('rustc --edition 2024 a.rs', '', 0),
                                    ('./a', 'hi\n', 0)])
        self.assertEqual(cap, '$ rustc --edition 2024 a.rs && ./a\nhi\n')

    def test_compile_output_keeps_two_steps(self):
        cap = rsrun.format_capture([('rustc --edition 2024 a.rs', 'warning: x\n', 0),
                                    ('./a', 'hi\n', 0)])
        self.assertEqual(cap, '$ rustc --edition 2024 a.rs\nwarning: x\n$ ./a\nhi\n')

    def test_nonzero_exit_is_recorded(self):
        cap = rsrun.format_capture([('rustc --edition 2024 a.rs', '', 0),
                                    ('./a', 'boom\n', 101)])
        self.assertTrue(cap.endswith('boom\n[종료 코드 101]\n'))

    def test_missing_final_newline_is_added(self):
        cap = rsrun.format_capture([('./a', 'no newline', 0)])
        self.assertEqual(cap, '$ ./a\nno newline\n')

    def test_trailing_spaces_survive(self):
        # 출력은 진짜여야 한다 — 줄 끝 공백도 프로그램이 찍은 것이다.
        cap = rsrun.format_capture([('./a', 'a  \n', 0)])
        self.assertEqual(cap, '$ ./a\na  \n')


class Prune(unittest.TestCase):
    def test_orphan_capture_and_row_are_removed(self):
        root = tempfile.mkdtemp(prefix='prune-test-')
        self.addCleanup(shutil.rmtree, root, True)
        for rel, text in (('ex/02/keep.rs', 'fn main() {}\n'), ('out/02/keep.txt', '$ x\n'),
                          ('ex/02/gone.rs', 'fn main() {}\n'), ('out/02/gone.txt', '$ y\n')):
            os.makedirs(os.path.dirname(os.path.join(root, rel)), exist_ok=True)
            with open(os.path.join(root, rel), 'w') as f:
                f.write(text)
        rsrun.manifest_update(root, 'ex/02/keep.rs', 'rustc 1')
        rsrun.manifest_update(root, 'ex/02/gone.rs', 'rustc 1')
        os.remove(os.path.join(root, 'ex/02/gone.rs'))         # 예제를 지웠거나 이름을 바꿨다
        self.assertEqual(rsrun.orphans(root), ['out/02/gone.txt'])
        rsrun.prune(root)
        self.assertEqual(rsrun.orphans(root), [])
        self.assertFalse(os.path.exists(os.path.join(root, 'out/02/gone.txt')))
        self.assertEqual(list(rsrun.manifest_load(root)), ['ex/02/keep.rs'])
        self.assertTrue(os.path.exists(os.path.join(root, 'out/02/keep.txt')))


@unittest.skipUnless(rsrun.toolchain_ok(), 'rustc 가 없다')
class RealCompiler(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='rsrun-test-')
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write(self, name, text):
        p = os.path.join(self.tmp, name)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(text)
        return p

    def run_ex(self, name, text):
        return rsrun.run_example(self.write(name, text),
                                 scratch=os.path.join(self.tmp, 'scratch'))

    def test_hello(self):
        cap = self.run_ex('hello.rs', 'fn main() {\n    println!("안녕");\n}\n')
        self.assertEqual(cap, '$ rustc --edition 2024 hello.rs && ./hello\n안녕\n')

    def test_expected_compile_error(self):
        cap = self.run_ex('moved.rs', (
            'fn main() {\n    let s = String::from("a");\n    let _t = s;\n'
            '    println!("{s}");\n}\n//@ expect: E0382\n'))
        self.assertTrue(cap.startswith('$ rustc --edition 2024 moved.rs\n'))
        self.assertIn('error[E0382]', cap)
        self.assertIn('--> moved.rs:4:', cap)        # 줄 번호가 화면과 같다
        self.assertTrue(cap.endswith('[종료 코드 1]\n'))

    def test_syntax_error_without_a_code(self):
        # 문법 오류에는 E 번호가 없다 — expect: error 는 "오류로 실패" 만 뜻한다.
        cap = self.run_ex('semi.rs', 'fn main() {\n    let a = 1\n}\n//@ expect: error\n')
        self.assertIn('error: expected `;`', cap)
        self.assertTrue(cap.endswith('[종료 코드 1]\n'))

    def test_wrong_expected_code_fails(self):
        with self.assertRaises(rsrun.RsrunError):
            self.run_ex('moved2.rs', (
                'fn main() {\n    let s = String::from("a");\n    let _t = s;\n'
                '    println!("{s}");\n}\n//@ expect: E0499\n'))

    def test_unexpected_compile_error_fails(self):
        with self.assertRaises(rsrun.RsrunError):
            self.run_ex('broken.rs', 'fn main() { let x: i32 = "a"; }\n')

    def test_expected_error_that_compiles_fails(self):
        with self.assertRaises(rsrun.RsrunError):
            self.run_ex('fine.rs', 'fn main() {}\n//@ expect: E0382\n')

    def test_panic_exit_code_and_tid(self):
        cap = self.run_ex('boom.rs', (
            'fn main() {\n    let v = vec![1];\n    let i = v.len() + 2;\n'
            '    println!("{}", v[i]);\n}\n//@ exit: 101\n'))
        self.assertIn("thread 'main' (tid) panicked at boom.rs:4:", cap)
        self.assertTrue(cap.endswith('[종료 코드 101]\n'))

    def test_unexpected_exit_code_fails(self):
        with self.assertRaises(rsrun.RsrunError):
            self.run_ex('exit3.rs', 'fn main() { std::process::exit(3); }\n')

    def test_warning_is_an_error_unless_shown(self):
        src = 'fn main() {\n    let x = 1;\n}\n'
        with self.assertRaises(rsrun.RsrunError):
            self.run_ex('warn.rs', src)
        cap = self.run_ex('warn2.rs', src + '//@ warnings: show\n')
        self.assertIn('warning: unused variable', cap)
        self.assertIn('\n$ ./warn2\n', cap)

    def test_stdin_and_args(self):
        cap = self.run_ex('echo.rs', (
            'use std::io::Read;\nfn main() {\n    let mut s = String::new();\n'
            '    std::io::stdin().read_to_string(&mut s).unwrap();\n'
            '    let a: Vec<String> = std::env::args().skip(1).collect();\n'
            '    println!("{} {:?}", s.trim(), a);\n}\n'
            '//@ stdin: hi\\n\n//@ args: x y\n'))
        self.assertEqual(cap.split('\n')[0],
                         "$ rustc --edition 2024 echo.rs && printf 'hi\\n' | ./echo x y")
        self.assertIn('hi ["x", "y"]', cap)

    def test_test_harness(self):
        cap = self.run_ex('t.rs', '#[test]\nfn two() {\n    assert_eq!(1 + 1, 2);\n}\n//@ test\n')
        self.assertIn('test two ... ok', cap)
        self.assertIn('finished in 0.00s', cap)

    def test_infinite_loop_times_out(self):
        with self.assertRaises(rsrun.RsrunError):
            rsrun.run_example(self.write('spin.rs', 'fn main() {\n    loop {}\n}\n'),
                              scratch=os.path.join(self.tmp, 'scratch'), timeout=2)

    def test_directory_example_with_run_file(self):
        d = os.path.join(self.tmp, 'multi')
        os.mkdir(d)
        with open(os.path.join(d, 'main.rs'), 'w') as f:
            f.write('mod util;\nfn main() {\n    println!("{}", util::two());\n}\n')
        with open(os.path.join(d, 'util.rs'), 'w') as f:
            f.write('pub fn two() -> i32 {\n    2\n}\n')
        with open(os.path.join(d, 'RUN'), 'w') as f:
            f.write('rustc --edition 2024 main.rs\n./main\n')
        cap = rsrun.run_example(d, scratch=os.path.join(self.tmp, 'scratch'))
        self.assertEqual(cap, '$ rustc --edition 2024 main.rs && ./main\n2\n')
        self.assertEqual(sorted(os.listdir(d)), ['RUN', 'main.rs', 'util.rs'])  # ex/ 는 깨끗하다


if __name__ == '__main__':
    unittest.main()
