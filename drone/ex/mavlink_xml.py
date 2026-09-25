# -*- coding: utf-8 -*-
"""MAVLink 메시지 정의(XML)에서 CRC_EXTRA 를 다시 계산한다 (6부).

mavlink_parse.py 는 HEARTBEAT 의 전송 순서를 손으로 적었다. 여기서는
XML 한 조각을 읽어 (1) 크기 순 안정 정렬로 전송 순서를 만들고
(2) 직렬화 문서의 message_checksum 절차대로 한 바이트를 만든다 —
배열 필드는 길이 한 바이트를 더 넣고, <extensions/> 뒤 필드는 뺀다.
시간 O(필드 수 · 이름 길이).
"""
import xml.etree.ElementTree as ET

from mavlink_parse import x25

# 전송 순서를 정하는 크기 — 배열은 원소 하나의 크기로 본다
SIZE = {'double': 8, 'uint64_t': 8, 'int64_t': 8,
        'float': 4, 'uint32_t': 4, 'int32_t': 4,
        'uint16_t': 2, 'int16_t': 2,
        'uint8_t': 1, 'int8_t': 1, 'char': 1}


def _field(t):
    """'uint8_t[8]' → ('uint8_t', 8), 마법 형은 기본 형으로."""
    n = 0
    if t.endswith(']'):
        t, n = t[:-1].split('[')
        n = int(n)
    if t == 'uint8_t_mavlink_version':
        t = 'uint8_t'
    return t, n


def parse(text):
    """<message> 하나의 글 → {'id', 'name', 'fields'}.

    fields 는 XML 순서의 (형, 이름, 배열 길이 또는 0)."""
    root = ET.fromstring(text)
    fields = []
    for el in root:
        if el.tag == 'extensions':
            break                      # 확장 필드는 CRC 에 넣지 않는다
        if el.tag == 'field':
            t, n = _field(el.get('type'))
            fields.append((t, el.get('name'), n))
    return {'id': int(root.get('id')), 'name': root.get('name'),
            'fields': fields}


def read(path):
    """발췌 파일(첫 줄은 출처 주석)을 읽는다."""
    with open(path, encoding='utf-8') as f:
        lines = f.read().split('\n')
    return parse('\n'.join(lines[1:]))


def wire_order(fields):
    """큰 형부터, 같은 크기는 XML 순서 — sorted 는 안정 정렬이다."""
    return sorted(fields, key=lambda f: -SIZE[f[0]])


def crc_extra(msg):
    """이름 + ' ', 필드마다 형 + ' ', 이름 + ' ', (배열이면 길이)."""
    crc = x25((msg['name'] + ' ').encode())
    for t, name, n in wire_order(msg['fields']):
        crc = x25((t + ' ').encode(), crc)
        crc = x25((name + ' ').encode(), crc)
        if n:
            crc = x25(bytes([n]), crc)
    return (crc & 0xFF) ^ (crc >> 8)


if __name__ == '__main__':
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    exc = os.path.join(here, '..', 'data', 'excerpts')
    for name in ('mavlink-heartbeat.xml',
                 'mavlink-protocol-version.xml'):
        m = read(os.path.join(exc, name))
        print('%s (id %d)' % (m['name'], m['id']))
        for t, f, n in wire_order(m['fields']):
            line = '  %-9s %-22s %s' % (t, f, '[%d]' % n if n else '')
            print(line.rstrip())
        print('  CRC_EXTRA =', crc_extra(m))
