#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""실험을 전부 차례로 돌려 out/ 를 다시 채운다 (PLAN.md §3.2).

    python3 run_all.py              # 전부
    python3 run_all.py --only merge # 이름에 merge 가 든 실험만
    python3 run_all.py --check      # 폭 검사와 manifest 대조만

덱에 실리는 캡처는 하나도 손으로 쓰지 않는다. 전부 여기서 진짜 git
(또는 mygit)을 돌려 나온다. 그래서 이 파일과 exps/ 는 덱의 **증거
목록** 이다.

  · 격리: 실험마다 scratch/repos/<이름>/ 을 새로 만든다. 이 덱의
    저장소(treasure_house)에는 git 명령을 한 번도 부르지 않는다
    (PLAN.md §0.11) — GIT_CEILING_DIRECTORIES 로 위를 막는다.
  · 결정론: tools/gitenv.sh 의 환경(고정 시각·설정 파일 없음). 그래도
    남는 것 — 이 기계의 scratch 절대 경로 — 은 /work 로 바꿔 적고,
    덱의 캡션이 그 사실을 밝힌다.
  · 폭: 캡처 한 줄이 108칸을 넘으면 폴더블 접힘에서 비어져 나간다.
  · 재현: out/manifest.json 에 파일마다 SHA-256 을 남긴다.
    tools/record.sh --check 가 세 번 돌려 같은지 본다.
