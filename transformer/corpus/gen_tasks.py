# -*- coding: utf-8 -*-
"""합성 과제 만들기 — 씨앗이 정해져 있어 몇 번을 돌려도 같은 파일.

    python3 corpus/gen_tasks.py           # corpus/tasks/*.txt 를 쓴다
    python3 corpus/gen_tasks.py --check   # 지금 파일과 같은지만 본다

과제 넷, 한 줄에 한 문제다. 줄 모양이 일정해야 학습 배치를 줄 머리에
맞춰 자를 수 있다(SPEC.md §6.1 aligned).

  덧셈   042+915=7590   세 자리 둘의 합을 네 자리로, **뒤집어** 적는다
  정렬   qwerty>eqrtwy  소문자 여섯 개를 가나다순으로
  뒤집기 qwerty<ytrewq  소문자 여섯 개를 거꾸로
  홀짝   0110100111010010=0  열여섯 비트의 1 의 개수가 홀수면 1

덧셈 답을 뒤집는 까닭: 사람이 손으로 더할 때처럼 일의 자리부터
적게 하면, 받아올림이 이미 적은 자리에서 오므로 앞을 내다볼 일이
없다. 뒤집지 않은 판과 견주는 실험은 8부에 있다.

훈련과 시험은 **처음부터 겹치지 않게** 만든다. 가능한 문제를 전부
늘어놓고(또는 중복 없이 뽑고) 섞은 뒤 앞쪽을 시험, 그다음을 훈련으로
자른다. 시험 문제가 훈련에 섞이면 정확도는 외운 양을 잰다.
시간 O(문제 공간) — 덧셈 100만 개를 섞는 것이 가장 크다.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'py'))
from transformerlib.rng import Rng                  # noqa: E402

TASKS = os.path.join(HERE, 'tasks')
LETTERS = 'abcdefghijklmnopqrstuvwxyz'

# (과제, 씨앗, 시험 수, 훈련 수)
# 훈련 수는 말뭉치 전체를 1.5 MB 안에 두려고 정했다(PLAN.md §1).
PLAN = [('add', 1001, 1000, 12000),
        ('addplain', 1001, 1000, 12000),
        ('sort', 1002, 1000, 6000),
        ('reverse', 1003, 1000, 6000),
        ('parity', 1004, 1000, 4000)]


def add_line(k, plain=False):
    a, b = divmod(k, 1000)
    s = '%04d' % (a + b)
    return '%03d+%03d=%s\n' % (a, b, s if plain else s[::-1])


def letters(r, n=6):
    return ''.join(LETTERS[r.randint(26)] for _ in range(n))


def unique(r, count, make):
    """중복 없이 count 개 — 나온 차례를 지킨다. O(count)."""
    seen, out = set(), []
    while len(out) < count:
        x = make(r)
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def problems(task, seed, n):
    r = Rng(seed)
    if task in ('add', 'addplain'):
        # 같은 씨앗 → 같은 섞음. 두 덧셈 판은 문제가 같고
        # 답을 적는 차례만 다르다.
        order = r.permutation(1000 * 1000)
        return [add_line(k, task == 'addplain') for k in order[:n]]
    if task == 'sort':
        xs = unique(r, n, letters)
        return ['%s>%s\n' % (x, ''.join(sorted(x))) for x in xs]
    if task == 'reverse':
        xs = unique(r, n, letters)
        return ['%s<%s\n' % (x, x[::-1]) for x in xs]
    if task == 'parity':
        xs = unique(r, n, lambda g: ''.join('01'[g.randint(2)]
                                            for _ in range(16)))
        return ['%s=%d\n' % (x, x.count('1') % 2) for x in xs]
    raise ValueError(task)


def build():
    """{파일 이름: 내용}"""
    files = {}
    for task, seed, n_test, n_train in PLAN:
        lines = problems(task, seed, n_test + n_train)
        files['%s_test.txt' % task] = ''.join(lines[:n_test])
        files['%s_train.txt' % task] = ''.join(lines[n_test:])
    return files


def main(argv):
    files = build()
    if '--check' in argv:
        bad = [n for n, t in sorted(files.items())
               if not os.path.exists(os.path.join(TASKS, n))
               or io.open(os.path.join(TASKS, n), encoding='utf-8',
                          newline='').read() != t]
        for n in bad:
            print('  ✗ tasks/%s 가 씨앗에서 만든 것과 다르다' % n)
        print('과제 파일 %d개 — 어긋남 %d건' % (len(files), len(bad)))
        return 1 if bad else 0
    if not os.path.isdir(TASKS):
        os.makedirs(TASKS)
    for name, text in sorted(files.items()):
        with io.open(os.path.join(TASKS, name), 'w', encoding='utf-8',
                     newline='\n') as f:
            f.write(text)
        print('  tasks/%-20s %6d줄 %8d바이트'
              % (name, text.count('\n'), len(text.encode('utf-8'))))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
