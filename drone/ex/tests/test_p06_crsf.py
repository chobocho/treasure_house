# -*- coding: utf-8 -*-
"""ex/crsf_crc.py 시험 — CRSF 규격의 CRC8(0xD5)과 틀.

첫 줄·끝 줄 16개 값은 TBS CRSF 규격(crsf-spec §CRC)의 crc8tab
에서 옮겼다. 우리 코드는 표를 쓰지 않고 비트마다 나눈다.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import crsf_crc as CR  # noqa: E402

FIRST = [0x00, 0xD5, 0x7F, 0xAA, 0xFE, 0x2B, 0x81, 0x54,
         0x29, 0xFC, 0x56, 0x83, 0xD7, 0x02, 0xA8, 0x7D]
LAST = [0x84, 0x51, 0xFB, 0x2E, 0x7A, 0xAF, 0x05, 0xD0,
        0xAD, 0x78, 0xD2, 0x07, 0x53, 0x86, 0x2C, 0xF9]


class Crsf(unittest.TestCase):
    def test_table_matches_spec(self):
        tab = [CR.crc8(bytes([b])) for b in range(256)]
        self.assertEqual(tab[:16], FIRST)
        self.assertEqual(tab[-16:], LAST)

    def test_frame_layout(self):
        f = CR.frame(CR.RC_CHANNELS, bytes(22))
        self.assertEqual(len(f), 26)
        self.assertEqual(f[0], 0xC8)
        self.assertEqual(f[1], 24)            # 유형 + 22 + CRC
        self.assertEqual(f[2], 0x16)

    def test_check_roundtrip(self):
        f = CR.frame(CR.RC_CHANNELS, bytes(range(22)))
        self.assertEqual(CR.check(f), (0x16, bytes(range(22))))

    def test_single_flip_detected(self):
        f = CR.frame(CR.RC_CHANNELS, bytes(range(22)))
        for i in range(2, len(f)):
            for b in range(8):
                bad = bytearray(f)
                bad[i] ^= 1 << b
                with self.assertRaises(ValueError):
                    CR.check(bytes(bad))

    def test_length_out_of_range(self):
        with self.assertRaises(ValueError):
            CR.check(bytes([0xC8, 1, 0x16]))

    def test_ticks(self):
        self.assertEqual(CR.us_to_ticks(1500), 992)
        self.assertEqual(CR.us_to_ticks(1000), 192)
        self.assertEqual(CR.us_to_ticks(2000), 1792)
        self.assertEqual(CR.ticks_to_us(992), 1500)

    def test_frame_time(self):
        # 26 바이트 × (시작 1 + 데이터 8 + 정지 1) 비트 / 416666 보
        self.assertAlmostEqual(CR.frame_time_us(26, 416666),
                               260 / 416666 * 1e6, places=9)


if __name__ == '__main__':
    unittest.main()
