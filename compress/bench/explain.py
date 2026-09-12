# -*- coding: utf-8 -*-
"""작은 입력 하나를 골라 **바이트를 하나씩 설명한다**.

    python3 bench/explain.py            # out/explain_*.txt 를 다시 쓴다
    python3 bench/explain.py huffman    # 화면으로 하나만

덱의 형식 설명은 표와 그림으로 한다. 그런데 표를 아무리 잘 그려도
"그래서 진짜 파일이 어떻게 생겼나" 는 안 보인다. 이 도구는 실제 출력의
바이트에 주석을 붙여, 표와 실물 사이의 마지막 한 칸을 메운다.

주석은 **부호기를 다시 돌려서** 만든다. 손으로 적으면 형식을 고칠 때
조용히 어긋난다 — 이 저장소의 다른 캡처와 같은 규칙이다.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
OUT = os.path.join(BASE, 'out')
sys.path.insert(0, os.path.join(BASE, 'src', 'py'))

from compresslib import bitio                       # noqa: E402
from compresslib import deflate                     # noqa: E402
from compresslib import huffman                     # noqa: E402
from compresslib import lz4block                    # noqa: E402
from compresslib import lzss                        # noqa: E402
from compresslib import rle                         # noqa: E402
from compresslib import varint                      # noqa: E402


def hexdump(data, width=16):
    """주석 없는 순수 덤프. 자리를 확인할 수 있게 자리 번호를 붙인다."""
    out = []
    for i in range(0, len(data), width):
        chunk = data[i:i + width]
        hx = ' '.join('%02X' % b for b in chunk)
        txt = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        out.append('%04X  %-47s  %s' % (i, hx, txt))
    return out


def note(pos, data, n, text):
    """바이트 n개에 한 줄 설명을 붙인다. 긴 것은 앞 여섯만 보인다."""
    part = data[pos:pos + n]
    hx = ' '.join('%02X' % b for b in part[:6])
    if n > 6:
        hx += ' …'
    return '  %04X  %-23s %s' % (pos, hx, text)


def explain_rle():
    src = b'aaaaabcdeffffff'
    enc = rle.encode(src)
    lines = ['== rle — %r (%d바이트) ==' % (src.decode(), len(src)),
             '결과 %d바이트' % len(enc), '']
    lines += hexdump(enc)
    lines.append('')
    lines.append('바이트마다:')
    pos = 0
    n, pos2 = varint.get(enc, 0)
    lines.append(note(pos, enc, pos2 - pos,
                      '원본 길이 %d (varint)' % n))
    pos = pos2
    while pos < len(enc):
        ctrl = enc[pos]
        if ctrl > 128:
            lines.append(note(pos, enc, 2, '런 — %r 를 %d번 (257-%d)'
                              % (chr(enc[pos + 1]), 257 - ctrl, ctrl)))
            pos += 2
        else:
            k = ctrl + 1
            body = enc[pos + 1:pos + 1 + k]
            lines.append(note(pos, enc, 1 + k, '리터럴 %d개 — %r'
                              % (k, body.decode('latin1'))))
            pos += 1 + k
    return lines


def explain_huffman():
    src = b'abracadabra'
    enc = huffman.encode(src)
    freqs = [0] * 256
    for b in src:
        freqs[b] += 1
    lengths = huffman.code_lengths(freqs, 15)
    codes = huffman.canonical_codes(lengths)
    lines = ['== huffman — %r (%d바이트) ==' % (src.decode(), len(src)),
             '결과 %d바이트 — 표 128바이트가 대부분이다' % len(enc), '']
    lines.append('부호표:')
    for s in sorted(set(src)):
        lines.append('  %r  %d회  길이 %d  부호 %s'
                     % (chr(s), freqs[s], lengths[s],
                        bin(codes[s])[2:].rjust(lengths[s], '0')))
    lines.append('')
    n, pos = varint.get(enc, 0)
    lines.append(note(0, enc, pos, '원본 길이 %d' % n))
    lines.append(note(pos, enc, 4, '부호 길이 표의 앞 4바이트'))
    lines.append('        …')
    body = pos + huffman.TABLE_BYTES
    lines.append(note(body, enc, len(enc) - body, '본문 비트'))
    bits = ''.join(bin(b)[2:].rjust(8, '0') for b in enc[body:])
    lines.append('')
    lines.append('본문 비트열: ' + bits)
    at = 0
    shown = []
    for ch in src:
        shown.append('%s=%s' % (chr(ch), bits[at:at + lengths[ch]]))
        at += lengths[ch]
    lines.append('  ' + ' '.join(shown))
    lines.append('  남은 %d비트는 채움(0)' % (len(bits) - at))
    return lines


def explain_lzss():
    src = b'abcabcabcabd'
    enc = lzss.encode(src)
    tokens = lzss.find_tokens(src)
    lines = ['== lzss — %r (%d바이트) ==' % (src.decode(), len(src)),
             '결과 %d바이트' % len(enc), '']
    lines += hexdump(enc)
    lines.append('')
    n, pos = varint.get(enc, 0)
    lines.append(note(0, enc, pos, '원본 길이 %d' % n))
    flag = enc[pos]
    lines.append(note(pos, enc, 1, '플래그 %s — 1이면 일치'
                      % bin(flag)[2:].rjust(8, '0')))
    at = pos + 1
    for t in tokens:
        if isinstance(t, tuple):
            ln, dist = t
            lines.append(note(at, enc, 3, '일치 — 길이 %d 거리 %d'
                              % (ln, dist)))
            at += 3
        else:
            lines.append(note(at, enc, 1, '리터럴 %r' % chr(t)))
            at += 1
    return lines


def explain_lz4():
    # 12바이트로는 일치가 안 나온다 — 형식이 그렇게 정해 뒀다.
    # 규칙을 보여 주려고 짧은 것과 긴 것을 둘 다 싣는다.
    src = b'abcabcabcabd' * 3
    enc = lz4block.encode(src)
    lines = ['== lz4block — %r (%d바이트) =='
             % (src.decode()[:24] + '…', len(src)),
             '결과 %d바이트' % len(enc), '',
             '짧은 입력(12바이트)에서는 일치가 아예 안 나온다 —',
             '마지막 5바이트는 리터럴, 일치는 끝에서 12바이트 안쪽',
             '금지라는 규칙 때문이다 (§14.2). 그래서 36바이트로 잰다.',
             '']
    lines += hexdump(enc)
    lines.append('')
    n, pos = varint.get(enc, 0)
    lines.append(note(0, enc, pos, '원본 길이 %d' % n))
    block = enc[pos:]
    seqs = lz4block.parse_sequences(block)
    at = pos
    for lit, match in seqs:
        tok = block[at - pos]
        lines.append(note(at, enc, 1,
                          '토큰 %02X — 리터럴 %d · 일치 %s'
                          % (tok, len(lit),
                             ('%d' % match[1]) if match else '없음')))
        at += 1
        if len(lit) >= 15:
            at += 1
        lines.append(note(at, enc, len(lit),
                          '리터럴 %r' % lit.decode('latin1')))
        at += len(lit)
        if match:
            lines.append(note(at, enc, 2, '오프셋 %d (리틀엔디언)'
                              % match[0]))
            at += 2
    return lines


def explain_deflate():
    src = b'abababababababab'
    enc = deflate.encode(src)
    lines = ['== deflate — %r (%d바이트) ==' % (src.decode(), len(src)),
             '결과 %d바이트' % len(enc), '']
    lines += hexdump(enc)
    lines.append('')
    bits = ''.join(bin(b)[2:].rjust(8, '0')[::-1] for b in enc)
    lines.append('LSB 먼저로 편 비트열 (앞 24비트):')
    lines.append('  ' + bits[:24])
    lines.append('  %s = BFINAL' % bits[0])
    lines.append('  %s = BTYPE (%s)'
                 % (bits[1:3][::-1],
                    {'00': '저장', '01': '고정', '10': '동적'}
                    .get(bits[1:3][::-1], '?')))
    lines.append('')
    lines.append('토큰 (LZ77 파서의 출력):')
    for t in deflate.parse(src):
        if isinstance(t, tuple):
            lines.append('  일치 길이 %d 거리 %d' % t)
        else:
            lines.append('  리터럴 %r' % chr(t))
    return lines


def explain_bitio():
    src = b'AB'
    enc = bitio.encode(src)
    lines = ['== bitio — %r (%d바이트) ==' % (src.decode(), len(src)),
             '결과 %d바이트 — 앞에 0비트 셋이 들어간다' % len(enc), '']
    lines += hexdump(enc)
    lines.append('')
    n, pos = varint.get(enc, 0)
    lines.append(note(0, enc, pos, '원본 길이 %d' % n))
    bits = ''.join(bin(b)[2:].rjust(8, '0') for b in enc[pos:])
    lines.append('  비트열 ' + bits)
    lines.append('  %s = 채움 3비트 (SPEC §1.4)' % bits[:3])
    at = 3
    for b in src:
        lines.append('  %s = %r (0x%02X)'
                     % (bits[at:at + 8], chr(b), b))
        at += 8
    lines.append('  %s = 마지막 바이트의 남은 자리 (0)' % bits[at:])
    return lines


MAKERS = [('bitio', explain_bitio), ('rle', explain_rle),
          ('huffman', explain_huffman), ('lzss', explain_lzss),
          ('lz4block', explain_lz4), ('deflate', explain_deflate)]


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    picked = [(n, f) for n, f in MAKERS if not argv or n in argv]
    for name, fn in picked:
        text = '\n'.join(fn()) + '\n'
        if argv:
            print(text)
        else:
            io.open(os.path.join(OUT, 'explain_%s.txt' % name), 'w',
                    encoding='utf-8', newline='\n').write(text)
    if not argv:
        print('  out/explain_*.txt — %d개' % len(picked))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
