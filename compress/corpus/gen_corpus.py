# -*- coding: utf-8 -*-
"""시험 자료(코퍼스)를 만든다. 씨앗이 고정이라 늘 같은 파일이 나온다.

    python3 corpus/gen_corpus.py          # 만들고 MANIFEST.txt 를 쓴다
    python3 corpus/gen_corpus.py --check  # 만들지 않고 대조만 한다

왜 코퍼스를 따로 두는가: 압축률은 "무엇을 넣었는가" 로 꾸밀 수 있다.
잘 나오는 파일만 골라 자랑하지 않으려면 재는 대상을 먼저 못 박아야 한다.
이 덱의 모든 비율·속도 숫자는 여기서 나온 파일에서만 나온다.

왜 파이썬 난수를 안 쓰는가: random.Random 의 출력은 파이썬 판이 바뀌면
달라질 수 있다. 코퍼스가 달라지면 골든 벡터가 통째로 무효가 된다. 그래서
난수는 xorshift64* 를 직접 구현했다 — 스무 줄이고 늘 같은 값을 낸다.

파일 열셋의 의도는 corpus/README.md 에 적어 두었다.
시간·공간 모두 O(만드는 바이트 수).
"""
import hashlib
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)                    # compress/
REPO = os.path.dirname(BASE)                    # treasure_house/

SEED = 0x2545F4914F6CDD1D
MASK64 = (1 << 64) - 1

# 한국어 산문을 뽑아 올 문서들. 끝난 문서만 고른다 — 계속 고쳐지는
# 문서를 쓰면 코퍼스가 조용히 바뀌고 골든 벡터가 통째로 무효가 된다.
KOREAN_DOCS = [
    'github-actions-book.md',
    'Linux_명령어_핸드북.md',
    'ripgrep 가이드.md',
    'Go 심화.md',
]
KOREAN_BYTES = 40000
ENGLISH_BYTES = 61000
# 영문은 이 덱 자신의 명세서다. SPEC.md 는 확정되면 안 바뀌고,
# PLAN.md 는 진행 로그만 뒤에 붙으므로 그 앞까지는 고정이다.
PLAN_CUT = '## Progress log'


class Rng:
    """xorshift64* — 씨앗 하나로 정해지는 난수. 언어·판본과 무관하다."""

    def __init__(self, seed):
        self.s = seed & MASK64

    def next_u64(self):
        x = self.s
        x ^= (x >> 12)
        x = (x ^ (x << 25)) & MASK64
        x ^= (x >> 27)
        self.s = x
        return (x * 0x2545F4914F6CDD1D) & MASK64

    def bytes(self, n):
        out = bytearray()
        while len(out) < n:
            out += self.next_u64().to_bytes(8, 'little')
        return bytes(out[:n])

    def below(self, n):
        return self.next_u64() % n


def read(path):
    return io.open(path, encoding='utf-8').read()


def cut_utf8(text, nbytes):
    """바이트 수로 자르되 글자 한가운데서 자르지 않는다."""
    raw = text.encode('utf-8')[:nbytes]
    while raw:
        try:
            raw.decode('utf-8')
            return raw
        except UnicodeDecodeError:
            raw = raw[:-1]
    return b''


FENCE = re.compile(r'^```')
MDSYM = re.compile(r'[`*_#>|]|\[|\]|\(https?://[^)]*\)')


def prose(text):
    """마크다운에서 산문만 남긴다 — 코드 블록·표·기호를 걷어낸다.

    코드가 섞이면 '한국어 산문의 압축률' 이 아니라 '한국어와 코드를 섞은
    것의 압축률' 이 된다. 소스 코드는 source.go 가 따로 맡는다.
    """
    out, infence = [], False
    for line in text.split('\n'):
        if FENCE.match(line):
            infence = not infence
            continue
        if infence:
            continue
        s = MDSYM.sub('', line).strip()
        if len(s) < 12:                  # 제목·표 줄·빈 줄은 버린다
            continue
        if s.count('|') or s.startswith('---'):
            continue
        out.append(s)
    return '\n'.join(out) + '\n'


def gen_zeros(n):
    """한 가지 기호만 있는 파일. 허프만의 1-기호 트리, BWT 의 "모든
    회전이 같다", RLE 의 최대 런을 한꺼번에 밟는다."""
    return b'\x00' * n


