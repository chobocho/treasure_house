# -*- coding: utf-8 -*-
"""팩 (SPEC.md §13) — 객체 여럿을 한 파일에, 비슷한 것은 델타로.

느슨한 객체는 파일 하나에 객체 하나지만, 팩은 객체들을 이어 붙이고
비슷한 객체는 "바탕에서 여기를 복사, 여기에 이것을 끼움" 이라는 델타로
적는다. 색인(.idx)은 이름 → 팩 안 자리의 표다. 팩 끝 20바이트는 팩
전체의 SHA-1 이고, 그것이 곧 파일 이름이다.
"""
import struct
import zlib as _z

from mygit import GitError, objects, zlib
from mygit.sha1 import Sha1

TYPE_NAMES = {1: 'commit', 2: 'tree', 3: 'blob', 4: 'tag'}
TYPE_CODES = {v: k for k, v in TYPE_NAMES.items()}
OFS_DELTA, REF_DELTA = 6, 7


class PackEntry(object):
    """팩 항목 하나를 되살린 것. packed_type 은 팩에 적힌 형식(6·7 은
    델타), type·body 는 되살린 객체, depth·base 는 델타 사슬."""

    def __init__(self, offset):
        self.offset, self.end, self.crc = offset, None, None
        self.packed_type, self.delta = None, None
        self.base_offset = self.base = None
        self.type = self.body = self.oid = None
        self.depth = 0


def _varint_le(data, pos):
    """7비트씩 작은 쪽부터(델타 머리의 크기). → (값, 다음 자리)."""
    val, shift = 0, 0
    while True:
        b = data[pos]
        pos += 1
        val |= (b & 0x7f) << shift
        shift += 7
        if not b & 0x80:
            return val, pos


def _entry_header(data, pos):
    """항목 머리 → (형식, 크기, 다음 자리). 첫 바이트의 낮은 4비트가
    크기의 시작이고, 이어지는 바이트는 7비트씩 위로 붙는다."""
    b = data[pos]
    pos += 1
    typ, size, shift = (b >> 4) & 7, b & 15, 4
    while b & 0x80:
        b = data[pos]
        pos += 1
        size |= (b & 0x7f) << shift
        shift += 7
    return typ, size, pos


def _ofs(data, pos):
    """OFS_DELTA 의 거리 — 큰 쪽부터, 이어지는 바이트마다 +1."""
    b = data[pos]
    pos += 1
    n = b & 0x7f
    while b & 0x80:
        b = data[pos]
        pos += 1
        n = ((n + 1) << 7) | (b & 0x7f)
    return n, pos


def apply_delta(base, delta):
    """델타를 바탕에 적용한다(SPEC.md §13.1). O(결과 길이)."""
    size, pos = _varint_le(delta, 0)
    if size != len(base):
        raise GitError('fatal: mygit: delta base size mismatch')
    want, pos = _varint_le(delta, pos)
    out = bytearray()
    while pos < len(delta):
        op = delta[pos]
        pos += 1
        if op & 0x80:                           # 복사
            off = n = 0
            for k in range(4):
                if op & (1 << k):
                    off |= delta[pos] << (8 * k)
                    pos += 1
            for k in range(3):
                if op & (0x10 << k):
                    n |= delta[pos] << (8 * k)
                    pos += 1
            n = n or 0x10000
            if off + n > len(base):
                raise GitError('fatal: mygit: delta copy out of range')
            out += base[off:off + n]
        elif op:                                # 끼움
            out += delta[pos:pos + op]
            pos += op
        else:
            raise GitError('fatal: mygit: delta opcode 0 is reserved')
    if len(out) != want:
        raise GitError('fatal: mygit: delta result size mismatch')
    return bytes(out)


def read_pack(data, external=None):
    """팩 바이트 → [PackEntry], 자리 차례. external(이름) 은 팩 밖의
    REF_DELTA 바탕을 (형식, 몸) 으로 준다(없으면 오류).

    앞에서부터 읽으며 zlib 스트림이 먹은 바이트 수로 다음 항목을 찾고,
    델타는 바탕을 먼저 되살린 뒤 적용한다. O(팩 크기 + 되살린 크기).
    """
    if len(data) < 32 or data[:4] != b'PACK':
        raise GitError('fatal: mygit: not a pack file')
    if Sha1().update(data[:-20]).digest() != data[-20:]:
        raise GitError('fatal: mygit: pack checksum mismatch')
    ver, count = struct.unpack('>II', data[4:12])
    if ver not in (2, 3):
        raise GitError('fatal: mygit: pack version %d' % ver)
    ents, pos = [], 12
    for _ in range(count):
        e = PackEntry(pos)
        e.packed_type, size, pos = _entry_header(data, pos)
        if e.packed_type == OFS_DELTA:
            n, pos = _ofs(data, pos)
            e.base_offset = e.offset - n
        elif e.packed_type == REF_DELTA:
            e.base = data[pos:pos + 20].hex()
            pos += 20
        elif e.packed_type not in TYPE_NAMES:
            raise GitError('fatal: mygit: bad pack entry type %d'
                           % e.packed_type)
        raw, used = zlib.decompress_prefix(data, pos)
        if len(raw) != size:
            raise GitError('fatal: mygit: pack entry size mismatch')
        pos += used
        e.end = pos
        e.crc = _z.crc32(data[e.offset:pos]) & 0xffffffff
        if e.packed_type in TYPE_NAMES:
            e.type, e.body = TYPE_NAMES[e.packed_type], raw
        else:
            e.delta = raw
        ents.append(e)
    if pos != len(data) - 20:
        raise GitError('fatal: mygit: pack has trailing garbage')
    _resolve(ents, external)
    return ents


