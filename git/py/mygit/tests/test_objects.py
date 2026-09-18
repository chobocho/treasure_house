# -*- coding: utf-8 -*-
"""zlib 겉옷과 느슨한 객체의 시험 — SPEC.md §3 · §4.1 · §4.6, 2단계.

golden/objects/ 는 진짜 git 이 쓴 파일 그대로이고(고정·동적 허프만
블록이 섞여 있다), golden/stored/ 는 C++ 이 쓸 저장 블록 꼴인데 진짜
git 이 읽고 fsck --strict 를 통과한 것이다(golden/stored_ok.txt).
"""
import os
import shutil
import stat
import tempfile
import unittest

from mygit import objects, zlib
from mygit.tests import golden

OBJS = golden.tsv('objects', 'objects.tsv')
HELLO = 'ce013625030ba8dba906f756967f9e9ca394464a'


def split(raw):
    """풀린 객체 바이트 → (형식, 크기, 몸)."""
    head, _, body = raw.partition(b'\0')
    t, n = head.split(b' ')
    return t.decode(), int(n), body


class TestZlib(unittest.TestCase):
    def test_s3_2_inflates_every_git_written_object(self):
        btypes = set()
        for row in OBJS:
            raw = zlib.decompress(golden.read('objects', row['id']))
            t, n, body = split(raw)
            self.assertEqual((t, n), (row['type'], int(row['size'])))
            self.assertEqual(len(body), n)
            btypes.add(row['btype'])
        # 고정(1)과 동적(2) 허프만이 둘 다 있어야 이 시험이 뜻이 있다
        self.assertEqual(btypes, {'1', '2'})

    def test_s3_2_inflates_stored_blocks(self):
        for name in os.listdir(golden.path('stored')):
            raw = zlib.decompress(golden.read('stored', name))
            t, n, body = split(raw)
            self.assertEqual(len(body), n, name)

    def test_s3_1_round_trip(self):
        for data in (b'', b'x', golden.make('counter:70000')):
            self.assertEqual(zlib.decompress(zlib.compress(data)), data)

    def test_s3_2_prefix_reports_consumed_bytes(self):
        # 팩 안에서는 스트림이 끝나는 곳을 알아야 다음 항목을 읽는다
        a = zlib.compress(b'first stream')
        b = zlib.compress(b'second')
        data = b'JUNK' + a + b
        out, used = zlib.decompress_prefix(data, 4)
        self.assertEqual((out, used), (b'first stream', len(a)))
        out, used = zlib.decompress_prefix(data, 4 + used)
        self.assertEqual((out, used), (b'second', len(b)))

    def test_s3_2_bad_adler_is_an_error(self):
        raw = bytearray(golden.read('objects', HELLO))
        raw[-1] ^= 0xff
        golden.assert_git_error(self, zlib.decompress, bytes(raw))

    def test_s3_adler32(self):
        self.assertEqual(zlib.adler32(b'Wikipedia'), 0x11e60398)
        self.assertEqual(zlib.adler32(b''), 1)


