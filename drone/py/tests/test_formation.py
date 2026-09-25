# -*- coding: utf-8 -*-
"""formation 시험 — 편대 생성기는 개수와 최소 간격을 지킨다 (T32)."""
import math
import unittest

from droneshow import collide
from droneshow import formation as F
from droneshow import rng

D = 1.5


def spacing(pts):
    return collide.min_distance(pts)[0]


class Shapes(unittest.TestCase):
    def check(self, pts, n, dmin=D):
        self.assertEqual(len(pts), n)
        self.assertGreaterEqual(spacing(pts), dmin - 1e-9)
        for p in pts:
            self.assertEqual(len(p), 3)

    def test_grid(self):
        self.check(F.grid(12, D), 12)
        self.check(F.grid(7, D, plane='xy'), 7)

    def test_circle(self):
        pts = F.circle(20, D)
        self.check(pts, 20)
        self.assertAlmostEqual(spacing(pts), D, places=9)

    def test_rings(self):
        self.check(F.rings(30, D, layers=3), 30)

    def test_sphere(self):
        self.check(F.sphere(60, D), 60)

    def test_heart(self):
        self.check(F.heart(40, D), 40)

    def test_globe(self):
        self.check(F.globe(80, D), 80)

    def test_curve_points_are_tight(self):
        # 곡선 위 점은 이웃과 거의 d 간격이어야 한다 — 호 길이 d 마다
        # 제안하면 현이 d 보다 조금 짧아 하나 걸러 버려지고, 모양이
        # 두 배로 커진다(실제로 그랬다, 16부 실습에서 발견).
        for pts in (F.heart(60, D), F.globe(120, D)):
            nn = [min(math.dist(p, q) for q in pts if q is not p)
                  for p in pts]
            self.assertLess(sum(nn) / len(nn), 1.2 * D)

    def test_text(self):
        pts = F.text('HI', D)
        # H 는 '#' 17개, I 는 11개 (5×7 글꼴)
        want = F.glyph_count('H') + F.glyph_count('I')
        self.assertEqual(len(pts), want)
        self.assertGreaterEqual(spacing(pts), D - 1e-9)

    def test_digit(self):
        self.check(F.digit(3, D), F.glyph_count('3'))

    def test_bottom_and_centre(self):
        pts = F.grid(9, D, z0=20.0)
        self.assertAlmostEqual(min(p[2] for p in pts), 20.0)
        xs = [p[0] for p in pts]
        self.assertAlmostEqual(min(xs) + max(xs), 0.0, places=12)

    def test_font_has_digits_and_letters(self):
        for ch in '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            self.assertGreater(F.glyph_count(ch), 0, ch)


class Spacing(unittest.TestCase):
    """T32 — 포아송 원판 표본은 만든 방식 그대로 간격 r 을 지킨다."""

    def test_poisson_min_distance(self):
        g = rng.Rng(4)
        pts = F.poisson_disk(lambda x, z: True, 20.0, 10.0, 1.0, g,
                             tries=3000)
        self.assertGreater(len(pts), 50)
        got = spacing([[x, 0, z] for x, z in pts])
        self.assertGreaterEqual(got, 1.0)

    def test_fibonacci_spacing_shrinks_like_inverse_sqrt(self):
        # 단위 구 위 n 점의 최소 간격 × √n 은 거의 일정하다
        a = F.fibonacci_unit_min(100) * math.sqrt(100)
        b = F.fibonacci_unit_min(400) * math.sqrt(400)
        self.assertAlmostEqual(a / b, 1.0, delta=0.1)

    def test_image_points(self):
        pgm = 'P2\n8 8\n255\n' + '\n'.join(
            ' '.join('255' if 2 <= i <= 5 and 2 <= j <= 5 else '0'
                     for i in range(8)) for j in range(8))
        pts = F.image(pgm, 6, D, rng.Rng(1))
        self.assertEqual(len(pts), 6)
        self.assertGreaterEqual(spacing(pts), D - 1e-9)


if __name__ == '__main__':
    unittest.main()
