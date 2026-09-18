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
            'uid=10123(u0_a123)\n{"ssid": "Home"}\n')
        imp = run_all.Import('native_device', self.src)
        e = run_all.record(imp, self.d, '2026-09-20', None)
        self.assertEqual(e, {'kind': 'snapshot', 'side': 'native',
                             'date': '2026-09-19',
                             'cmds': ['tools/native_facts.sh']})
        text = io.open(os.path.join(self.d, 'native_device.txt')).read()
        self.assertTrue(text.startswith('# snapshot 2026-09-19\n'))
        self.assertIn('"<ssid>"', text)
        self.assertNotIn('native_facts 2026', text)

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

    def test_generated_tables_are_not_captures(self):
        self.put('tbl_x.html', '<table></table>\n')
        self.man({})
        self.assertEqual(run_all.check(self.d), [])

    def test_no_manifest_with_captures(self):
        self.put('a.txt', 'x\n')
        self.assertTrue(run_all.check(self.d))


if __name__ == '__main__':
    unittest.main()
