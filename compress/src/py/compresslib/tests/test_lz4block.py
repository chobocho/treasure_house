# -*- coding: utf-8 -*-
"""lz4block 시험 — SPEC §14.

이 모듈의 진짜 시험은 진짜 lz4 와 주고받는 것이다(interop/).
여기서는 그 검사가 못 보는 것 — 꼬리 규칙과 LSIC 의 경계 — 을 본다.
"""
import unittest

from compresslib import lz4block as lz4


class TestLsic(unittest.TestCase):

    TABLE = [(0, [0]), (1, [1]), (254, [254]), (255, [255, 0]),
             (256, [255, 1]), (509, [255, 254]), (510, [255, 255, 0])]

    def test_table(self):
        for v, want in self.TABLE:
            self.assertEqual(list(lz4.put_lsic(v)), want, v)

    def test_round_trip(self):
        for v, _ in self.TABLE:
            raw = lz4.put_lsic(v)
            self.assertEqual(lz4.get_lsic(raw, 0), (v, len(raw)), v)

    def test_runaway_raises(self):
        # 이어짐만 있고 끝나지 않으면 입력이 바닥날 때 멈춘다
        with self.assertRaises(ValueError):
            lz4.get_lsic(b'\xff' * 2000, 0)

    def test_long_value_is_not_capped(self):
        # 256 KiB 짜리 일치는 이어짐 1028바이트가 필요하다. 고정 상한을
        # 두면 정당한 입력이 거절된다 (mixed_1m.bin 에서 겪었다).
        raw = lz4.put_lsic(262144)
        self.assertGreater(len(raw), 1000)
        self.assertEqual(lz4.get_lsic(raw, 0), (262144, len(raw)))


class TestBlock(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(lz4.encode(b''), b'\x00')

    def test_short_input_is_all_literals(self):
        # 12바이트 이하는 일치를 만들 수 없다 — 토큰 하나와 리터럴뿐
        src = b'hello'
        out = lz4.encode(src)
        self.assertEqual(out, b'\x05' + bytes([5 << 4]) + src)

    def test_tail_rules(self):
        # 마지막 5바이트는 반드시 리터럴이고, 일치는 끝에서 12바이트
        # 안쪽에서 시작할 수 없다. 꼬리는 늘 리터럴이 된다.
        src = b'abcd' * 100
        block = lz4.encode(src)[len(lz4.varint.put(len(src))):]
        seqs = lz4.parse_sequences(block)
        last_lit = seqs[-1]
        self.assertIsNone(last_lit[1])     # 마지막에 일치 없음
        self.assertGreaterEqual(len(last_lit[0]), 5)

    def test_round_trip(self):
        cases = [b'', b'A', b'hello', b'a' * 13, b'a' * 100,
                 b'abcd' * 500, bytes(range(256)),
                 b'the quick brown fox ' * 300,
                 bytes((i * 37 + 11) & 0xFF for i in range(20000)),
                 bytes((i * 251 + 97) & 0xFF for i in range(4096))]
        for src in cases:
            self.assertEqual(lz4.decode(lz4.encode(src)), src, src[:8])

    def test_shrinks_repetitive(self):
        src = b'the quick brown fox ' * 500
        self.assertLess(len(lz4.encode(src)), len(src) // 4)

    def test_loses_to_deflate(self):
        # 엔트로피 부호가 없으니 당연히 진다. 그게 이 형식의 거래다.
        from compresslib import deflate
        src = b'the quick brown fox jumps over the lazy dog ' * 200
        self.assertGreater(len(lz4.encode(src)),
                           len(deflate.encode(src)))


class TestErrors(unittest.TestCase):

    def test_offset_zero_raises(self):
        # 리터럴 0개 + 일치 길이 4 + 거리 0
        bad = b'\x08' + bytes([0x00, 0x00, 0x00])
        with self.assertRaises(ValueError):
            lz4.decode(bad)

    def test_offset_too_far_raises(self):
        bad = b'\x08' + bytes([0x00, 0x10, 0x00])
        with self.assertRaises(ValueError):
            lz4.decode(bad)

    def test_truncated_raises(self):
        out = lz4.encode(b'the quick brown fox ' * 50)
        with self.assertRaises(ValueError):
            lz4.decode(out[:10])

    def test_length_mismatch_raises(self):
        out = bytearray(lz4.encode(b'hello world'))
        out[0] = 3
        with self.assertRaises(ValueError):
            lz4.decode(bytes(out))


class TestFrame(unittest.TestCase):
    """프레임은 읽기만 한다. 진짜 lz4 명령이 쓰는 것이 이 모양이다."""

    def test_bad_magic_raises(self):
        with self.assertRaises(ValueError):
            lz4.frame_decode(b'\x00\x00\x00\x00' + b'\x00' * 20)

    def test_uncompressed_block_flag(self):
        # 압축 안 된 블록(최상위 비트 1)도 읽어야 한다
        body = b'hello world!'
        frame = (b'\x04\x22\x4d\x18' + bytes([0x60, 0x40, 0x00])
                 + (len(body) | 0x80000000).to_bytes(4, 'little') + body
                 + b'\x00\x00\x00\x00')
        self.assertEqual(lz4.frame_decode(frame), body)


if __name__ == '__main__':
    unittest.main()
