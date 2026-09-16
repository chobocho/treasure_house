# -*- coding: utf-8 -*-
"""TFX1 — 파이썬이 C 시험에 넘기는 대조용 배열 묶음.

    "TFX1"  (int32 이름길이, 이름, int32 개수, float64 × 개수) 반복

텍스트로 적지 않는 까닭: %.17g 로 적고 다시 읽어도 같은 double 이
나오기는 하지만, C 에서 strtod 로 수만 개를 읽는 코드가 시험보다
길어진다. 이름 붙은 배열의 나열이면 C 쪽은 fread 몇 줄이다.
"""
import io
import struct


def write(path, arrays):
    """arrays: [(이름, float 리스트)] — 차례를 지킨다."""
    with io.open(path, 'wb') as f:
        f.write(b'TFX1')
        for name, values in arrays:
            raw = name.encode('utf-8')
            f.write(struct.pack('<i', len(raw)) + raw)
            f.write(struct.pack('<i', len(values)))
            f.write(struct.pack('<%dd' % len(values),
                                *[float(v) for v in values]))


def read(path):
    raw = io.open(path, 'rb').read()
    assert raw[:4] == b'TFX1'
    off, out = 4, {}
    while off < len(raw):
        (n,) = struct.unpack('<i', raw[off:off + 4])
        name = raw[off + 4:off + 4 + n].decode('utf-8')
        off += 4 + n
        (k,) = struct.unpack('<i', raw[off:off + 4])
        out[name] = list(struct.unpack('<%dd' % k,
                                       raw[off + 4:off + 4 + 8 * k]))
        off += 4 + 8 * k
    return out


def fnv1a64(data):
    """.bin 이 바이트까지 같은지 C 와 견줄 지문.
    md5 를 C 로 짜기보다 짧다."""
    h = 0xcbf29ce484222325
    for b in data:
        h ^= b
        h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h
