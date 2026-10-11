#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rsrun — 예제 하나를 진짜 rustc 로 컴파일해 돌리고, 그 화면을 out/ 에 남긴다.

   이 덱에서 코드를 돌리는 것은 이 도구 하나뿐이다(PLAN.md §2). 조립기는
   여기서 남긴 캡처를 싣기만 하고, 캡처가 소스보다 낡았으면 조립을 거부한다.

     python3 tools/rsrun.py ex/06/move.rs      돌려서 out/06/move.txt 를 쓴다
     python3 tools/rsrun.py --check ex/06      다시 돌려 이미 있는 캡처와 같은지만 본다
     python3 tools/rsrun.py --all --stale      캡처가 없거나 낡은 것만 돌린다
     python3 tools/rsrun.py --manifest-check   돌리지 않고 해시만 대조한다

   예제의 꼴은 둘이다.
     ex/NN/name.rs   파일 하나. 파일 **끝**에 `//@ key: value` 지시자를 둔다.
                     끝에 두는 까닭 — 컴파일러가 말하는 줄 번호가 슬라이드의 줄
                     번호와 같아야 하기 때문이다(지시자는 컴파일 전에 떼어 낸다).
     ex/NN/name/     여러 파일. RUN 파일에 셸 명령을 한 줄에 하나씩 적는다.

   캡처에 손대는 곳은 normalize() 의 세 가지뿐이다 — 스레드 번호, 걸린 시간,
   작업 디렉터리 경로. 실행할 때마다 달라져 "두 번 돌려 같다" 를 깨는 것들이다.
