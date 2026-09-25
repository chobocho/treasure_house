#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""실험을 전부 차례로 돌려 out/ 를 다시 채운다 (PLAN.md §3.3, §5 7단계).

    python3 run_all.py              # 전부 (exps/ORDER 차례)
    python3 run_all.py --only p09   # 묶음 하나 — 그 묶음의 옛 캡처를
    먼저 지운다
    python3 run_all.py --check      # 폭 검사와 manifest 대조만

덱에 실리는 출력은 하나도 손으로 쓰지 않는다. 전부 여기서 이 기계의
python3·node 로 시뮬레이터와 예제를 돌려 나온다. 그래서 이 파일과
exps/ 는 덱의 **증거 목록** 이다.

  · 실험 묶음: exps/<이름>.py 가 run(ctx) 하나를 내놓는다. 차례는
    exps/ORDER — 덱의 부 차례다. 묶음이 쓴 파일은 out/batches.json 에
    적어 두고, --only 로 다시 돌릴 때 그 목록을 먼저 지운다(이름을 바꾼
    캡처가 유령으로 남던 일이 git 덱에서 있었다).
  · ctx.cmd(): 명령 하나를 돌려 out/<이름>.txt 에 '$ 명령' 첫 줄과 함께
    남긴다. 기대한 종료 코드가 아니면 멈춘다 — 캡처가 뜻밖에 성공하면
    슬라이드의 주장이 틀린 것이다.
  · ctx.red()/green(): tools/testcap.py 로 모듈 하나의 시험 결과를 시간
    없이 남긴다(14부의 RED → GREEN).
  · ctx.table(): out/tbl_<이름>.html — <!--TABLE--> 로 실리는 측정 표.
  · ctx.show(): out/show_<이름>.json — <!--SHOW--> 가 그리는 쇼 파일.
  · 재현: out/manifest.json 에 파일마다 SHA-256. tools/record.sh --check
  가
    세 번 돌려 같은지 본다. 이 기계는 메모리가 빠듯하다 — 실험은
    하나씩, 묶음마다 60초 안쪽을 목표로 한다(PLAN.md §0.8).