def _resolve(ents, external):
    """델타 사슬을 풀어 형식·몸·이름·깊이를 채운다."""
    by_off = {e.offset: e for e in ents}
    by_oid = {}
    for e in ents:
        if e.body is not None:
            e.oid = objects.hash_object(e.type, e.body)
            by_oid[e.oid] = e
    pending = [e for e in ents if e.body is None]
    while pending:
        left = []
        for e in pending:
            if e.base_offset is not None:
                b = by_off.get(e.base_offset)
                if b is None:
                    raise GitError('fatal: mygit: bad OFS_DELTA base')
            else:
                b = by_oid.get(e.base)
                if b is None and external is not None:
                    t, body = external(e.base)
                    e.type, e.body = t, apply_delta(body, e.delta)
                    e.depth = 1
                    e.oid = objects.hash_object(e.type, e.body)
                    by_oid[e.oid] = e
                    continue
            if b is None or b.body is None:
                left.append(e)
                continue
            e.type = b.type
            e.body = apply_delta(b.body, e.delta)
            e.depth, e.base = b.depth + 1, b.oid
            e.oid = objects.hash_object(e.type, e.body)
            by_oid[e.oid] = e
        if len(left) == len(pending):
            raise GitError('fatal: mygit: unresolved delta base')
        pending = left


def read_idx(data):
    """색인 판 2 → {'entries': [(이름, 자리, crc)],
    'pack_sum': 20바이트}."""
    if data[:8] != b'\xfftOc\x00\x00\x00\x02':
        raise GitError('fatal: mygit: not a version 2 pack index')
    if Sha1().update(data[:-20]).digest() != data[-20:]:
        raise GitError('fatal: mygit: pack index checksum mismatch')
    n = struct.unpack('>I', data[8 + 255 * 4:8 + 256 * 4])[0]
    p = 8 + 256 * 4
    oids = [data[p + 20 * k:p + 20 * k + 20].hex() for k in range(n)]
    p += 20 * n
    crcs = struct.unpack('>%dI' % n, data[p:p + 4 * n])
    p += 4 * n
    small = struct.unpack('>%dI' % n, data[p:p + 4 * n])
    p += 4 * n
    offs = []
    for v in small:
        if v & 0x80000000:                  # 2 GiB 넘는 자리의 표
            k = v & 0x7fffffff
            v = struct.unpack('>Q', data[p + 8 * k:p + 8 * k + 8])[0]
        offs.append(v)
    return {'entries': list(zip(oids, offs, crcs)),
            'pack_sum': data[-40:-20]}


def write_idx(entries, pack_sum):
    """[PackEntry] → 색인 판 2 바이트(SPEC.md §13.2).

    이름 차례로 정렬한 fanout·이름·CRC·자리, 팩 체크섬, 그 앞 전부의
    SHA-1. 같은 팩이면 git 의 .idx 와 바이트까지 같다.
    """
    ents = sorted(entries, key=lambda e: e.oid)
    fan = [0] * 256
    for e in ents:
        fan[int(e.oid[:2], 16)] += 1
    for k in range(1, 256):
        fan[k] += fan[k - 1]
    big = [e.offset for e in ents if e.offset >= 0x80000000]
    small = []
    for e in ents:
        if e.offset >= 0x80000000:
            small.append(0x80000000 | big.index(e.offset))
        else:
            small.append(e.offset)
    body = b''.join([b'\xfftOc', struct.pack('>I', 2),
                     struct.pack('>256I', *fan),
                     b''.join(bytes.fromhex(e.oid) for e in ents),
                     struct.pack('>%dI' % len(ents),
                                 *[e.crc for e in ents]),
                     struct.pack('>%dI' % len(ents), *small),
                     b''.join(struct.pack('>Q', o) for o in big),
                     pack_sum])
    return body + Sha1().update(body).digest()


def _varint_out(n):
    out = bytearray()
    while True:
        b = n & 0x7f
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def _copy_op(off, n):
    """복사 명령 — 0 이 아닌 바이트만 쓴다. 길이 0x10000 은 길이
    바이트 없이."""
    op, tail = 0x80, bytearray()
    for k in range(4):
        byte = (off >> (8 * k)) & 0xff
        if byte:
            op |= 1 << k
            tail.append(byte)
    if n != 0x10000:
        for k in range(3):
            byte = (n >> (8 * k)) & 0xff
            if byte:
                op |= 0x10 << k
                tail.append(byte)
    return bytes([op]) + bytes(tail)


