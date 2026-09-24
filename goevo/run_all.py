#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""실험을 전부 차례로 돌려 out/ 를 다시 채운다 (PLAN.md §3.3).

    python3 run_all.py              # 전부 (exps/ORDER 차례)
    python3 run_all.py --only p07   # 묶음 하나 — 그 묶음의 옛 캡처를 먼저 지운다
    python3 run_all.py --check      # 폭 검사와 manifest 대조만

덱에 실리는 go 출력은 하나도 손으로 쓰지 않는다. 전부 여기서 이 기계의
go 1.27.1 을 돌려 나온다. 그래서 이 파일과 exps/ 는 덱의 **증거 목록** 이다.

  · 실험 묶음: exps/<이름>.py 가 run(ctx) 하나를 내놓는다. 차례는
    exps/ORDER — 덱의 부 차례다. 묶음이 쓴 캡처는 out/batches.json 에
    적어 두고, --only 로 다시 돌릴 때 그 목록을 먼저 지운다 — 이름을
    바꾼 캡처가 유령으로 남아 덱이 옛 출력을 싣던 일이 git 덱에서 있었다.
  · ctx.go(): 예제 하나를 tools/gover.py 로 돌려 out/<goverslug>.txt 에
    남긴다. 이름과 첫 줄('$ 명령')의 규칙은 deck/build_deck.py 의
    goverslug()·gover_cmdline() 이 정한다 — 조립기와 한 규칙이어야 한다.
    기대한 종료 코드(expect)가 아니면 멈춘다: '1.21 로 내리면 컴파일이
    거절된다' 는 캡처가 뜻밖에 통과했다면 슬라이드의 주장이 틀린 것이다.
  · 폭: 캡처 한 줄이 108칸을 넘으면 폴더블 접힘에서 비어져 나간다.
  · 재현: out/manifest.json 에 파일마다 SHA-256. tools/record.sh --check 가
    세 번 돌려 같은지 본다.
