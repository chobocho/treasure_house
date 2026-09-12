# -*- coding: utf-8 -*-
"""zlib 과 gzip 컨테이너 — SPEC §10.8 (RFC 1950, RFC 1952).

DEFLATE 스트림 자체에는 "무엇이었는지" 도 "제대로 풀렸는지" 도 없다.
그 둘을 얹은 것이 컨테이너다. zlib 은 2바이트 머리 + Adler-32,
gzip 은 10바이트 머리 + CRC-32 + 원본 길이.

gzip 머리의 MTIME 을 **0 으로 못 박는다.** 진짜 gzip 은 파일의 수정
시각을 적어서 같은 입력에 같은 바이트가 안 나온다 — 재현이 안 된다.
우리는 make record 를 세 번 돌려 md5 가 같아야 하므로 0 을 쓴다. 이 차이
자체가 9부의 이야깃거리다.
"""
from compresslib import checksums, deflate, inflate

# CMF = 0x78 (CM 8 = deflate, CINFO 7 = 32 KiB 창)
# FLG = 0x9C — FDICT 0, FLEVEL 2, 그리고 (CMF<<8 | FLG) 가 31 의 배수
ZLIB_CMF = 0x78
ZLIB_FLG = 0x9C

GZIP_MAGIC = b'\x1f\x8b'
GZIP_DEFLATE = 8
GZIP_OS_UNKNOWN = 255


def zlib_compress(src):
    head = bytes([ZLIB_CMF, ZLIB_FLG])
    tail = checksums.adler32(src).to_bytes(4, 'big')
    return head + deflate.deflate_raw(src) + tail


def zlib_decompress(src):
    if len(src) < 6:
        raise ValueError('zlib 스트림이 너무 짧다')
    cmf, flg = src[0], src[1]
    if (cmf & 0x0F) != 8:
        raise ValueError('zlib CM 이 8 이 아니다: %d' % (cmf & 0x0F))
    if ((cmf << 8) | flg) % 31:
        raise ValueError('zlib 머리의 검사식이 31 로 안 나눠진다')
    if flg & 0x20:
        raise ValueError('미리 정한 사전(FDICT)은 지원하지 않는다')
    out = inflate.inflate_raw(src[2:-4])
    want = int.from_bytes(src[-4:], 'big')
    if checksums.adler32(out) != want:
        raise ValueError('Adler-32 가 다르다')
    return out


def gzip_compress(src):
    head = GZIP_MAGIC + bytes([GZIP_DEFLATE, 0,
                               0, 0, 0, 0,        # MTIME = 0 (재현성)
                               0, GZIP_OS_UNKNOWN])
    tail = (checksums.crc32(src).to_bytes(4, 'little')
            + (len(src) & 0xFFFFFFFF).to_bytes(4, 'little'))
    return head + deflate.deflate_raw(src) + tail


def gzip_decompress(src):
    if len(src) < 18:
        raise ValueError('gzip 스트림이 너무 짧다')
    if src[:2] != GZIP_MAGIC:
        raise ValueError('gzip 매직이 아니다')
    if src[2] != GZIP_DEFLATE:
        raise ValueError('gzip CM 이 8 이 아니다: %d' % src[2])
    flg = src[3]
    pos = 10
    if flg & 0x04:                                   # FEXTRA
        n = src[pos] | (src[pos + 1] << 8)
        pos += 2 + n
    for bit in (0x08, 0x10):                         # FNAME, FCOMMENT
        if flg & bit:
            while pos < len(src) and src[pos]:
                pos += 1
            pos += 1
    if flg & 0x02:                                   # FHCRC
        pos += 2
    if pos >= len(src) - 8:
        raise ValueError('gzip 머리가 잘렸다')
    out = inflate.inflate_raw(src[pos:-8])
    crc = int.from_bytes(src[-8:-4], 'little')
    size = int.from_bytes(src[-4:], 'little')
    if checksums.crc32(out) != crc:
        raise ValueError('CRC-32 가 다르다')
    if (len(out) & 0xFFFFFFFF) != size:
        raise ValueError('ISIZE 가 푼 길이와 다르다')
    return out
