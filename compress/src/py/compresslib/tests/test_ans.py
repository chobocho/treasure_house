# -*- coding: utf-8 -*-
"""ans 시험 — SPEC §13.

rANS 는 스택이다. 부호기가 뒤에서부터 밀어 넣고 복호기가 앞에서부터
꺼낸다. 그래서 "왕복이 된다" 만 보면 부호기와 복호기가 같은 방향으로
틀려 있어도 통과한다 — 빈도 정규화의 나머지 배분 같은 자리가 특히 그렇다.
그래서 정규화와 표 만들기를 따로 떼어 눈으로 볼 수 있는 값으로 시험한다.
"""
import unittest

from compresslib import ans


class TestNormalise(unittest.TestCase):

    def test_sums_to_total(self):
        for counts in ([1] + [0] * 255,
                       [5, 2, 1] + [0] * 253,
                       [1] * 256,
                       [1000000, 1] + [0] * 254):
            f = ans.normalise(counts)
            self.assertEqual(sum(f), ans.TOTAL, counts[:4])

    def test_used_symbols_never_zero(self):
        counts = [0] * 256
        counts[0] = 10 ** 9
        for s in range(1, 256):
            counts[s] = 1
        f = ans.normalise(counts)
        self.assertTrue(all(f[s] >= 1 for s in range(256)))

    def test_single_symbol_takes_everything(self):
        counts = [0] * 256
        counts[7] = 42
        f = ans.normalise(counts)
        self.assertEqual(f[7], ans.TOTAL)
        self.assertEqual(sum(f), ans.TOTAL)

    def test_surplus_goes_to_the_largest(self):
        # 5:2:1 → 2560:1024:512 이 되고 남는 것은 없다.
        # 3:1 은 3072:1024 로 딱 맞는다. 나머지가 생기는 쪽을 본다.
        counts = [0] * 256
        counts[0], counts[1], counts[2] = 7, 2, 1
        f = ans.normalise(counts)
        self.assertEqual(sum(f), ans.TOTAL)
        self.assertEqual(max(range(256), key=lambda s: (f[s], -s)), 0)

    def test_deterministic(self):
        counts = [0] * 256
        for s in range(256):
            counts[s] = (s * 37 + 11) % 100
        self.assertEqual(ans.normalise(counts), ans.normalise(counts))


class TestSlotTable(unittest.TestCase):

    def test_slot_table_covers_every_slot(self):
        counts = [0] * 256
        counts[1], counts[2], counts[3] = 3, 5, 2
        f = ans.normalise(counts)
        cum = ans.cumulative(f)
        slots = ans.slot_symbols(f, cum)
        self.assertEqual(len(slots), ans.TOTAL)
        for s in (1, 2, 3):
            self.assertEqual(slots.count(s), f[s])


class TestTansTable(unittest.TestCase):
    """tANS 는 골든 벡터에 안 들어가지만, 표가 맞는지는 봐야 한다."""

    def test_every_slot_filled_once(self):
        counts = [0] * 256
        for s in range(10):
            counts[s] = s + 1
        f = ans.normalise(counts)
        table = ans.tans_table(f)
        self.assertEqual(len(table), ans.TOTAL)
        for s in range(10):
            self.assertEqual(table.count(s), f[s], s)

    def test_step_is_coprime_with_total(self):
        # 걸음이 홀수라야 2의 거듭제곱 칸을 빠짐없이 돈다 — 상수가
        # 이상해 보이는 이유가 이것 하나다.
        self.assertEqual(ans.SPREAD_STEP % 2, 1)


class TestCodec(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(ans.encode(b''), b'\x00')

    def test_round_trip(self):
        cases = [b'', b'A', b'AB', b'\x00' * 5000, bytes(range(256)),
                 b'hello world ' * 300,
                 bytes((i * 37 + 11) & 0xFF for i in range(20000)),
                 bytes((i * 251 + 97) & 0xFF for i in range(4096))]
        for src in cases:
            self.assertEqual(ans.decode(ans.encode(src)), src, src[:8])

    def test_reaches_entropy_on_skewed_data(self):
        # 0차 엔트로피에 아주 가까워야 한다. 허프만은 기호당 정수 비트라
        # 여기서 크게 진다.
        from compresslib import huffman
        src = b'a' * 9000 + b'b' * 900 + b'c' * 100
        self.assertLess(len(ans.encode(src)), len(huffman.encode(src)))

    def test_grows_on_random(self):
        src = bytes((i * 251 + 97) & 0xFF for i in range(4096))
        self.assertGreater(len(ans.encode(src)), len(src))

    def test_truncated_raises(self):
        out = ans.encode(b'hello world' * 50)
        with self.assertRaises(ValueError):
            ans.decode(out[:len(out) // 2])

    def test_bad_frequency_table_raises(self):
        # 빈도 합이 TOTAL 이 아니면 거절한다. 합이 안 맞는 표로는 칸 배치가
        # 성립하지 않아서, 검사 없이 풀면 엉뚱한 기호가 줄줄이 나온다.
        from compresslib import varint
        head = bytearray(varint.put(1))
        head += b'\x00' * 256          # 빈도가 전부 0
        with self.assertRaises(ValueError):
            ans.decode(bytes(head) + b'\x00' * 4)

    def test_frequency_over_total_raises(self):
        from compresslib import varint
        head = bytearray(varint.put(1))
        head += varint.put(ans.TOTAL + 1)
        head += b'\x00' * 255
        with self.assertRaises(ValueError):
            ans.decode(bytes(head) + b'\x00' * 4)


if __name__ == '__main__':
    unittest.main()
