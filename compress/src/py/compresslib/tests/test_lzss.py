# -*- coding: utf-8 -*-
"""lzss 시험 — SPEC §6.

일치를 어떻게 고르는가가 전부다. 같은 길이면 가까운 쪽, 사슬은 32번까지,
거리는 32768 까지. 셋 다 정상적으로 복호되는 파일을 만들면서 바이트만
달라지는 종류의 결정이라, 시험이 없으면 다섯 언어가 갈라진 줄도 모른다.
"""
import unittest

from compresslib import lzss, varint

MIN = lzss.MIN_MATCH


class TestTokens(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(lzss.encode(b''), b'\x00')

    def test_single_literal(self):
        # 길이 1, 플래그 바이트 0x00, 리터럴 'A'
        self.assertEqual(lzss.encode(b'A'), b'\x01\x00A')

    def test_two_literals_share_one_flag_byte(self):
        self.assertEqual(lzss.encode(b'AB'), b'\x02\x00AB')

    def test_first_match(self):
        # 'AAAA' → 리터럴 A, 그 다음 (길이 3, 거리 1)
        # 플래그: 0번 리터럴, 1번 일치 → 0b01000000 = 0x40
        self.assertEqual(lzss.encode(b'AAAA'),
                         b'\x04\x40A\x00\x00\x00')

    def test_run_of_two_is_not_a_match(self):
        # 최소 일치가 3 이라 'AA' 는 리터럴 둘이다
        self.assertEqual(lzss.encode(b'AA'), b'\x02\x00AA')

    def test_max_match_258(self):
        # 300바이트 런 → 리터럴 1 + 일치 258 + 일치 41.
        # 길이 300 은 varint 로 두 바이트라 몸통은 3번째부터다.
        out = lzss.encode(b'A' * 300)
        body = out[len(varint.put(300)):]
        self.assertEqual(body[0], 0b01100000)     # 리터럴·일치·일치
        self.assertEqual(body[2], 258 - MIN)      # 첫 일치는 상한까지
        self.assertEqual(body[5], 41 - MIN)       # 남은 41

    def test_overlapping_match_round_trips(self):
        # 거리 1 짜리 긴 일치는 자기 자신을 덮어 가며 복사한다.
        # memmove 로 옮기면 여기서 깨진다.
        for n in (3, 4, 100, 1000):
            self.assertEqual(lzss.decode(lzss.encode(b'A' * n)),
                             b'A' * n)


class TestWindowBoundary(unittest.TestCase):

    def _mark_file(self, dist):
        mark = bytes((i * 47 + 3) & 0xFF for i in range(64))
        fill = bytes(b'0123456789abcdef'[(i * 7) % 16]
                     for i in range(dist - 64))
        return mark + fill + mark

    def test_distance_32768_is_found(self):
        src = self._mark_file(32768)
        out = lzss.encode(src)
        self.assertIn(b'\xff\x7f', out)          # (거리 - 1) = 32767
        self.assertEqual(lzss.decode(out), src)

    def test_distance_32769_is_not_found(self):
        src = self._mark_file(32769)
        out = lzss.encode(src)
        # 마지막 64바이트가 리터럴로 나가므로 32768 짜리보다 커야 한다
        inside = lzss.encode(self._mark_file(32768))
        self.assertGreater(len(out), len(inside))
        self.assertEqual(lzss.decode(out), src)


class TestRoundTrip(unittest.TestCase):

    def test_various(self):
        cases = [b'', b'A', b'AB', b'ab' * 5000, bytes(range(256)),
                 b'hello world ' * 500,
                 bytes((i * 37 + 11) & 0xFF for i in range(20000)),
                 b'\x00' * 70000]
        for src in cases:
            self.assertEqual(lzss.decode(lzss.encode(src)), src,
                             src[:8])

    def test_shrinks_repetitive_input(self):
        src = b'the quick brown fox ' * 500
        self.assertLess(len(lzss.encode(src)), len(src) // 4)


class TestErrors(unittest.TestCase):

    def test_truncated_raises(self):
        out = lzss.encode(b'hello world' * 20)
        with self.assertRaises(ValueError):
            lzss.decode(out[:10])

    def test_distance_before_start_raises(self):
        # 길이 3, 거리 2 인데 아직 아무것도 안 나왔다
        bad = b'\x03\x80\x00\x01\x00'
        with self.assertRaises(ValueError):
            lzss.decode(bad)

    def test_trailing_garbage_raises(self):
        good = lzss.encode(b'AAAA')
        with self.assertRaises(ValueError):
            lzss.decode(good + b'\x00')


if __name__ == '__main__':
    unittest.main()
