#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""덱에 실을 그림(SVG)을 만든다. 손으로 그리지 않는다.

    python3 deck/gen_figs.py            # deck/figs/*.svg 를 다시 만든다
    python3 deck/gen_figs.py --check    # 지금 것과 같은지만 본다

곡선은 py/transformerlib 의 함수를 실제로 불러 얻은 값이거나,
run_all.py 가 남긴 out/ 의 캡처(학습 곡선·어텐션 지도)를 읽은 값이다.
구조도(블록·헤드 나누기·KV 캐시)는 설명용이다.

만든 뒤에는 **눈으로 본다**. `make figs-png` 가 .svgrender/ 에 PNG 를
뽑는다. 압축 덱은 28장 중 8장, 무선 덱은 30장 중 4장을 그 단계에서
고쳤다 — 글자가 겹치거나 축이 잘리는 것은 기계가 못 잡는다.
(wireless/deck/gen_figs.py 의 틀을 물려받았다.)
"""
import io
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
FIGS = os.path.join(HERE, 'figs')
OUT = os.path.join(BASE, 'out')
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(BASE, 'py'))

import svgkit as sk                                    # noqa: E402
from svgkit import Axes, Fig                           # noqa: E402
from transformerlib import ops, optim, posenc, scalar  # noqa: E402
from transformerlib import model as M                  # noqa: E402
from transformerlib import tensor as T                 # noqa: E402

FIGURES = {}


def fig(name):
    def deco(fn):
        FIGURES[name] = fn
        return fn
    return deco


def section(name, title_part):
    """out/<name> 에서 제목에 title_part 가 든 절의 본문 줄들."""
    text = io.open(os.path.join(OUT, name), encoding='utf-8').read()
    lines, on = [], False
    for line in text.split('\n'):
        if line.startswith('== '):
            on = title_part in line
            continue
        if on:
            lines.append(line)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def heat(f, x0, y0, size, mat, labels=None, color='#25507f'):
    """행렬을 칸 진하기로. mat 은 [0, 1] 값의 행 목록.
    칸 테두리를 그리지 않는다 — 작은 칸에서는 테두리가 색을 덮는다."""
    n = len(mat)
    c = size / float(n)
    for i, row in enumerate(mat):
        for j, v in enumerate(row):
            if v > 0.004:
                f.rect(x0 + j * c, y0 + i * c, c + 0.2, c + 0.2, 'cell',
                       ' style="fill:%s;fill-opacity:%.3f;stroke:none"'
                       % (color, min(1.0, v)))
    f.rect(x0, y0, size, size, 'frame')
    if labels:
        for k, s in enumerate(labels):
            f.text(x0 + (k + 0.5) * c, y0 - 3, s, 'tick')
            f.text(x0 - 3, y0 + (k + 0.5) * c + 3, s, 'tick', 'end')


# ── 3부: 자동미분 ─────────────────────────────────────────────


@fig('comp_graph')
def comp_graph():
    """scalar.example_graph 의 12노드. 값은 실제로 계산한 것."""
    out, leaves = scalar.example_graph()
    out.backward()
    n12 = out
    n11 = n12.prev[0]
    n8, n10 = n11.prev
    n6, n7 = n8.prev
    n5 = n6.prev[0]
    n4 = n5.prev[0]
    n9 = n10.prev[0]
    x1, x2, x3 = leaves
    pos = {
        'x1': (30, 40, x1), 'x2': (30, 95, x2), 'x3': (30, 150, x3),
        'n4': (95, 67, n4), 'n7': (95, 20, n7), 'n9': (95, 175, n9),
        'n5': (155, 110, n5), 'n10': (155, 175, n10),
        'n6': (210, 110, n6), 'n8': (255, 60, n8),
        'n11': (275, 140, n11), 'n12': (315, 140, n12)}
    ops_ = {'n4': '×', 'n5': '+', 'n6': 'tanh', 'n7': 'exp', 'n8': '×',
            'n9': 'x²', 'n10': 'log', 'n11': '+', 'n12': 'relu'}
    edges = [('x1', 'n4'), ('x2', 'n4'), ('n4', 'n5'), ('x3', 'n5'),
             ('n5', 'n6'), ('x1', 'n7'), ('n6', 'n8'), ('n7', 'n8'),
             ('x3', 'n9'), ('n9', 'n10'), ('n8', 'n11'), ('n10', 'n11'),
             ('n11', 'n12')]
    f = Fig(215, title='12노드 계산 그래프와 기울기')
    for a, b in edges:
        xa, ya, _ = pos[a]
        xb, yb, _ = pos[b]
        f.line(xa + 13, ya, xb - 13, yb, 'tie')
    for name, (x, y, v) in pos.items():
        f.rect(x - 13, y - 11, 26, 22, 'box g2' if name[0] == 'x'
               else 'box')
        f.text(x, y - 1, ops_.get(name, name), 'tick')
        f.text(x, y + 8, '%.2f' % v.data, 'tick')
        f.text(x, y + 20, '∂ %.2f' % v.grad, 'cap')
    f.text(170, 210, '칸 안: 연산과 값 · 아래: ∂출력/∂노드', 'cap')
    return f


# ── 2·4부: 소프트맥스·활성함수 ─────────────────────────────────


@fig('softmax_temps')
def softmax_temps():
    z = [2.0, 1.0, 0.0, -1.0]
    f = Fig(170, title='온도에 따른 소프트맥스')
    for k, tau in enumerate((0.5, 1.0, 2.0)):
        p = ops.softmax(T.tensor([v / tau for v in z])).data
        x0 = 20 + k * 108
        f.text(x0 + 45, 16, 'τ = %.1f' % tau, 'key')
        for j, v in enumerate(p):
            h = 110 * v
            f.rect(x0 + j * 23, 135 - h, 18, h, 'cell a')
            f.text(x0 + j * 23 + 9, 131 - h, '%.2f' % v, 'tick')
            f.text(x0 + j * 23 + 9, 148, '%g' % z[j], 'tick')
    f.text(170, 164, '로짓 2 · 1 · 0 · −1 을 온도로 나눈 뒤의 확률', 'cap')
    return f


@fig('activations')
def activations():
    f = Fig(200, title='ReLU · GELU · SiLU')
    ax = Axes(f, 36, 12, 280, 150, (-4, 3), (-0.6, 3))
    ax.frame()
    ax.grid(xs=(-3, -2, -1, 0, 1, 2), ys=(0, 1, 2))
    xs = [-4 + i * 0.05 for i in range(141)]
    ax.curve([(x, max(0.0, x)) for x in xs], 'cvd')
    # 두 GELU 는 그림 폭에서 겹친다(차이 4.7e-4 이하). tanh 근사를 굵게
    # 먼저 그리고 erf 정의를 파선으로 위에 얹어 둘 다 보이게 한다.
    ax.curve([(x, ops.gelu(T.tensor([x])).data[0]) for x in xs], 'cv5')
    f.path([ax.at(x, ops.gelu_exact(x)) for x in xs], 'cv2',
           ' style="stroke-dasharray:5 3"')
    ax.curve([(x, x / (1 + math.exp(-x))) for x in xs], 'cv3')
    ax.xticks((-4, -2, 0, 2), '%d')
    ax.yticks((0, 1, 2, 3), '%d')
    sk.legend(f, 50, 30, [('ReLU', 'cvd'), ('GELU (erf, 파선)', 'cv2'),
                          ('GELU tanh 근사', 'cv5'),
                          ('SiLU x·σ(x)', 'cv3')])
    f.text(176, 190, 'GELU 는 0 근처 음수를 조금 통과시킨다', 'cap')
    return f


# ── 6부: 어텐션 ──────────────────────────────────────────────


@fig('dot_variance')
def dot_variance():
    """out/attention.txt 1절 표를 읽는다 — 1만 쌍을 실제로 뽑은 값."""
    rows = []
    for line in section('attention.txt', 'q·k 의 분산'):
        m = re.match(r'^\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', line)
        if m:
            rows.append(tuple(float(v) for v in m.groups()))
    f = Fig(200, title='내적의 분산과 √d')
    ax = Axes(f, 42, 12, 270, 150, (3, 300), (0.5, 400), xlog=True,
              ylog=True)
    ax.frame()
    ax.grid(xs=(4, 16, 64, 256), ys=(1, 10, 100))
    ax.curve([(d, d) for d in (3, 300)], 'cvd')
    ax.curve([(d, v) for d, v, _, _ in rows], 'cv2')
    ax.dots([(d, v) for d, v, _, _ in rows], 2.2, 'dot2')
    ax.curve([(d, s) for d, _, _, s in rows], 'cv5')
    ax.dots([(d, s) for d, _, _, s in rows], 2.2, 'dot5')
    ax.xticks((4, 16, 64, 256), '%d', 'd')
    ax.yticks((1, 10, 100), '%g')
    sk.legend(f, 52, 30, [('Var(q·k)', 'cv2'), ('Var(q·k/√d)', 'cv5'),
                          ('분산 = d', 'cvd')])
    f.text(176, 196, '성분 분산 1 인 q, k 를 d 마다 1만 쌍 (out/attention.txt)',
           'cap')
    return f


@fig('causal_mask')
def causal_mask():
    f = Fig(190, title='인과 마스크')
    n, c, x0, y0 = 6, 22, 40, 34
    toks = ['나', '는', '밥', '을', '먹', '다']
    for i in range(n):
        f.text(x0 - 6, y0 + i * c + 14, toks[i], 'tick', 'end')
        f.text(x0 + i * c + 11, y0 - 5, toks[i], 'tick')
        for j in range(n):
            f.rect(x0 + j * c, y0 + i * c, c, c,
                   'cell a' if j <= i else 'cell off')
    f.text(x0 - 22, y0 - 16, '질의↓ 키→', 'cap', 'start')
    f.text(250, 70, '칠한 칸: 볼 수 있다', 'cap')
    f.text(250, 84, '(j ≤ i)', 'cap')
    f.text(250, 116, '빈 칸: −∞ 를 더한다', 'cap')
    f.text(250, 130, '소프트맥스 뒤 0', 'cap')
    return f


@fig('multihead_split')
def multihead_split():
    f = Fig(190, title='멀티헤드 — 폭을 나눠 따로 본다')
    d, h = 8, 4
    cw = 18
    x0 = 170 - d * cw / 2
    f.text(170, 16, '한 토큰의 q (폭 d = 8)', 'key')
    for j in range(d):
        f.rect(x0 + j * cw, 24, cw, 18, 'box g%d' % (j // 2 + 2))
        f.text(x0 + j * cw + 9, 37, str(j), 'tick')
    for k in range(h):
        cx = 45 + k * 83
        f.line(x0 + (2 * k + 1) * cw, 44, cx, 82, 'arw')
        f.rect(cx - 22, 84, 44, 30, 'box g%d' % (k + 2))
        f.text(cx, 97, '헤드 %d' % k, 'tick')
        f.text(cx, 108, '열 %d‥%d' % (2 * k, 2 * k + 1), 'cap')
        f.line(cx, 116, cx, 140, 'arw')
    f.rect(20, 142, 300, 22, 'box')
    f.text(170, 157, '헤드마다 softmax(qkᵀ/√d_k)·v — 그 뒤 다시 이어 붙인다',
           'tick')
    f.text(170, 182, 'd_k = d / h = 2 · 파라미터 수는 헤드 수와 무관하다', 'cap')
    return f


@fig('sinusoidal_heatmap')
def sinusoidal_heatmap():
    n, d = 32, 32
    pe = posenc.sinusoidal(n, d).tolist()
    f = Fig(225, title='사인 위치 인코딩')
    c = 5.5
    x0, y0 = 70, 18
    for p in range(n):
        for i in range(d):
            v = pe[p][i]
            color = '#b8322a' if v >= 0 else '#25507f'
            f.rect(x0 + i * c, y0 + p * c, c + 0.2, c + 0.2, 'cell',
                   ' style="fill:%s;fill-opacity:%.3f;stroke:none"'
                   % (color, abs(v)))
    f.rect(x0, y0, d * c, n * c, 'frame')
    f.text(x0 + d * c / 2, y0 + n * c + 12, '차원 i (왼쪽이 빠르다)', 'axname')
    f.text(x0 - 8, y0 + n * c / 2, '위치 p', 'axname', 'end')
    f.text(170, 218, '붉은 칸 +, 푸른 칸 − · 진하기가 크기 · d = 32', 'cap')
    return f


@fig('rope_rotation')
def rope_rotation():
    f = Fig(190, title='RoPE — 위치만큼 돌린다')
    cx, cy, r = 90, 100, 70
    f.circle(cx, cy, r, 'frame')
    f.line(cx - r - 8, cy, cx + r + 8, cy, 'ax')
    f.line(cx, cy - r - 8, cx, cy + r + 8, 'ax')
    q = (0.9, 0.3)
    for m, cls in ((0, 'cv2'), (1, 'cv3'), (2, 'cv5')):
        th = m * 0.6
        x = q[0] * math.cos(th) - q[1] * math.sin(th)
        y = q[0] * math.sin(th) + q[1] * math.cos(th)
        f.line(cx, cy, cx + x * r, cy - y * r, cls)
        f.text(cx + x * r * 1.12, cy - y * r * 1.12, 'm=%d' % m, 'tick')
    f.text(245, 50, '짝 (2i, 2i+1) 을', 'cap')
    f.text(245, 62, 'θ = m·10000^(−2i/d_k) 만큼', 'cap')
    f.text(245, 90, '⟨R_m q, R_n k⟩ 는', 'key')
    f.text(245, 104, 'm − n 에만 달린다', 'key')
    f.text(245, 132, '(out/posenc.txt 3절)', 'cap')
    return f


# ── 7부: 블록과 크기 ────────────────────────────────────────────


@fig('pre_ln_block')
def pre_ln_block():
    f = Fig(230, title='pre-LN 블록과 잔차 스트림')
    x = 60
    f.line(x, 214, x, 12, 'arw hot')
    f.text(x - 6, 222, 'x', 'key', 'end')
    f.text(x - 6, 10, 'x′', 'key', 'end')
    for k, (y, parts) in enumerate(((150, [('LN', 'g4'), ('어텐션', 'g2')]),
                                    (70, [('LN', 'g4'), ('FFN', 'g3')]))):
        f.line(x, y + 30, 110, y + 30, 'tie')
        xx = 110
        for name, cls in parts:
            f.rect(xx, y + 18, 70 if name != 'LN' else 36, 24, 'box ' + cls)
            f.text(xx + (35 if name != 'LN' else 18), y + 34, name, 'tick')
            xx += 80 if name != 'LN' else 46
        f.line(xx - 10, y + 30, xx + 10, y + 30, 'tie')
        f.line(xx + 10, y + 30, xx + 10, y + 6, 'tie')
        f.line(xx + 10, y + 6, x + 8, y + 6, 'arw')
        f.circle(x, y + 6, 7, 'frame')
        f.text(x, y + 10, '+', 'key')
    f.text(250, 212, '잔차 길(굵은 선)에는 연산이 없다', 'cap')
    f.text(250, 224, '— 기울기가 그대로 내려간다', 'cap')
    return f


@fig('param_breakdown')
def param_breakdown():
    c = M.Config(V=50257, T=1024, d=768, L=12, h=12, d_ff=3072)
    d = c.d
    parts = [('wte V·d', c.V * d, 'g1'), ('wpe T·d', c.T * d, 'g6'),
             ('어텐션 12×(4d²+4d)', 12 * (4 * d * d + 4 * d), 'g2'),
             ('FFN 12×(8d²+5d)', 12 * (8 * d * d + 5 * d), 'g3'),
             ('LN 12×4d + 2d', 12 * 4 * d + 2 * d, 'g4')]
    total = M.count_params(c)
    f = Fig(160, title='GPT-2 small 파라미터가 사는 곳')
    x = 20
    for name, n, cls in parts:
        w = 300.0 * n / total
        f.rect(x, 30, w, 26, 'box ' + cls)
        x += w
    y = 76
    for name, n, cls in parts:
        f.rect(22, y - 8, 9, 9, 'box ' + cls)
        f.text(36, y, name, 'tick', 'start')
        f.text(318, y, '{:,} ({:.2f}%)'.format(n, 100.0 * n / total),
               'tick', 'end')
        y += 15
    f.text(170, 20, '합 {:,} (M.count_params)'.format(total), 'key')
    return f


@fig('attn_vs_ffn')
def attn_vs_ffn():
    """토큰 하나의 곱셈 수 — 블록 하나, d = 768."""
    d = 768
    f = Fig(200, title='어텐션 대 사영 — 문맥이 길어지면')
    ax = Axes(f, 48, 12, 262, 150, (64, 8192), (1e5, 1e8), xlog=True,
              ylog=True)
    ax.frame()
    ax.grid(xs=(128, 512, 2048, 8192), ys=(1e6, 1e7))
    ns = [64 * 2 ** (k / 4.0) for k in range(29)]
    ax.curve([(n, 2 * n * d) for n in ns], 'cv2')
    ax.curve([(n, 12.0 * d * d) for n in ns], 'cv3')
    ax.curve([(n, 12.0 * d * d + 2 * n * d) for n in ns], 'cvd')
    xc = 6 * d
    ax.dots([(xc, 2 * xc * d)], 2.6, 'dot2')
    ax.xticks((64, 512, 4096), '%d', '문맥 n')
    ax.yticks((1e5, 1e6, 1e7, 1e8), '%.0e')
    sk.legend(f, 58, 30, [('점수·가중합 2nd', 'cv2'),
                          ('사영 12d²', 'cv3'), ('합', 'cvd')])
    f.text(176, 196, '두 곡선은 n = 6d = %d 에서 만난다' % xc, 'cap')
    return f


@fig('gpt2_family')
def gpt2_family():
    rows = [('small', 768, 12, 12), ('medium', 1024, 24, 16),
            ('large', 1280, 36, 20), ('XL', 1600, 48, 25)]
    counts = [M.count_params(M.Config(V=50257, T=1024, d=d, L=L, h=h,
                                      d_ff=4 * d)) for _, d, L, h in rows]
    f = Fig(170, title='GPT-2 네 크기 — 식으로 센 파라미터')
    for k, ((name, d, L, h), n) in enumerate(zip(rows, counts)):
        y = 24 + k * 34
        w = 170.0 * n / counts[-1]
        f.rect(110, y, w, 22, 'box g2')
        f.text(104, y + 10, name, 'tick', 'end')
        f.text(104, y + 20, 'd%d · L%d' % (d, L), 'cap', 'end')
        f.text(114 + w, y + 15, '%.1fM' % (n / 1e6), 'tick', 'start')
    f.text(170, 164, 'd·L·h 는 data/models.tsv, 수는 model.count_params', 'cap')
    return f


# ── 8부: 학습 ────────────────────────────────────────────────


@fig('lr_schedule')
def lr_schedule():
    f = Fig(190, title='학습률 일정')
    ax = Axes(f, 48, 12, 262, 140, (0, 3000), (0, 6.5e-3))
    ax.frame()
    ax.grid(xs=(1000, 2000), ys=(2e-3, 4e-3, 6e-3))
    ax.curve([(t, optim.lr_schedule(t, 6e-3, 6e-4, 150, 3000))
              for t in range(1, 3001, 10)], 'cv5')
    ax.xticks((0, 1000, 2000, 3000), '%d', '스텝')
    ax.yticks((0, 2e-3, 4e-3, 6e-3), '%.0e')
    f.text(176, 186, '덧셈 과제의 설정: 워밍업 150 뒤 코사인으로 1/10 까지', 'cap')
    return f


# ── 10·11부: 추론과 그 너머 ──────────────────────────────────────


@fig('kv_cache')
def kv_cache():
    f = Fig(215, title='KV 캐시')
    for row, (label, n_new) in enumerate((('다시 계산', 5), ('캐시', 1))):
        y = 30 + row * 80
        f.text(20, y - 8, label, 'key', 'start')
        for t in range(5):
            x = 30 + t * 44
            new = t >= 5 - n_new
            f.rect(x, y, 36, 22, 'box g2' if new else 'box off')
            f.text(x + 18, y + 15, 'k,v %d' % t, 'tick')
        f.rect(250, y, 60, 22, 'box g5')
        f.text(280, y + 15, 'q 4', 'tick')
        f.text(280, y + 36, 'k,v 0‥4 를 본다', 'cap')
        f.text(118, y + 36, '새로 계산' if n_new == 5 else
               '꺼내 쓴다 · 4 만 새로', 'cap')
    f.text(170, 170, '위: 새 토큰마다 앞 위치의 k·v 를 전부 다시 만든다', 'cap')
    f.text(170, 183, '아래: 저장해 둔 k·v 에 새 위치 하나만 더한다', 'cap')
    f.text(170, 204, '인과 마스크 덕에 앞 위치의 k·v 는 뒤에 무엇이 와도 같다',
           'cap')
    return f


@fig('online_tiles')
def online_tiles():
    f = Fig(190, title='온라인 소프트맥스 — 조각씩 읽기')
    n, tile = 12, 4
    for j in range(n):
        x = 30 + j * 24
        f.rect(x, 40, 20, 20, 'box g%d' % (j // tile + 2))
        f.text(x + 10, 54, 'x%d' % j, 'cap')
    for k in range(n // tile):
        x = 30 + k * tile * 24
        f.line(x + 2, 66, x + tile * 24 - 6, 66, 'tie hot')
        f.text(x + tile * 12 - 2, 80, '조각 %d' % k, 'tick')
    f.rect(30, 100, 280, 44, 'box')
    f.text(170, 116, '들고 다니는 것 셋: m (최댓값) · s (Σ e^(x−m))', 'tick')
    f.text(170, 132, '· o (지금까지의 가중평균)', 'tick')
    f.text(170, 166, '새 최댓값이 오면 s·e^(m−m′), o 는 옛 합에 비례해 다시 섞는다',
           'cap')
    f.text(170, 180, '메모리 O(조각) — 결과는 한 번에 계산한 것과 같다', 'cap')
    return f


@fig('lora_block')
def lora_block():
    f = Fig(180, title='LoRA — 얼린 W 옆의 낮은 계수 갱신')
    f.rect(40, 70, 70, 40, 'box off')
    f.text(75, 94, 'W (얼림)', 'tick')
    f.rect(170, 40, 40, 30, 'box g3')
    f.text(190, 60, 'A', 'key')
    f.rect(230, 40, 40, 30, 'box g5')
    f.text(250, 60, 'B = 0', 'tick')
    f.text(20, 94, 'x', 'key')
    f.line(26, 90, 38, 90, 'arw')
    f.line(26, 90, 26, 55, 'tie')
    f.line(26, 55, 168, 55, 'arw')
    f.line(212, 55, 228, 55, 'arw')
    f.line(272, 55, 300, 55, 'tie')
    f.line(300, 55, 300, 84, 'arw')
    f.line(112, 90, 290, 90, 'arw')
    f.circle(300, 90, 8, 'frame')
    f.text(300, 94, '+', 'key')
    f.text(190, 30, 'A [d_in, r]', 'cap')
    f.text(250, 30, 'B [r, d_out] · α/r', 'cap')
    f.text(170, 140, 'B 가 0 이라 처음 출력은 원래 모델과 같다', 'cap')
    f.text(170, 154, '그때 A 의 기울기는 0, B 가 먼저 배운다 (시험으로 확인)',
           'cap')
    return f


@fig('enc_dec')
def enc_dec():
    f = Fig(180, title='인코더-디코더 · 디코더 전용 · 인코더 전용')
    cols = [('원래 트랜스포머', ['인코더 ×N', '디코더 ×N']),
            ('GPT (이 덱)', ['디코더 ×N']),
            ('BERT', ['인코더 ×N'])]
    for k, (name, boxes) in enumerate(cols):
        x = 20 + k * 106
        f.text(x + 48, 20, name, 'key')
        for b, label in enumerate(boxes):
            cls = 'box g2' if '디코더' in label else 'box g3'
            f.rect(x + 8, 34 + b * 52, 80, 38, cls)
            f.text(x + 48, 56 + b * 52, label, 'tick')
    f.text(170, 150, '디코더: 인과 마스크 · 인코더: 양방향', 'cap')
    f.text(170, 164, '원래 트랜스포머의 디코더는 인코더 출력도 본다(교차 어텐션)',
           'cap')
    return f


# ── 1부: 연표 ────────────────────────────────────────────────


@fig('timeline')
def timeline():
    """data/timeline.tsv 의 해마다 사건 수와 이정표 여섯."""
    rows = []
    for line in io.open(os.path.join(BASE, 'data', 'timeline.tsv'),
                        encoding='utf-8'):
        if line.startswith('#') or line.startswith('year'):
            continue
        cols = line.rstrip('\n').split('\t')
        if len(cols) >= 4 and cols[0].isdigit():
            rows.append((int(cols[0]), cols[3]))
    f = Fig(210, title='트랜스포머 이전과 이후 — 연표의 사건 수')
    early = sorted(set(y for y, _ in rows if y < 2012))
    for k, y in enumerate(early):
        x = 22 + k * 20
        f.circle(x, 150, 3, 'dot')
        f.text(x, 166 + (k % 2) * 10, str(y), 'cap')
    f.line(150, 150, 158, 150, 'tie')
    f.text(154, 140, '⋯', 'tick')
    per = {}
    for y, _ in rows:
        if y >= 2012:
            per[y] = per.get(y, 0) + 1
    x0, dx = 170, 11.2
    for y in range(2013, 2027):
        x = x0 + (y - 2013) * dx
        for i in range(per.get(y, 0)):
            f.circle(x, 150 - i * 8, 3, 'dot')
        if y % 2 == 1:
            f.text(x, 166, "'%02d" % (y % 100), 'cap')
    marks = [('vaswani2017', 'Transformer'), ('radford2018', 'GPT-1'),
             ('devlin2018', 'BERT'), ('brown2020', 'GPT-3'),
             ('hoffmann2022', 'Chinchilla'), ('touvron2023', 'LLaMA')]
    for k, (key, label) in enumerate(marks):
        ys = [y for y, p in rows if p == key]
        if not ys:
            continue
        x = x0 + (ys[0] - 2013) * dx
        ty = 30 + k * 14
        top = 150 - (per.get(ys[0], 1) - 1) * 8 - 5
        f.line(x, top, x, ty + 3, 'tie')
        f.text(x + 3, ty, label, 'tick', 'start')
    f.text(170, 196, '점 하나가 data/timeline.tsv 의 한 줄 (출처가 붙은 사건)',
           'cap')
    return f


# ── 학습 결과를 읽는 그림 ──────────────────────────────────────


def curve(name, part='학습 곡선'):
    pts = []
    for line in section(name, part):
        cols = line.split()
        if len(cols) >= 2:
            pts.append((int(cols[0]), float(cols[1])))
    return pts


@fig('loss_tasks')
def loss_tasks():
    f = Fig(210, title='합성 과제의 학습 곡선 (C)')
    ax = Axes(f, 38, 12, 270, 150, (0, 3000), (0, 3.5))
    ax.frame()
    ax.grid(xs=(1000, 2000), ys=(1, 2, 3))
    items = [('덧셈(뒤집음)', 'curve_c_add.txt', 'cv2'),
             ('덧셈(그대로)', 'curve_c_addplain.txt', 'cvd'),
             ('정렬', 'curve_c_sort.txt', 'cv3'),
             ('뒤집기', 'curve_c_reverse.txt', 'cv4'),
             ('홀짝', 'curve_c_parity.txt', 'cv5')]
    for label, name, cls in items:
        ax.curve(curve(name), cls)
    ax.xticks((0, 1000, 2000, 3000), '%d', '스텝')
    ax.yticks((0, 1, 2, 3), '%d', '손실')
    sk.legend(f, 200, 30, [(a, c) for a, _, c in items])
    f.text(176, 206, '줄마다 입력 부분은 무작위라 손실이 0 으로 가지 않는다',
           'cap')
    return f


@fig('loss_lm')
def loss_lm():
    f = Fig(210, title='언어 모델의 학습 곡선 (C, 어휘 512)')
    ax = Axes(f, 38, 12, 270, 150, (0, 640), (2.0, 6.5))
    ax.frame()
    ax.grid(xs=(200, 400, 600), ys=(3, 4, 5, 6))
    for lang, cls, dot in (('ko', 'cv5', 'dot5'), ('en', 'cv2', 'dot2')):
        name = 'curve_c_%s.txt' % lang
        ax.curve(curve(name), cls)
        ax.dots(curve(name, '검증 손실'), 2.4, dot)
    ax.xticks((0, 200, 400, 600), '%d', '스텝')
    ax.yticks((2, 3, 4, 5, 6), '%d', '손실')
    sk.legend(f, 200, 30, [('한국어 학습', 'cv5'), ('영어 학습', 'cv2')])
    f.circle(206, 58, 2.4, 'dot5')
    f.circle(213, 58, 2.4, 'dot2')
    f.text(222, 61, '검증 손실(색은 언어)', 'tick', 'start')
    f.text(176, 206, '토큰 하나가 담는 바이트가 달라 두 언어의 손실은 직접 견줄 수'
           ' 없다', 'cap')
    return f


def attn_matrix(name, block, head):
    lines = section('attnmaps.txt', '%s — 가중치 행렬 전부' % name)
    labels = lines[0].split(': ', 1)[1].split(' ')
    n = len(labels)
    start = lines.index('블록 %d 헤드 %d' % (block, head)) + 1
    mat = [[float(v) for v in lines[start + i].split()] for i in range(n)]
    return labels, mat


def attn_fig(name, title, heads, block=None, text=None):
    """text 를 주면 토큰 대신 원문을 적는다 — 한국어 바이트 BPE 에는
    음절의 앞 바이트만 담은 토큰이 있어 토큰마다 적으면 � 가 된다."""
    f = Fig(190, title=title)
    size, gap = 72, 12
    left = (340 - len(heads) * size - (len(heads) - 1) * gap) / 2.0
    for k, h in enumerate(heads):
        labels, mat = attn_matrix(name, block, h)
        x0 = left + k * (size + gap)
        heat(f, x0, 30, size, mat)
        f.text(x0 + size / 2, 24, '헤드 %d' % h, 'tick')
    labels, _ = attn_matrix(name, block, heads[0])
    if text:
        f.text(170, 128, '%s (토큰 %d개)' % (text, len(labels)), 'tick')
    else:
        f.text(170, 128, ' '.join(labels), 'tick')
    f.text(170, 146, '행 = 질의 토큰, 열 = 키 토큰, 진할수록 큰 가중치', 'cap')
    f.text(170, 160, '블록 %d · C 가 학습한 체크포인트를 파이썬이 읽어 계산' % block,
           'cap')
    return f


@fig('attn_sort')
def attn_sort():
    return attn_fig('sort', '정렬 과제의 어텐션 지도', (0, 1, 2, 3), 1)


@fig('attn_add')
def attn_add():
    return attn_fig('add', '덧셈 과제의 어텐션 지도', (0, 1, 2, 3), 1)


@fig('attn_ko')
def attn_ko():
    return attn_fig('ko', '한국어 모델의 어텐션 지도', (0, 1, 2, 3), 2,
                    text='김 첨지는 오래간만에 돈을 벌었다.')


def render_all():
    made = {}
    for name in sorted(FIGURES):
        made[name + '.svg'] = FIGURES[name]().render() + '\n'
    return made


def main(argv):
    made = render_all()
    if '--check' in argv:
        bad = []
        for name, want in sorted(made.items()):
            p = os.path.join(FIGS, name)
            cur = (io.open(p, encoding='utf-8').read()
                   if os.path.exists(p) else '')
            if cur != want:
                bad.append(name)
        for name in bad:
            print('  ✗ %s 가 소스와 어긋난다' % name)
        print('그림 %d장 — 어긋남 %d건' % (len(made), len(bad)))
        return 1 if bad else 0
    if not os.path.isdir(FIGS):
        os.makedirs(FIGS)
    for name, text in sorted(made.items()):
        io.open(os.path.join(FIGS, name), 'w', encoding='utf-8',
                newline='\n').write(text)
    print('그림 %d장 → deck/figs/' % len(made))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