"""
import argparse
import fcntl
import hashlib
import io
import os
import re
import shutil
import signal
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      # rust/
TERMUX = os.environ.get('RSRUN_PREFIX', '/data/data/com.termux/files/usr')
RUSTC = os.path.join(TERMUX, 'bin', 'rustc')
CARGO = os.path.join(TERMUX, 'bin', 'cargo')
# proot 안의 cc 는 glibc 용이라 안드로이드 대상(-llog, -lunwind)을 못 잇는다.
LINKER = os.path.join(TERMUX, 'bin', 'clang')

EDITIONS = ('2015', '2018', '2021', '2024')
KEYS = ('edition', 'expect', 'exit', 'flags', 'test', 'norun', 'warnings',
        'args', 'stdin')
COMPILE_TIMEOUT = 120
RUN_TIMEOUT = 10
DIRECTIVE = re.compile(r'^//@\s*([a-z]+)\s*(?::\s*(.*?))?\s*$')


class RsrunError(Exception):
    pass


def _read(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()


def _bytes(p):
    with open(p, 'rb') as f:
        return f.read()


def toolchain_ok():
    return os.access(RUSTC, os.X_OK) and os.access(LINKER, os.X_OK)


# ── 지시자 ─────────────────────────────────────────────────────────
def parse_directives(text):
    """(지시자를 뗀 소스, 설정) 을 돌려준다. 지시자는 파일 끝에만 올 수 있다."""
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    tail = []
    while lines and lines[-1].startswith('//@'):
        tail.append(lines.pop())
    while tail and lines and lines[-1] == '':
        lines.pop()
    if not lines:
        raise RsrunError('소스가 비었다')
    for i, ln in enumerate(lines, 1):
        if ln.startswith('//@'):
            raise RsrunError('%d번 줄: 지시자(//@)는 파일 끝에만 둔다' % i)
    d = {'edition': '2024', 'expect': [], 'exit': 0, 'flags': [], 'test': False,
         'norun': False, 'warnings': False, 'args': '', 'stdin': None}
    for ln in reversed(tail):
        m = DIRECTIVE.match(ln)
        if not m or m.group(1) not in KEYS:
            raise RsrunError('모르는 지시자: %s' % ln)
        key, val = m.group(1), m.group(2) or ''
        if key == 'edition':
            if val not in EDITIONS:
                raise RsrunError('없는 에디션: %s' % val)
            d[key] = val
        elif key == 'expect':
            d[key] = [c.strip() for c in val.split(',') if c.strip()]
            if not d[key]:
                raise RsrunError('expect 에는 오류 코드를 적는다 (예: E0382)')
        elif key == 'exit':
            d[key] = int(val)
        elif key == 'flags':
            d[key] = val.split()
        elif key in ('test', 'norun'):
            d[key] = True
        elif key == 'warnings':
            if val != 'show':
                raise RsrunError('warnings 는 show 만 받는다')
            d[key] = True
        elif key == 'args':
            d[key] = val
        elif key == 'stdin':
            if "'" in val or '%' in val:
                raise RsrunError("stdin 에 ' 와 %% 는 못 쓴다 (printf 로 보이기 때문)")
            d[key] = val.replace('\\n', '\n')
    return '\n'.join(lines) + '\n', d


def shown_commands(name, d):
    """화면에 보일 명령 — 그리고 실제로 도는 명령이기도 하다(링커는 shim 이 붙인다)."""
    parts = ['rustc', '--edition', d['edition']] + d['flags']
    if d['test']:
        parts.append('--test')
    parts.append(name + '.rs')
    cmds = [' '.join(parts)]
    if d['expect'] or d['norun']:
        return cmds
    run = './' + name
    if d['args']:
        run += ' ' + d['args']
    if d['stdin'] is not None:
        run = "printf '%s' | %s" % (d['stdin'].replace('\n', '\\n'), run)
    cmds.append(run)
    return cmds


# ── 캡처 ───────────────────────────────────────────────────────────
_TID = re.compile(r"^(thread '[^'\n]*' \()\d+(\) panicked)", re.M)
_TEST_TIME = re.compile(r'(finished in )\d+\.\d+s')
_CARGO_TIME = re.compile(r'(target\(s\) in )\d+\.\d+s')


def normalize(text, sandbox):
    """실행마다 달라지는 세 가지만 고정한다. 그 밖의 글자는 건드리지 않는다."""
    text = text.replace(sandbox, '/work')
    text = _TID.sub(r'\1tid\2', text)
    text = _TEST_TIME.sub(r'\g<1>0.00s', text)
    text = _CARGO_TIME.sub(r'\g<1>0.00s', text)
    return text


def format_capture(steps):
    """[(명령, 출력, 종료 코드)] → 캡처 글. 말없이 끝난 rustc 는 다음 줄과 && 로 잇는다."""
    out = []
    pending = ''
    for i, (cmd, text, rc) in enumerate(steps):
        last = i == len(steps) - 1
        if cmd.startswith('rustc ') and text == '' and rc == 0 and not last:
            pending += cmd + ' && '
            continue
        out.append('$ ' + pending + cmd + '\n')
        pending = ''
        if text:
            out.append(text if text.endswith('\n') else text + '\n')
        if rc != 0:
            out.append('[종료 코드 %d]\n' % rc)
    return ''.join(out)


# ── 실행 ───────────────────────────────────────────────────────────
def _shim(scratch):
    """PATH 맨 앞에 설 rustc·cargo. 화면의 명령을 글자 그대로 돌리기 위한 것이다."""
    d = os.path.join(scratch, 'shim')
    os.makedirs(d, exist_ok=True)
    for name, body in (
            ('rustc', 'exec %s -C linker=%s -C codegen-units=1 "$@"\n' % (RUSTC, LINKER)),
            ('cargo', 'exec %s "$@"\n' % CARGO)):
        p = os.path.join(d, name)
        want = '#!/bin/sh\n' + body
        if not os.path.exists(p) or _read(p) != want:
            with io.open(p, 'w', encoding='utf-8') as f:
                f.write(want)
            os.chmod(p, 0o755)
    return d


def _env(scratch, sandbox):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('CARGO', 'RUST'))}
    env.update({
        'PATH': _shim(scratch) + os.pathsep + env.get('PATH', '/usr/bin:/bin'),
        'HOME': sandbox, 'TMPDIR': os.path.join(scratch, 'tmp'),
        'LANG': 'C.UTF-8', 'TERM': 'dumb', 'NO_COLOR': '1',
        # cargo — 받지 않고, 한 번에 하나만, 산출물은 scratch 아래에.
        'CARGO_HOME': os.path.join(scratch, 'cargo'),
        'CARGO_TARGET_DIR': os.path.join(sandbox, 'target'),
        'CARGO_NET_OFFLINE': 'true', 'CARGO_BUILD_JOBS': '1',
        'CARGO_INCREMENTAL': '0', 'CARGO_TERM_COLOR': 'never',
        'CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER': LINKER,
    })
    os.makedirs(env['TMPDIR'], exist_ok=True)
    return env


def _sh(cmd, cwd, env, timeout):
    p = subprocess.Popen(['/bin/sh', '-c', cmd], cwd=cwd, env=env,
                         stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, start_new_session=True)
    try:
        raw, _ = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        p.communicate()
        raise RsrunError('%d초 안에 끝나지 않았다: %s' % (timeout, cmd))
    return raw.decode('utf-8', 'replace'), p.returncode


def _read_run_file(path):
    """RUN 파일 → [(명령, 기대 종료 코드)]"""
    cmds = []
    for ln in _read(path).split('\n'):
        ln = ln.strip()
        m = re.match(r'^#@\s*exit:\s*(\d+)$', ln)
        if m:
            if not cmds:
                raise RsrunError('RUN: #@ exit 앞에 명령이 없다')
            cmds[-1] = (cmds[-1][0], int(m.group(1)))
        elif ln and not ln.startswith('#'):
            cmds.append((ln, 0))
    if not cmds:
        raise RsrunError('RUN 파일에 명령이 없다')
    return cmds


def run_example(path, scratch=None, timeout=RUN_TIMEOUT):
    """예제를 돌려 캡처 글을 돌려준다. 기대와 다르면 RsrunError."""
    scratch = os.path.abspath(scratch or os.path.join(ROOT, 'scratch'))
    os.makedirs(scratch, exist_ok=True)
    path = os.path.abspath(path.rstrip('/'))
    name = os.path.basename(path)
    if name.endswith('.rs'):
        name = name[:-3]
    with open(os.path.join(scratch, 'rustc.lock'), 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)        # rustc 는 한 번에 하나(PLAN.md §0.8)
        sandbox = os.path.join(scratch, 'run', name)
        shutil.rmtree(sandbox, True)
        env = _env(scratch, sandbox)
        try:
            if os.path.isdir(path):
                return _run_dir(path, sandbox, env, timeout)
            return _run_file(path, name, sandbox, env, timeout)
        finally:
            shutil.rmtree(sandbox, True)


def _run_dir(path, sandbox, env, timeout):
    shutil.copytree(path, sandbox, ignore=shutil.ignore_patterns('RUN', 'target'))
    steps = []
    for cmd, want in _read_run_file(os.path.join(path, 'RUN')):
        slow = cmd.startswith(('rustc ', 'cargo '))
        text, rc = _sh(cmd, sandbox, env, COMPILE_TIMEOUT if slow else timeout)
        text = normalize(text, sandbox)
        if rc != want:
            raise RsrunError('`%s` 의 종료 코드가 %d (기대 %d)\n%s' % (cmd, rc, want, text))
        steps.append((cmd, text, rc))
    return format_capture(steps)


def _run_file(path, name, sandbox, env, timeout):
    code, d = parse_directives(_read(path))
    os.makedirs(sandbox)
    with io.open(os.path.join(sandbox, name + '.rs'), 'w', encoding='utf-8',
                 newline='') as f:
        f.write(code)
    cmds = shown_commands(name, d)
    text, rc = _sh(cmds[0], sandbox, env, COMPILE_TIMEOUT)
    text = normalize(text, sandbox)
    steps = [(cmds[0], text, rc)]
    if d['expect']:
        if rc == 0:
            raise RsrunError('컴파일 오류를 기대했는데(%s) 컴파일됐다' % ','.join(d['expect']))
        for c in d['expect']:
            if 'error[%s]' % c not in text:
                raise RsrunError('기대한 오류 %s 가 없다\n%s' % (c, text))
        return format_capture(steps)
    if rc != 0:
        raise RsrunError('컴파일 실패 (일부러라면 //@ expect: 를 단다)\n' + text)
    if text and not d['warnings']:
        raise RsrunError('경고가 났다 — 고치거나 //@ warnings: show 를 단다\n' + text)
    if len(cmds) > 1:
        text, rc = _sh(cmds[1], sandbox, env, timeout)
        text = normalize(text, sandbox)
        if rc != d['exit']:
            raise RsrunError('종료 코드 %d (기대 %d — //@ exit: 로 적는다)\n%s'
                             % (rc, d['exit'], text))
        steps.append((cmds[1], text, rc))
    return format_capture(steps)


# ── 예제 찾기 · 해시 · 장부 ────────────────────────────────────────
def capture_path(rel):
    """ex/06/a.rs → out/06/a.txt,  ex/13/mods → out/13/mods.txt"""
    rel = rel.rstrip('/')
    assert rel.startswith('ex/'), rel
    body = rel[3:]
    if body.endswith('.rs'):
        body = body[:-3]
    return 'out/' + body + '.txt'


def example_of(rel):
    """ex/13/mods/src/main.rs → ex/13/mods (예제의 뿌리).  ex/06/a.rs → 그대로."""
    parts = rel.split('/')
    return '/'.join(parts[:3])


def examples(root):
    """ex/NN/ 아래의 예제 전부 — .rs 파일이거나 RUN 을 가진 디렉터리."""
    found = []
    ex = os.path.join(root, 'ex')
    for part in sorted(os.listdir(ex)) if os.path.isdir(ex) else []:
        pdir = os.path.join(ex, part)
        if not os.path.isdir(pdir):
            continue
        for n in sorted(os.listdir(pdir)):
            p = os.path.join(pdir, n)
            if n.endswith('.rs') and os.path.isfile(p):
                found.append('ex/%s/%s' % (part, n))
            elif os.path.isfile(os.path.join(p, 'RUN')):
                found.append('ex/%s/%s' % (part, n))
    return found


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def source_hash(root, rel):
    p = os.path.join(root, rel)
    if os.path.isfile(p):
        return _sha(_bytes(p))
    h = hashlib.sha256()
    for base, dirs, files in os.walk(p):
        dirs[:] = sorted(x for x in dirs if x != 'target')
        for n in sorted(files):
            fp = os.path.join(base, n)
            h.update(os.path.relpath(fp, p).encode('utf-8') + b'\0')
            h.update(_bytes(fp) + b'\0')
    return h.hexdigest()


def capture_hash(root, rel):
    p = os.path.join(root, capture_path(rel))
    return _sha(_bytes(p)) if os.path.isfile(p) else ''


def manifest_load(root):
    """{예제: (소스 해시, 캡처 해시, rustc 판)}"""
    p = os.path.join(root, 'out', 'MANIFEST.tsv')
    rows = {}
    if os.path.isfile(p):
        for ln in _read(p).split('\n'):
            f = ln.split('\t')
            if len(f) == 4 and f[0].startswith('ex/'):
                rows[f[0]] = (f[1], f[2], f[3])
    return rows


def manifest_update(root, rel, rustc_version):
    """rel 의 지금 소스·캡처 해시를 장부에 적는다. 장부는 예제 이름순."""
    os.makedirs(os.path.join(root, 'out'), exist_ok=True)
    with open(os.path.join(root, 'out', '.manifest.lock'), 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        rows = manifest_load(root)
        rows[rel] = (source_hash(root, rel), capture_hash(root, rel), rustc_version)
        p = os.path.join(root, 'out', 'MANIFEST.tsv')
        with io.open(p + '.tmp', 'w', encoding='utf-8', newline='') as f:
            f.write('example\tsource_sha256\tcapture_sha256\trustc\n')
            for k in sorted(rows):
                f.write('\t'.join((k,) + rows[k]) + '\n')
        os.replace(p + '.tmp', p)


def stale(root, rel, rows=None):
    """캡처가 없거나, 소스·캡처가 장부와 다르면 까닭을 돌려준다. 멀쩡하면 ''."""
    rows = manifest_load(root) if rows is None else rows
    if not os.path.isfile(os.path.join(root, capture_path(rel))):
        return '캡처가 없다'
    if rel not in rows:
        return '장부에 없다'
    if rows[rel][0] != source_hash(root, rel):
        return '소스가 캡처 뒤에 바뀌었다'
    if rows[rel][1] != capture_hash(root, rel):
        return '캡처가 손으로 고쳐졌다'
    return ''


def rustc_version():
    out = subprocess.run([RUSTC, '--version'], capture_output=True, text=True).stdout
    m = re.match(r'rustc (\S+)', out)
    return 'rustc ' + (m.group(1) if m else '?')


# ── 명령 줄 ────────────────────────────────────────────────────────
def _targets(root, args):
    if args.all:
        return examples(root)
    out = []
    for a in args.paths:
        rel = os.path.relpath(os.path.abspath(a), root).rstrip('/')
        p = os.path.join(root, rel)
        if os.path.isdir(p) and not os.path.isfile(os.path.join(p, 'RUN')):
            out += [e for e in examples(root) if e.startswith(rel + '/')]   # ex/06 통째로
        else:
            out.append(rel)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description='예제를 돌려 캡처를 남긴다')
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--all', action='store_true', help='ex/ 의 예제 전부')
    ap.add_argument('--stale', action='store_true', help='캡처가 없거나 낡은 것만')
    ap.add_argument('--check', action='store_true', help='다시 돌려 캡처와 같은지만 본다')
    ap.add_argument('--manifest-check', action='store_true', help='돌리지 않고 해시만 본다')
    ap.add_argument('-q', '--quiet', action='store_true', help='캡처를 화면에 찍지 않는다')
    args = ap.parse_args(argv)
    root = ROOT

    if args.manifest_check:
        rows = manifest_load(root)
        bad = [(e, stale(root, e, rows)) for e in examples(root)]
        bad = [(e, why) for e, why in bad if why]
        for e, why in bad:
            print('  ✗ %s — %s' % (e, why))
        print('  예제 %d개 — 낡은 캡처 %d개' % (len(examples(root)), len(bad)))
        return 1 if bad else 0

    targets = _targets(root, args)
    if not targets:
        ap.error('돌릴 예제가 없다 (경로를 주거나 --all)')
    ver = rustc_version()
    failed = 0
    for rel in targets:
        if args.stale and not stale(root, rel):
            continue
        try:
            cap = run_example(os.path.join(root, rel))
        except RsrunError as e:
            print('  ✗ %s\n%s' % (rel, e))
            failed += 1
            continue
        out = os.path.join(root, capture_path(rel))
        if args.check:
            old = _read(out) if os.path.isfile(out) else None
            if old != cap:
                print('  ✗ %s — 다시 돌리니 캡처와 다르다\n%s' % (rel, cap))
                failed += 1
            else:
                print('  ✓ %s' % rel)
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with io.open(out, 'w', encoding='utf-8', newline='') as f:
            f.write(cap)
        manifest_update(root, rel, ver)
        print('  ✓ %s → %s' % (rel, capture_path(rel)))
        if not args.quiet:
            sys.stdout.write(cap)
    if failed:
        print('  실패 %d개' % failed)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
