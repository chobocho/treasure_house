# -*- coding: utf-8 -*-
"""문서 안 추론 데모에 실을 모델 — ckpt/c_add.ckpt 를 JS 로.

    python3 tools/export_js.py            deck/demos_model.js 를 쓴다
    python3 tools/export_js.py --check    시험 줄 1000개를 C 와 대조

float32 그대로면 파라미터 101,760개가 base64 로 543 KB 라 PLAN §4 의
상한(400 KB)을 넘는다. float16 으로 줄이면 절반이다. 반올림한 만큼
로짓이 달라지므로 "greedy 답이 C 와 같다" 는 믿지 않고 잰다:
--check 가 C 의 답(tfs accuracy --show 1000)과 node 로 돌린 데모
함수(deck/demos.js 의 __tfmGreedy)의 답을 한 줄씩 맞춰 본다.
시간 O(시험 줄 × 순전파), 공간 O(파라미터).
"""
import base64
import io
import json
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'py'))

from transformerlib import model as M          # noqa: E402
from transformerlib import tokenizer, train    # noqa: E402

CKPT = os.path.join(HERE, 'ckpt', 'c_add.ckpt')
VOCAB = os.path.join(HERE, 'ckpt', 'tok', 'add')
TEST = os.path.join(HERE, 'corpus', 'tasks', 'add_test.txt')
OUT = os.path.join(HERE, 'deck', 'demos_model.js')


def export():
    cfg, params = train.load_ckpt(CKPT)
    vocab, _ = tokenizer.load(VOCAB)
    raw = bytearray()
    shapes = []
    for name, shape, _ in M.shapes(cfg):
        data = params[name].data
        # struct 'e' 는 float16 범위(±65504)를 넘으면 예외를 던진다 —
        # 조용히 inf 가 되는 일은 없다
        raw += struct.pack('<%de' % len(data), *data)
        shapes.append([name, list(shape)])
    doc = {
        'cfg': dict(V=cfg.V, T=cfg.T, d=cfg.d, L=cfg.L, h=cfg.h,
                    d_ff=cfg.d_ff),
        'vocab': [b.decode('ascii') for b in vocab],
        'shapes': shapes,
        'data': base64.b64encode(bytes(raw)).decode('ascii'),
    }
    text = ('/* tools/export_js.py 가 ckpt/c_add.ckpt 에서 만든다 — '
            '손대지 말 것 */\nwindow.__TFM_ADD = %s;\n'
            % json.dumps(doc, separators=(',', ':')))
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(text)
    print('%s — 파라미터 %d개 · %.0f KB'
          % (os.path.relpath(OUT, HERE), M.count_params(cfg),
             len(text) / 1024.0))


NODE = r"""
const fs = require('fs');
global.window = {};
global.window.__demo = () => {};
global.document = {};
for (const f of process.argv.slice(1, 3)) {
  new Function('window', 'document', fs.readFileSync(f, 'utf8'))(
    global.window, global.document);
}
const M = global.window.__TFM_ADD;
const prompts = fs.readFileSync(0, 'utf8').split('\n').filter(Boolean);
const greedy = global.window.__tfmGreedy;
for (const p of prompts) console.log(p + greedy(M, p, 4));
"""


def check():
    c = subprocess.run(
        [os.path.join(HERE, 'c', 'tfs'), 'accuracy', CKPT, VOCAB, TEST,
         '--sep', '=', '--show', '1000'],
        cwd=HERE, stdout=subprocess.PIPE, check=True,
        universal_newlines=True).stdout
    c_lines = [ln.split()[0] for ln in c.splitlines()
               if ln.startswith('  ') and '=' in ln]
    prompts = '\n'.join(ln[:ln.index('=') + 1] for ln in c_lines)
    js = subprocess.run(
        ['node', '-e', NODE,
         os.path.join(HERE, 'deck', 'demos_model.js'),
         os.path.join(HERE, 'deck', 'demos.js')],
        input=prompts, stdout=subprocess.PIPE, check=True,
        universal_newlines=True).stdout.split()
    diff = [(a, b) for a, b in zip(c_lines, js) if a != b]
    if len(js) != len(c_lines) or not c_lines:
        print('줄 수가 다르다: C %d · JS %d' % (len(c_lines), len(js)))
        return 1
    for a, b in diff[:10]:
        print('  C %s  JS %s' % (a, b))
    print('문서 안 추론 %d줄 중 C 와 다른 답 %d줄'
          % (len(c_lines), len(diff)))
    return 1 if diff else 0


if __name__ == '__main__':
    if '--check' in sys.argv:
        sys.exit(check())
    export()
