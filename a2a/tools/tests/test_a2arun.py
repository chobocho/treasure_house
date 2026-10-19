# -*- coding: utf-8 -*-
"""a2arun.py 시험 — 지시자·명령 줄·정규화 표·명세 해석·포트 규칙·장부, 그리고 진짜로 돌려 보기.

   진짜 실행 시험은 임시 뿌리(ex/·out/·scratch/)를 만들어 그 안에서 돌린다.
   파이썬은 a2a/.venv 의 것을, node 와 go 는 PATH 의 것을 쓴다.
   명세(spec) 시험의 핵심은 '고아 프로세스가 남지 않는다' 다 — 성공해도, 실패해도.
"""
import os
import shutil
import socket
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import a2arun  # noqa: E402

HAVE_GO = shutil.which('go') is not None
HAVE_NODE = shutil.which('node') is not None
HAVE_CURL = shutil.which('curl') is not None


class Directives(unittest.TestCase):
    def test_defaults(self):
        body, d = a2arun.parse_directives('print(1)\n', 'py')
        self.assertEqual(body, 1)
        self.assertEqual(d, {'args': '', 'stdin': None, 'exit': 0, 'timeout': 20,
                             'norun': False, 'env': []})

    def test_trailing_py_directives(self):
        body, d = a2arun.parse_directives(
            'print(1)\n\n#@ args: a b\n#@ exit: 3\n#@ timeout: 5\n#@ stdin: x\\ny\\n\n', 'py')
        self.assertEqual(body, 1)                       # 빈 줄과 지시자는 본문이 아니다
        self.assertEqual((d['args'], d['exit'], d['timeout'], d['stdin']),
                         ('a b', 3, 5, 'x\ny\n'))

    def test_ruff_formatted_python_directive(self):
        # ruff format 은 '#@' 를 '# @' 로 고친다 — 고친 꼴도 지시자다.
        body, d = a2arun.parse_directives('print(1)\n# @ exit: 3\n# @ norun\n', 'py')
        self.assertEqual((body, d['exit'], d['norun']), (1, 3, True))

    def test_go_and_ts_use_slashes(self):
        body, d = a2arun.parse_directives('package main\n//@ norun\n', 'go')
        self.assertEqual((body, d['norun']), (1, True))
        _, d = a2arun.parse_directives('x;\n//@ env: A=1\n//@ env: B=two\n', 'ts')
        self.assertEqual(d['env'], [('A', '1'), ('B', 'two')])

    def test_directive_in_the_middle_is_an_error(self):
        with self.assertRaises(a2arun.RunError):
            a2arun.parse_directives('#@ exit: 1\nprint(1)\n', 'py')

    def test_unknown_key_is_an_error(self):
        with self.assertRaises(a2arun.RunError):
            a2arun.parse_directives('x\n#@ arg: 1\n', 'py')

    def test_bad_env_is_an_error(self):
        with self.assertRaises(a2arun.RunError):
            a2arun.parse_directives('x\n//@ env: NOEQUALS\n', 'ts')

    def test_empty_file_is_an_error(self):
        with self.assertRaises(a2arun.RunError):
            a2arun.parse_directives('', 'py')


class Shown(unittest.TestCase):
    def d(self, text='x\n', lang='py'):
        return a2arun.parse_directives(text, lang)[1]

    def test_python(self):
        self.assertEqual(a2arun.shown_command('py', '02/x.py', self.d()), 'python 02/x.py')

    def test_args_env_stdin(self):
        d = self.d('x\n#@ args: --port 10201\n#@ env: A2A_DEBUG=1\n#@ stdin: hi\\n\n')
        self.assertEqual(a2arun.shown_command('py', '02/x.py', d),
                         "printf 'hi\\n' | A2A_DEBUG=1 python 02/x.py --port 10201")

    def test_node_and_go(self):
        self.assertEqual(a2arun.shown_command('ts', '02/x.ts', self.d('x\n', 'ts')),
                         'node 02/x.ts')
        self.assertEqual(a2arun.shown_command('go', '02/hello', self.d('x\n//@ args: a\n', 'go')),
                         'go run ./02/hello a')


