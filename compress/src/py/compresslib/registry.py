# -*- coding: utf-8 -*-
"""알고리즘 이름 → 부호기·복호기. 이름이 곧 golden/ 의 디렉터리다.

한 자리에 모아 두는 이유: 골든 벡터 만들기, 5×5 교차 복호, 벤치마크,
명령줄 도구가 전부 같은 목록을 봐야 한다. 어딘가 하나가 빠지면 그 모듈만
조용히 검증 밖으로 나간다. 다섯 언어 모두 같은 이름·같은 순서로 둔다.
"""
from compresslib import (ans, bitio, bwt, bzip2dec, deflate, huffman,
                         intcode, lz4block, lzss, lzw, mtf, rangecoder,
                         rle)

# 순서가 곧 배우는 순서다 (PLAN.md §3). Tier 1 뒤에 Tier 2 가 온다.
# ORDER 는 **부호기가 있는** 모듈만이다 — 골든 벡터와 파서티가 이 목록을
# 돈다.
ORDER = ['bitio', 'intcode', 'rle', 'mtf', 'huffman',
         'lzss', 'lzw', 'rangecoder', 'bwt', 'deflate',
         'ans', 'lz4block']

# 복호기만 있는 모듈 (PLAN.md §0.4). 골든 벡터가 없다 — 우리가 만들지
# 않은 파일, 즉 **진짜 도구가 만든 파일** 을 다섯 언어가 같게 푸는 것이
# 시험이다.
DECODE_ONLY = ['bzip2dec']

ALL = ORDER + DECODE_ONLY

MODULES = {
    'bitio': bitio,
    'intcode': intcode,
    'rle': rle,
    'mtf': mtf,
    'huffman': huffman,
    'lzss': lzss,
    'lzw': lzw,
    'rangecoder': rangecoder,
    'bwt': bwt,
    'deflate': deflate,
    'ans': ans,
    'lz4block': lz4block,
    'bzip2dec': bzip2dec,
}


def encode(algo, data):
    if algo in DECODE_ONLY:
        raise ValueError('%s 는 복호기만 있다' % algo)
    return MODULES[algo].encode(data)


def decode(algo, data):
    return MODULES[algo].decode(data)