"""
import hashlib
import importlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
SCRATCH = os.path.join(HERE, 'scratch')
REPOS = os.path.join(SCRATCH, 'repos')
MAX_COLS = 108
WORK = '/work'                  # 캡처에 적는 scratch/repos 의 이름

sys.path.insert(0, os.path.join(HERE, 'tools'))
sys.path.insert(0, os.path.join(HERE, 'deck'))
import gitenv                   # noqa: E402
from build_deck import gitslug  # noqa: E402  같은 규칙이어야 한다

# 실험 모듈의 차례 — 덱의 부 차례를 따른다(가벼운 것부터)
ORDER = ['hello', 'concepts', 'objects', 'anatomy', 'tree_sort',
         'refs', 'refs2', 'index', 'index2', 'cmds', 'dag', 'merge',
         'merge2', 'rebase', 'rebase2', 'diff', 'diff2', 'pack',
         'pack2', 'proto', 'proto2', 'collab', 'config_hooks',
         'tools2', 'limits', 'daily', 'recovery', 'mygit', 'cmdref',
         'history', 'appendix', 'demos']


def cells(s):
    n = 0
    for ch in s:
        if unicodedata.combining(ch):
            continue
        n += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return n


class Repo(object):
    """실험 저장소 하나 — scratch/repos/<name>/ 에서 명령을 돌린다.

    cap() 은 명령을 돌리고 out/<label>__<gitslug>.txt 로 남긴다. 첫
    줄은 '$ 명령' 이고 그 아래가 표준 출력·표준 오류를 합친 것(sh 의
    2>&1), 0 이 아닌 종료 코드는 끝에 '[exit N]' 으로 적는다. 같은
    명령을 한 저장소에서 두 번 찍을 때는 label 을 바꿔 부른다.
    """

    written = set()             # 한 번의 run_all 에서 쓴 캡처 이름들

    def __init__(self, name, env, label=None):
        self.name, self.label = name, label or name
        self.path = os.path.join(REPOS, name)
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        os.makedirs(self.path)
        self.env = dict(env)
        self.cwd = self.path

    def at(self, sub):
        """하위 디렉터리에서 명령을 돌리게 한다(장면의 cd)."""
        self.cwd = os.path.normpath(os.path.join(self.path, sub))
        os.makedirs(self.cwd, exist_ok=True)
        return self

    def _run(self, cmd, stdin):
        """입력이 없으면 /dev/null — 무엇을 묻는 명령이 멈추지 않게."""
        extra = {'input': stdin} if stdin is not None \
            else {'stdin': subprocess.DEVNULL}
        return subprocess.run(['sh', '-c', cmd], cwd=self.cwd,
                              env=self.env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, **extra)

    def sh(self, cmd, stdin=None, ok=(0,)):
        """캡처 없이 돌린다. 기대한 종료 코드가 아니면 멈춘다 —
        실험의 준비가 조용히 실패한 채 캡처가 남으면 안 되기 때문."""
        p = self._run(cmd, stdin)
        if ok is not None and p.returncode not in ok:
            raise RuntimeError('[%s] %s → %d\n%s'
                               % (self.name, cmd, p.returncode,
                                  p.stdout.decode('utf-8', 'replace')))
        return p.stdout.decode('utf-8', 'replace')

    def norm(self, text):
        """절대 경로를 /work 로, 그리고 진행 표시처럼 \\r 로 덮어쓰는
        조각은 터미널이 마지막에 보여 주는 것만 남긴다."""
        text = text.replace(REPOS, WORK).replace(SCRATCH, '/scratch')
        text = text.replace('\r\n', '\n')
        return re.sub(r'[^\n]*\r(?!\n)', '', text)

    def cap(self, cmd, label=None, ok=(0,), stdin=None, edit=None):
        """돌리고 캡처한다. edit 은 정규화 함수(캡션에 적을 것)."""
        p = self._run(cmd, stdin)
        text = self.norm(p.stdout.decode('utf-8', 'replace'))
        if edit:
            text = edit(text)
        if ok is not None and p.returncode not in ok:
            raise RuntimeError('[%s] %s → %d\n%s'
                               % (self.name, cmd, p.returncode, text))
        if text and not text.endswith('\n'):
            text += '\n'
        if p.returncode:
            text += '[exit %d]\n' % p.returncode
        save('%s__%s.txt' % (label or self.label, gitslug(cmd)),
             '$ %s\n%s' % (cmd, text))
        return text

    def write(self, rel, data, mode=None):
        """작업 트리에 파일을 쓴다(바이트나 글자)."""
        p = os.path.join(self.cwd, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'wb') as f:
            f.write(data.encode('utf-8') if isinstance(data, str)
                    else data)
        if mode is not None:
            os.chmod(p, mode)


def write(name, text):
    """out/ 에 캡처나 표를 쓴다 — 줄바꿈은 늘 \\n."""
    with io.open(os.path.join(OUT, name), 'w', encoding='utf-8',
                 newline='\n') as f:
        f.write(text)


def save(name, text):
    """캡처 하나를 남긴다 — 한 번의 run_all 안에서 이름이 겹치면 멈춘다
    (뒤의 것이 앞의 것을 조용히 덮으면 덱이 엉뚱한 출력을 싣는다)."""
    if name in Repo.written:
        raise RuntimeError('캡처 이름이 겹친다: out/%s — label 을 '
                           '바꿔 부를 것' % name)
    Repo.written.add(name)
    write(name, text)


def table(name, head, rows, caption=''):
    """out/tbl_<name>.html — <!--TABLE--> 로 실리는 측정 표."""
    esc = lambda s: (str(s).replace('&', '&amp;').replace('<', '&lt;')
                     .replace('>', '&gt;'))
    lines = ['<table class="data">']
    if caption:
        lines.append('<caption>%s</caption>' % esc(caption))
    lines.append('<tr>' + ''.join('<th>%s</th>' % esc(h) for h in head)
                 + '</tr>')
    for r in rows:
        lines.append('<tr>' + ''.join('<td>%s</td>' % esc(c) for c in r)
                     + '</tr>')
    lines.append('</table>')
    write('tbl_%s.html' % name, '\n'.join(lines) + '\n')


class Ctx(object):
    """실험 모듈이 받는 것 — 결정론 환경과 저장소 만들기."""

    def __init__(self):
        self.env = gitenv.load(os.path.join(SCRATCH, 'home'))
        # 위로 올라가다 treasure_house 를 찾지 않게 (PLAN.md §0.11)
        self.env['GIT_CEILING_DIRECTORIES'] = REPOS
        self.write, self.table, self.save = write, table, save

    def repo(self, name, init=True, label=None, bare=False):
        """새 저장소. init 이면 git init -b main 까지(§0.9)."""
        r = Repo(name, self.env, label)
        if init:
            r.sh('git init -q %s-b main' % ('--bare ' if bare else ''))
        return r


def run(only):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(REPOS, exist_ok=True)
    ctx = Ctx()
    if not only:            # 전부 다시 뜰 때는 옛 캡처를 먼저 비운다
        for f in os.listdir(OUT):
            if '__' in f and f.endswith('.txt'):
                os.remove(os.path.join(OUT, f))
    for name in ORDER:
        if only and only not in name:
            continue
        path = os.path.join(HERE, 'exps', name + '.py')
        if not os.path.exists(path):
            continue
        before = len(Repo.written)
        importlib.import_module('exps.' + name).run(ctx)
        print('  %-14s 캡처 %d개' % (name, len(Repo.written) - before))
        sys.stdout.flush()


def width_problems():
    bad = []
    for name in sorted(os.listdir(OUT)):
        if not name.endswith('.txt'):
            continue
        text = io.open(os.path.join(OUT, name), encoding='utf-8').read()
        for i, line in enumerate(text.split('\n'), 1):
            w = cells(line)
            if w > MAX_COLS:
                bad.append('out/%s:%d %d칸 (최대 %d)'
                           % (name, i, w, MAX_COLS))
            # NUL 은 화면에 안 보이고 덱의 글꼴 내장을 멈춘다 — 캡처
            # 명령에서 tr '\0' '@' 로 바꿔 둘 것(11부의 광고 줄)
            if '\0' in line:
                bad.append('out/%s:%d NUL 바이트' % (name, i))
    return bad


def manifest():
    out = {}
    for name in sorted(os.listdir(OUT)):
        if name.endswith('.txt') or name.endswith('.html'):
            raw = io.open(os.path.join(OUT, name), 'rb').read()
            out[name] = hashlib.sha256(raw).hexdigest()
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
    old = json.load(io.open(p, encoding='utf-8')) \
        if os.path.exists(p) else {}
    if '--check' in argv:
        stale = sorted(k for k in man if old.get(k) != man[k])
        for k in stale:
            print('  ✗ out/%s 가 manifest 와 어긋난다' % k)
        if stale:
            return 1
    else:
        io.open(p, 'w', encoding='utf-8', newline='\n').write(
            json.dumps(man, indent=1, sort_keys=True) + '\n')
    print('캡처 %d개 · 108칸 넘는 줄 %d개' % (len(man), len(bad)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
