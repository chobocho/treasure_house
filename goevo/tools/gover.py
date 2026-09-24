# -*- coding: utf-8 -*-
"""gover.py — 예제 하나를 결정론 환경에서 go 로 돌린다 (PLAN.md §3.3).

이 기계에는 go 1.27.1 하나뿐이고 옛 툴체인은 받을 수 없다(§0.6). 그래서
'전과 후' 는 네 가지로만 보인다 — go.mod 의 언어 버전(go 1.N), GODEBUG,
GOEXPERIMENT, 그리고 사라진 문법의 컴파일 오류. 이 모듈은 그 넷을 한
함수 execute() 로 돌린다:

  1. ex/<부>/<예제>/ 를 scratch/work/<캡처 이름>/ 에 통째로 베끼고,
     lang 이 있으면 **사본의** go.mod 'go' 줄만 바꾼다. ex/ 는
     건드리지 않는다.
  2. 고정한 환경(env_for)에서 명령을 돌린다. 명령 앞의 VAR=값 은
     환경으로 옮긴다(GOTOOLCHAIN=go1.26.0 go version). 셸은 쓰지
     않는다 — 파이프·리다이렉트가 끼면 캡처가 무엇을 증명하는지
     흐려진다.
  3. 표준 출력과 오류를 합쳐 받고 normalise() 로 이 실행의 우연을
     지운다.

go 는 한 번에 하나만 돈다(§0.8). 서브에이전트 둘이 동시에 실험을 돌려도
scratch/go.lock 의 flock 이 줄을 세운다. 실험 하나는 60초를 넘길 수
없다.

캡처 이름·첫 줄 규칙은 여기 없다 — deck/build_deck.py 의 goverslug()·
gover_cmdline() 이 정하고 run_all.py 가 그것을 부른다. 한 규칙은
한 곳에.
"""
import fcntl
import io
import os
import re
import shlex
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SCRATCH = os.path.join(BASE, 'scratch')
GOROOT = '/data/data/com.termux/files/usr/lib/go'
TIMEOUT = 60


def env_for(scratch, godebug=None, exp=None, extra=None):
    """캡처가 기계·시각·사용자 설정에 기대지 않게 하는 환경.

    GOCACHE 만은 늘 저장소의 scratch/gocache 를 쓴다 — 캐시는 출력을
    바꾸지 않고, 실험마다 새로 컴파일하면 이 기계에서 몇 배 느리다."""
    env = {
        'PATH': os.environ.get('PATH', ''),
        'HOME': os.path.join(scratch, 'home'),
        'TMPDIR': os.path.join(scratch, 'tmp'),
        'GOCACHE': os.path.join(SCRATCH, 'gocache'),
        'GOPATH': os.path.join(scratch, 'gopath'),
        'GOMODCACHE': os.path.join(scratch, 'gopath', 'pkg', 'mod'),
        'GOTOOLCHAIN': 'local', 'GOPROXY': 'off', 'GOSUMDB': 'off',
        'GOFLAGS': '-trimpath -p=1', 'CGO_ENABLED': '0',
        'LANG': 'C', 'LC_ALL': 'C', 'TZ': 'UTC',
    }
    for k in ('HOME', 'TMPDIR'):
        os.makedirs(env[k], exist_ok=True)
    if godebug:
        env['GODEBUG'] = godebug
    if exp:
        env['GOEXPERIMENT'] = exp
    env.update(extra or {})
    return env


def split_cmd(cmd):
    """'A=1 go vet .' → ({'A': '1'}, ['go', 'vet', '.']).

    셸 기호는 거절한다."""
    if re.search(r'[|&;<>`$]', cmd):
        raise ValueError('셸 기능은 쓰지 않는다: %r' % cmd)
    words = shlex.split(cmd)
    env = {}
    while words and re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', words[0]):
        k, v = words.pop(0).split('=', 1)
        env[k] = v
    return env, words


def mod_version(src):
    """예제 go.mod 의 'go 1.N' 줄."""
    with io.open(os.path.join(src, 'go.mod'), encoding='utf-8') as f:
        m = re.search(r'^go (\d+\.\d+(?:\.\d+)?)\s*$', f.read(), re.M)
    if not m:
        raise ValueError('%s/go.mod 에 go 줄이 없다' % src)
    return m.group(1)


def prepare(src, dst, lang=None):
    """ex/ 의 예제를 작업 디렉터리로 베끼고, 사본의 go 줄만 바꾼다."""
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    if lang:
        p = os.path.join(dst, 'go.mod')
        with io.open(p, encoding='utf-8') as f:
            text = f.read()
        text = re.sub(r'^go \d+\.\d+(?:\.\d+)?[ \t]*$', 'go ' + lang,
                      text, count=1, flags=re.M)
        with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)


def normalise(text, work, scratch):
    """이 실행의 우연을 지운다 — 무엇을 지웠는지는 덱 0부가 밝힌다.

    경로(작업 사본 → /work, scratch → /scratch, GOROOT → $GOROOT),
    고루틴 번호, 힙 주소·명령 주소, 임시 빌드 디렉터리, 벤치마크의 반복
    횟수와 ns/op, 시험 소요 시간. allocs/op·B/op 는 결정적이라 남긴다.
    프로그램이 찍은 짧은 16진 값(0xff)은 증거라 남긴다. O(길이)."""
    text = text.replace('\r\n', '\n')
    text = text.replace(GOROOT, '$GOROOT')
    # 경로는 경계까지 맞춰 바꾼다 — '/s' 가 '/src' 의 앞머리를
    # 먹으면 안 된다
    for path, name in ((work, '/work'), (scratch, '/scratch')):
        text = re.sub(re.escape(path) + r'(?![\w.-])', name, text)
    text = re.sub(r'\bgoroutine \d+\b', 'goroutine N', text)
    text = re.sub(r'\b0xc[0-9a-f]{9,}\b', '0xc…', text)
    text = re.sub(r'\+0x[0-9a-f]+\b', '+0x…', text)
    text = re.sub(r'\b(pc|sp|fp|lr)=0x[0-9a-f]+\b', r'\1=0x…', text)
    text = re.sub(r'/go-build\d+', '/go-buildN', text)
    text = re.sub(r'^(Benchmark\S*[ ]*\t)[ ]*\d+\t[ ]*[\d.]+ ns/op',
                  r'\1…\t… ns/op', text, flags=re.M)
    text = re.sub(r'^(--- (?:PASS|FAIL|SKIP): .*\()[\d.]+s\)',
                  r'\1…s)', text, flags=re.M)
    text = re.sub(r'^((?:ok|FAIL)\s+\S+\s+)[\d.]+s\b', r'\1…s', text,
                  flags=re.M)
    return text


def execute(src, cmd, lang=None, godebug=None, exp=None, name=None,
            scratch=SCRATCH):
    """예제 src 에서 cmd 를 돌린다 → (종료 코드, 정규화한 출력)."""
    work = os.path.join(scratch, 'work', name or os.path.basename(src))
    prepare(src, work, lang)
    extra, argv = split_cmd(cmd)
    env = env_for(scratch, godebug, exp, extra)
    os.makedirs(SCRATCH, exist_ok=True)
    with open(os.path.join(SCRATCH, 'go.lock'), 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)          # go 는 한 번에 하나
        p = subprocess.run(argv, cwd=work, env=env,
                           stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=TIMEOUT)
    text = normalise(p.stdout.decode('utf-8', 'replace'), work, scratch)
    return p.returncode, text
