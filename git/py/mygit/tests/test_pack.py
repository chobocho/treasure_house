# -*- coding: utf-8 -*-
"""팩의 시험 — SPEC.md §13, 11단계 "packfile — 읽기, 그다음 쓰기".

golden/pack/ 은 진짜 git 이 쓴 팩 둘이다 — ofs(repack 이 쓴, OFS_DELTA)
와 ref(pack-objects 가 쓴, REF_DELTA). .verify 는 git verify-pack -v,
.show-index 는 git show-index 의 출력이다. 가장 강한 시험은 git 의
팩에서 mygit 이 다시 만든 색인이 git 의 .idx 와 바이트까지 같은가다.
"""
import os
import shutil
import tempfile
import unittest

from mygit import cli, objects, pack
from mygit.tests import golden

NAMES = ('ofs', 'ref')


def show_index(name):
    """git show-index → [(자리, 이름, crc 8글자)]."""
    rows = []
    text = golden.read('pack', name + '.show-index').decode()
    for line in text.split('\n'):
        if line:
            off, oid, crc = line.split(' ')
            rows.append((int(off), oid, crc.strip('()')))
    return rows


class TestRead(unittest.TestCase):
    def test_s13_1_every_object_and_its_delta_chain(self):
        for name in NAMES:
            ents = pack.read_pack(golden.read('pack', name + '.pack'))
            want = {}
            for line in golden.read('pack', name + '.verify').decode() \
                    .split('\n'):
                cols = line.split()
                if len(cols) >= 5 and len(cols[0]) == 40:
                    want[cols[0]] = cols
            self.assertEqual(set(e.oid for e in ents), set(want), name)
            for e in ents:
                cols = want[e.oid]
                # 크기 칸은 팩에 적힌 크기 — 델타면 델타의 크기(§13.3)
                size = len(e.delta if e.delta is not None else e.body)
                self.assertEqual((e.type, size, e.offset),
                                 (cols[1], int(cols[2]), int(cols[4])))
                if len(cols) > 5:
                    self.assertEqual((e.depth, e.base),
                                     (int(cols[5]), cols[6]), e.oid)
                self.assertEqual(objects.hash_object(e.type, e.body),
                                 e.oid)
            kinds = set(e.packed_type for e in ents)
            self.assertIn(6 if name == 'ofs' else 7, kinds, name)

    def test_s13_2_idx_matches_show_index(self):
        for name in NAMES:
            idx = pack.read_idx(golden.read('pack', name + '.idx'))
            got = sorted((off, oid, '%08x' % crc)
                         for oid, off, crc in idx['entries'])
            self.assertEqual(got, sorted(show_index(name)), name)

    def test_s13_1_bad_trailer(self):
        data = bytearray(golden.read('pack', 'ofs.pack'))
        data[-1] ^= 1
        golden.assert_git_error(self, pack.read_pack, bytes(data))


class TestWriteIdx(unittest.TestCase):
    def test_s13_2_rebuilt_idx_is_byte_identical_to_git(self):
        for name in NAMES:
            data = golden.read('pack', name + '.pack')
            ents = pack.read_pack(data)
            self.assertEqual(pack.write_idx(ents, data[-20:]),
                             golden.read('pack', name + '.idx'), name)


class TestDelta(unittest.TestCase):
    def test_s13_1_apply_deltas_from_git(self):
        n = 0
        for name in NAMES:
            ents = {e.offset: e for e in
                    pack.read_pack(golden.read('pack', name + '.pack'))}
            by_oid = {e.oid: e for e in ents.values()}
            for e in ents.values():
                if e.base:
                    self.assertEqual(
                        pack.apply_delta(by_oid[e.base].body, e.delta),
                        e.body)
                    n += 1
        self.assertGreater(n, 0)

    def test_s13_3_make_delta_bytes_are_pinned(self):
        # SPEC.md §13.3 의 알고리즘을 손으로 따라가 얻은 바이트:
        # 크기 32 · 34, 복사(0,16), 끼움 "XY", 복사(0,16)
        base = b'0123456789abcdef' * 2
        target = base[:16] + b'XY' + base[16:]
        self.assertEqual(pack.make_delta(base, target),
                         b'\x20\x22\x90\x10\x02XY\x90\x10')

    def test_s13_3_round_trip(self):
        base = golden.make('counter:70000')
        for target in (base, base[:30000] + b'!' + base[30000:],
                       b'', b'x' * 300, base[::-1][:5000] + base):
            d = pack.make_delta(base, target)
            self.assertEqual(pack.apply_delta(base, d), target)

    def test_s13_1_delta_errors(self):
        golden.assert_git_error(self, pack.apply_delta, b'abc',
                                b'\x03\x01\x00')   # 예약 명령 0
        golden.assert_git_error(self, pack.apply_delta, b'abc',
                                b'\x04\x01\x01x')  # 바탕 크기가 틀림


