# -*- coding: utf-8 -*-
"""render 시험 — SVG 스냅숏·PNG·투영·감마 (SPEC §9.5, T33, T34)."""
import math
import struct
import unittest
import zlib

from droneshow import formation as F
from droneshow import params
from droneshow import render as R
from droneshow import show as SH


def tiny():
    p = params.load()
    return SH.plan([{'name': 'a', 'points': F.circle(8, 3.0, z0=10.0),
                     'hold': 1.0, 'rgb': (255, 0, 0)}], p)


class Svg(unittest.TestCase):
    def test_viewbox_and_count(self):
        svg = R.snapshot_svg(tiny(), 0, 'front')
        head = '<svg class="show" viewBox="0 0 340 '
        self.assertTrue(svg.startswith(head))
        self.assertEqual(svg.count('<circle'), 2 * 8)
        self.assertIn('rgb(255,0,0)', svg)

    def test_deterministic(self):
        self.assertEqual(R.snapshot_svg(tiny(), 3, 'top'),
                         R.snapshot_svg(tiny(), 3, 'top'))

    def test_views_differ(self):
        s = tiny()
        self.assertNotEqual(R.snapshot_svg(s, 0, 'front'),
                            R.snapshot_svg(s, 0, 'top'))


class Png(unittest.TestCase):
    def test_png_header_and_size(self):
        b = R.png(tiny(), 0, 64, 40, 'front')
        self.assertEqual(b[:8], b'\x89PNG\r\n\x1a\n')
        w, h = struct.unpack('>II', b[16:24])
        self.assertEqual((w, h), (64, 40))

    def test_png_crc_valid(self):
        b = R.png(tiny(), 0, 32, 20, 'front')
        pos = 8
        while pos < len(b):
            n = struct.unpack('>I', b[pos:pos + 4])[0]
            kind = b[pos + 4:pos + 8]
            data = b[pos + 8:pos + 8 + n]
            crc = struct.unpack('>I', b[pos + 8 + n:pos + 12 + n])[0]
            self.assertEqual(zlib.crc32(kind + data) & 0xffffffff, crc)
            pos += 12 + n


class Perspective(unittest.TestCase):
    """T33 — 거리 D 에서 너비 W 는 약 W/D 라디안으로 보인다."""

    def test_small_angle(self):
        for w, d in ((20.0, 200.0), (60.0, 300.0)):
            exact = 2 * math.atan(w / (2 * d))
            self.assertLess(abs(exact - w / d) / exact,
                            (w / d) ** 2 / 12 * 1.01)

    def test_depth_barely_changes_size(self):
        # 200 m 밖에서 5 m 앞뒤로 움직이면 크기가 2.5 % 쯤만 변한다
        a = R.apparent_size(20.0, 200.0)
        b = R.apparent_size(20.0, 205.0)
        self.assertAlmostEqual(a / b, 205 / 200, places=2)

    def test_project_audience_centre(self):
        cam = R.camera([0.0, 0.0, 20.0], 200.0, 2.0)
        x, y = R.project(cam, [0.0, 0.0, 20.0])
        self.assertAlmostEqual(x, 0.0, places=12)
        self.assertAlmostEqual(y, 0.0, places=9)


class Gamma(unittest.TestCase):
    """T34 — 8비트 값은 감마로 부호화된 값이다. 빛의 양은
    (v/255)^2.2."""

    def test_roundtrip(self):
        for v in (0, 1, 64, 128, 255):
            self.assertEqual(R.encode(R.decode(v)), v)

    def test_half_code_is_not_half_light(self):
        self.assertAlmostEqual(R.decode(128), (128 / 255) ** 2.2,
                               places=12)
        self.assertLess(R.decode(128), 0.25)

    def test_mix_in_linear_light(self):
        # 빨강과 초록을 반반 — 부호 값을 평균하면 어둡게 보인다
        naive = R.mix_codes([255, 0, 0], [0, 255, 0], 0.5, False)
        right = R.mix_codes([255, 0, 0], [0, 255, 0], 0.5, True)
        self.assertEqual(naive, [128, 128, 0])
        self.assertGreater(right[0], naive[0])


if __name__ == '__main__':
    unittest.main()