class Repo(unittest.TestCase):
    """임시 .git 을 만들고 golden 객체를 넣어 둔다."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gitdir = os.path.join(self.tmp, '.git')
        os.makedirs(os.path.join(self.gitdir, 'objects', 'pack'))

    def tearDown(self):
        for root, dirs, files in os.walk(self.tmp):
            for f in files:
                os.chmod(os.path.join(root, f), 0o644)
        shutil.rmtree(self.tmp)

    def plant(self, oid):
        d = os.path.join(self.gitdir, 'objects', oid[:2])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, oid[2:]), 'wb') as f:
            f.write(golden.read('objects', oid))


class TestHash(unittest.TestCase):
    def test_s4_1_known_names(self):
        self.assertEqual(objects.hash_object('blob', b'hello\n'), HELLO)
        self.assertEqual(objects.hash_object('blob', b''),
                         'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391')
        self.assertEqual(objects.hash_object('tree', b''),
                         '4b825dc642cb6eb9a060e54bf8d69288fbee4904')

    def test_s4_1_every_golden_object_hashes_to_its_name(self):
        for row in OBJS:
            raw = zlib.decompress(golden.read('objects', row['id']))
            t, _n, body = split(raw)
            self.assertEqual(objects.hash_object(t, body), row['id'])


def honours_readonly(where):
    """이 파일 시스템이 0444 를 지키는가.

    이 덱을 만든 기계(안드로이드 위 proot)의 저장소 디렉터리는 쓰기
    비트를 지우지 못한다 — 진짜 git 이 쓴 객체도 여기서는 0644 로
    보인다(2026-09-18 확인). 권한을 못 지키는 곳에서 0444 를 단언하면
    구현이 아니라 기계를 시험하게 된다.
    """
    probe = os.path.join(where, 'probe')
    with open(probe, 'wb'):
        pass
    os.chmod(probe, 0o444)
    os.rename(probe, probe + '2')
    ok = stat.S_IMODE(os.stat(probe + '2').st_mode) == 0o444
    os.chmod(probe + '2', 0o644)
    os.remove(probe + '2')
    return ok


class TestWrite(Repo):
    def test_s4_6_path_and_content(self):
        oid = objects.write_object(self.gitdir, 'blob', b'hello\n')
        self.assertEqual(oid, HELLO)
        p = os.path.join(self.gitdir, 'objects', 'ce', HELLO[2:])
        raw = zlib.decompress(open(p, 'rb').read())
        self.assertEqual(raw, b'blob 6\0hello\n')

    def test_s4_6_readonly(self):
        if not honours_readonly(self.tmp):
            self.skipTest('이 파일 시스템은 0444 를 지키지 않는다')
        objects.write_object(self.gitdir, 'blob', b'hello\n')
        p = os.path.join(self.gitdir, 'objects', 'ce', HELLO[2:])
        self.assertEqual(stat.S_IMODE(os.stat(p).st_mode), 0o444)

    def test_s4_6_second_write_is_a_no_op(self):
        objects.write_object(self.gitdir, 'blob', b'hello\n')
        # 파일이 0444 여도 두 번째 쓰기가 실패하면 안 된다
        objects.write_object(self.gitdir, 'blob', b'hello\n')
        d = os.path.join(self.gitdir, 'objects', 'ce')
        self.assertEqual(os.listdir(d), [HELLO[2:]])

    def test_s4_6_no_temp_files_left(self):
        objects.write_object(self.gitdir, 'blob', b'x' * 1000)
        for root, _d, files in os.walk(self.gitdir):
            for f in files:
                self.assertEqual(len(os.path.basename(root) + f), 40,
                                 f)


class TestRead(Repo):
    def test_s4_6_reads_what_git_wrote(self):
        for row in OBJS:
            self.plant(row['id'])
            t, body = objects.read_object(self.gitdir, row['id'])
            self.assertEqual((t, len(body)),
                             (row['type'], int(row['size'])))

    def test_s4_6_reads_what_it_wrote(self):
        oid = objects.write_object(self.gitdir, 'commit', b'x\n')
        self.assertEqual(objects.read_object(self.gitdir, oid),
                         ('commit', b'x\n'))

    def test_s4_6_missing_object(self):
        golden.assert_git_error(self, objects.read_object, self.gitdir,
                                HELLO)

    def test_s4_6_size_mismatch_is_an_error(self):
        d = os.path.join(self.gitdir, 'objects', 'ce')
        os.makedirs(d)
        with open(os.path.join(d, HELLO[2:]), 'wb') as f:
            f.write(zlib.compress(b'blob 7\0hello\n'))
        golden.assert_git_error(self, objects.read_object, self.gitdir,
                                HELLO)


class TestFind(Repo):
    def test_s4_6_prefix(self):
        for row in OBJS:
            self.plant(row['id'])
        ids = [r['id'] for r in OBJS]
        for oid in ids:
            self.assertEqual(objects.find_object(self.gitdir, oid[:7]),
                             oid)
            self.assertEqual(objects.find_object(self.gitdir, oid), oid)
        self.assertIsNone(objects.find_object(self.gitdir, 'ffffff'))

    def test_s4_6_ambiguous_prefix(self):
        # 앞 네 글자가 같아질 때까지 blob 을 만들어 본다 — 65,536 칸에
        # 생일 문제라 수백 번이면 짝이 나온다
        seen = {}
        k = 0
        while True:
            body = b'%d\n' % k
            oid = objects.hash_object('blob', body)
            if oid[:4] in seen:
                break
            seen[oid[:4]] = body
            k += 1
        objects.write_object(self.gitdir, 'blob', seen[oid[:4]])
        objects.write_object(self.gitdir, 'blob', b'%d\n' % k)
        golden.assert_git_error(self, objects.find_object, self.gitdir,
                                oid[:4])

    def test_s4_6_short_prefix_is_refused(self):
        self.plant(HELLO)
        self.assertIsNone(objects.find_object(self.gitdir, 'ce0'))


if __name__ == '__main__':
    unittest.main()