class Normalize(unittest.TestCase):
    """선언한 정규화 — 규칙 하나에 시험 하나. 그 밖의 글자는 그대로여야 한다."""
    ROOT = '/x/repo/a2a'

    def n(self, s):
        return a2arun.normalize(s, self.ROOT)

    def test_rule_table_is_exactly_these(self):
        self.assertEqual([r[0] for r in a2arun.RULES],
                         ['path', 'timestamp', 'duration', 'port', 'uuid'])

    def test_uuid_numbered_by_first_appearance(self):
        a, b = '3f2c1b7e-0d9a-4c1e-9b7a-1c2d3e4f5a6b', 'AAAAAAAA-BBBB-4CCC-8DDD-EEEEEEEEEEEE'
        s = 'task %s ctx %s again %s %s' % (a, b, a, b.lower())
        self.assertEqual(self.n(s), 'task <id1> ctx <id2> again <id1> <id2>')

    def test_go_log_timestamps(self):
        # Go 의 log·slog 기본 머리(2026/10/16 11:53:57)도 실행마다 다르다.
        s = '2026/10/16 11:53:57 INFO x\n2026/10/16 11:53:57.123456 y ; 2026/10/16 stays'
        self.assertEqual(self.n(s), '<시각> INFO x\n<시각> y ; 2026/10/16 stays')

    def test_timestamps(self):
        s = ('"timestamp": "2026-10-16T07:04:05.123456Z" at 2026-10-16T07:04:05+09:00 '
             'and 2026-10-16 07:04:05.5 ; date 2026-11-07 stays')
        self.assertEqual(self.n(s), '"timestamp": "<시각>" at <시각> and <시각> ; date 2026-11-07 stays')

    def test_durations(self):
        self.assertEqual(self.n('took 12.3ms, budget 300ms, 0.5s'),
                         'took <ms>, budget 300ms, 0.5s')

    def test_repo_paths(self):
        s = ('File "/x/repo/a2a/ex/py/workshop/a.py", line 3\n'
             'cwd /x/repo/a2a and /x/repo/rust/x\n')
        self.assertEqual(self.n(s), 'File "ex/py/workshop/a.py", line 3\n'
                                    'cwd . and /x/repo/rust/x\n')

    def test_ephemeral_ports(self):
        s = 'INFO: 127.0.0.1:54321 - "POST / HTTP/1.1" 200 / http://127.0.0.1:10201/ localhost:40000'
        self.assertEqual(self.n(s), 'INFO: 127.0.0.1:<port> - "POST / HTTP/1.1" 200 / '
                                    'http://127.0.0.1:10201/ localhost:<port>')

    def test_ordinary_text_is_untouched(self):
        s = 'id 12345, 3.5 ms apart, port 8080, 2026-10 report, deadbeef-1234\n'
        self.assertEqual(self.n(s), s)


class Paths(unittest.TestCase):
    def test_capture_paths(self):
        cp = a2arun.capture_path
        self.assertEqual(cp('ex/py/02/x.py'), 'out/02/x.py.txt')
        self.assertEqual(cp('ex/ts/02/x.ts'), 'out/02/x.ts.txt')
        self.assertEqual(cp('ex/go/02/hello'), 'out/02/hello.go.txt')
        self.assertEqual(cp('ex/run/11/push.run'), 'out/11/push.txt')

    def test_source_of_capture_is_the_inverse(self):
        for rel in ('ex/py/02/x.py', 'ex/ts/02/x.ts', 'ex/go/02/hello', 'ex/run/11/push.run'):
            self.assertEqual(a2arun.source_of(a2arun.capture_path(rel)), rel)

    def test_example_root(self):
        self.assertEqual(a2arun.example_of('ex/go/02/hello/main.go'), 'ex/go/02/hello')
        self.assertEqual(a2arun.example_of('ex/go/02/hello/'), 'ex/go/02/hello')
        self.assertEqual(a2arun.example_of('ex/py/02/x.py'), 'ex/py/02/x.py')
        self.assertIsNone(a2arun.example_of('ex/py/workshop/a.py'))
        self.assertIsNone(a2arun.example_of('ex/fixtures/a.json'))

    def test_part_and_port_range(self):
        self.assertEqual(a2arun.part_of('ex/run/11/push.run'), 11)
        self.assertEqual(a2arun.port_range(11), (11100, 11199))
        self.assertEqual(a2arun.port_range(2), (10200, 10299))


