# -*- coding: utf-8 -*-
"""zlib 겉옷 (SPEC.md §3) — 느슨한 객체와 팩 항목이 입는 옷.

Python 은 표준 zlib 을 쓴다(SPEC.md §3.1 의 표). 이 모듈이 따로 있는
까닭은 둘이다. 하나, 다섯 언어가 같은 이름(compress·decompress·
decompress_prefix·adler32)으로 부르게 하려고 — C++ 은 이 자리를 손으로
짠다. 둘, 팩 안에서는 "스트림이 몇 바이트에서 끝나는가" 가 필요한데
zlib.decompress 는 그것을 알려 주지 않는다.
"""
import zlib as _z

from mygit import GitError

LEVEL = 1          # git 의 느슨한 객체 기본값과 같은 "가장 빠르게"


def compress(data):
    return _z.compress(data, LEVEL)


def decompress_prefix(data, start=0):
    """data[start:] 에서 zlib 스트림 하나를 풀어 (바이트, 먹은 수).

    먹은 수에는 머리 2바이트와 Adler-32 꼬리 4바이트가 들어간다 —
    다음 팩 항목은 정확히 거기서 시작한다. O(스트림 길이).
    """
    d = _z.decompressobj()
    try:
        out = d.decompress(data[start:])
    except _z.error:
        raise GitError('fatal: mygit: corrupt zlib stream')
    if not d.eof:
        raise GitError('fatal: mygit: truncated zlib stream')
    used = len(data) - start - len(d.unused_data)
    return out, used


def decompress(data):
    """스트림 하나를 끝까지. 뒤에 남는 바이트가 있으면 오류다."""
    out, used = decompress_prefix(data)
    if used != len(data):
        raise GitError('fatal: mygit: garbage after zlib stream')
    return out


def adler32(data):
    return _z.adler32(data) & 0xffffffff
