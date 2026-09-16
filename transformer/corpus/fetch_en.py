# -*- coding: utf-8 -*-
"""영어 말뭉치 받기 — tinyshakespeare 의 앞부분.

    python3 corpus/fetch_en.py           # corpus/en/shakespeare.txt
    python3 corpus/fetch_en.py --check   # 받은 원본의 해시가 맞나

왜 영어도 싣나 (PLAN.md §9 결정 3): 한글 음절은 UTF-8 로 세 바이트,
영어 글자는 한 바이트다. 같은 바이트 BPE 가 두 언어에서 어휘를 어떻게
쓰는지 나란히 보려면 영어 쪽이 있어야 한다.

셰익스피어의 희곡은 공유저작물이다. 원본 파일(약 1.1 MB)을 통째로
받아 SHA-256 을 확인한 뒤, 말뭉치 크기 예산 때문에 앞 LIMIT 바이트
안의 마지막 줄바꿈까지만 싣는다. 시간 O(파일 크기).
"""
import hashlib
import io
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
URL = ('https://raw.githubusercontent.com/karpathy/char-rnn/master/'
       'data/tinyshakespeare/input.txt')
# 2026-09-16 에 받아 찍은 값. 원본이 바뀌면 여기서 멈춘다.
SHA256 = ('86c4e6aa9db7c042ec79f339dcb96d42'
          'b0075e16b8fc2e86bf0ca57e2dc565ed')
LIMIT = 300000
DST = os.path.join(HERE, 'en', 'shakespeare.txt')
UA = 'treasure_house-deck/1.0 (+github.com/chobocho/treasure_house)'


def fetch():
    req = urllib.request.Request(URL, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def cut(raw):
    """LIMIT 바이트 안의 마지막 줄바꿈까지. 원본은 ASCII 다."""
    head = raw[:LIMIT]
    return head[:head.rfind(b'\n') + 1]


def main(argv):
    raw = fetch()
    digest = hashlib.sha256(raw).hexdigest()
    if SHA256 and digest != SHA256:
        print('  ✗ 원본이 바뀌었다: %s' % digest)
        return 1
    body = cut(raw)
    if '--check' in argv:
        same = (os.path.exists(DST)
                and io.open(DST, 'rb').read() == body)
        print('원본 %d바이트 sha256 %s — 실린 것과 %s'
              % (len(raw), digest[:16], '같다' if same else '다르다'))
        return 0 if same else 1
    if not os.path.isdir(os.path.dirname(DST)):
        os.makedirs(os.path.dirname(DST))
    with io.open(DST, 'wb') as f:
        f.write(body)
    print('  en/shakespeare.txt %d바이트 (원본 %d · sha256 %s)'
          % (len(body), len(raw), digest))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
