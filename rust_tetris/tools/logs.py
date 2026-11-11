# -*- coding: utf-8 -*-
"""logs.py — 덱의 "실행 결과" 상자에 들어갈 명령 출력을 실제로 돌려 out/logs/ 에 남긴다.

각 파일의 첫 줄은 화면에 보일 명령(`$ ...`), 그 아래가 실제 출력이다.
기대한 종료 코드와 다르면 그 자리에서 멈춘다 — 실패한 출력을 덱에 싣지 않기 위해.

정규화는 세 가지뿐이다:
  - 저장소 절대 경로를 지운다(덱에 기계 경로가 새지 않게)
  - 패닉 줄의 스레드 번호 `(12345)` 를 지운다(실행마다 달라진다)
  - cargo 의 `Compiling …` 줄을 지운다(캐시 상태에 따라 있다 없다 해서 덱의 pick 줄 번호가 밀린다)
"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)                         # rust_tetris
OUT = os.path.join(SRC, 'out', 'logs')
TPFX = '/data/data/com.termux/files/usr'
CARGO = '/usr/bin/cargo'
RUSTC = '/usr/bin/rustc'
ERR = os.path.join(HERE, 'errors')
TENV = {'CARGO_TARGET_DIR': 'target-termux', 'RUSTC': TPFX + '/bin/rustc',
        'PATH': TPFX + '/bin:' + os.environ['PATH']}
# wasm 빌드에만 사설 sysroot(Makefile 의 WASM_SYSROOT). 비어 있으면 툴체인 기본값
WENV = dict(TENV, **({'RUSTFLAGS': '--sysroot=' + os.environ['WASM_SYSROOT']}
                    if os.environ.get('WASM_SYSROOT') else {}))

# (파일 이름, 화면에 보일 명령, 실제 명령, 작업 폴더, 추가 환경, 기대 종료 코드)
JOBS = [
    ('test_core', 'cargo test -p tetris-core',
     [CARGO, 'test', '-p', 'tetris-core'], SRC, {}, 0),
    ('test_render', 'cargo test -p tetris-render',
     [CARGO, 'test', '-p', 'tetris-render'], SRC, {}, 0),
    ('test_tui', 'cargo test -p tetris-tui',
     [CARGO, 'test', '-p', 'tetris-tui'], SRC, {}, 0),
    ('test_gui', 'cargo test -p tetris-gui',
     [CARGO, 'test', '-p', 'tetris-gui'], SRC, {}, 0),
    ('test_wasm', 'cargo test -p tetris-wasm',
     [CARGO, 'test', '-p', 'tetris-wasm'], SRC, {}, 0),
    ('gravity', 'cargo run -q -p tetris-core --example gravity',
     [CARGO, 'run', '-q', '-p', 'tetris-core', '--example', 'gravity'], SRC, {}, 0),
    ('sizes', 'cargo run -q -p tetris-core --example sizes',
     [CARGO, 'run', '-q', '-p', 'tetris-core', '--example', 'sizes'], SRC, {}, 0),
    ('bytes', 'cargo run -q -p tetris-tui --example bytes',
     [CARGO, 'run', '-q', '-p', 'tetris-tui', '--example', 'bytes'], SRC, {}, 0),
    ('snapshot', 'cargo run -q -p tetris-render --example snapshot -- out/snapshot.ppm',
     [CARGO, 'run', '-q', '-p', 'tetris-render', '--example', 'snapshot', '--',
      'out/snapshot.ppm'], SRC, {}, 0),
    ('clippy', 'cargo clippy --workspace --all-targets --exclude tetris-gui -- -D warnings',
     [TPFX + '/bin/cargo', 'clippy', '--workspace', '--all-targets', '--exclude',
      'tetris-gui', '--', '-D', 'warnings'], SRC, TENV, 0),
    ('wasm_build', 'cargo build -p tetris-wasm --target wasm32-unknown-unknown --profile wasm',
     [TPFX + '/bin/cargo', 'build', '-p', 'tetris-wasm', '--target',
      'wasm32-unknown-unknown', '--profile', 'wasm'], SRC, WENV, 0),
    ('wasm_node', 'node wasm/test/node_test.mjs out/tetris_wasm.wasm',
     ['node', 'wasm/test/node_test.mjs', 'out/tetris_wasm.wasm'], SRC, {}, 0),
    # 컴파일 오류와 런타임 오류 — 실제 메시지를 싣는다
    ('e0004', 'rustc --edition 2024 e0004_match.rs',
     [RUSTC, '--edition', '2024', 'e0004_match.rs', '-o', '/dev/null'], ERR, {}, 1),
    ('e0382', 'rustc --edition 2024 e0382_move.rs',
     [RUSTC, '--edition', '2024', 'e0382_move.rs', '-o', '/dev/null'], ERR, {}, 1),
    ('e0502', 'rustc --edition 2024 e0502_borrow.rs',
     [RUSTC, '--edition', '2024', 'e0502_borrow.rs', '-o', '/dev/null'], ERR, {}, 1),
    ('static_mut', 'rustc --edition 2024 static_mut.rs',
     [RUSTC, '--edition', '2024', 'static_mut.rs', '-o', '/dev/null'], ERR, {}, 1),
    ('no_mangle', 'rustc --edition 2024 no_mangle.rs',
     [RUSTC, '--edition', '2024', 'no_mangle.rs', '-o', '/dev/null'], ERR, {}, 1),
    ('clippy_next', 'clippy-driver --edition 2024 clippy_next.rs',
     [TPFX + '/bin/clippy-driver', '--edition', '2024', '--emit=metadata',
      '-o', os.path.join(SRC, 'scratch', 'clippy_next.rmeta'), 'clippy_next.rs'],
     ERR, TENV, 0),
]

# 빌드한 뒤 실행하는 두 단계짜리
RUNS = [
    ('ffi_panic', 'rustc --edition 2024 ffi_panic.rs && ./ffi_panic',
     'ffi_panic.rs', [], 134),
    ('overflow_debug', 'rustc --edition 2024 overflow.rs && ./overflow',
     'overflow.rs', [], 101),
    ('overflow_release', 'rustc --edition 2024 -O overflow.rs && ./overflow',
     'overflow.rs', ['-O'], 0),
]


def clean(text):
    text = text.replace(SRC + '/', '').replace(SRC, '.')
    text = re.sub(r"(thread '[^']*') \(\d+\)", r'\1', text)
    text = re.sub(r'(?m)^ +Compiling .*\n', '', text)
    return text


def run(cmd, cwd, env):
    e = dict(os.environ, CARGO_BUILD_JOBS='1', **env)
    p = subprocess.run(cmd, cwd=cwd, env=e, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout


def save(name, shown, rc, out, want):
    if rc != want:
        sys.exit(f'{name}: 종료 코드 {rc} (기대 {want})\n{out}')
    body = clean(out).rstrip('\n')
    with open(os.path.join(OUT, name + '.txt'), 'w', encoding='utf-8') as f:
        f.write(f'$ {shown}\n{body}\n')
    print(f'{name:<18} rc={rc}  {len(body.splitlines())}줄')


def main():
    os.makedirs(OUT, exist_ok=True)
    only = set(sys.argv[1:])
    for name, shown, cmd, cwd, env, want in JOBS:
        if only and name not in only:
            continue
        rc, out = run(cmd, cwd, env)
        save(name, shown, rc, out, want)
        if name == 'wasm_build':
            src = os.path.join(SRC, 'target-termux/wasm32-unknown-unknown/wasm/tetris_wasm.wasm')
            data = open(src, 'rb').read()
            open(os.path.join(SRC, 'out', 'tetris_wasm.wasm'), 'wb').write(data)
    for name, shown, src, flags, want in RUNS:
        if only and name not in only:
            continue
        exe = os.path.join(ERR, src[:-3])
        rc, out = run([RUSTC, '--edition', '2024', *flags, src, '-o', exe], ERR, {})
        if rc != 0:
            sys.exit(f'{name}: 컴파일 실패\n{out}')
        rc, out = run([exe], ERR, {})
        os.remove(exe)
        # 셸은 시그널로 죽은 프로세스를 128+번호로 보인다(SIGABRT=6 → 134)
        rc = 128 - rc if rc < 0 else rc
        save(name, shown, rc, out, want)


if __name__ == '__main__':
    main()