class Repo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = os.path.join(self.tmp, 'w')
        os.makedirs(self.root)
        self.env = dict(os.environ, GIT_CEILING_DIRECTORIES=self.tmp,
                        GIT_AUTHOR_NAME='A', GIT_AUTHOR_EMAIL='a@x',
                        GIT_AUTHOR_DATE='1700000000 +0900',
                        GIT_COMMITTER_NAME='C',
                        GIT_COMMITTER_EMAIL='c@x',
                        GIT_COMMITTER_DATE='1700000000 +0900')
        self.run_ok('init')

    def tearDown(self):
        for r, _d, files in os.walk(self.tmp):
            for f in files:
                os.chmod(os.path.join(r, f), 0o644)
        shutil.rmtree(self.tmp)

    def run_ok(self, *args):
        code, out, err = cli.run(list(args), cwd=self.root,
                                 env=self.env)
        self.assertEqual(code, 0, (args, err))
        return out

    def gitdir(self):
        return os.path.join(self.root, '.git')


class TestVerifyPack(Repo):
    def test_s13_3_output_is_git_verbatim(self):
        for name in NAMES:
            for ext in ('pack', 'idx'):
                with open(os.path.join(self.root, name + '.' + ext),
                          'wb') as f:
                    f.write(golden.read('pack', name + '.' + ext))
            out = self.run_ok('verify-pack', '-v', name + '.idx')
            self.assertEqual(out, golden.read('pack', name + '.verify'),
                             name)


class TestObjectsInPacks(Repo):
    def test_s13_3_unpack_then_read_loose(self):
        with open(os.path.join(self.root, 'ofs.pack'), 'wb') as f:
            f.write(golden.read('pack', 'ofs.pack'))
        self.run_ok('unpack-pack', 'ofs.pack')
        for off, oid, _crc in show_index('ofs'):
            p = objects.object_path(self.gitdir(), oid)
            self.assertTrue(os.path.exists(p), oid)

    def test_s5_2_read_object_finds_packed_objects(self):
        pdir = os.path.join(self.gitdir(), 'objects', 'pack')
        for ext in ('pack', 'idx'):
            with open(os.path.join(pdir, 'pack-x.' + ext), 'wb') as f:
                f.write(golden.read('pack', 'ofs.' + ext))
        for _off, oid, _crc in show_index('ofs'):
            t, body = objects.read_object(self.gitdir(), oid)
            self.assertEqual(objects.hash_object(t, body), oid)
            found = objects.find_object(self.gitdir(), oid[:8])
            self.assertEqual(found, oid)


class TestPackObjects(Repo):
    def make_history(self):
        body = b''.join(b'line %d of a growing file\n' % i
                        for i in range(200))
        for v in range(4):
            with open(os.path.join(self.root, 'grow.txt'), 'wb') as f:
                f.write(body + b'extra %d\n' % v * (v + 1))
            self.run_ok('add', '.')
            self.run_ok('commit', '-m', 'v%d' % v)

    def check(self, delta):
        self.make_history()
        args = ['pack-objects'] + (['--delta'] if delta else []) + \
            ['.git/objects/pack/pack']
        sha = self.run_ok(*args).strip().decode()
        pdir = os.path.join(self.gitdir(), 'objects', 'pack')
        stem = os.path.join(pdir, 'pack-%s' % sha)
        with open(stem + '.pack', 'rb') as f:
            data = f.read()
        self.assertEqual(data[-20:].hex(), sha)
        ents = pack.read_pack(data)
        with open(stem + '.idx', 'rb') as f:
            idx = pack.read_idx(f.read())
        self.assertEqual(sorted(o for o, _f, _c in idx['entries']),
                         sorted(e.oid for e in ents))
        loose = objects.all_loose(self.gitdir())
        self.assertEqual(sorted(e.oid for e in ents), sorted(loose))
        return ents

    def test_s13_3_plain_pack_holds_every_object(self):
        ents = self.check(False)
        self.assertTrue(all(e.packed_type < 5 for e in ents))

    def test_s13_3_delta_pack_uses_ofs_deltas(self):
        ents = self.check(True)
        deltas = [e for e in ents if e.packed_type == 6]
        # 옛 판 셋이 한 판씩 새것을 바탕으로 — 깊이 1·2·3
        self.assertEqual(len(deltas), 3)
        self.assertEqual(sorted(e.depth for e in deltas), [1, 2, 3])


if __name__ == '__main__':
    unittest.main()
