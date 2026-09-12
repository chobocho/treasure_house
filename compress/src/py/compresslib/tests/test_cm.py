# -*- coding: utf-8 -*-
"""cm 시험 — SPEC §18.

문맥 혼합에서 깨진 곳은 **왕복으로 안 잡힌다.** 부호기와 복호기가 같은
모델을 쓰므로 모델이 틀려도 둘이 사이좋게 틀리고 왕복은 완벽하다.
드러나는 것은 **크기** 뿐이다. 그래서 여기서는 왕복만이 아니라 비율의
하한을 시험한다 — APM 의 곱수를 23 으로 두었을 때 실제로 그렇게 잡혔다.
"""
import unittest

from compresslib import cm


class TestSquashStretch(unittest.TestCase):

    def test_squash_is_monotone(self):
        prev = -1
        for x in range(-2047, 2048):
            v = cm.squash(x)
            self.assertGreaterEqual(v, prev)
            prev = v

    def test_squash_endpoints(self):
        self.assertEqual(cm.squash(-3000), 0)
        self.assertEqual(cm.squash(3000), 4095)
        # 표의 가운데 값이 2047 이라 squash(0) 도 2047 이다.
        # 2048 이 아니다 — 정수 표를 쓰는 값이자 한계다.
        self.assertEqual(cm.squash(0), 2047)

    def test_stretch_inverts_squash(self):
        # 정수 표라 정확한 역은 아니다. 한 칸 안쪽이면 된다.
        for x in range(-2000, 2001, 37):
            self.assertLessEqual(abs(cm.stretch(cm.squash(x)) - x), 128)

    def test_table_has_33_entries(self):
        self.assertEqual(len(cm.SQUASH_TABLE), 33)


class TestApm(unittest.TestCase):

    def test_cold_apm_is_almost_identity(self):
        # 아직 아무것도 안 배운 APM 은 받은 확률을 거의 그대로 돌려줘야 한다.
        # 곱수를 23 으로 두면 3200 위가 잘려서 이 시험이 잡는다 (§18.5).
        apm = cm.Apm(4)
        for pr in (100, 1000, 2048, 3000, 3800, 4000):
            got = apm.pp(pr, 1)
            self.assertLess(abs(got - pr), 200, pr)


class TestCodec(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(cm.encode(b''), b'\x00')

    def test_round_trip(self):
        cases = [b'', b'A', b'AB', b'\x00' * 3000, bytes(range(256)),
                 b'hello world ' * 200, b'ab' * 1000,
                 bytes((i * 37 + 11) & 0xFF for i in range(5000))]
        for src in cases:
            self.assertEqual(cm.decode(cm.encode(src)), src, src[:8])

    def test_beats_deflate_on_text(self):
        # 이 덱에서 텍스트를 가장 잘 줄이는 코덱이어야 한다. 왕복은 되는데
        # 이 시험이 깨지면 모델이 틀린 것이다.
        import io as _io
        import os
        from compresslib import deflate
        here = os.path.dirname(os.path.abspath(__file__))
        base = os.path.abspath(os.path.join(here, '..', '..', '..', '..'))
        with _io.open(os.path.join(base, 'corpus', 'source.go'), 'rb') as f:
            src = f.read()
        ours = len(cm.encode(src))
        self.assertLess(ours, len(deflate.encode(src)))
        self.assertLess(ours / len(src), 0.40)

    def test_truncated_raises(self):
        out = cm.encode(b'hello world ' * 50)
        with self.assertRaises(ValueError):
            cm.decode(out[:4])


if __name__ == '__main__':
    unittest.main()