"""
import hashlib
import importlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
MAX_COLS = 200          # deck/build_deck.py 의 MAX_WRAP_COLS 와 같다
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'py'))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import testcap                                        # noqa: E402


def cells(s):
    return sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1
               for c in s)


def write(name, text):
    with io.open(os.path.join(OUT, name), 'w', encoding='utf-8',
                 newline='\n') as f:
        f.write(text)


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;'))


# node --test 의 보고에는 걸린 시간이 섞인다 — 캡처에서 지운다
# (지웠다는 사실은 슬라이드 캡션이 말한다).
TIMING = re.compile(r' \(\d+(?:\.\d+)?ms\)|^ℹ duration_ms .*$', re.M)


class Ctx(object):
    """실험 묶음 하나가 받는 것."""
    taken = set()

    def __init__(self, batch):
        self.batch = batch
        self.written = set()

    def save(self, name, text):
        if name in Ctx.taken or name in self.written:
            raise RuntimeError('캡처 이름이 겹친다: out/%s' % name)
        Ctx.taken.add(name)
        self.written.add(name)
        write(name, text)

    def cmd(self, name, argv, expect=0, strip_timing=False, env=None):
        """argv 를 drone/ 에서 돌린다 → out/<name>.txt. 출력을 돌려준다.

        env 로 준 변수는 캡처 첫 줄에도 'VAR=값 명령' 으로 적는다 —
        독자가 그대로 따라 칠 수 있어야 한다."""
        extra = env or {}
        env = dict(os.environ, PYTHONHASHSEED='0', LANG='C.UTF-8',
                   PYTHONDONTWRITEBYTECODE='1', TZ='UTC', **extra)
        r = subprocess.run(argv, cwd=HERE, env=env,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        text = r.stdout.decode('utf-8')
        if strip_timing:
            text = TIMING.sub('', text)
            text = '\n'.join(l for l in text.split('\n')
                             if l.strip() != '') + '\n'
        ok = expect if isinstance(expect, (tuple, list)) else (expect,)
        if expect is not None and r.returncode not in ok:
            raise RuntimeError('[%s] %s → 종료 %d, 기대 %s\n%s'
                               % (self.batch, ' '.join(argv),
                                  r.returncode, expect, text))
        shown = ''.join('%s=%s ' % kv for kv in sorted(extra.items()))
        # 따라 칠 수 있게 셸 따옴표를 붙인다('-c' 뒤의 코드 같은 것)
        shown += ' '.join('python3' if a == sys.executable
                          else shlex.quote(a) for a in argv)
        if r.returncode:
            text += '[exit %d]\n' % r.returncode
        self.save(name + '.txt', '$ %s\n%s' % (shown, text))
        return text

    def py(self, name, *args, **kw):
        return self.cmd(name, [sys.executable] + list(args), **kw)

    def red(self, module):
        out = io.StringIO()
        testcap.run('red', module, out)
        self.save('red_%s.txt' % module,
                  '$ python3 tools/testcap.py red %s\n%s'
                  % (module, out.getvalue()))

    def green(self, module):
        out = io.StringIO()
        code = testcap.run('green', module, out)
        if code:
            raise RuntimeError('[%s] %s 시험이 초록이 아니다\n%s'
                               % (self.batch, module, out.getvalue()))
        self.save('green_%s.txt' % module, '$ python3 tools/testcap.py '
                  'green %s\n%s' % (module, out.getvalue()))

    def text(self, name, body):
        """계산 결과를 글로 — 첫 줄에 무엇을 돌렸는지 적는 것은 호출자
        몫."""
        self.save(name + '.txt', body if body.endswith('\n')
                  else body + '\n')

    def table(self, name, head, rows, caption='', num=()):
        """out/tbl_<name>.html. num 은 오른쪽 정렬할 열 번호들."""
        lines = ['<table class="data">']
        if caption:
            lines.append('<caption>%s</caption>' % esc(caption))
        lines.append('<tr>' + ''.join(
            '<th%s>%s</th>' % (' class="num"' if i in num else '',
                               esc(h))
            for i, h in enumerate(head)) + '</tr>')
        for r in rows:
            lines.append('<tr>' + ''.join(
                '<td%s>%s</td>' % (' class="num"' if i in num else '',
                                   esc(c)) for i, c in enumerate(r))
                + '</tr>')
        lines.append('</table>')
        self.save('tbl_%s.html' % name, '\n'.join(lines) + '\n')

    def adopt(self, name):
        """명령이 직접 out/ 에 쓴 파일을 이 묶음의 것으로 등록한다."""
        if not os.path.exists(os.path.join(OUT, name)):
            raise RuntimeError('[%s] out/%s 가 만들어지지 않았다'
                               % (self.batch, name))
        if name in Ctx.taken or name in self.written:
            raise RuntimeError('캡처 이름이 겹친다: out/%s' % name)
        Ctx.taken.add(name)
        self.written.add(name)

    def show(self, name, show):
        from droneshow import show as SH
        self.save('show_%s.json' % name, SH.dumps(show))


def load_batches():
    p = os.path.join(OUT, 'batches.json')
    if not os.path.exists(p):
        return {}
    with io.open(p, encoding='utf-8') as f:
        return json.load(f)


def save_batches(b):
    write('batches.json',
          json.dumps(b, indent=1, sort_keys=True) + '\n')


def clear_batch(batch):
    for name in load_batches().get(batch, []):
        p = os.path.join(OUT, name)
        if os.path.exists(p):
            os.remove(p)


def order():
    p = os.path.join(HERE, 'exps', 'ORDER')
    if not os.path.exists(p):
        return []
    with io.open(p, encoding='utf-8') as f:
        return [l.split('#')[0].strip() for l in f
                if l.split('#')[0].strip()]


def run(only):
    os.makedirs(OUT, exist_ok=True)
    Ctx.taken = set()
    batches = load_batches()
    names = [n for n in order() if not only or n == only]
    if only and not names:
        raise SystemExit('exps/ORDER 에 %s 가 없다' % only)
    if not only:
        for b in list(batches):
            clear_batch(b)
        batches = {}
    else:
        # 다른 묶음이 이미 쓴 이름과 겹치는지도 본다
        for b, files in batches.items():
            if b != only:
                Ctx.taken.update(files)
    for name in names:
        if not os.path.exists(os.path.join(HERE, 'exps', name + '.py')):
            print('  %-14s (아직 없다)' % name)
            continue
        clear_batch(name)
        ctx = Ctx(name)
        importlib.import_module('exps.' + name).run(ctx)
        batches[name] = sorted(ctx.written)
        save_batches(batches)
        print('  %-14s 파일 %d개' % (name, len(ctx.written)))
        sys.stdout.flush()


def width_problems():
    bad = []
    for name in sorted(os.listdir(OUT)):
        if not name.endswith('.txt'):
            continue
        with io.open(os.path.join(OUT, name), encoding='utf-8') as f:
            for i, line in enumerate(f.read().split('\n'), 1):
                w = cells(line.expandtabs(8))
                if w > MAX_COLS:
                    bad.append('out/%s:%d  %d칸' % (name, i, w))
    return bad


def manifest():
    """실험 묶음이 쓴 파일(batches.json)만의 SHA-256.

    out/ 에는 deck/gen_tables.py 가 자료에서 만드는 표(tbl_d_*)도
    있다. 그것은 실험의 결과가 아니라 자료의 모습이라 여기서 세지
    않고, gen_tables.py --check 가 따로 본다."""
    rows = {}
    for batch in load_batches().values():
        for name in batch:
            p = os.path.join(OUT, name)
            if os.path.exists(p):
                with open(p, 'rb') as f:
                    rows[name] = hashlib.sha256(f.read()).hexdigest()
    return dict(sorted(rows.items()))


def main(argv):
    if '--check' in argv:
        bad = width_problems()
        p = os.path.join(OUT, 'manifest.json')
        want = {}
        if os.path.exists(p):
            want = json.load(io.open(p, encoding='utf-8'))
        got = manifest()
        for n in sorted(set(want) | set(got)):
            if want.get(n) != got.get(n):
                bad.append('manifest 와 다르다: out/%s' % n)
        for b in bad:
            print('  ✗ ' + b)
        print('  out/ 파일 %d개 — 문제 %d건' % (len(got), len(bad)))
        return 1 if bad else 0
    only = argv[argv.index('--only') + 1] if '--only' in argv else None
    run(only)
    write('manifest.json', json.dumps(manifest(), indent=1,
                                      sort_keys=True) + '\n')
    bad = width_problems()
    for b in bad:
        print('  ✗ ' + b)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
