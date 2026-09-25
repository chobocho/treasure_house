# -*- coding: utf-8 -*-
"""ex/mavlink_xml.py 시험 — XML 정의에서 CRC_EXTRA 를 다시 계산한다.

기댓값 50 과 217 은 c_library_v2 minimal.h 의 MAVLINK_MESSAGE_CRCS
(생성기가 만든 값, 6부 CITE mavlink-minimal-h)에서 옮겼다.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import mavlink_parse as MP  # noqa: E402
import mavlink_xml as MX  # noqa: E402

EXC = os.path.join(HERE, '..', '..', 'data', 'excerpts')
HB = os.path.join(EXC, 'mavlink-heartbeat.xml')
PV = os.path.join(EXC, 'mavlink-protocol-version.xml')


class Xml(unittest.TestCase):
    def test_heartbeat_extra_is_50(self):
        msg = MX.read(HB)
        self.assertEqual((msg['id'], msg['name']), (0, 'HEARTBEAT'))
        self.assertEqual(MX.crc_extra(msg), 50)

    def test_protocol_version_extra_is_217(self):
        msg = MX.read(PV)
        self.assertEqual((msg['id'], msg['name']),
                         (300, 'PROTOCOL_VERSION'))
        self.assertEqual(MX.crc_extra(msg), 217)

    def test_array_field_parsed(self):
        msg = MX.read(PV)
        self.assertIn(('uint8_t', 'spec_version_hash', 8),
                      msg['fields'])

    def test_wire_order_matches_hand_list(self):
        # mavlink_parse.FIELDS 에 손으로 적은 전송 순서와 같아야 한다
        fields = MX.read(HB)['fields']
        got = [(t, n) for t, n, _ in MX.wire_order(fields)]
        self.assertEqual(got, MP.FIELDS)

    def test_order_is_stable(self):
        fields = [('uint8_t', 'a', 0), ('uint16_t', 'b', 0),
                  ('uint8_t', 'c', 0), ('uint16_t', 'd', 0)]
        self.assertEqual([n for _, n, _ in MX.wire_order(fields)],
                         ['b', 'd', 'a', 'c'])

    def test_array_length_changes_extra(self):
        msg = MX.read(PV)
        short = dict(msg, fields=[
            (t, n, 7 if k == 8 else k) for t, n, k in msg['fields']])
        self.assertNotEqual(MX.crc_extra(short), 217)

    def test_extensions_are_left_out(self):
        text = ('<message id="9" name="T">'
                '<field type="uint8_t" name="a">x</field>'
                '<extensions/>'
                '<field type="uint32_t" name="b">y</field></message>')
        plain = ('<message id="9" name="T">'
                 '<field type="uint8_t" name="a">x</field></message>')
        self.assertEqual(MX.crc_extra(MX.parse(text)),
                         MX.crc_extra(MX.parse(plain)))


if __name__ == '__main__':
    unittest.main()