"""
import hashlib
import importlib
import io
import json
import os
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = HERE
OUT = os.path.join(HERE, 'out')
# 캡처 줄의 상한. 108칸을 넘는 줄은 덱이 화면에서 접어 싣고(term wrap),
# 200칸을 넘으면 못 싣는다 — deck/build_deck.py 의 MAX_WRAP_COLS 와 같다.
MAX_COLS = 200

sys.path.insert(0, os.path.join(HERE, 'tools'))
sys.path.insert(0, os.path.join(HERE, 'deck'))
import gover                                          # noqa: E402
from build_deck import goverslug, gover_cmdline       # noqa: E402


def cells(s):
    n = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        n += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return n


def write(name, text):
    """out/ 에 캡처나 표를 쓴다 — 줄바꿈은 늘 \\n."""
    with io.open(os.path.join(OUT, name), 'w', encoding='utf-8',
                 newline='\n') as f:
        f.write(text)


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;'))


class Ctx(object):
    """실험 묶음 하나가 받는 것."""

    taken = set()                 # 한 번의 run_all 에서 쓴 이름 전부

    def __init__(self, batch):
        self.batch = batch
        self.written = set()

    def save(self, name, text):
        """이름이 겹치면 멈춘다 — 뒤의 것이 앞의 것을 조용히 덮으면
        덱이 엉뚱한 출력을 싣는다."""
        if name in Ctx.taken or name in self.written:
            raise RuntimeError('캡처 이름이 겹친다: out/%s — tag 를 달 것'
                               % name)
        Ctx.taken.add(name)
        self.written.add(name)
        write(name, text)

    def go(self, ex, cmd='go run .', v=None, godebug=None, exp=None,
           tag=None, expect=0):
        """ex/… 예제에서 cmd 를 돌려 캡처한다 → 정규화한 출력."""
        src = os.path.join(BASE, ex)
        v = v or gover.mod_version(src)
        lang = v if v != gover.mod_version(src) else None
        stem = goverslug(ex, v=v, godebug=godebug, exp=exp, tag=tag)
        code, text = gover.execute(src, cmd, lang=lang, godebug=godebug,
                                   exp=exp, name=stem)
        ok = expect if isinstance(expect, (tuple, list)) else (expect,)
        if expect is not None and code not in ok:
            raise RuntimeError('[%s] %s (go %s) → 종료 %d, 기대 %s\n%s'
                               % (self.batch, ex, v, code, expect, text))
        if text and not text.endswith('\n'):
            text += '\n'
        if code:
            text += '[exit %d]\n' % code
        self.save(stem + '.txt', '$ %s\n%s'
                  % (gover_cmdline(cmd, godebug, exp), text))
        return text

    def table(self, name, head, rows, caption=''):
        """out/tbl_<name>.html — <!--TABLE--> 로 실리는 측정 표."""
        lines = ['<table class="data">']
        if caption:
            lines.append('<caption>%s</caption>' % esc(caption))
        lines.append('<tr>' + ''.join('<th>%s</th>' % esc(h) for h in head)
                     + '</tr>')
        for r in rows:
            lines.append('<tr>' + ''.join('<td>%s</td>' % esc(c) for c in r)
                         + '</tr>')
        lines.append('</table>')
        self.save('tbl_%s.html' % name, '\n'.join(lines) + '\n')


def load_batches():
    p = os.path.join(OUT, 'batches.json')
    if not os.path.exists(p):
        return {}
    with io.open(p, encoding='utf-8') as f:
        return json.load(f)


def save_batches(b):
    with io.open(os.path.join(OUT, 'batches.json'), 'w', encoding='utf-8',
                 newline='\n') as f:
        f.write(json.dumps(b, indent=1, sort_keys=True) + '\n')


def clear_batch(batch):
    """그 묶음이 지난번에 쓴 캡처를 지운다."""
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
    for name in names:
        if not os.path.exists(os.path.join(HERE, 'exps', name + '.py')):
            print('  %-14s (아직 없다)' % name)     # 그 부를 아직 안 썼다
            continue
        clear_batch(name)
        ctx = Ctx(name)
        importlib.import_module('exps.' + name).run(ctx)
        batches[name] = sorted(ctx.written)
        save_batches(batches)
        print('  %-14s 캡처 %d개' % (name, len(ctx.written)))
        sys.stdout.flush()


def width_problems():
    bad = []
    for name in sorted(os.listdir(OUT)):
        if not name.endswith('.txt'):
            continue
        with io.open(os.path.join(OUT, name), encoding='utf-8') as f:
            text = f.read()
        for i, line in enumerate(text.split('\n'), 1):
            w = cells(line.expandtabs(8))
            if w > MAX_COLS:
                bad.append('out/%s:%d %d칸 (최대 %d)' % (name, i, w, MAX_COLS))
            if '\0' in line:
                bad.append('out/%s:%d NUL 바이트' % (name, i))
    return bad


def manifest():
    out = {}
    for name in sorted(os.listdir(OUT)):
        if name.endswith('.txt') or name.endswith('.html'):
            with open(os.path.join(OUT, name), 'rb') as f:
                out[name] = hashlib.sha256(f.read()).hexdigest()
    return out


def main(argv):
    only = argv[argv.index('--only') + 1] if '--only' in argv else None
    if '--check' not in argv:
        print('실험을 돌린다 —')
        run(only)
    bad = width_problems()
    for line in bad:
        print('  ✗ ' + line)
    man = manifest()
    p = os.path.join(OUT, 'manifest.json')
    old = {}
    if os.path.exists(p):
        with io.open(p, encoding='utf-8') as f:
            old = json.load(f)
    if '--check' in argv:
        stale = sorted(k for k in set(man) | set(old)
                       if old.get(k) != man.get(k))
        for k in stale:
            print('  ✗ out/%s 가 manifest 와 어긋난다' % k)
        if stale:
            return 1
    else:
        with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(man, indent=1, sort_keys=True) + '\n')
    print('캡처 %d개 · 200칸 넘는 줄 %d개' % (len(man), len(bad)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