def gen_abab(n):
    """LZW 의 KwKwK 자리를 강제한다 — 부호화기가 방금 만든 항목을
    복호기가 아직 모르는 그 한 순간이다."""
    return (b'ab' * ((n + 1) // 2))[:n]


def gen_runs(rng):
    """런 길이의 경계만 모아 놓은 파일.

    PackBits 는 런 128 에서 제어 바이트가 꽉 차고, LZSS 는 일치 길이 258
    에서 꽉 찬다. 그 바로 앞뒤(127·128·129, 257·258·259)를 다 넣는다.
    런이 2 인 자리도 넣는다 — 문턱이 3 이라 리터럴로 나가야 하는 자리다.
    """
    out = bytearray()
    for ch, n in ((0x41, 127), (0x42, 128), (0x43, 129),
                  (0x44, 257), (0x45, 258), (0x46, 259),
                  (0x47, 2), (0x48, 3), (0x49, 1)):
        out += bytes([ch]) * n
    # 리터럴만 128·129 바이트 — 리터럴 묶음의 상한을 밟는다
    out += bytes((i * 37 + 11) & 0xFF for i in range(128))
    out += bytes((i * 53 + 7) & 0xFF for i in range(129))
    out += b'\x00' * 300
    out += rng.bytes(256)
    return bytes(out)


def gen_alphabet(rng):
    """256가지 기호가 모두 나오는 파일. 허프만 표가 꽉 차고, 길이도
    고르게 갈린다 — 128바이트 헤더가 통째로 쓰이는 유일한 경우다."""
    out = bytearray(range(256))
    out += bytes(reversed(range(256)))
    pool = bytearray()
    for v in range(256):
        pool += bytes([v]) * 16
    # 피셔–예이츠. 섞는 순서까지 씨앗으로 정해진다.
    for i in range(len(pool) - 1, 0, -1):
        j = rng.below(i + 1)
        pool[i], pool[j] = pool[j], pool[i]
    return bytes(out + pool)


def gen_boundary(rng, dist):
    """창 경계를 밟는 파일. 앞뒤에 같은 64바이트 표식을 두고, 그 사이를
    거리 dist 가 되도록 채운다.

    dist = 32768 이면 창 안쪽의 마지막 한 칸이라 반드시 일치가 잡혀야
    하고, 32769 면 한 칸 바깥이라 절대 잡히면 안 된다. 두 파일의 압축
    크기 차이가 곧 "창 크기" 라는 말의 뜻이다. 파일 이름의 숫자는 파일
    크기가 아니라 이 거리를 가리킨다.
    """
    mark = rng.bytes(64)
    # 채움은 기호 16개짜리 저엔트로피 바이트다. 난수로 채우면 DEFLATE 가
    # 그 구간을 통째로 stored 블록으로 내보내고, stored 블록에는 일치가
    # 아예 없어서 창 경계를 시험하지 못한다.
    fill = bytearray()
    while len(fill) < dist - len(mark):
        fill.append(b'0123456789abcdef'[rng.below(16)])
    return mark + bytes(fill[:dist - len(mark)]) + mark


def gen_mixed(rng, total):
    """성격이 다른 구간을 이어 붙인 1 MiB. 한 파일 안에서 블록마다 다른
    선택을 해야 하는 부호화기(DEFLATE 의 블록 종류 고르기)를 흔든다."""
    k = 1024
    parts = []
    parts.append(b'\x00' * (128 * k))                    # 0 — RLE 천국
    parts.append(rng.bytes(128 * k))              # 난수 — 줄지 않는다
    block = rng.bytes(4 * k)                             # 먼 거리 반복
    parts.append(block * 64)
    ctr = bytearray()                             # 증가하는 32비트 수
    for i in range(32 * k):
        ctr += (i & 0xFFFFFFFF).to_bytes(4, 'little')
    parts.append(bytes(ctr))
    runs = bytearray()                            # 길이가 제각각인 런
    while len(runs) < 128 * k:
        runs += bytes([rng.below(256)]) * (1 + rng.below(200))
    parts.append(bytes(runs[:128 * k]))
    low = bytearray()                             # 기호 16개짜리 난수
    while len(low) < 128 * k:
        low.append(b'0123456789abcdef'[rng.below(16)])
    parts.append(bytes(low))
    text = bytearray()                            # 영문처럼 보이는 것
    letters = b'abcdefghijklmnopqrstuvwxyz'
    while len(text) < total:
        text.append(letters[rng.below(26)])
        if rng.below(7) == 0:
            text.append(0x20)
    out = b''.join(parts)
    return (out + bytes(text))[:total]


def gen_korean():
    """한국어 산문 40 KB. 이 저장소의 끝난 문서에서 산문만 걷어 온다.

    왜 지어내지 않는가: 만들어 낸 문장은 어휘가 좁아 압축이 실제보다
    훨씬 잘 된다. 그 숫자를 덱에 실으면 거짓말이 된다. 한글은 UTF-8 에서
    글자당 3바이트이고, 그 3바이트 중 앞 두 바이트가 거의 고정이라
    바이트 엔트로피가 낮다 — 이걸 보이려면 진짜 글이 있어야 한다.
    """
    text = []
    for name in KOREAN_DOCS:
        path = os.path.join(REPO, name)
        if not os.path.exists(path):
            sys.exit('코퍼스 원본이 없다: %s' % name)
        text.append(prose(read(path)))
    return cut_utf8('\n'.join(text), KOREAN_BYTES)


def gen_english():
    """영문 산문 61 KB — 이 덱 자신의 명세서(SPEC.md + PLAN.md 앞부분).

    저장소 안에 영문 장문이 이 둘뿐이라 그렇기도 하지만, 마침 맞는
    자료이기도 하다. 표·코드·산문이 섞인 기술 문서는 DEFLATE 가 가장
    흔하게 만나는 종류의 입력이다.
    """
    spec = read(os.path.join(BASE, 'SPEC.md'))
    plan = read(os.path.join(BASE, 'PLAN.md'))
    cut = plan.find(PLAN_CUT)
    if cut < 0:
        sys.exit('PLAN.md 에서 진행 로그 표시를 못 찾았다')
    return cut_utf8(spec + '\n' + plan[:cut], ENGLISH_BYTES)


# 진짜 소스 파일 하나. 손으로 쓴 코드가 어떤 모양인지가 필요해서,
# 만들어 낸 것이 아니라 이 저장소에서 이미 돌아가는 파일을 가져온다.
GO_SRC = os.path.join(REPO, 'keycloak_ad', 'ldap', 'ber', 'ber.go')


def build(rng):
    """(이름, 바이트) 목록. 순서가 곧 corpus/README.md 의 표 순서다."""
    return [
        ('empty.bin', b''),
        ('one.bin', b'A'),
        ('zeros_64k.bin', gen_zeros(65536)),
        ('random_64k.bin', rng.bytes(65536)),
        ('abab_4k.txt', gen_abab(4096)),
        ('runs.bin', gen_runs(rng)),
        ('alphabet.bin', gen_alphabet(rng)),
        ('boundary_32768.bin', gen_boundary(rng, 32768)),
        ('boundary_32769.bin', gen_boundary(rng, 32769)),
        ('korean_utf8.txt', gen_korean()),
        ('english.txt', gen_english()),
        ('source.go', io.open(GO_SRC, 'rb').read()),
        ('mixed_1m.bin', gen_mixed(rng, 1024 * 1024)),
    ]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def manifest(files):
    """만든 파일과 그 원본의 지문. 원본이 바뀌면 여기서 드러난다.

    코퍼스가 조용히 바뀌는 것이 이 프로젝트에서 가장 나쁜 사고다 —
    골든 벡터가 통째로 무효가 되는데 아무 소리도 안 나기 때문이다.
    """
    rows = ['# gen_corpus.py 가 만든 파일과 그 지문 (SHA-256)',
            '# 원본이 바뀌면 아래 지문이 달라진다 — 그때는 골든 벡터를',
            '# 다시 만들어야 하고, 왜 바뀌었는지 커밋에 적어야 한다.',
            '']
    for name, data in files:
        rows.append('%-20s %10d  %s' % (name, len(data), sha(data)))
    rows.append('')
    rows.append('# 바깥에서 가져온 원본')
    srcs = [os.path.join(REPO, n) for n in KOREAN_DOCS]
    srcs += [os.path.join(BASE, 'SPEC.md'),
             os.path.join(BASE, 'PLAN.md'), GO_SRC]
    for p in srcs:
        rel = os.path.relpath(p, REPO)
        raw = io.open(p, 'rb').read()
        if os.path.basename(p) == 'PLAN.md':
            raw = raw[:raw.find(PLAN_CUT.encode())]
            rel += ' (진행 로그 앞까지)'
        rows.append('%-40s %s' % (rel, sha(raw)))
    return '\n'.join(rows) + '\n'


def main(argv):
    rng = Rng(SEED)
    files = build(rng)
    check = '--check' in argv
    bad = 0
    for name, data in files:
        path = os.path.join(HERE, name)
        if check:
            if not os.path.exists(path):
                print('  없음 %s' % name)
                bad += 1
            elif io.open(path, 'rb').read() != data:
                print('  다름 %s' % name)
                bad += 1
        else:
            io.open(path, 'wb').write(data)
    text = manifest(files)
    mpath = os.path.join(HERE, 'MANIFEST.txt')
    if check:
        if not os.path.exists(mpath) or read(mpath) != text:
            print('  다름 MANIFEST.txt')
            bad += 1
    else:
        io.open(mpath, 'w', encoding='utf-8', newline='\n').write(text)
    total = sum(len(d) for _, d in files)
    print('코퍼스 %d개 파일 · %d 바이트' % (len(files), total))
    if check:
        print('대조 결과 어긋남 %d건' % bad)
        return 1 if bad else 0
    for name, data in files:
        print('  %-20s %9d' % (name, len(data)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