BLOCK = 16


def make_delta(base, target):
    """바탕 → 결과의 델타(SPEC.md §13.3). 다섯 언어가 같은 바이트를
    낸다.

    바탕을 16바이트 칸으로 잘라 "칸 내용 → 처음 나온 자리" 표를 만들고,
    결과를 앞에서부터 훑으며 표에 있는 칸이면 앞으로 늘일 수 있는 만큼
    복사, 없으면 한 바이트씩 끼울 것에 모은다. git 의 델타 찾기(rolling
    hash 와 바탕 뒤로 늘이기)보다 단순하고, 그래서 보통 더 길다.
    O(결과 길이 × 복사 길이) 최악.
    """
    table = {}
    for off in range(0, len(base) - BLOCK + 1, BLOCK):
        table.setdefault(base[off:off + BLOCK], off)
    out = bytearray(_varint_out(len(base)) + _varint_out(len(target)))
    pend = bytearray()

    def flush():
        for k in range(0, len(pend), 127):
            chunk = pend[k:k + 127]
            out.append(len(chunk))
            out.extend(chunk)
        del pend[:]
    i = 0
    while i < len(target):
        o = table.get(target[i:i + BLOCK]) \
            if i + BLOCK <= len(target) else None
        if o is None:
            pend.append(target[i])
            i += 1
            if len(pend) == 127:
                flush()
            continue
        n = BLOCK
        while o + n < len(base) and i + n < len(target) and \
                base[o + n] == target[i + n]:
            n += 1
        flush()
        k = 0
        while k < n:
            step = min(0x10000, n - k)
            out += _copy_op(o + k, step)
            k += step
        i += n
    flush()
    return bytes(out)


def _entry_head(typ, size):
    b = (typ << 4) | (size & 15)
    size >>= 4
    out = bytearray()
    while size:
        out.append(b | 0x80)
        b = size & 0x7f
        size >>= 7
    out.append(b)
    return bytes(out)


def _ofs_out(n):
    """OFS_DELTA 거리 — 큰 쪽부터, 이어지는 바이트마다 1 을 뺀다."""
    out = bytearray([n & 0x7f])
    n >>= 7
    while n:
        n -= 1
        out.insert(0, 0x80 | (n & 0x7f))
        n >>= 7
    return bytes(out)


def write_pack(items):
    """[(형식, 몸, 델타 바탕의 목록 번호 또는 None)] → (팩 바이트,
    [PackEntry]). 바탕은 목록에서 앞에 있어야 한다(OFS_DELTA)."""
    out = bytearray(b'PACK' + struct.pack('>II', 2, len(items)))
    ents = []
    for type_, body, base in items:
        e = PackEntry(len(out))
        e.type, e.body = type_, body
        e.oid = objects.hash_object(type_, body)
        if base is None:
            e.packed_type = TYPE_CODES[type_]
            raw = body
            head = _entry_head(e.packed_type, len(raw))
        else:
            b = ents[base]
            raw = e.delta = make_delta(b.body, body)
            e.packed_type, e.base = OFS_DELTA, b.oid
            e.depth = b.depth + 1
            head = _entry_head(OFS_DELTA, len(raw)) + \
                _ofs_out(e.offset - b.offset)
        out += head + zlib.compress(raw)
        e.end = len(out)
        e.crc = _z.crc32(out[e.offset:e.end]) & 0xffffffff
        ents.append(e)
    out += Sha1().update(bytes(out)).digest()
    return bytes(out), ents


def verify_lines(entries, pack_path):
    """git verify-pack -v 와 바이트까지 같은 줄들(SPEC.md §13.3)."""
    rows = []
    ents = sorted(entries, key=lambda e: e.offset)
    ends = [e.offset for e in ents[1:]] + [None]
    hist = {}
    for e, nxt in zip(ents, ends):
        size_in = (nxt if nxt is not None else e.end) - e.offset
        # 크기는 팩에 적힌 크기 — 델타면 델타의 크기다(git 과 같다)
        size = len(e.delta if e.delta is not None else e.body)
        row = '%s %-6s %d %d %d' % (e.oid, e.type, size, size_in,
                                    e.offset)
        if e.depth:
            row += ' %d %s' % (e.depth, e.base)
        rows.append(row)
        hist[e.depth] = hist.get(e.depth, 0) + 1
    plural = lambda n: '%d object%s' % (n, '' if n == 1 else 's')
    rows.append('non delta: ' + plural(hist.pop(0, 0)))
    for d in sorted(hist):
        rows.append('chain length = %d: %s' % (d, plural(hist[d])))
    rows.append('%s: ok' % pack_path)
    return rows
