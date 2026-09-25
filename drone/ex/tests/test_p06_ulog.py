# -*- coding: utf-8 -*-
"""ex/ulog_mini.py 시험 — PX4 ULog 형식 문서(px4-ulog)의 바이트 약속.

머리 16바이트, 'B' 가 머리 바로 뒤, msg_size 40, 구독 id 는 0 부터 —
문서가 적은 것만 시험한다. pyulog 로 읽어 보지는 않았다(이 기계에
numpy 가 없다).
"""
import os
import struct
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import ulog_mini as U  # noqa: E402

FMT = [('uint64_t', 'timestamp'), ('float', 'x'), ('float', 'y')]


def sample():
    w = U.Writer(1000)
    w.info('sys_name', 'droneshow')
    w.format('pos', FMT)
    w.subscribe('pos')
    for k in range(3):
        w.data('pos', [1000 + 20000 * k, 0.5 * k, -1.0])
    w.text('6', 41000, 'hello')
    return w.bytes()


class Ulog(unittest.TestCase):
    def test_header(self):
        b = sample()
        self.assertEqual(b[:7], bytes([0x55, 0x4C, 0x6F, 0x67,
                                       0x01, 0x12, 0x35]))
        self.assertEqual(b[7], 1)
        self.assertEqual(struct.unpack('<Q', b[8:16])[0], 1000)

    def test_flag_bits_first(self):
        b = sample()
        size, kind = struct.unpack('<HB', b[16:19])
        self.assertEqual((size, chr(kind)), (40, 'B'))

    def test_roundtrip(self):
        log = U.read(sample())
        self.assertEqual(log['start'], 1000)
        self.assertEqual(log['info']['sys_name'], 'droneshow')
        self.assertEqual(log['formats']['pos'], FMT)
        rows = log['data']['pos']
        self.assertEqual([r['timestamp'] for r in rows],
                         [1000, 21000, 41000])
        self.assertEqual([r['x'] for r in rows], [0.0, 0.5, 1.0])
        self.assertEqual(log['text'], [('6', 41000, 'hello')])

    def test_first_msg_id_is_zero(self):
        w = U.Writer(0)
        w.format('a', [('uint64_t', 'timestamp')])
        w.format('b', [('uint64_t', 'timestamp')])
        self.assertEqual((w.subscribe('a'), w.subscribe('b')), (0, 1))

    def test_timestamp_must_increase(self):
        w = U.Writer(0)
        w.format('a', [('uint64_t', 'timestamp')])
        w.subscribe('a')
        w.data('a', [5])
        with self.assertRaises(ValueError):
            w.data('a', [5])

    def test_unknown_message_skipped(self):
        # 모르는 유형은 msg_size 만큼 건너뛴다
        b = sample()
        extra = struct.pack('<HB', 3, ord('Z')) + b'abc'
        log = U.read(b[:16 + 43] + extra + b[16 + 43:])
        self.assertEqual(len(log['data']['pos']), 3)


if __name__ == '__main__':
    unittest.main()