class Tree(unittest.TestCase):
    """ex/ 를 가진 임시 뿌리."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='a2arun-test-')
        self.addCleanup(shutil.rmtree, self.root, True)
        self.scratch = os.path.join(self.root, 'scratch')

    def put(self, rel, text):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        return p

    def run_ex(self, rel, **kw):
        return a2arun.run_example(self.root, rel, scratch=self.scratch, **kw)


class Discover(Tree):
    def test_examples_and_sources(self):
        self.put('ex/py/02/a.py', 'print(1)\n')
        self.put('ex/py/02/srv.py', 'print(1)\n#@ norun\n')
        self.put('ex/py/workshop/w.py', 'X = 1\n')
        self.put('ex/ts/02/b.ts', 'console.log(1);\n')
        self.put('ex/ts/gate/g.ts', 'console.log(1);\n')
        self.put('ex/ts/node_modules/m/x.ts', '')
        self.put('ex/go/02/hello/main.go', 'package main\n')
        self.put('ex/go/gate/server/main.go', 'package main\n')
        self.put('ex/run/02/c.run', 'run cmd="sh:true"\n')
        self.assertEqual(a2arun.examples(self.root),
                         ['ex/go/02/hello', 'ex/py/02/a.py', 'ex/run/02/c.run', 'ex/ts/02/b.ts'])
        self.assertEqual(a2arun.sources(self.root),
                         ['ex/go/02/hello', 'ex/py/02/a.py', 'ex/py/02/srv.py',
                          'ex/run/02/c.run', 'ex/ts/02/b.ts'])


    def test_targets_all_only_and_paths(self):
        self.put('ex/py/02/a.py', 'print(1)\n')
        self.put('ex/py/03/b.py', 'print(1)\n')
        self.put('ex/run/02/c.run', 'run cmd="sh:true"\n')
        ns = a2arun.argparse.Namespace
        t = a2arun._targets
        self.assertEqual(t(self.root, ns(all=True, paths=[], only='ex/py')),
                         ['ex/py/02/a.py', 'ex/py/03/b.py'])
        self.assertEqual(t(self.root, ns(all=True, paths=[], only='ex/run/02/c.run')),
                         ['ex/run/02/c.run'])
        self.assertEqual(t(self.root, ns(all=False, only=None,
                                         paths=[os.path.join(self.root, 'ex/py/02')])),
                         ['ex/py/02/a.py'])


class Spec(unittest.TestCase):
    def test_parse(self):
        steps = a2arun.parse_spec(
            '# 주석\n'
            'serve name=bus  cmd="go:11/bus --port 11151" ready=http://127.0.0.1:11151/.well-known/agent-card.json\n'
            'serve name=hook cmd="py:11/webhook.py --port 11102" ready=tcp:11102\n'
            'tap   name=bus-wire listen=11101 target=11151 order=sorted\n'
            'run   cmd="ts:11/c.ts http://127.0.0.1:11101" exit=1 timeout=30\n'
            '\n'
            'wait  ms=300   # 푸시가 닿을 시간\n')
        self.assertEqual([s['verb'] for s in steps], ['serve', 'serve', 'tap', 'run', 'wait'])
        self.assertEqual(steps[0]['cmd'], 'go:11/bus --port 11151')
        self.assertEqual(steps[1]['ready'], 'tcp:11102')
        self.assertEqual((steps[2]['listen'], steps[2]['target'], steps[2]['order']),
                         (11101, 11151, 'sorted'))
        self.assertEqual((steps[3]['exit'], steps[3]['timeout']), (1, 30))
        self.assertEqual(steps[4]['ms'], 300)

    def test_backslash_continues_a_line(self):
        # 명세도 슬라이드에 실린다(72칸) — 긴 줄은 \ 로 잇는다.
        steps = a2arun.parse_spec('serve name=bus \\\n'
                                  '      cmd="py:02/s.py \\\n'
                                  '           --port 10251" \\\n'
                                  '      ready=tcp:10251\n'
                                  'run cmd="sh:true"\n')
        self.assertEqual((steps[0]['cmd'], steps[0]['ready'], steps[0]['line']),
                         ('py:02/s.py --port 10251', 'tcp:10251', 1))
        self.assertEqual(steps[1]['line'], 5)

    def test_errors(self):
        for bad in ('jump x=1\n',                                   # 모르는 동사
                    'serve name=a cmd="py:a.py"\n',                 # ready 없음
                    'serve name=a cmd="perl:a.pl" ready=tcp:1\n',   # 모르는 언어
                    'tap name=t listen=1\n',                        # target 없음
                    'run cmd="sh:true" colour=red\n',               # 모르는 키
                    'serve name=a cmd="sh:x" ready=tcp:1\nserve name=a cmd="sh:y" ready=tcp:2\n',
                    'serve name=a cmd="sh:x" ready=tcp:1\n'):     # run 이 하나도 없다
            with self.assertRaises(a2arun.RunError, msg=bad):
                a2arun.parse_spec(bad)

    def test_restart_names_an_earlier_server(self):
        # 17부 — 서버를 SIGKILL 로 죽이고 같은 명령으로 다시 띄운다(영속 저장소 실험).
        steps = a2arun.parse_spec('serve name=bus cmd="sh:x" ready=tcp:10251\n'
                                  'run cmd="sh:true"\n'
                                  'restart name=bus\n'
                                  'run cmd="sh:true"\n')
        self.assertEqual([s['verb'] for s in steps], ['serve', 'run', 'restart', 'run'])
        self.assertEqual(steps[2]['name'], 'bus')
        for bad in ('serve name=a cmd="sh:x" ready=tcp:10251\nrestart name=b\nrun cmd="sh:true"\n',
                    'tap name=t listen=10201 target=10251\nrestart name=t\nrun cmd="sh:true"\n',
                    'restart name=a\nserve name=a cmd="sh:x" ready=tcp:10251\nrun cmd="sh:true"\n',
                    'serve name=a cmd="sh:x" ready=tcp:10251\nrestart\nrun cmd="sh:true"\n'):
            with self.assertRaises(a2arun.RunError, msg=bad):
                a2arun.parse_spec(bad)

    def test_ports_must_be_in_the_part_range(self):
        text = 'serve name=a cmd="py:05/s.py --port 10501" ready=tcp:10501\nrun cmd="sh:curl http://127.0.0.1:10601/"\n'
        with self.assertRaises(a2arun.RunError) as e:
            a2arun.check_ports(5, a2arun.ports_in(text))
        self.assertIn('10601', str(e.exception))
        a2arun.check_ports(5, a2arun.ports_in(text.replace('10601', '10599')))

    def test_ready_must_not_go_through_a_tap(self):
        text = ('serve name=a cmd="sh:x" ready=http://127.0.0.1:10251/\n'
                'tap name=w listen=10201 target=10251\n'
                'serve name=b cmd="sh:y" ready=http://127.0.0.1:10201/\n'
                'run cmd="sh:true"\n')
        with self.assertRaises(a2arun.RunError):
            a2arun.parse_spec(text)

    def test_sort_exchanges(self):
        log = ('→ POST / HTTP/1.1\n  {"b": "%s"}\n← 200 OK\n  1\n'
               '→ GET /x HTTP/1.1\n← 200 OK\n'
               '→ POST / HTTP/1.1\n  {"a": "%s"}\n← 200 OK\n  2\n'
               % ('3f2c1b7e-0d9a-4c1e-9b7a-1c2d3e4f5a6b', 'ffffffff-0d9a-4c1e-9b7a-1c2d3e4f5a6b'))
        got = a2arun.sort_exchanges(log)
        self.assertEqual([ln for ln in got.split('\n') if ln.startswith(('→', '  {'))],
                         ['→ GET /x HTTP/1.1', '→ POST / HTTP/1.1', '  {"a": "ffffffff-0d9a-4c1e-9b7a-1c2d3e4f5a6b"}',
                          '→ POST / HTTP/1.1', '  {"b": "3f2c1b7e-0d9a-4c1e-9b7a-1c2d3e4f5a6b"}'])
        self.assertEqual(sorted(got.split('\n')), sorted(log.split('\n')))


class Manifest(Tree):
    def setUp(self):
        super().setUp()
        self.put('ex/py/02/a.py', 'print(1)\n')
        self.put('out/02/a.py.txt', '$ python 02/a.py\n1\n')
        a2arun.manifest_update(self.root, 'ex/py/02/a.py', 'python 3')

    def test_fresh(self):
        self.assertEqual(a2arun.stale(self.root, 'ex/py/02/a.py'), '')

    def test_inputs_cover_example_workshop_fixtures(self):
        names = [p for p, _ in a2arun.inputs(self.root, 'ex/py/02/a.py')]
        self.assertEqual(names, ['ex/py/02/a.py', 'ex/py/02', 'ex/py/workshop', 'ex/fixtures'])

    def test_other_shared_dirs_are_inputs_but_gate_and_caches_are_not(self):
        for rel in ('ex/py/agents/bus.py', 'ex/py/gate/x.py', 'ex/py/__pycache__/x.pyc',
                    'ex/py/.ruff_cache/x', 'ex/py/requirements.txt'):
            self.put(rel, 'x\n')
        names = [p for p, _ in a2arun.inputs(self.root, 'ex/py/02/a.py')]
        self.assertEqual(names, ['ex/py/02/a.py', 'ex/py/02', 'ex/py/agents', 'ex/py/workshop',
                                 'ex/fixtures'])

    def test_sibling_in_the_same_part_dir_makes_it_stale(self):
        # 07/drive.py 가 07/step1_echo.py 를 import 하듯, 같은 부 디렉터리의
        # 형제가 바뀌어도 캡처는 낡은 것이 되어야 한다.
        self.put('ex/py/02/helper.py', 'X = 1\n')
        a2arun.manifest_update(self.root, 'ex/py/02/a.py', 'python 3')
        self.assertEqual(a2arun.stale(self.root, 'ex/py/02/a.py'), '')
        self.put('ex/py/02/helper.py', 'X = 2\n')
        self.assertIn('ex/py/02', a2arun.stale(self.root, 'ex/py/02/a.py'))

    def test_example_changed(self):
        self.put('ex/py/02/a.py', 'print(2)\n')
        self.assertIn('ex/py/02/a.py', a2arun.stale(self.root, 'ex/py/02/a.py'))

    def test_workshop_or_fixture_changed(self):
        self.put('ex/py/workshop/w.py', 'X = 1\n')
        self.assertIn('ex/py/workshop', a2arun.stale(self.root, 'ex/py/02/a.py'))
        a2arun.manifest_update(self.root, 'ex/py/02/a.py', 'python 3')
        self.put('ex/fixtures/lodging.json', '{}\n')
        self.assertIn('ex/fixtures', a2arun.stale(self.root, 'ex/py/02/a.py'))

    def test_capture_edited_by_hand(self):
        self.put('out/02/a.py.txt', '$ python 02/a.py\n2\n')
        self.assertIn('캡처', a2arun.stale(self.root, 'ex/py/02/a.py'))

    def test_spec_inputs_include_every_program_and_the_tap(self):
        self.put('ex/py/02/s.py', 'x\n#@ norun\n')
        self.put('ex/run/02/c.run', 'serve name=s cmd="py:02/s.py" ready=tcp:10251\n'
                 'tap name=w listen=10201 target=10251\nrun cmd="ts:02/c.ts"\n')
        self.put('ex/ts/02/c.ts', 'x;\n')
        names = [p for p, _ in a2arun.inputs(self.root, 'ex/run/02/c.run')]
        self.assertEqual(names, ['ex/run/02/c.run', 'ex/py/02/s.py', 'ex/ts/02/c.ts',
                                 'ex/py/02', 'ex/ts/02',
                                 'ex/py/workshop', 'ex/ts/workshop', 'ex/fixtures',
                                 'tools/wiretap.py'])

    def test_spec_data_dirs_beside_the_spec_are_inputs(self):
        # 명세가 curl -d @rpc/x.json 처럼 읽는 자료(명세 옆 하위 디렉터리)가
        # 바뀌어도 캡처는 낡은 것이 되어야 한다.
        self.put('ex/run/03/c.run', 'run cmd="sh:curl -s -d @rpc/a.json x"\n')
        self.put('ex/run/03/rpc/a.json', '{}\n')
        self.put('ex/run/03/cards/b.json', '{}\n')
        self.put('ex/run/03/other.run', 'run cmd="sh:true"\n')
        names = [p for p, _ in a2arun.inputs(self.root, 'ex/run/03/c.run')]
        self.assertEqual(names, ['ex/run/03/c.run', 'ex/run/03/cards',
                                 'ex/run/03/rpc', 'ex/fixtures'])

    def test_orphans_and_prune(self):
        self.put('out/02/gone.py.txt', 'x\n')
        self.assertEqual(a2arun.orphans(self.root), ['out/02/gone.py.txt'])
        a2arun.prune(self.root)
        self.assertEqual(a2arun.orphans(self.root), [])
        self.assertTrue(os.path.exists(os.path.join(self.root, 'out/02/a.py.txt')))


def alive(pid):
    """좀비는 죽은 것으로 친다."""
    try:
        with open('/proc/%d/stat' % pid) as f:
            return f.read().rsplit(')', 1)[1].split()[0] != 'Z'
    except OSError:
        return False


class RealPython(Tree):
    def test_hello(self):
        self.put('ex/py/02/hi.py', 'print("안녕")\n')
        self.assertEqual(self.run_ex('ex/py/02/hi.py'), '$ python 02/hi.py\n안녕\n')

    def test_workshop_is_importable(self):
        self.put('ex/py/workshop/__init__.py', 'NAME = "보물상사"\n')
        self.put('ex/py/02/w.py', 'import workshop\nprint(workshop.NAME)\n')
        self.assertEqual(self.run_ex('ex/py/02/w.py'), '$ python 02/w.py\n보물상사\n')

    def test_args_stdin_env(self):
        self.put('ex/py/02/e.py', 'import os, sys\nprint(sys.argv[1:], sys.stdin.read().strip(), os.environ["K"])\n'
                 '#@ args: a b\n#@ stdin: hi\\n\n#@ env: K=v\n')
        self.assertEqual(self.run_ex('ex/py/02/e.py'),
                         "$ printf 'hi\\n' | K=v python 02/e.py a b\n['a', 'b'] hi v\n")

    def test_expected_exit_code_is_recorded(self):
        self.put('ex/py/02/x.py', 'import sys\nprint("나감")\nsys.exit(3)\n#@ exit: 3\n')
        self.assertEqual(self.run_ex('ex/py/02/x.py'), '$ python 02/x.py\n나감\n[종료 코드 3]\n')

    def test_unexpected_exit_code_fails(self):
        self.put('ex/py/02/x.py', 'raise SystemExit(2)\n')
        with self.assertRaises(a2arun.RunError):
            self.run_ex('ex/py/02/x.py')

    def test_traceback_paths_are_relative(self):
        self.put('ex/py/workshop/__init__.py', 'def boom():\n    raise ValueError("x")\n')
        self.put('ex/py/02/t.py', 'import workshop\nworkshop.boom()\n#@ exit: 1\n')
        cap = self.run_ex('ex/py/02/t.py')
        self.assertIn('File "ex/py/workshop/__init__.py", line 2', cap)
        self.assertNotIn(self.root, cap)

    def test_timeout(self):
        self.put('ex/py/02/spin.py', 'while True:\n    pass\n#@ timeout: 1\n')
        with self.assertRaises(a2arun.RunError):
            self.run_ex('ex/py/02/spin.py')

    def test_norun_compiles_only(self):
        self.put('ex/py/02/s.py', 'print(1)\n#@ norun\n')
        self.assertIsNone(self.run_ex('ex/py/02/s.py'))
        self.put('ex/py/02/bad.py', 'def (:\n#@ norun\n')
        with self.assertRaises(a2arun.RunError):
            self.run_ex('ex/py/02/bad.py')

    def test_ports_in_args_are_range_checked(self):
        self.put('ex/py/02/p.py', 'print(1)\n#@ args: --port 10301\n')
        with self.assertRaises(a2arun.RunError):
            self.run_ex('ex/py/02/p.py')


@unittest.skipUnless(HAVE_NODE, 'node 가 없다')
class RealNode(Tree):
    def test_hello_ts(self):
        self.put('ex/ts/02/hi.ts', 'const n: number = 2;\nconsole.log(`둘=${n}`);\n')
        self.assertEqual(self.run_ex('ex/ts/02/hi.ts'), '$ node 02/hi.ts\n둘=2\n')


@unittest.skipUnless(HAVE_GO, 'go 가 없다')
class RealGo(Tree):
    def test_build_once_then_run(self):
        self.put('ex/go/go.mod', 'module example.com/t\n\ngo 1.27.1\n')
        self.put('ex/go/02/hello/main.go',
                 'package main\n\nimport "fmt"\n\nfunc main() {\n\tfmt.Println("안녕")\n}\n//@ args: x\n')
        self.assertEqual(self.run_ex('ex/go/02/hello'), '$ go run ./02/hello x\n안녕\n')
        binp = os.path.join(self.scratch, 'bin', '02_hello')
        t0 = os.path.getmtime(binp)
        time.sleep(0.05)
        self.assertEqual(self.run_ex('ex/go/02/hello/main.go'), '$ go run ./02/hello x\n안녕\n')
        self.assertEqual(os.path.getmtime(binp), t0)            # 소스가 같으면 다시 짓지 않는다

    def test_sibling_package_change_rebuilds(self):
        # 13/restmount·14/budget 처럼 같은 부 디렉터리의 도우미 패키지를 고치면
        # 낡은 바이너리를 다시 쓰면 안 된다(14부에서 실제로 걸렸다).
        self.put('ex/go/go.mod', 'module example.com/t\n\ngo 1.27.1\n')
        self.put('ex/go/02/helper/h.go', 'package helper\n\nconst Word = "하나"\n')
        self.put('ex/go/02/hello/main.go',
                 'package main\n\nimport (\n\t"fmt"\n\n\t"example.com/t/02/helper"\n)\n\n'
                 'func main() {\n\tfmt.Println(helper.Word)\n}\n')
        self.assertEqual(self.run_ex('ex/go/02/hello'), '$ go run ./02/hello\n하나\n')
        self.put('ex/go/02/helper/h.go', 'package helper\n\nconst Word = "둘"\n')
        self.assertEqual(self.run_ex('ex/go/02/hello'), '$ go run ./02/hello\n둘\n')


SERVER = '''import http.server, os, subprocess, sys
port = int(sys.argv[1])
# 손자 프로세스 — 프로세스 그룹째 내려야 함께 죽는다.
kid = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(300)"])
with open(sys.argv[2], "w") as f:
    f.write("%d %d" % (os.getpid(), kid.pid))
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass
    def do_GET(self):
        body = b'{"name": "card", "id": "3f2c1b7e-0d9a-4c1e-9b7a-1c2d3e4f5a6b"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
print("listening", port)
http.server.HTTPServer(("127.0.0.1", port), H).serve_forever()
#@ norun
'''


@unittest.skipUnless(HAVE_CURL, 'curl 이 없다')
class RealSpec(Tree):
    P = 10250            # 2부 범위(10200–10299) 안

    def setUp(self):
        super().setUp()
        self.pids = os.path.join(self.root, 'pids')
        self.put('ex/py/02/srv.py', SERVER)

    def spec(self, body):
        self.put('ex/run/02/c.run', body)
        return 'ex/run/02/c.run'

    def assert_all_dead(self):
        with open(self.pids) as f:
            pids = [int(x) for x in f.read().split()]
        deadline = time.time() + 3
        while time.time() < deadline and any(alive(p) for p in pids):
            time.sleep(0.05)
        self.assertEqual([p for p in pids if alive(p)], [])

    def test_server_tap_curl(self):
        rel = self.spec(
            'serve name=card cmd="py:02/srv.py %d %s" ready=tcp:%d\n'
            'tap   name=card-wire listen=%d target=%d\n'
            'run   cmd="sh:curl -s http://127.0.0.1:%d/.well-known/agent-card.json"\n'
            % (self.P + 1, self.pids, self.P + 1, self.P, self.P + 1, self.P))
        cap = self.run_ex(rel)
        self.assertEqual(cap,
                         '[터미널 1] $ python 02/srv.py %d pids\n' % (self.P + 1)
                         + '[터미널 2] $ python tools/wiretap.py %d %d\n' % (self.P, self.P + 1)
                         + '[터미널 3] $ curl -s http://127.0.0.1:%d/.well-known/agent-card.json\n' % self.P
                         + '{"name": "card", "id": "<id1>"}\n'
                         '── 터미널 1 (card) 출력 ──\n'
                         'listening %d\n' % (self.P + 1)
                         + '── 와이어 (card-wire) ──\n'
                         '→ GET /.well-known/agent-card.json HTTP/1.1\n'
                         '  Accept: */*\n'
                         '← 200 OK\n'
                         '  Content-Type: application/json\n'
                         '  {\n    "name": "card",\n    "id": "<id1>"\n  }\n')
        self.assert_all_dead()

    def test_failure_still_kills_everything(self):
        rel = self.spec('serve name=card cmd="py:02/srv.py %d %s" ready=tcp:%d\n'
                        'run cmd="sh:echo 망함; exit 4"\n' % (self.P + 1, self.pids, self.P + 1))
        with self.assertRaises(a2arun.RunError) as e:
            self.run_ex(rel)
        self.assertIn('망함', str(e.exception))
        self.assert_all_dead()

    def test_expected_client_exit_code(self):
        rel = self.spec('serve name=card cmd="py:02/srv.py %d %s" ready=tcp:%d\n'
                        'run cmd="sh:exit 4" exit=4\n' % (self.P + 1, self.pids, self.P + 1))
        self.assertIn('[터미널 2] $ exit 4\n[종료 코드 4]\n', self.run_ex(rel))
        self.assert_all_dead()

    def test_ready_timeout(self):
        self.put('ex/py/02/mute.py', 'import time\ntime.sleep(60)\n#@ norun\n')
        rel = self.spec('serve name=m cmd="py:02/mute.py" ready=tcp:%d\nrun cmd="sh:true"\n' % (self.P + 9))
        t0 = time.time()
        with self.assertRaises(a2arun.RunError) as e:
            self.run_ex(rel, ready_timeout=2)
        self.assertLess(time.time() - t0, 10)
        self.assertIn('m', str(e.exception))

    def test_default_ready_timeout_survives_swap(self):
        # 스왑이 찬 이 기계에서는 파이썬 SDK 서버가 15초 넘게 걸려 뜨기도 했다(11부 --check).
        self.assertGreaterEqual(a2arun.READY_TIMEOUT, 60)

    def test_busy_port_fails_before_anything_starts(self):
        s = socket.socket()
        self.addCleanup(s.close)
        # 앞 시험이 남긴 TIME_WAIT 때문에 bind 가 실패하지 않게 — 서버들도 이렇게 묶는다.
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', self.P + 1))
        s.listen(1)
        rel = self.spec('serve name=card cmd="py:02/srv.py %d %s" ready=tcp:%d\nrun cmd="sh:true"\n'
                        % (self.P + 1, self.pids, self.P + 1))
        with self.assertRaises(a2arun.RunError) as e:
            self.run_ex(rel)
        self.assertIn(str(self.P + 1), str(e.exception))
        self.assertFalse(os.path.exists(self.pids))             # 서버는 뜨지도 않았다

    def test_stderr_drop_hides_only_stderr_and_says_so(self):
        # SDK 가 stderr 에 주소가 든 traceback 을 흘리는 서버를 위해:
        # 명령 줄에 2>/dev/null 을 붙여 보여 주고, stdout 은 그대로 둔다.
        self.put('ex/py/02/noisy.py', 'import socket, sys, time\n'
                 's = socket.socket()\ns.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n'
                 's.bind(("127.0.0.1", int(sys.argv[1])))\ns.listen(1)\n'
                 'print("보이는 줄", flush=True)\n'
                 'print("0x7f00 같은 소음", file=sys.stderr, flush=True)\n'
                 'time.sleep(60)\n#@ norun\n')
        rel = self.spec('serve name=n cmd="py:02/noisy.py %d" ready=tcp:%d stderr=drop\n'
                        'wait ms=200\nrun cmd="sh:true"\n' % (self.P + 3, self.P + 3))
        cap = self.run_ex(rel)
        self.assertIn('[터미널 1] $ python 02/noisy.py %d 2>/dev/null\n' % (self.P + 3), cap)
        self.assertIn('── 터미널 1 (n) 출력 ──\n보이는 줄', cap)
        self.assertNotIn('소음', cap)

    def test_stderr_takes_only_drop(self):
        with self.assertRaises(a2arun.RunError):
            a2arun.parse_spec('serve name=a cmd="py:x.py" ready=tcp:10201 stderr=keep\n'
                              'run cmd="sh:true"\n')

    def test_restart_kills_the_group_and_starts_the_same_command(self):
        # 손자까지 SIGKILL — 우아한 종료 없이 "넘어진" 서버. 같은 명령을 다시 띄우고
        # 준비를 기다린 뒤 다음 run 으로 간다. 출력은 한 구역에 이어 붙는다.
        self.put('ex/py/02/srv2.py', SERVER.replace('open(sys.argv[2], "w")', 'open(sys.argv[2], "a")')
                 .replace('f.write("%d %d" % (os.getpid(), kid.pid))',
                          'f.write("%d %d\\n" % (os.getpid(), kid.pid))'))
        url = 'http://127.0.0.1:%d/x' % (self.P + 4)
        rel = self.spec('serve name=card cmd="py:02/srv2.py %d %s" ready=tcp:%d\n'
                        'run cmd="sh:curl -s %s"\n'
                        'restart name=card\n'
                        'run cmd="sh:curl -s %s"\n'
                        % (self.P + 4, self.pids, self.P + 4, url, url))
        cap = self.run_ex(rel)
        shown = 'python 02/srv2.py %d pids' % (self.P + 4)
        body = '{"name": "card", "id": "<id1>"}\n'
        self.assertEqual(cap,
                         '[터미널 1] $ %s\n' % shown
                         + '[터미널 2] $ curl -s %s\n' % url + body
                         + '[터미널 1] (SIGKILL 로 죽이고 다시 띄움) $ %s\n' % shown
                         + '[터미널 2] $ curl -s %s\n' % url + body
                         + '── 터미널 1 (card) 출력 ──\n'
                         'listening %d\n' % (self.P + 4)
                         + '(SIGKILL 로 죽이고 다시 띄움)\n'
                         'listening %d\n' % (self.P + 4))
        with open(self.pids) as f:
            pids = [int(x) for x in f.read().split()]
        self.assertEqual(len(pids), 4)                          # 두 번 떴다, 손자와 함께
        self.assert_all_dead()

    def test_each_spec_run_gets_a_fresh_tmpdir(self):
        # 파일 저장소 실험이 앞 실행의 찌꺼기를 보지 않게 — 명세마다 새 TMPDIR.
        # 같은 명세 안에서는(재시작을 넘어) 같은 TMPDIR 이다.
        self.put('ex/py/02/mark.py', 'import os, tempfile\n'
                 'p = os.path.join(tempfile.gettempdir(), "mark")\n'
                 'print("있었다" if os.path.exists(p) else "없었다")\n'
                 'open(p, "w").close()\n#@ norun\n')
        rel = self.spec('serve name=card cmd="py:02/srv.py %d %s" ready=tcp:%d\n'
                        'run cmd="py:02/mark.py"\nrun cmd="py:02/mark.py"\n'
                        % (self.P + 5, self.pids, self.P + 5))
        for _ in range(2):
            cap = self.run_ex(rel)
            self.assertIn('[터미널 2] $ python 02/mark.py\n없었다\n'
                          '[터미널 2] $ python 02/mark.py\n있었다\n', cap)

    def test_server_dying_early_is_an_error(self):
        self.put('ex/py/02/quit.py', 'import socket, sys\ns = socket.socket()\n'
                 's.bind(("127.0.0.1", int(sys.argv[1])))\ns.listen(1)\nprint("곧 끝")\n#@ norun\n')
        rel = self.spec('serve name=q cmd="py:02/quit.py %d" ready=tcp:%d\nwait ms=300\nrun cmd="sh:true"\n'
                        % (self.P + 2, self.P + 2))
        with self.assertRaises(a2arun.RunError):
            self.run_ex(rel, ready_timeout=3)


if __name__ == '__main__':
    unittest.main()


class ReadKeepsCarriageReturns(unittest.TestCase):
    """curl -i 처럼 CR 이 든 캡처는 읽을 때도 CR 을 지켜야 --check 가
    방금 돌린 출력과 글자까지 같다고 볼 수 있다."""

    def test_crlf_survives_write_then_read(self):
        d = tempfile.mkdtemp(prefix='a2arun-cr-')
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, 'out', 'x.txt')
        a2arun._write(p, 'HTTP/1.1 200 OK\r\nA: b\r\n\r\nbody\n')
        self.assertEqual(a2arun._read(p), 'HTTP/1.1 200 OK\r\nA: b\r\n\r\nbody\n')
