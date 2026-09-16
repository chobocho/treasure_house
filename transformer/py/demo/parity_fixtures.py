# -*- coding: utf-8 -*-
"""파이썬 → C 대조 자료 만들기 (PLAN.md §5 6단계).

    python3 py/demo/parity_fixtures.py

C 시험은 이 파일이 만든 값과 견준다. 그래서 C 코드보다 **먼저**
만들어 커밋한다 — 그래야 C 시험이 "구현이 없어서" 가 아니라
"값이 달라서" 실패한다.

  ckpt/parity/matmul.tfx     7×5 · 5×3 행렬곱
  ckpt/parity/ops.tfx        소프트맥스·CE·레이어놈·GELU·인과 소프트맥스
  ckpt/parity/tiny_*.ckpt    작은 모델 셋(learned·sin·rope)
  ckpt/parity/tiny_*.tfx     그 모델의 입력·로짓·손실·모든 기울기
  ckpt/parity/train.tfx      같은 씨앗으로 20 스텝 학습한 손실
  ckpt/parity/sample.tfx     greedy 이어 쓰기
  ckpt/tok/*.vocab·merges    토크나이저(한국어·영어 BPE 512, 과제 문자)
  out/parity_tokens.txt      파일마다 .bin 의 토큰 수와 FNV-1a 지문
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))

from demo import tfx                                     # noqa: E402
from transformerlib import model as M                    # noqa: E402
from transformerlib import ops                           # noqa: E402
from transformerlib import sample as S                   # noqa: E402
from transformerlib import tensor as T                   # noqa: E402
from transformerlib import tokenizer as tk               # noqa: E402
from transformerlib import train as TR                   # noqa: E402
from transformerlib.rng import Rng                       # noqa: E402

PAR = os.path.join(BASE, 'ckpt', 'parity')
TOK = os.path.join(BASE, 'ckpt', 'tok')
CORPUS = os.path.join(BASE, 'corpus')
TINY = dict(V=11, T=6, d=8, L=2, h=2, d_ff=32)


def randt(shape, r, scale=1.0, grad=False):
    return T.Tensor([r.normal() * scale for _ in range(T.numel(shape))],
                    shape, requires_grad=grad)


def backward_with(out, dy):
    """출력에 임의의 윗기울기 dy 를 흘린다: Σ dy·out 의 역전파."""
    T.sum(T.mul(out, dy)).backward()


def matmul_fixture():
    r = Rng(101)
    a, b = randt((7, 5), r), randt((5, 3), r)
    tfx.write(os.path.join(PAR, 'matmul.tfx'),
              [('A', a.data), ('B', b.data),
               ('C', T.matmul(a, b).data)])


def ops_fixture():
    r = Rng(102)
    arrays = []
    x = randt((3, 6), r, 30.0)                 # 넘치기 쉬운 큰 로짓
    arrays += [('softmax_x', x.data),
               ('softmax_y', ops.softmax(x).data)]

    z = randt((4, 9), r, 3.0, grad=True)
    tg = [r.randint(9) for _ in range(4)]
    loss = ops.cross_entropy(z, tg)
    loss.backward()
    arrays += [('ce_z', z.data), ('ce_t', tg), ('ce_loss', loss.data),
               ('ce_dz', z.grad)]

    x = randt((3, 8), r, 2.0, grad=True)
    g = T.Tensor([1.0 + 0.3 * r.normal() for _ in range(8)], (8,),
                 requires_grad=True)
    b = randt((8,), r, 0.5, grad=True)
    y = ops.layernorm(x, g, b)
    dy = randt((3, 8), r)
    backward_with(y, dy)
    arrays += [('ln_x', x.data), ('ln_g', g.data), ('ln_b', b.data),
               ('ln_dy', dy.data), ('ln_y', y.data), ('ln_dx', x.grad),
               ('ln_dg', g.grad), ('ln_db', b.grad)]

    x = randt((20,), r, 2.5, grad=True)
    y = ops.gelu(x)
    dy = randt((20,), r)
    backward_with(y, dy)
    arrays += [('gelu_x', x.data), ('gelu_y', y.data),
               ('gelu_dy', dy.data), ('gelu_dx', x.grad)]

    s = randt((2, 5, 5), r, 2.0, grad=True)
    y = ops.causal_softmax(s)
    dy = randt((2, 5, 5), r)
    backward_with(y, dy)
    arrays += [('cs_x', s.data), ('cs_y', y.data), ('cs_dy', dy.data),
               ('cs_dx', s.grad)]
    tfx.write(os.path.join(PAR, 'ops.tfx'), arrays)


def reload(cfg, params, name):
    """체크포인트로 쓰고 다시 읽는다 — float32 로 반올림된 값에서
    계산해야 C 가 같은 파일을 읽어 견줄 수 있다."""
    path = os.path.join(PAR, name)
    TR.save_ckpt(path, cfg, params)
    return TR.load_ckpt(path)[1]


def model_fixture(pos):
    cfg = M.Config(pos=pos, **TINY)
    # 씨앗 9·×10: greedy 이어 쓰기가 한 토큰만 되풀이하지 않는 설정.
    # (씨앗 7 은 0 만 내서 대조가 아무것도 확인하지 못했다.)
    params = M.init_params(cfg, 9)
    for t in params.values():                # 0.02 는 너무 평평하다
        t.data[:] = [v * 10 for v in t.data]
    params = reload(cfg, params, 'tiny_%s.ckpt' % pos)
    for t in params.values():
        t.requires_grad = True
    r = Rng(103)
    ids = [[r.randint(cfg.V) for _ in range(cfg.T)] for _ in range(2)]
    tg = [[r.randint(cfg.V) for _ in range(cfg.T)] for _ in range(2)]
    logits, loss = M.forward(params, cfg, ids, tg)
    loss.backward()
    arrays = [('ids', sum(ids, [])), ('targets', sum(tg, [])),
              ('logits', logits.data), ('loss', loss.data)]
    arrays += [('grad_' + n, params[n].grad)
               for n in M.param_names(cfg)]
    tfx.write(os.path.join(PAR, 'tiny_%s.tfx' % pos), arrays)
    return params


def train_fixture():
    text = io.open(os.path.join(CORPUS, 'tasks', 'add_train.txt'),
                   encoding='utf-8').read()[:1300]
    vocab = tk.char_vocab(text)
    ids = tk.Tokenizer(vocab, []).encode(text)
    nl = vocab.index(b'\n')
    cfg = M.Config(V=len(vocab), T=8, d=8, L=2, h=2, d_ff=32)
    _, log = TR.train(cfg, ids, steps=20, B=4, lr_max=1e-2, warmup=5,
                      seed=5, newline=nl)
    tfx.write(os.path.join(PAR, 'train.tfx'), [
        ('config', [cfg.V, cfg.T, cfg.d, cfg.L, cfg.h, cfg.d_ff]),
        # 스텝·B·lr·워밍업·씨앗·줄바꿈 id
        ('run', [20, 4, 1e-2, 5, 5, nl]),
        ('tokens', ids), ('loss', [row[1] for row in log]),
        ('lr', [row[2] for row in log]),
        ('norm', [row[3] for row in log])])


def sample_fixture(params):
    cfg = M.Config(**TINY)
    out = S.generate(params, cfg, [1, 2, 3], 12, 0.0, None, None,
                     seed=0)
    tfx.write(os.path.join(PAR, 'sample.tfx'),
              [('prompt', [1, 2, 3]), ('greedy', out)])


def vocab_for(name):
    if name.startswith('ko/'):
        return 'ko512'
    if name.startswith('en/'):
        return 'en512'
    task = name.split('/')[1].split('_')[0]
    return 'add' if task == 'addplain' else task


def tokens_fixture():
    files = []
    for sub in ('ko', 'en', 'tasks'):
        d = os.path.join(CORPUS, sub)
        files += ['%s/%s' % (sub, n) for n in sorted(os.listdir(d))]
    read = lambda n: io.open(os.path.join(CORPUS, n), encoding='utf-8',
                             newline='').read()
    ko = ''.join(read(n) for n in files if n.startswith('ko/'))
    tk.save(os.path.join(TOK, 'ko512'), *tk.train_bpe(ko, 512))
    en = ''.join(read(n) for n in files if n.startswith('en/'))
    tk.save(os.path.join(TOK, 'en512'), *tk.train_bpe(en, 512))
    for task in ('add', 'sort', 'reverse', 'parity'):
        text = read('tasks/%s_train.txt' % task)
        tk.save(os.path.join(TOK, task), tk.char_vocab(text), [])
    toks = {}
    lines = ['== 1. 말뭉치 파일마다 토큰 수와 .bin 지문 ==',
             '# 파일\t어휘\t바이트\t토큰\tFNV-1a64']
    for n in files:
        v = vocab_for(n)
        if v not in toks:
            toks[v] = tk.Tokenizer(*tk.load(os.path.join(TOK, v)))
        text = read(n)
        ids = toks[v].encode(text)
        raw = b''.join(i.to_bytes(2, 'little') for i in ids)
        lines.append('%s\t%s\t%d\t%d\t%016x'
                     % (n, v, len(text.encode('utf-8')), len(ids),
                        tfx.fnv1a64(raw)))
    with io.open(os.path.join(BASE, 'out', 'parity_tokens.txt'), 'w',
                 encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')


def main():
    for d in (PAR, TOK):
        if not os.path.isdir(d):
            os.makedirs(d)
    matmul_fixture()
    ops_fixture()
    learned = model_fixture('learned')
    model_fixture('sin')
    model_fixture('rope')
    train_fixture()
    sample_fixture(learned)
    tokens_fixture()
    print('대조 자료 → ckpt/parity · ckpt/tok · out/parity_tokens.txt')


if __name__ == '__main__':
    main()
