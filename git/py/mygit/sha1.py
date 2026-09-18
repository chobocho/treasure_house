# -*- coding: utf-8 -*-
"""SHA-1 을 손으로 (SPEC.md §2 · FIPS 180-4).

git 의 모든 객체 이름이 이 함수의 출력이다. 표준 라이브러리의
hashlib 을 부르면 한 줄이지만, 그러면 "40글자 이름이 어디서 오나" 가
블랙박스로 남는다. 그래서 다섯 언어가 모두 같은 80라운드를 직접
돈다. hashlib 은 시험에서 답을 맞춰 볼 때만 쓴다.

한 블록(64바이트) = 80라운드, 전체 O(n) 시간, O(1) 추가 공간.
파이썬 정수는 넘치지 않으므로 32비트 덧셈을 & MASK 로 흉내 낸다.
"""
import struct

MASK = 0xffffffff
# 초기값과 라운드 상수 — FIPS 180-4 §5.3.1·§4.2.1
H0 = (0x67452301, 0xefcdab89, 0x98badcfe, 0x10325476, 0xc3d2e1f0)
K = (0x5a827999, 0x6ed9eba1, 0x8f1bbcdc, 0xca62c1d6)


def _rotl(x, n):
    return ((x << n) | (x >> (32 - n))) & MASK


def _compress(h, block):
    """64바이트 한 블록으로 상태 다섯 개를 갱신한다."""
    w = list(struct.unpack('>16I', block))
    for t in range(16, 80):
        w.append(_rotl(w[t - 3] ^ w[t - 8] ^ w[t - 14] ^ w[t - 16], 1))
    a, b, c, d, e = h
    for t in range(80):
        if t < 20:
            f, k = (b & c) | (~b & d), K[0]
        elif t < 40:
            f, k = b ^ c ^ d, K[1]
        elif t < 60:
            f, k = (b & c) | (b & d) | (c & d), K[2]
        else:
            f, k = b ^ c ^ d, K[3]
        tmp = (_rotl(a, 5) + (f & MASK) + e + k + w[t]) & MASK
        a, b, c, d, e = tmp, a, _rotl(b, 30), c, d
    return tuple((x + y) & MASK for x, y in zip(h, (a, b, c, d, e)))


class Sha1(object):
    """스트리밍 SHA-1. 인덱스와 팩의 끝 체크섬을 파일을 읽어 가며
    셀 때 쓴다 — 전체를 한 번에 메모리에 올리지 않아도 된다."""

    def __init__(self):
        self._h = H0
        self._buf = b''
        self._len = 0

    def update(self, data):
        self._len += len(data)
        buf = self._buf + data
        whole = len(buf) - len(buf) % 64
        h = self._h
        for k in range(0, whole, 64):
            h = _compress(h, buf[k:k + 64])
        self._h = h
        self._buf = buf[whole:]
        return self

    def digest(self):
        """덧붙임: 0x80, 0 들, 비트 길이(빅 엔디언 64비트).

        상태를 건드리지 않는 사본에서 마무리하므로 두 번 불러도 같다.
        55바이트까지는 덧붙임이 한 블록에, 56바이트부터는 두 블록에
        들어간다 — 시험이 그 경계를 촘촘히 본다.
        """
        tail = self._buf + b'\x80'
        tail += b'\0' * ((56 - len(tail)) % 64)
        tail += struct.pack('>Q', (self._len * 8) & (2 ** 64 - 1))
        h = self._h
        for k in range(0, len(tail), 64):
            h = _compress(h, tail[k:k + 64])
        return struct.pack('>5I', *h)

    def hexdigest(self):
        return self.digest().hex()


def sha1(data):
    """바이트열의 SHA-1, 20바이트."""
    return Sha1().update(data).digest()


def sha1_hex(data):
    """소문자 16진 40글자 — git 이 화면에 찍는 객체 이름의 꼴."""
    return sha1(data).hex()
