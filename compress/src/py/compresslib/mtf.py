# -*- coding: utf-8 -*-
"""move-to-front — SPEC §4.

방금 본 바이트를 표의 맨 앞으로 옮긴다. 그러면 "최근에 본 것" 이 작은
숫자가 되고, 같은 바이트가 몰려 있는 열은 0 이 줄줄이 나오는 열이 된다.
BWT 뒤에 붙이면 그 성질이 극대화된다 — 10부의 본론이 그것이다.

이것만으로는 한 바이트도 안 준다. 길이가 그대로인 **치환**이기 때문이다.
줄이는 일은 그 다음에 오는 0런 부호와 허프만이 한다.

옮기는 것이지 바꿔치는 것이 아니다. 바꿔치기(swap)도 자기들끼리는 왕복이
되기 때문에, 골든 벡터가 없으면 다섯 언어가 갈라진 줄도 모른다.

표를 그냥 리스트로 둔다 — 최악 O(n·256). 이 덱이 다루는 크기에서는
충분하고, 무엇보다 **덱에 실린 코드가 곧 숫자를 낸 코드** 여야 한다.
더 빠른 변형(자기 균형 트리·비트 벡터)은 10부에서 말로만 다룬다.
"""
from compresslib import varint

ALPHABET = 256


def transform(src):
    table = list(range(ALPHABET))
    out = bytearray()
    for b in src:
        i = table.index(b)
        out.append(i)
        if i:
            del table[i]
            table.insert(0, b)
    return bytes(out)


def inverse(src):
    table = list(range(ALPHABET))
    out = bytearray()
    for i in src:
        b = table[i]
        out.append(b)
        if i:
            del table[i]
            table.insert(0, b)
    return bytes(out)


def encode(src):
    return varint.put(len(src)) + transform(src)


def decode(src):
    n, pos = varint.get_length(src)
    body = src[pos:]
    if len(body) != n:
        raise ValueError('몸통 길이가 헤더와 다르다: %d != %d'
                         % (len(body), n))
    return inverse(body)
