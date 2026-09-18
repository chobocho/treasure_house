# -*- coding: utf-8 -*-
"""전송의 시험 — SPEC.md §14, 12단계 "pkt-line 으로 진짜 git 과 대화".

fetch-pack 은 진짜 git upload-pack 을 자식으로 띄워 말한다(PLAN.md
§9 결정 8 — 서버는 git 이다). golden/pkt/<경우>.log 는 SPEC §14.3 의
요청을 그대로 보냈을 때 git 이 돌려준 대화의 기록이고, mygit 의 기록은
글자까지 같아야 한다. 받은 팩 바이트와 표준 출력도 같아야 한다.
멍청한 clone 은 golden/scen/clone.scn 이 장면 시험으로 본다.
"""
import os
import shutil
import tempfile
import unittest

from mygit import cli, objects, refs, transport
from mygit.tests import golden

CASES = ('full', 'two-refs', 'have-first')


class TestPktLine(unittest.TestCase):
    def test_s14_1_length_counts_itself(self):
        self.assertEqual(transport.pkt_line(b'a\n'), b'0006a\n')
        self.assertEqual(transport.pkt_line(b''), b'0004')
        self.assertEqual(transport.pkt_line(b'x' * 65516)[:4], b'fff0')

    def test_s14_3_render_like_the_golden_log(self):
        self.assertEqual(transport.render(b'command=ls-refs\n'),
                         '0014command=ls-refs\\n')


class TestFetchPack(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.src = os.path.join(self.tmp, 'src')
        shutil.copytree(golden.path('pkt', 'src', 'git'),
                        os.path.join(self.src, '.git'))
        for d in ('objects/pack', 'refs/tags'):
            os.makedirs(os.path.join(self.src, '.git', d),
                        exist_ok=True)
        self.root = os.path.join(self.tmp, 'local')
        os.makedirs(self.root)
        self.env = dict(os.environ, GIT_CEILING_DIRECTORIES=self.tmp)
        cli.run(['init'], cwd=self.root, env=self.env)
        self.gitdir = os.path.join(self.root, '.git')

    def tearDown(self):
        for r, _d, files in os.walk(self.tmp):
            for f in files:
                os.chmod(os.path.join(r, f), 0o644)
        shutil.rmtree(self.tmp)

    def fetch(self, case):
        wants, haves = golden.read('pkt', case + '.args').decode() \
            .split('\n')[:2]
        if haves:
            # 가진 값 = 로컬 참조. 원본의 객체를 넣고 참조를 세운다
            shutil.rmtree(os.path.join(self.gitdir, 'objects'))
            shutil.copytree(os.path.join(self.src, '.git', 'objects'),
                            os.path.join(self.gitdir, 'objects'))
            refs.update_ref(self.gitdir, 'refs/heads/old', haves, None,
                            'test', 'T <t@t> 0 +0000')
        log = os.path.join(self.tmp, case + '.log')
        env = dict(self.env, MYGIT_PKT_LOG=log)
        code, out, err = cli.run(['fetch-pack', self.src] +
                                 wants.split(), cwd=self.root, env=env)
        with open(log) as f:
            return code, out, err, f.read()

    def test_s14_3_conversation_matches_git(self):
        for case in CASES:
            code, out, err, log = self.fetch(case)
            self.assertEqual((code, err), (0, b''), case)
            self.assertEqual(out, golden.read('pkt', case + '.stdout'),
                             case)
            self.assertEqual(log, golden.read('pkt', case + '.log')
                             .decode(), case)
            self.tearDown()
            self.setUp()

    def test_s14_3_received_pack_is_stored_and_readable(self):
        self.fetch('full')
        want = golden.read('pkt', 'full.pack')
        name = 'pack-%s.pack' % want[-20:].hex()
        with open(os.path.join(self.gitdir, 'objects', 'pack', name),
                  'rb') as f:
            self.assertEqual(f.read(), want)
        head = golden.read('pkt', 'full.stdout').split()[0].decode()
        t, _ = objects.read_object(self.gitdir, head)
        self.assertEqual(t, 'commit')


if __name__ == '__main__':
    unittest.main()
