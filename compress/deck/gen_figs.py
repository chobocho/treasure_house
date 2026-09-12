# -*- coding: utf-8 -*-
"""도해를 그린다 — 손으로 그리지 않는 이유가 이 파일의 전부다.

    python3 deck/gen_figs.py            # deck/figs/*.svg 를 새로 쓴다
    python3 deck/gen_figs.py --list     # 만드는 목록만

이 덱의 그림 중 상당수는 **숫자가 들어 있는 그림** 이다. 허프만 나무의
가지에 붙은 빈도, BWT 행렬의 줄 순서, 산술 부호기의 구간 경계, 코퍼스
파일의 엔트로피 — 전부 본문의 코드가 실제로 내는 값이다. 손으로 그리면
코드를 고칠 때마다 그림이 조용히 거짓말을 시작한다. 그래서 그림은
`compresslib` 를 불러서 그린다. 코드가 달라지면 그림도 달라진다.

폭 계약: viewBox 는 340 칸이다(다른 덱과 같다). 갤럭시 폴드 접힘
(374px)에서 카드 안쪽이 334px 라 거의 1:1 로 그려지고, 글자 크기 12 가
화면에서도 12px 근처가 된다. 높이는 그림마다 다르다.

색은 head.html 의 CSS 변수를 쓴다. rsvg-convert 로 눈으로 볼 때는
tools/render_figs.sh 가 변수를 literal 로 바꿔 임시 복사본을 만든다 —
덱에 실리는 원본은 변수 그대로다.
"""
import io
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
FIGS = os.path.join(HERE, 'figs')
CORPUS = os.path.join(BASE, 'corpus')
sys.path.insert(0, os.path.join(BASE, 'src', 'py'))

from compresslib import bwt as bwtmod              # noqa: E402
from compresslib import huffman                    # noqa: E402
from compresslib import lossy                      # noqa: E402
from compresslib import lzss                       # noqa: E402
from compresslib import rle                        # noqa: E402

W = 340

MARKER = ('<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5"'
          ' markerWidth="6" markerHeight="6"'
          ' orient="auto-start-reverse">'
          '<path d="M0,0 L10,5 L0,10 z"/></marker></defs>')


