# -*- coding: utf-8 -*-
"""run_all.py 시험 — 캡처를 뜨고, 적고, 매니페스트를 맞추는 일.

진짜 명령은 돌리지 않는다. runner 를 가짜로 바꿔 끼워 "tmx.sh 가
이렇게 답했다면 out/ 에 무엇이 남나" 만 본다. 진짜로 도는지는
make run 과 make record 가 본다.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, BASE)
import run_all                                     # noqa: E402

TR = '## tmx: side=%s cwd=/x exit=%d'


def fake(outputs):
    """명령 → (출력, 종료 코드) 표로 답하는 가짜 runner."""
    def runner(side, cmd, cwd, timeout, install):
        out, rc = outputs[cmd]
        return out + (TR % (side, rc)) + '\n', rc
    return runner


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def cap(self, kind='stable', side='termux', steps=None):
        return run_all.Capture('t1', side, kind, steps or [
            run_all.Step('인사', 'echo hi'),
            run_all.Step('실패', 'false')])

    def test_sections_prompt_and_trailer(self):
        run = fake({'echo hi': ('hi\n', 0), 'false': ('', 1)})
        run_all.record(self.cap(), self.d, '2026-09-18', run)
        text = io.open(os.path.join(self.d, 't1.txt')).read()
        self.assertEqual(text, '== 1. 인사 ==\n$ echo hi\nhi\n'
                         + TR % ('termux', 0) + '\n\n'
                         '== 2. 실패 ==\n$ false\n'
                         + TR % ('termux', 1) + '\n')

    def test_proot_prompt_is_hash(self):
        run = fake({'echo hi': ('hi\n', 0), 'false': ('', 1)})
        run_all.record(self.cap(side='proot'), self.d, '2026-09-18',
                       run)
        text = io.open(os.path.join(self.d, 't1.txt')).read()
        self.assertIn('\n# echo hi\n', '\n' + text)

    def test_snapshot_header_and_manifest(self):
        run = fake({'echo hi': ('hi\n', 0), 'false': ('', 1)})
        e = run_all.record(self.cap('snapshot'), self.d, '2026-09-18',
                           run)
        text = io.open(os.path.join(self.d, 't1.txt')).read()
        self.assertTrue(text.startswith('# snapshot 2026-09-18\n'))
        self.assertEqual(e['kind'], 'snapshot')
        self.assertEqual(e['side'], 'termux')
        self.assertEqual(e['date'], '2026-09-18')
        self.assertEqual(e['cmds'], ['echo hi', 'false'])

    def test_snapshot_is_never_rerecorded_silently(self):
        run = fake({'echo hi': ('hi\n', 0), 'false': ('', 1)})
        run_all.record(self.cap('snapshot'), self.d, '2026-09-18', run)
        run2 = fake({'echo hi': ('CHANGED\n', 0), 'false': ('', 1)})
        e = run_all.record(self.cap('snapshot'), self.d, '2026-09-20',
                           run2)
        text = io.open(os.path.join(self.d, 't1.txt')).read()
        self.assertNotIn('CHANGED', text)
        self.assertEqual(e['date'], '2026-09-18')

    def test_forced_resnap(self):
        run = fake({'echo hi': ('hi\n', 0), 'false': ('', 1)})
        run_all.record(self.cap('snapshot'), self.d, '2026-09-18', run)
        run2 = fake({'echo hi': ('NEW\n', 0), 'false': ('', 1)})
        e = run_all.record(self.cap('snapshot'), self.d, '2026-09-20',
                           run2, force=True)
        self.assertEqual(e['date'], '2026-09-20')

    def test_output_is_scrubbed(self):
        run = fake({'echo hi': ('{"ssid": "HomeNet"}\n', 0),
                    'false': ('', 1)})
        run_all.record(self.cap(), self.d, '2026-09-18', run)
        text = io.open(os.path.join(self.d, 't1.txt')).read()
        self.assertIn('"<ssid>"', text)
        self.assertNotIn('HomeNet', text)

    def test_app_id_is_faked(self):
        # 앱 번호·미러는 고정 캡처에서도 가짜로(tools/anon.py)
        run = fake({'echo hi': ('20456(u0_a456_cache)\n', 0),
                    'false': ('', 1)})
        run_all.record(self.cap(), self.d, '2026-09-18', run)
        text = io.open(os.path.join(self.d, 't1.txt')).read()
        self.assertNotIn('456', text)

    def test_missing_final_newline_is_added(self):
        run = fake({'echo hi': ('no-newline', 0), 'false': ('', 1)})
        run_all.record(self.cap(), self.d, '2026-09-18', run)
        text = io.open(os.path.join(self.d, 't1.txt')).read()
        self.assertIn('no-newline\n## tmx:', text)

    def test_stable_entry_has_no_date(self):
        # 날짜가 들어가면 같은 내용을 다른 날 떴을 때
        # 매니페스트가 바뀐다
        run = fake({'echo hi': ('hi\n', 0), 'false': ('', 1)})
        e = run_all.record(self.cap(), self.d, '2026-09-18', run)
        self.assertNotIn('date', e)


class ImportTest(unittest.TestCase):
    """사용자가 네이티브에서 뜬 파일을 캡처로 들여오기."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.src = os.path.join(self.d, 'device.txt')

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_import_as_native_snapshot(self):
        io.open(self.src, 'w').write(
            '# native_facts 2026-09-19\n\n== 1. id ==\n'
            'uid=10456(u0_a456)\n{"ssid": "Home"}\n')
        imp = run_all.Import('native_device', self.src)
        e = run_all.record(imp, self.d, '2026-09-20', None)
        self.assertEqual(e, {'kind': 'snapshot', 'side': 'native',
                             'date': '2026-09-19',
                             'cmds': ['tools/native_facts.sh']})
        text = io.open(os.path.join(self.d, 'native_device.txt')).read()
        self.assertTrue(text.startswith('# snapshot 2026-09-19\n'))
        self.assertIn('"<ssid>"', text)
        self.assertNotIn('native_facts 2026', text)

    def test_long_lines_are_folded(self):
        # 네이티브 줄(id·uname·셔뱅 오류)은 108칸을 넘는다. 사람이 뜬
        # 파일이라 명령에 cut 을 걸 수 없으니 들여올 때 접는다
        m = run_all.MAX_COLS
        exact, long_, wide = 'a' * m, 'b' * (2 * m + 5), '가' * m
        io.open(self.src, 'w', encoding='utf-8').write(
            '# native_facts 2026-09-19\n%s\n%s\n%s\n'
            % (exact, long_, wide))
        imp = run_all.Import('native_device', self.src)
        run_all.record(imp, self.d, '2026-09-20', None)
        lines = io.open(os.path.join(self.d, 'native_device.txt'),
                        encoding='utf-8').read().split('\n')[1:-1]
        self.assertEqual(lines[0], exact)            # 딱 108칸은 그대로
        for ln in lines:
            self.assertLessEqual(run_all.cells(ln), m)
        rest = lines[1:]
        # 원래 줄의 첫 조각만 표시 없이, 이어지는 조각은 '↪ ' 로 시작
        self.assertEqual([ln.startswith('↪ ') for ln in rest],
                         [False, True, True, False, True, True])
        joined = ''.join(ln[2:] if ln.startswith('↪ ') else ln
                         for ln in rest)
        # 글자를 잃지 않는다
        self.assertEqual(joined, long_ + wide)

    def test_device_ids_are_faked(self):
        # 기기 식별값은 들여올 때 tools/anon.py 가 가짜로 바꾼다
        io.open(self.src, 'w', encoding='utf-8').write(
            '# native_facts 2026-09-19\nDevice model:\nSM-G999N\n')
        imp = run_all.Import('native_device', self.src)
        run_all.record(imp, self.d, '2026-09-20', None)
        text = io.open(os.path.join(self.d, 'native_device.txt'),
                       encoding='utf-8').read()
        self.assertNotIn('SM-G999N', text)
        self.assertIn('Device model:', text)

    def test_fold_prefers_space(self):
        # uname 의 날짜처럼 낱말 가운데서 끊기면 읽는 사람이 속는다
        m = run_all.MAX_COLS
        # '2026' 이 108칸 경계에 걸친다
        line = 'x' * (m - 3) + ' 2026 aarch64'
        self.assertEqual(run_all.fold(line),
                         ['x' * (m - 3), '\u21aa 2026 aarch64'])

    def test_missing_source_is_skipped(self):
        imp = run_all.Import('native_device', self.src)
        self.assertIsNone(run_all.record(imp, self.d, '2026-09-20',
                                         None))

    def test_header_without_date_is_error(self):
        io.open(self.src, 'w').write('no header\n')
        imp = run_all.Import('native_device', self.src)
        with self.assertRaises(ValueError):
            run_all.record(imp, self.d, '2026-09-20', None)


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.d)

    def put(self, name, text):
        io.open(os.path.join(self.d, name), 'w', encoding='utf-8',
                newline='\n').write(text)

    def man(self, m):
        self.put('manifest.json', json.dumps(m))

    def test_clean(self):
        self.put('a.txt', 'x\n')
        self.man({'a.txt': {'kind': 'stable', 'side': 'termux'}})
        self.assertEqual(run_all.check(self.d), [])

    def test_orphan_capture(self):
        self.put('a.txt', 'x\n')
        self.man({})
        self.assertIn('manifest', run_all.check(self.d)[0])

    def test_manifest_points_to_missing_file(self):
        self.man({'b.txt': {'kind': 'stable', 'side': 'termux'}})
        self.assertIn('b.txt', run_all.check(self.d)[0])

    def test_wide_line(self):
        self.put('a.txt', 'x' * 109 + '\n')
        self.man({'a.txt': {'kind': 'stable', 'side': 'termux'}})
        self.assertIn('109', run_all.check(self.d)[0])

    def test_korean_counts_double(self):
        self.put('a.txt', '가' * 55 + '\n')
        self.man({'a.txt': {'kind': 'stable', 'side': 'termux'}})
        self.assertEqual(len(run_all.check(self.d)), 1)

    def test_snapshot_without_header(self):
        self.put('a.txt', 'x\n')
        self.man({'a.txt': {'kind': 'snapshot', 'side': 'termux',
                            'date': '2026-09-18'}})
        self.assertIn('snapshot', run_all.check(self.d)[0])

    def test_control_character(self):
        # /proc/self/attr/current 는 끝에 NUL 을 준다(실제로 샜다)
        self.put('a.txt', 'u:r:x\x00\n')
        self.man({'a.txt': {'kind': 'stable', 'side': 'termux'}})
        self.assertIn('제어 문자', run_all.check(self.d)[0])

    def test_privacy_hit(self):
        self.put('a.txt', 'call 010-1234-5678\n')
        self.man({'a.txt': {'kind': 'stable', 'side': 'termux'}})
        self.assertIn('phone', run_all.check(self.d)[0])

    def test_tool_failure_in_capture(self):
        # 소스 캡처의 도구가 실패한 채 실리면 안 된다 — 14부 리뷰에서
        # srcpin 의 glob 이 파일 넷에 맞아 오류 문구가 덱에 실렸다
        self.put('a.txt', '$ python3 deck/srcpin.py grep x y\n'
                 'termux-app:*/x.xml 에 맞는 파일이 4개\n')
        self.put('b.txt', 'Traceback (most recent call last):\n')
        self.man({'a.txt': {'kind': 'stable', 'side': 'termux'},
                  'b.txt': {'kind': 'stable', 'side': 'termux'}})
        bad = run_all.check(self.d)
        self.assertEqual(len(bad), 2)
        self.assertIn('a.txt:2', bad[0])
        self.assertIn('b.txt:1', bad[1])

    def test_app_id_split_by_fold(self):
        # 이미 접힌 파일에 가명 처리를 돌리면 줄 경계에서 쪼개진
        # 이름(all_a78 / ↪ 9)이 규칙에 안 걸린다 — 실제로 샜다
        self.put('a.txt', 'uid=10123(u0_a123) 50123(all_a78\n'
                 '↪ 9) context=u:r:x\n')
        self.put('b.txt', 'uid=10123(u0_a123) 50123(all_a123)\n')
        self.man({'a.txt': {'kind': 'stable', 'side': 'termux'},
                  'b.txt': {'kind': 'stable', 'side': 'termux'}})
        bad = run_all.check(self.d)
        self.assertEqual(len(bad), 1)
        self.assertIn('a.txt', bad[0])
        self.assertIn('가명', bad[0])
        self.assertNotIn('789', bad[0])       # 진짜 값은 찍지 않는다

    def test_unfaked_mirror_in_capture(self):
        self.put('a.txt', 'deb https://mirror.real.edu/termux/apt/'
                 'termux-main stable main\n')
        self.man({'a.txt': {'kind': 'stable', 'side': 'termux'}})
        bad = run_all.check(self.d)
        self.assertEqual(len(bad), 1)
        self.assertIn('가명', bad[0])

    def test_generated_tables_are_not_captures(self):
        self.put('tbl_x.html', '<table></table>\n')
        self.man({})
        self.assertEqual(run_all.check(self.d), [])

    def test_no_manifest_with_captures(self):
        self.put('a.txt', 'x\n')
        self.assertTrue(run_all.check(self.d))


if __name__ == '__main__':
    unittest.main()
