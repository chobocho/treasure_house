# -*- coding: utf-8 -*-
"""ULog 의 아주 작은 부분집합을 쓰고 읽는다 (6부, PX4 ULog 형식 문서).

머리(마법 7바이트 + 판 1 + 시작 시각 8) 뒤에 'B'(깃발 40바이트)를
맨 먼저 두고, 'I'(정보)·'F'(형식) 로 정의를 적은 다음 'A'(구독)와
'D'(기록)·'L'(글) 을 이어 쓴다. 모든 수는 리틀 엔디언. 기본 형만
다루고(배열·중첩 형식은 빼었다) 모르는 메시지는 크기만큼 건너뛴다.
PX4 의 로거가 아니다 — 형식 문서가 적은 바이트 약속을 따른 연습이다.
"""
import struct

MAGIC = bytes([0x55, 0x4C, 0x6F, 0x67, 0x01, 0x12, 0x35])
CODE = {'uint8_t': 'B', 'int8_t': 'b', 'uint16_t': 'H', 'int16_t': 'h',
        'uint32_t': 'I', 'int32_t': 'i', 'uint64_t': 'Q',
        'int64_t': 'q', 'float': 'f', 'double': 'd', 'bool': '?'}


def _msg(kind, body):
    """메시지 머리: uint16 msg_size(머리 제외) + uint8 msg_type."""
    return struct.pack('<HB', len(body), ord(kind)) + body


class Writer:
    def __init__(self, start_us):
        self.out = bytearray(MAGIC + bytes([1])
                             + struct.pack('<Q', start_us))
        # 'B': 호환·비호환 깃발 8+8 바이트, 덧붙인 자리 3개 — 모두 0
        self.out += _msg('B', bytes(16) + struct.pack('<3Q', 0, 0, 0))
        self.fmt, self.ids, self.last = {}, {}, {}

    def info(self, key, text):
        k = ('char[%d] %s' % (len(text.encode()), key)).encode()
        self.out += _msg('I', bytes([len(k)]) + k + text.encode())

    def format(self, name, fields):
        """fields = [(형, 이름)], 첫 칸은 uint64_t timestamp."""
        self.fmt[name] = fields
        s = name + ':' + ''.join('%s %s;' % f for f in fields)
        self.out += _msg('F', s.encode())

    def subscribe(self, name):
        """msg_id 는 0 부터 하나씩."""
        mid = len(self.ids)
        self.ids[name] = mid
        body = struct.pack('<BH', 0, mid) + name.encode()
        self.out += _msg('A', body)
        return mid

    def data(self, name, values):
        if name in self.last and values[0] <= self.last[name]:
            raise ValueError('timestamp 는 늘기만 해야 한다')
        self.last[name] = values[0]
        codes = '<' + ''.join(CODE[t] for t, _ in self.fmt[name])
        self.out += _msg('D', struct.pack('<H', self.ids[name])
                         + struct.pack(codes, *values))

    def text(self, level, t_us, s):
        """'L': 글자 하나로 된 수준('0'…'7') + 시각 + 글."""
        self.out += _msg('L', level.encode() + struct.pack('<Q', t_us)
                         + s.encode())

    def bytes(self):
        return bytes(self.out)


def read(b):
    """→ {'start', 'info', 'formats', 'data', 'text'}. O(파일 길이)."""
    if b[:7] != MAGIC:
        raise ValueError('ULog 마법 바이트가 아니다')
    log = {'start': struct.unpack('<Q', b[8:16])[0], 'info': {},
           'formats': {}, 'data': {}, 'text': []}
    subs, i = {}, 16
    while i + 3 <= len(b):
        size, kind = struct.unpack('<HB', b[i:i + 3])
        body, i = b[i + 3:i + 3 + size], i + 3 + size
        kind = chr(kind)
        if kind == 'I':
            k = body[1:1 + body[0]].decode().split(' ')[1]
            log['info'][k] = body[1 + body[0]:].decode()
        elif kind == 'F':
            name, rest = body.decode().split(':', 1)
            log['formats'][name] = [tuple(f.split(' '))
                                    for f in rest.split(';') if f]
        elif kind == 'A':
            subs[struct.unpack('<H', body[1:3])[0]] = body[3:].decode()
        elif kind == 'D':
            name = subs[struct.unpack('<H', body[:2])[0]]
            fields = log['formats'][name]
            codes = '<' + ''.join(CODE[t] for t, _ in fields)
            vals = struct.unpack(codes, body[2:])
            log['data'].setdefault(name, []).append(
                {n: v for (_, n), v in zip(fields, vals)})
        elif kind == 'L':
            t = struct.unpack('<Q', body[1:9])[0]
            log['text'].append((chr(body[0]), t, body[9:].decode()))
    return log


if __name__ == '__main__':
    w = Writer(0)
    w.format('pos', [('uint64_t', 'timestamp'), ('float', 'x')])
    w.subscribe('pos')
    w.data('pos', [20000, 1.5])
    b = w.bytes()
    print(len(b), '바이트:', b[:16].hex(' '))
    print(read(b)['data'])