def esc(text):
    return (str(text).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;'))


class Svg(object):
    """한 장의 그림. 좌표는 전부 viewBox 340 칸 기준이다."""

    def __init__(self, height, label, marker=False):
        self.h = height
        self.parts = ['<svg class="diag" viewBox="0 0 %d %d" role="img"'
                      ' aria-label="%s">' % (W, height, esc(label))]
        if marker:
            self.parts.append(MARKER)

    def add(self, part):
        self.parts.append(part)
        return self

    def text(self, x, y, s, cls=None, anchor=None, size=None,
             fill=None):
        attrs = ''
        if cls:
            attrs += ' class="%s"' % cls
        if anchor:
            attrs += ' text-anchor="%s"' % anchor
        style = ''
        if size:
            style += 'font-size:%dpx;' % size
        if fill:
            style += 'fill:%s;' % fill
        if style:
            attrs += ' style="%s"' % style
        return self.add('<text x="%g" y="%g"%s>%s</text>'
                        % (x, y, attrs, esc(s)))

    def mono(self, x, y, s, anchor=None, size=11, fill=None):
        """고정폭 글자 — 표와 비트열은 칸이 맞아야 읽힌다."""
        attrs = ' style="font-family:ui-monospace,DeckMono,monospace;'
        attrs += 'font-size:%dpx;' % size
        if fill:
            attrs += 'fill:%s;' % fill
        attrs += '"'
        if anchor:
            attrs += ' text-anchor="%s"' % anchor
        return self.add('<text x="%g" y="%g"%s>%s</text>'
                        % (x, y, attrs, esc(s)))

    def rect(self, x, y, w, h, cls='box', extra=''):
        return self.add('<rect x="%g" y="%g" width="%g" height="%g"'
                        ' class="%s"%s/>' % (x, y, w, h, cls, extra))

    def fill(self, x, y, w, h, colour, opacity=1.0, rx=2):
        return self.add('<rect x="%g" y="%g" width="%g" height="%g"'
                        ' rx="%g" fill="%s" fill-opacity="%g"/>'
                        % (x, y, w, h, rx, colour, opacity))

    def line(self, x1, y1, x2, y2, colour='var(--border)', width=1,
             dash=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ''
        return self.add('<line x1="%g" y1="%g" x2="%g" y2="%g"'
                        ' stroke="%s" stroke-width="%g"%s/>'
                        % (x1, y1, x2, y2, colour, width, d))

    def path(self, d, cls=None, colour=None, width=1.4, fill='none'):
        if cls:
            return self.add('<path d="%s" class="%s"/>' % (d, cls))
        return self.add('<path d="%s" stroke="%s" stroke-width="%g"'
                        ' fill="%s"/>' % (d, colour, width, fill))

    def dump(self):
        return '\n'.join(self.parts + ['</svg>']) + '\n'


FIGURES = []


def figure(name, title):
    """그리는 함수를 목록에 올린다. 이름이 곧 파일 이름이다."""
    def wrap(fn):
        FIGURES.append((name, title, fn))
        return fn
    return wrap


# ------------------------------------------------------- 1부 정보이론
@figure('entropy_binary', '동전 하나의 엔트로피')
def fig_entropy_binary():
    """H(p) = -p log2 p - (1-p) log2 (1-p). 점은 계산해서 찍는다."""
    s = Svg(190, '확률에 따른 이진 엔트로피 곡선')
    x0, y0, w, h = 42, 20, 274, 120
    s.line(x0, y0 + h, x0 + w, y0 + h)
    s.line(x0, y0, x0, y0 + h)
    pts = []
    for i in range(0, 101):
        p = i / 100.0
        if p in (0.0, 1.0):
            hh = 0.0
        else:
            hh = -p * math.log(p, 2) - (1 - p) * math.log(1 - p, 2)
        pts.append('%g,%g' % (x0 + w * p, y0 + h - h * hh))
    s.path('M' + ' L'.join(pts), colour='var(--accent)', width=2)
    # 0.5 에서 1비트. 그 한 점이 "동전 한 번은 1비트" 의 뜻이다.
    s.line(x0 + w / 2, y0, x0 + w / 2, y0 + h,
           'var(--special)', 1, '3 3')
    s.text(x0 + w / 2 + 4, y0 + 12, '1비트', size=11,
           fill='var(--special)')
    for p, lab in ((0.0, '0'), (0.5, '0.5'), (1.0, '1')):
        s.text(x0 + w * p, y0 + h + 14, lab, anchor='middle', size=11)
    s.text(x0 - 6, y0 + 4, '1', anchor='end', size=11)
    s.text(x0 - 6, y0 + h + 4, '0', anchor='end', size=11)
    s.text(x0 + w / 2, 176, 'p — 앞면이 나올 확률', anchor='middle',
           cls='lbl')
    s.text(10, y0 + h / 2, 'H', cls='lbl')
    return s


@figure('entropy_corpus', '코퍼스 파일의 0차 엔트로피')
def fig_entropy_corpus():
    """파일마다 바이트 빈도로 잰 엔트로피. 진짜 파일을 읽어 센다."""
    names = ['zeros_64k.bin', 'abab_4k.txt', 'source.go', 'english.txt',
             'korean_utf8.txt', 'random_64k.bin']
    rows = []
    for n in names:
        data = io.open(os.path.join(CORPUS, n), 'rb').read()
        counts = [0] * 256
        for b in data:
            counts[b] += 1
        total = float(len(data))
        ent = 0.0
        for c in counts:
            if c:
                p = c / total
                ent -= p * math.log(p, 2)
        rows.append((n, ent))
    s = Svg(28 + 24 * len(rows), '파일별 바이트 엔트로피 막대')
    s.text(8, 14, '바이트 하나에 든 정보량 (비트)', cls='lbl')
    x0, w = 116, 176
    for i, (n, ent) in enumerate(rows):
        y = 28 + 24 * i
        s.mono(112, y + 12, n.split('.')[0], anchor='end')
        s.fill(x0, y + 2, w * ent / 8.0, 13, 'var(--accent)', 0.75)
        s.mono(x0 + w * ent / 8.0 + 4, y + 12, '%.2f' % ent,
               fill='var(--muted)')
    s.line(x0 + w, 26, x0 + w, 28 + 24 * len(rows) - 6,
           'var(--bad)', 1, '3 3')
    s.text(W - 4, 14, '← 8비트, 즉 못 줄인다', anchor='end', size=10,
           fill='var(--bad)')
    return s


@figure('kraft', '크래프트 부등식 — 부호가 차지하는 자리')
def fig_kraft():
    """부호 길이 L 은 [0,1) 에서 2^-L 만큼을 가져간다. 합이 1을 넘으면
    그 부호표는 존재할 수 없다 — 자리가 모자라기 때문이다."""
    s = Svg(168, '부호 길이가 구간을 나눠 갖는 그림')
    x0, w = 14, 312
    good = [('A', 1), ('B', 2), ('C', 3), ('D', 3)]
    bad = [('A', 1), ('B', 2), ('C', 2), ('D', 2)]
    for row, (title, table, colour) in enumerate((
            ('된다 — 합 1.0', good, 'var(--ok)'),
            ('안 된다 — 합 1.25', bad, 'var(--bad)'))):
        y = 26 + row * 62
        s.text(x0, y - 8, title, size=11, fill=colour)
        total = sum(2.0 ** -ln for _sym, ln in table)
        # 넘치는 쪽은 줄여서 그린다 — 안 줄이면 마지막 상자가 화면
        # 밖으로 나가 버려서, 정작 보여 주려는 '넘침' 이 안 보인다.
        scale = 1.0 / total if total > 1.0 else 1.0
        at = 0.0
        for sym, ln in table:
            width = w * scale * (2 ** -ln)
            left = x0 + w * scale * at
            s.fill(left, y, max(width - 2, 2), 26, colour, 0.18)
            s.rect(left, y, max(width - 2, 2), 26, 'box')
            mid = left + width / 2
            s.mono(mid, y + 12, sym, anchor='middle')
            s.mono(mid, y + 23, '%d비트' % ln, anchor='middle',
                   size=9, fill='var(--muted)')
            at += 2 ** -ln
        if total > 1.0:
            edge = x0 + w * scale
            s.line(edge, y - 6, edge, y + 32, colour, 1.8)
            s.text(edge, y + 44, '↑ 여기까지가 1.0', anchor='middle',
                   size=11, fill=colour)
            s.text(x0, y + 60, 'D 가 설 자리는 이미 남이 가져갔다',
                   size=11, fill=colour)
    return s


@figure('bitio_pack', 'MSB 우선으로 비트를 바이트에 싣는 그림')
def fig_bitio_pack():
    """비트 순서를 못 박지 않으면 다섯 언어가 갈린다 (SPEC §1.1)."""
    s = Svg(160, '비트가 바이트에 채워지는 순서')
    items = [('3', 2), ('1', 1), ('5', 3), ('0', 4)]
    bits = ''
    for val, ln in items:
        bits += bin(int(val))[2:].rjust(ln, '0')
    bits = bits.ljust(16, '0')
    s.text(10, 16, '쓴 값:  ' + '  '.join('%s(%d비트)' % (v, l)
                                          for v, l in items), size=11)
    x0, cw = 14, 19
    for i, b in enumerate(bits):
        x = x0 + cw * i
        used = i < sum(l for _v, l in items)
        s.rect(x, 30, cw - 2, 22, 'box' if used else 'box off')
        s.mono(x + (cw - 2) / 2, 45, b, anchor='middle')
    at = 0
    for val, ln in items:
        x = x0 + cw * at
        s.line(x, 56, x + cw * ln - 2, 56, 'var(--accent)', 1.6)
        s.mono(x + (cw * ln - 2) / 2, 68, val, anchor='middle',
               fill='var(--accent)')
        at += ln
    s.line(x0 + cw * 8 - 1, 26, x0 + cw * 8 - 1, 56,
           'var(--special)', 1.6)
    s.text(x0 + cw * 4, 104, '첫 바이트', anchor='middle', cls='lbl')
    s.text(x0 + cw * 12, 104, '둘째 바이트', anchor='middle',
           cls='lbl')
    s.text(10, 130, '채우고 남은 자리는 0 — 그래서 빈 입력도', size=11)
    s.text(10, 146, '바이트 하나가 나온다 (SPEC §0.3 의 예외).',
           size=11)
    return s


@figure('varint', 'LEB128 — 이어짐 비트 하나로 길이를 정한다')
def fig_varint():
    """300 을 싣는다. 7비트씩 낮은 자리부터, 맨 앞 비트가 '더 있다'."""
    n = 300
    groups = []
    v = n
    while True:
        groups.append(v & 0x7F)
        v >>= 7
        if not v:
            break
    s = Svg(150, 'LEB128 로 300 을 싣는 그림')
    s.text(10, 16, '값 300 = 0b%s' % bin(n)[2:], size=11)
    x0, bw = 14, 150
    for i, g in enumerate(groups):
        x = x0 + (bw + 12) * i
        more = i + 1 < len(groups)
        s.rect(x, 30, bw, 34, 'box')
        s.line(x + 22, 30, x + 22, 64)
        s.mono(x + 11, 50, '1' if more else '0', anchor='middle',
               fill='var(--special)' if more else 'var(--muted)')
        s.mono(x + 22 + (bw - 22) / 2, 50,
               bin(g)[2:].rjust(7, '0'), anchor='middle')
        s.mono(x + bw / 2, 78, '0x%02X' % (g | (0x80 if more else 0)),
               anchor='middle', fill='var(--muted)')
    s.text(10, 104, '앞 비트 1 = 뒤에 더 있다, 0 = 여기까지.', size=11)
    s.text(10, 120, '낮은 자리를 먼저 싣는다 — 그래야 읽는 쪽이',
           size=11)
    s.text(10, 136, '자리올림을 하며 한 번에 훑을 수 있다.', size=11)
    return s


@figure('zigzag', '지그재그 — 음수를 작은 자연수로')
def fig_zigzag():
    """부호 있는 수를 그대로 varint 에 넣으면 -1 이 10바이트가 된다."""
    s = Svg(130, '지그재그 사상 표')
    vals = [0, -1, 1, -2, 2, -3, 3]
    x0, cw = 40, 40
    s.text(8, 30, '값', cls='lbl')
    s.text(8, 60, 'zig', cls='lbl')
    for i, v in enumerate(vals):
        x = x0 + cw * i
        s.mono(x + cw / 2, 30, str(v), anchor='middle')
        z = (abs(v) * 2 - 1) if v < 0 else v * 2
        s.mono(x + cw / 2, 60, str(z), anchor='middle',
               fill='var(--accent)')
        s.line(x + cw / 2, 36, x + cw / 2, 48, 'var(--border)')
    s.text(10, 88, '음수는 홀수, 양수는 짝수로 간다. 0 근처의 수가',
           size=11)
    s.text(10, 104, '0 근처에 남으므로 varint 한 바이트로 끝난다.',
           size=11)
    s.text(10, 120, '-1 을 그냥 실으면 10바이트다 (SPEC §2.2).',
           size=11, fill='var(--bad)')
    return s


@figure('rice', '골롬–라이스 — k 를 잘못 잡으면 벌을 받는다')
def fig_rice():
    """같은 값 100 을 k 마다 몇 비트로 적는지 실제로 센다."""
    s = Svg(170, 'k 에 따른 Rice 부호 길이')
    s.text(10, 16, '값 100 을 Rice(k) 로 적을 때의 비트 수', size=11)
    x0, y0, bw = 30, 26, 34
    best = None
    for i, k in enumerate(range(0, 8)):
        q = 100 >> k
        bits = q + 1 + k
        if best is None or bits < best[1]:
            best = (k, bits)
        x = x0 + bw * i
        hh = min(bits, 110)
        s.fill(x, y0 + 110 - hh * 110.0 / 110, bw - 6,
               hh * 110.0 / 110, 'var(--accent)', 0.7)
        s.mono(x + (bw - 6) / 2, y0 + 122, 'k=%d' % k, anchor='middle',
               size=9)
        s.mono(x + (bw - 6) / 2, y0 + 106 - hh, str(bits),
               anchor='middle', size=9, fill='var(--muted)')
    s.text(10, 166, 'k=%d 에서 %d비트로 가장 짧다.'
           % (best[0], best[1]), size=11)
    return s


# ----------------------------------------------------- 3·4부 RLE·허프만
@figure('packbits', 'PackBits — 한 바이트로 런과 리터럴을 가른다')
def fig_packbits():
    """제어 바이트를 진짜 부호기에서 뽑는다. 손으로 적으면 틀린다 —
    첫 판에서 실제로 0x82 라고 적었다가 잡혔다 (257-n 이다)."""
    run_tok = rle.pack(b'AAA')
    lit_tok = rle.pack(b'abc')
    s = Svg(170, 'PackBits 토큰 두 종류')
    x0 = 14
    s.rect(x0, 24, 150, 30, 'box')
    s.line(x0 + 46, 24, x0 + 46, 54)
    s.mono(x0 + 23, 43, '0x%02X' % run_tok[0], anchor='middle',
           fill='var(--special)')
    s.mono(x0 + 46 + 52, 43, "'A'", anchor='middle')
    s.text(x0, 70, '런: 257 - 3 = %d' % run_tok[0], size=11)
    s.text(x0, 86, '128 보다 크면 런 (되풀이는 최소 3)', cls='lbl')

    s.rect(x0 + 176, 24, 150, 30, 'box')
    s.line(x0 + 176 + 36, 24, x0 + 176 + 36, 54)
    s.mono(x0 + 176 + 18, 43, '0x%02X' % lit_tok[0], anchor='middle',
           fill='var(--accent)')
    s.mono(x0 + 176 + 36 + 57, 43, "'a' 'b' 'c'", anchor='middle')
    s.text(x0 + 176, 70, '리터럴: 3 - 1 = %d' % lit_tok[0], size=11)
    s.text(x0 + 176, 86, '128 보다 작으면 그대로 싣기', cls='lbl')

    s.text(x0, 116, '머리 하나로 두 가지를 가르는 것이 요점이다.',
           size=11)
    s.text(x0, 132, '따로 깃발 비트를 두면 리터럴마다 붙어', size=11)
    s.text(x0, 148, '늘어나는 입력에서 손해를 본다.', size=11)
    s.text(x0, 166, '제어 128 은 안 쓴다 — 한 입력에 답이 둘이 된다',
           cls='lbl')
    return s


@figure('mtf', 'MTF — 바꿔치기가 아니라 옮기기다')
def fig_mtf():
    """앞으로 옮기기. 방금 본 글자가 다음에도 나오면 0 이 된다."""
    s = Svg(150, 'MTF 표가 움직이는 모습')
    seq = 'bbaac'
    table = ['a', 'b', 'c', 'd']
    rows = []
    for ch in seq:
        i = table.index(ch)
        rows.append((ch, i, ''.join(table)))
        table.insert(0, table.pop(i))
    s.text(10, 16, '입력 %s · 표 시작 abcd' % seq, size=11)
    for k, (ch, i, before) in enumerate(rows):
        y = 30 + 22 * k
        s.mono(14, y + 12, ch, fill='var(--accent)')
        s.mono(34, y + 12, before)
        s.mono(110, y + 12, '→ %d' % i,
               fill='var(--ok)' if i == 0 else 'var(--text)')
    s.text(160, 46, '두 번째 b 는 0 이 된다 —', size=11)
    s.text(160, 62, '방금 앞으로 옮겨졌기 때문이다.', size=11)
    s.text(160, 86, '값 자체는 안 줄어든다. 줄어드는', size=11)
    s.text(160, 102, '것은 분포다 — 0 이 몰리면', size=11)
    s.text(160, 118, '뒤의 엔트로피 부호기가 먹는다.', size=11)
    return s


@figure('huffman_tree', '허프만 나무 — 진짜 빈도로 자란다')
def fig_huffman_tree():
    """문장 하나의 빈도로 package-merge 를 돌려 길이를 얻고,
    그 길이대로 나무를 그린다. 손으로 그린 나무가 아니다."""
    text = b'abracadabra'
    freqs = [0] * 256
    for b in text:
        freqs[b] += 1
    lengths = huffman.code_lengths(freqs, 15)
    used = sorted((lengths[c], c) for c in range(256) if freqs[c])
    depth = max(l for l, _c in used)
    s = Svg(60 + 46 * depth, 'abracadabra 의 허프만 나무')
    s.text(10, 16, "'abracadabra' 의 빈도로 자란 나무", size=11)
    # 캐노니컬 부호를 그대로 좌표로 쓴다 — 0 은 왼쪽, 1 은 오른쪽.
    codes = huffman.canonical_codes(lengths)
    for ln, c in used:
        code = bin(codes[c])[2:].rjust(ln, '0')
        x, span = W / 2.0, W / 4.0
        py_ = 30
        for bit in code:
            nx = x - span if bit == '0' else x + span
            s.line(x, py_, nx, py_ + 40, 'var(--border)', 1.2)
            s.mono((x + nx) / 2 + (-9 if bit == '0' else 3),
                   py_ + 22, bit, size=9, fill='var(--muted)')
            x, py_, span = nx, py_ + 40, span / 2.0
        s.fill(x - 13, py_ - 11, 26, 18, 'var(--accent)', 0.16)
        s.mono(x, py_ + 2, chr(c), anchor='middle')
        s.mono(x, py_ + 16, '%d회 %d비트' % (freqs[c], ln),
               anchor='middle', size=8, fill='var(--muted)')
    s.fill(W / 2.0 - 4, 26, 8, 8, 'var(--accent2)', 0.8, rx=4)
    return s


@figure('canonical', '캐노니컬 — 길이만 보내면 표가 재구성된다')
def fig_canonical():
    """같은 길이는 알파벳 순, 길이가 늘면 왼쪽 자리올림 뒤 << 1."""
    lengths = [0] * 256
    for ch, ln in zip('abcde', (2, 2, 2, 3, 3)):
        lengths[ord(ch)] = ln
    codes = huffman.canonical_codes(lengths)
    s = Svg(150, '캐노니컬 부호 배정 표')
    s.text(10, 16, '길이만 보낸다: a2 b2 c2 d3 e3', size=11)
    x0 = 20
    for i, ch in enumerate('abcde'):
        ln = lengths[ord(ch)]
        y = 32 + 22 * i
        s.mono(x0, y + 12, ch, fill='var(--accent)')
        s.mono(x0 + 24, y + 12, '%d비트' % ln, fill='var(--muted)')
        s.mono(x0 + 80, y + 12, bin(codes[ord(ch)])[2:].rjust(ln, '0'))
    s.text(150, 54, '값을 하나씩 올리다가,', size=11)
    s.text(150, 70, '길이가 늘면 왼쪽으로', size=11)
    s.text(150, 86, '한 칸 민다. 그것뿐이다.', size=11)
    s.text(150, 110, '그래서 부호표를 보낼 때', size=11)
    s.text(150, 126, '길이 목록이면 족하다.', size=11,
           fill='var(--special)')
    return s


# ------------------------------------------- 5·6부 산술·레인지·ANS
@figure('range_interval', '구간이 좁아지는 것이 곧 부호화다')
def fig_range_interval():
    """확률 A .6 / B .3 / C .1 로 'A B A' 를 넣으며 구간을 줄인다."""
    probs = [('A', 0.0, 0.6), ('B', 0.6, 0.9), ('C', 0.9, 1.0)]
    seq = 'ABA'
    s = Svg(56 + 54 * (len(seq) + 1), '구간이 좁아지는 그림')
    x0, w = 14, 312
    lo, hi = 0.0, 1.0
    for step in range(len(seq) + 1):
        y = 30 + 54 * step
        for sym, a, b in probs:
            xa = x0 + w * (lo + (hi - lo) * a)
            xb = x0 + w * (lo + (hi - lo) * b)
            hot = step < len(seq) and sym == seq[step]
            s.fill(xa, y, max(xb - xa - 1, 1), 24,
                   'var(--special)' if hot else 'var(--accent)',
                   0.30 if hot else 0.10)
            if xb - xa > 16:
                s.mono((xa + xb) / 2, y + 16, sym, anchor='middle')
        s.line(x0, y + 24, x0 + w, y + 24)
        s.mono(x0, y + 38, '[%.4f, %.4f)' % (lo, hi), size=9,
               fill='var(--muted)')
        if step < len(seq):
            sym = seq[step]
            a, b = [(a, b) for c, a, b in probs if c == sym][0]
            lo, hi = lo + (hi - lo) * a, lo + (hi - lo) * b
    s.text(10, 16, "'ABA' 를 넣을 때 구간 — 폭이 곧 확률이다", size=11)
    return s


@figure('carry', '캐리 — 올림 하나가 이미 낸 바이트를 건드린다')
def fig_carry():
    """0xFF 가 이어진 자리에 올림이 오면 앞으로 번진다. 레인지
    코더가 '캐시 + 몇 개'를 들고 있는 이유가 이것이다 (SPEC §5.4)."""
    s = Svg(170, '캐리가 앞 바이트로 번지는 그림', marker=True)
    x0, cw = 24, 56
    before = ['0x2A', '0xFF', '0xFF', '0x13']
    after = ['0x2B', '0x00', '0x00', '0x13']
    for row, (label, cells, colour) in enumerate((
            ('올림 전', before, 'var(--muted)'),
            ('올림 후', after, 'var(--ok)'))):
        y = 34 + row * 56
        s.text(10, y - 8 if row else y - 6, label, cls='lbl')
        for i, c in enumerate(cells):
            x = x0 + cw * i
            changed = before[i] != after[i]
            s.rect(x, y, cw - 6, 26, 'box')
            s.mono(x + (cw - 6) / 2, y + 17, c, anchor='middle',
                   fill=colour if changed and row else None)
    # 올림은 오른쪽에서 왼쪽으로 번진다 — 화살표를 두 줄 사이에 둔다.
    s.path('M%d,80 L%d,80' % (x0 + cw * 3, x0 + 30), cls='arw')
    s.text(x0 + cw * 3 + 6, 86, '+1', size=11, fill='var(--bad)')
    s.text(10, 152, '0xFF 은 아직 못 내보낸 바이트다 — 개수만 센다',
           size=11)
    return s


@figure('rans', 'rANS — 상태 하나가 곧 부호다')
def fig_rans():
    """상태 x 가 기호를 먹을 때마다 자란다. 정규화가 바이트를 뱉는다."""
    s = Svg(170, 'rANS 상태 변화', marker=True)
    s.text(10, 16, '빈도 A:3 B:1 (합 4) · x 가 자라는 모습', size=11)
    x = 16
    steps = [('', x)]
    for sym, f, c in (('A', 3, 0), ('A', 3, 0), ('B', 1, 3)):
        x = (x // f) * 4 + (x % f) + c
        steps.append((sym, x))
    x0, gap = 16, 80
    for i, (sym, xv) in enumerate(steps):
        left = x0 + gap * i
        s.mono(left, 56, 'x=%d' % xv)
        if sym:
            # 화살표는 글자 줄 **위** 에 둔다. 같은 줄에 두면 선이
            # 글자를 관통해 읽히지 않는다 (첫 판이 그랬다).
            s.path('M%g,38 L%g,38' % (left - gap + 30, left - 6),
                   cls='arw')
            s.mono(left - 32, 32, sym, anchor='middle',
                   fill='var(--accent)')
    s.text(10, 88, '드문 기호일수록 x 가 크게 뛴다. 그 뜀이', size=11)
    s.text(10, 104, '곧 비트를 더 썼다는 뜻이다.', size=11)
    s.text(10, 128, '푸는 쪽은 거꾸로 간다. 그래서 rANS 는', size=11)
    s.text(10, 144, '넣은 순서의 반대로 읽는다 (SPEC §13.3).',
           size=11, fill='var(--special)')
    return s


# ------------------------------------------------------- 7·8부 LZ·BWT
@figure('lz_window', 'LZ77 — 이미 내보낸 문서가 곧 사전이다')
def fig_lz_window():
    """진짜 파서에 문자열을 넣어 나온 토큰으로 그린다."""
    text = b'abcabcabcabd'
    tokens = lzss.find_tokens(text)
    s = Svg(190, 'LZ77 창과 일치')
    x0, cw = 14, 26
    for i, ch in enumerate(text):
        x = x0 + cw * i
        s.rect(x, 30, cw - 3, 24, 'box')
        s.mono(x + (cw - 3) / 2, 46, chr(ch), anchor='middle')
        s.mono(x + (cw - 3) / 2, 66, str(i), anchor='middle', size=8,
               fill='var(--muted)')
    pos = 0
    y = 84
    for tok in tokens:
        if isinstance(tok, tuple):
            ln, dist = tok
            src = pos - dist
            a = x0 + cw * src
            b = x0 + cw * pos
            s.path('M%g,%g Q%g,%g %g,%g'
                   % (a + 6, 78, (a + b) / 2, y + 26, b + 6, 78),
                   colour='var(--special)', width=1.6)
            s.mono(b + 8, y + 30, '거리 %d 길이 %d' % (dist, ln),
                   size=10, fill='var(--special)')
            y += 22
            pos += ln
        else:
            pos += 1
    s.text(10, 16, "'%s' 를 실제 파서에 넣어 나온 토큰"
           % text.decode(), size=11)
    s.text(10, 172, '겹치는 일치 — 길이가 거리보다 길어도 된다.',
           size=11)
    return s


@figure('lz_overlap', '겹치는 일치 — 쓰면서 읽는다')
def fig_lz_overlap():
    """거리 1, 길이 5 는 방금 쓴 바이트를 그 자리에서 다시 읽는다.
    한 번에 memcpy 하면 틀린다 (SPEC §6.3)."""
    s = Svg(170, '거리 1 짜리 겹치는 복사', marker=True)
    x0, cw = 24, 44
    s.text(10, 16, '거리 1 · 길이 5 를 풀면', size=11)
    for i in range(6):
        x = x0 + cw * i
        known = i == 0
        s.rect(x, 46, cw - 6, 26, 'box' if known else 'box off')
        s.mono(x + (cw - 6) / 2, 64, 'a', anchor='middle',
               fill=None if known else 'var(--muted)')
        if i:
            a = x0 + cw * (i - 1) + (cw - 6) / 2
            b = x + (cw - 6) / 2
            s.path('M%g,42 Q%g,24 %g,42' % (a, (a + b) / 2, b),
                   cls='arw')
    s.text(10, 110, '한 바이트를 쓰고, 그 바이트를 곧바로 읽는다.',
           size=11)
    s.text(10, 126, 'memcpy 로 한 번에 옮기면 겹친 자리가 틀린다 —',
           size=11)
    s.text(10, 142, '여기서 한 바이트씩은 게으름이 아니라 규칙이다.',
           size=11, fill='var(--special)')
    return s


@figure('bwt_matrix', 'BWT — banana 의 회전을 줄 세운다')
def fig_bwt_matrix():
    """실제 변환을 돌려 마지막 열과 원본 위치를 얻는다."""
    block = b'banana'
    last, primary = bwtmod.transform_block(block)
    rots = sorted(block[i:] + block[:i] for i in range(len(block)))
    s = Svg(60 + 20 * len(rots), 'banana 의 회전 행렬')
    s.text(10, 16, 'banana 의 회전을 사전순으로 줄 세우면', size=11)
    x0, cw = 60, 26
    for r, rot in enumerate(rots):
        y = 32 + 20 * r
        for c, ch in enumerate(rot):
            x = x0 + cw * c
            lastcol = c == len(rot) - 1
            if lastcol:
                s.fill(x - 2, y, cw - 2, 17, 'var(--special)', 0.14)
            s.mono(x + 8, y + 13, chr(ch), anchor='middle',
                   fill='var(--special)' if lastcol else None)
        if rot == block:
            s.mono(x0 - 8, y + 13, '원본 →', anchor='end', size=9,
                   fill='var(--accent)')
    s.text(10, 46 + 20 * len(rots),
           '마지막 열 %s · 원본 자리 %d'
           % (last.decode(), primary), size=11,
           fill='var(--special)')
    return s


# ------------------------------------------ 9·10부 DEFLATE·컨테이너
@figure('deflate_block', 'DEFLATE 블록 머리 — 3비트로 갈린다')
def fig_deflate_block():
    """BFINAL 1비트 + BTYPE 2비트. 그 다음이 종류마다 다르다."""
    s = Svg(210, 'DEFLATE 블록 세 종류의 머리')
    rows = [('00 저장', '길이를 경계에 맞춰 그대로', 'var(--muted)'),
            ('01 고정', '표를 안 보낸다 — 규격이 정했다',
             'var(--ok)'),
            ('10 동적', '표를 먼저 보낸다 (부호길이의 부호)',
             'var(--special)')]
    s.text(10, 16, '블록 머리 3비트', size=11)
    x0 = 14
    s.rect(x0, 26, 40, 26, 'box')
    s.mono(x0 + 20, 43, 'FIN', anchor='middle', size=10)
    s.rect(x0 + 44, 26, 54, 26, 'box')
    s.mono(x0 + 71, 43, 'TYPE', anchor='middle', size=10)
    s.rect(x0 + 102, 26, 224, 26, 'box off')
    s.mono(x0 + 214, 43, '블록 내용', anchor='middle', size=10,
           fill='var(--muted)')
    for i, (kind, note, colour) in enumerate(rows):
        y = 76 + 30 * i
        s.mono(x0, y + 12, kind, fill=colour)
        s.text(x0 + 76, y + 12, note, size=11)
    s.text(10, 182, '세 번째 종류가 gzip 의 거의 전부다. 표를 보내는',
           size=11)
    s.text(10, 198, '값보다 그 표로 아끼는 값이 크기 때문이다.',
           size=11)
    return s


@figure('deflate_pipeline', 'DEFLATE — 두 단이 이어 붙은 것')
def fig_deflate_pipeline():
    """LZ77 가 되풀이를 줄이고, 허프만이 남은 치우침을 먹는다."""
    s = Svg(140, 'DEFLATE 의 두 단', marker=True)
    boxes = [(10, 34, 88, 44, '원본', 'off'),
             (110, 34, 100, 44, 'LZ77', ''),
             (222, 34, 104, 44, '허프만', '')]
    for x, y, w, h, title, cls in boxes:
        s.rect(x, y, w, h, 'box %s' % cls if cls else 'box')
        s.text(x + w / 2, y + 20, title, anchor='middle')
    s.text(60, 72, '바이트', anchor='middle', cls='lbl')
    s.text(160, 72, '토큰', anchor='middle', cls='lbl')
    s.text(274, 72, '비트', anchor='middle', cls='lbl')
    s.path('M98,56 L108,56', cls='arw')
    s.path('M210,56 L220,56', cls='arw')
    s.text(10, 104, '되풀이는 LZ77 이, 치우침은 허프만이 먹는다.',
           size=11)
    s.text(10, 120, '둘 중 하나만으로는 여기까지 못 온다.', size=11)
    return s


@figure('gzip_layout', 'gzip 멤버 — 앞 10바이트와 뒤 8바이트')
def fig_gzip_layout():
    """MTIME 을 0 으로 못 박은 이유가 여기 있다 (SPEC §11.2)."""
    s = Svg(170, 'gzip 멤버의 자리')
    parts = [('1f 8b', 34, 'magic'), ('08', 20, 'CM'),
             ('00', 20, 'FLG'), ('00000000', 62, 'MTIME'),
             ('00', 20, 'XFL'), ('03', 20, 'OS'),
             ('deflate…', 70, '본문'), ('CRC32', 42, ''),
             ('ISIZE', 42, '')]
    x = 10
    for label, w, note in parts:
        hot = note == 'MTIME'
        s.rect(x, 34, w - 3, 30, 'box')
        if hot:
            s.fill(x, 34, w - 3, 30, 'var(--bad)', 0.12)
        s.mono(x + (w - 3) / 2, 53, label, anchor='middle', size=9,
               fill='var(--bad)' if hot else None)
        if note:
            s.mono(x + (w - 3) / 2, 78, note, anchor='middle', size=8,
                   fill='var(--muted)')
        x += w
    s.text(10, 108, 'MTIME 을 넣으면 같은 입력이 다른 파일이',
           size=11)
    s.text(10, 124, '된다. 그러면 골든 벡터를 만들 수 없다 — 그래서',
           size=11)
    s.text(10, 140, '이 책의 gzip 은 시각을 0 으로 못 박는다.', size=11,
           fill='var(--special)')
    s.text(10, 160, '주고받은 기록은 out/interop_deflate.txt',
           cls='lbl')
    return s


@figure('lz4_frame', 'LZ4 프레임 — 블록 앞의 길이 하나')
def fig_lz4_frame():
    s = Svg(160, 'LZ4 프레임과 블록')
    s.text(10, 16, '프레임', cls='lbl')
    parts = [('04 22 4D 18', 86, 'magic'), ('FLG BD', 50, '기술자'),
             ('HC', 24, '검사'), ('블록…', 80, ''),
             ('00000000', 62, '끝')]
    x = 10
    for label, w, note in parts:
        s.rect(x, 26, w - 3, 28, 'box')
        s.mono(x + (w - 3) / 2, 44, label, anchor='middle', size=9)
        if note:
            s.mono(x + (w - 3) / 2, 68, note, anchor='middle', size=8,
                   fill='var(--muted)')
        x += w
    s.text(10, 96, '블록', cls='lbl')
    parts = [('블록 크기 4B', 96, ''), ('토큰', 40, ''),
             ('리터럴', 60, ''), ('오프셋 2B', 72, ''),
             ('일치 길이', 62, '')]
    x = 10
    for label, w, _n in parts:
        s.rect(x, 106, w - 3, 28, 'box')
        s.mono(x + (w - 3) / 2, 124, label, anchor='middle', size=9)
        x += w
    s.text(10, 154, '토큰 한 바이트가 두 길이를 함께 든다',
           cls='lbl')
    return s


# ------------------------------------------------ 11·12부 PPM·문맥 혼합
@figure('ppm_escape', 'PPM — 못 본 기호는 탈출로 알린다')
def fig_ppm_escape():
    """차수 2 에서 못 찾으면 1 로, 거기서도 못 찾으면 0 으로."""
    s = Svg(200, 'PPM 의 차수 사다리', marker=True)
    levels = [('차수 2', '"ab" 다음에 본 것들', 'var(--special)'),
              ('차수 1', '"b" 다음에 본 것들', 'var(--accent)'),
              ('차수 0', '지금까지 본 모든 바이트', 'var(--muted)'),
              ('차수 -1', '256가지 균등 — 여기선 반드시 찾는다',
               'var(--ok)')]
    for i, (name, note, colour) in enumerate(levels):
        y = 26 + 42 * i
        s.rect(14, y, 96, 30, 'box')
        s.text(62, y + 20, name, anchor='middle')
        s.text(122, y + 20, note, size=11, fill=colour)
        if i + 1 < len(levels):
            s.path('M62,%d L62,%d' % (y + 32, y + 40), cls='arw')
            s.mono(70, y + 40, '탈출', size=9, fill='var(--muted)')
    s.text(10, 196, '탈출도 기호다 — 그만큼 값을 치른다',
           cls='lbl')
    return s


@figure('cm_mixer', '문맥 혼합 — 로지스틱 영역에서 더한다')
def fig_cm_mixer():
    """확률을 그냥 평균 내면 확신이 사라진다 (SPEC §18.3)."""
    s = Svg(210, '문맥 혼합의 구조', marker=True)
    models = ['차수 0', '차수 1', '차수 2', '차수 3', '차수 4']
    for i, name in enumerate(models):
        y = 24 + 30 * i
        s.rect(10, y, 86, 24, 'box')
        s.text(53, y + 16, name, anchor='middle', size=11)
        s.path('M96,%d L146,100' % (y + 12), cls='arw')
    s.rect(150, 76, 80, 48, 'box')
    s.text(190, 96, '섞기', anchor='middle')
    s.text(190, 112, 'stretch', anchor='middle', cls='lbl')
    s.path('M230,100 L254,100', cls='arw')
    s.rect(258, 76, 70, 48, 'box')
    s.text(293, 96, 'APM ×2', anchor='middle')
    s.text(293, 112, '되짚기', anchor='middle', cls='lbl')
    s.text(10, 180, '평균을 내면 0.01 과 0.99 가 0.5 가 된다.', size=11)
    s.text(10, 196, 'stretch 영역에서 더해야 확신이 산다.', size=11,
           fill='var(--special)')
    return s


# ----------------------------------------------------------- 13부 손실
@figure('zigzag_order', '지그재그 — 낮은 주파수부터 훑는다')
def fig_zigzag_order():
    """순서는 표가 아니라 규칙에서 나온다 (lossy.ZIGZAG)."""
    s = Svg(220, '8×8 지그재그 순서')
    cw = 34
    x0, y0 = 24, 20
    pos = [0] * 64
    for k, idx in enumerate(lossy.ZIGZAG):
        pos[idx] = k
    for idx in range(64):
        r, c = idx // 8, idx % 8
        x, y = x0 + cw * c, y0 + 22 * r
        k = pos[idx]
        s.fill(x, y, cw - 3, 20, 'var(--accent)',
               0.30 * (1.0 - k / 63.0) + 0.04)
        s.mono(x + (cw - 3) / 2, y + 14, str(k), anchor='middle',
               size=9)
    s.text(10, 212, '왼쪽 위가 낮은 주파수 — 0 이 뒤에 몰리게 훑는다',
           cls='lbl')
    return s


@figure('jpeg_pipeline', 'jpeglite — 버리는 자리는 하나뿐이다')
def fig_jpeg_pipeline():
    s = Svg(192, 'jpeglite 의 단계', marker=True)
    steps = [('8×8 자르기', 'var(--muted)', '무손실'),
             ('정수 DCT', 'var(--muted)', '무손실'),
             ('양자화', 'var(--bad)', '여기서 버린다'),
             ('지그재그+런', 'var(--muted)', '무손실'),
             ('허프만', 'var(--muted)', '무손실')]
    for i, (name, colour, note) in enumerate(steps):
        y = 22 + 30 * i
        s.rect(10, y, 130, 24, 'box')
        s.text(75, y + 16, name, anchor='middle', size=11)
        s.text(150, y + 16, note, size=11, fill=colour)
        if i + 1 < len(steps):
            s.path('M75,%d L75,%d' % (y + 26, y + 30), cls='arw')
    s.text(10, 188, 'DCT 는 되돌아간다. 못 되돌리는 것은 나눗셈뿐',
           cls='lbl')
    return s


@figure('png_paeth', 'PNG 필터 — 세 이웃으로 고른다')
def fig_png_paeth():
    """a+b-c 에 가장 가까운 것. 동점은 a, 그다음 b (SPEC §19.5)."""
    s = Svg(180, 'Paeth 예측기의 이웃')
    x0, y0, cw = 96, 26, 54
    cells = [(0, 0, 'c', 'var(--muted)'), (1, 0, 'b', 'var(--muted)'),
             (0, 1, 'a', 'var(--muted)'), (1, 1, 'x', 'var(--special)')]
    for c, r, name, colour in cells:
        x, y = x0 + cw * c, y0 + 40 * r
        s.rect(x, y, cw - 4, 36, 'box')
        s.mono(x + (cw - 4) / 2, y + 23, name, anchor='middle',
               fill=colour)
    s.text(220, 46, 'c  왼쪽 위', size=11)
    s.text(220, 62, 'b  위', size=11)
    s.text(220, 86, 'a  왼쪽', size=11)
    s.text(220, 102, 'x  지금 칸', size=11, fill='var(--special)')
    vals = (10, 20, 15)
    got = lossy.paeth(*vals)
    s.text(10, 140, 'paeth(a=%d, b=%d, c=%d) = %d' % (vals + (got,)),
           size=11)
    s.text(10, 156, 'p = a+b-c = %d 이고, 가장 가까운 것이 c 다.'
           % (vals[0] + vals[1] - vals[2]), size=11)
    s.text(10, 172, '동점 규칙을 안 맞추면 다섯 언어가 갈린다.',
           cls='lbl')
    return s


@figure('adpcm', 'IMA ADPCM — 예측기를 안 보낸다')
def fig_adpcm():
    """부호기와 복호기가 같은 사다리를 같은 순서로 오른다."""
    s = Svg(180, 'ADPCM 걸음 사다리')
    x0, y0, w, h = 30, 22, 282, 96
    steps = lossy.ADPCM_STEP
    s.line(x0, y0 + h, x0 + w, y0 + h)
    s.line(x0, y0, x0, y0 + h)
    pts = []
    for i, v in enumerate(steps):
        x = x0 + w * i / float(len(steps) - 1)
        y = y0 + h - h * v / float(steps[-1])
        pts.append('%g,%g' % (x, y))
    s.path('M' + ' L'.join(pts), colour='var(--accent)', width=2)
    # 표의 성질은 "다음 칸이 약 1.1배" 다. 몇 칸만 숫자로 보여 준다.
    for i in (0, 30, 60, 88):
        x = x0 + w * i / float(len(steps) - 1)
        y = y0 + h - h * steps[i] / float(steps[-1])
        s.fill(x - 2, y - 2, 4, 4, 'var(--special)', 1, rx=2)
        last = i == 88
        s.mono(x - 4 if last else x + 4, y - 4, str(steps[i]),
               anchor='end' if last else None, size=9,
               fill='var(--special)')
    s.mono(x0, y0 + h + 14, '0', size=9, fill='var(--muted)')
    s.mono(x0 + w, y0 + h + 14, '88', anchor='end', size=9,
           fill='var(--muted)')
    s.text(10, 152, '걸음은 칸마다 약 1.1배씩 자란다. 큰 소리와',
           size=11)
    s.text(10, 168, '작은 소리를 같은 4비트로 담기 위해서다.', size=11)
    return s


@figure('pipeline_all', '이 책의 전체 그림 — 어디서 무엇을 줄이나')
def fig_pipeline_all():
    """모듈을 '무엇을 줄이는가' 로 줄 세운 그림. 부 번호와 맞춘다."""
    s = Svg(230, '압축 모듈의 자리', marker=True)
    groups = [('되풀이를 줄인다', ['RLE', 'LZSS', 'LZ4', 'LZW'],
               'var(--accent)'),
              ('치우침을 줄인다', ['허프만', '레인지', 'ANS'],
               'var(--special)'),
              ('문맥을 쓴다', ['PPM', 'CM'], 'var(--ok)'),
              ('자리를 바꾼다', ['MTF', 'BWT'], 'var(--warn)'),
              ('버린다', ['DCT+양자화', 'ADPCM'], 'var(--bad)')]
    for i, (title, mods, colour) in enumerate(groups):
        y = 22 + 42 * i
        s.text(10, y + 14, title, size=11, fill=colour)
        x = 130
        for m in mods:
            w = 12 + 7 * len(m)
            s.rect(x, y, w, 24, 'box')
            s.mono(x + w / 2, y + 16, m, anchor='middle', size=9)
            x += w + 6
    s.text(10, 226, '섞어 쓰면 DEFLATE·bzip2·LZMA 가 된다 — 9·15·16부',
           cls='lbl')
    return s


def main(argv):
    if '--list' in argv:
        for name, title, _fn in FIGURES:
            print('  %-20s %s' % (name + '.svg', title))
        return 0
    os.makedirs(FIGS, exist_ok=True)
    wrote = 0
    for name, title, fn in FIGURES:
        svg = fn().dump()
        path = os.path.join(FIGS, '%s.svg' % name)
        old = None
        if os.path.exists(path):
            old = io.open(path, encoding='utf-8').read()
        if old != svg:
            io.open(path, 'w', encoding='utf-8',
                    newline='\n').write(svg)
            wrote += 1
    print('  도해 %d장 — 바뀐 것 %d장' % (len(FIGURES), wrote))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
