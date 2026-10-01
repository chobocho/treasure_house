# -*- coding: utf-8 -*-
"""csver.py — 예제 하나를 결정론 환경에서 csrun 으로 돌린다.

(PLAN.md §0.6–0.10) 이 기계에는 .NET SDK 10.0.112(Roslyn 5, C# 14)
하나뿐이고 옛 컴파일러는 없다. 그래서 '전과 후' 는 지금의 Roslyn 이
보여 주는 것으로만 보인다 — -langversion 을 내렸을 때의 거절("Feature
'X' is not available in C# N"), 버전에 묶인 동작, 런타임의 동작, 사라진
문법의 진단. 이 모듈은 그 캡처를 한 함수 execute() 로 뜬다:

  1. ex/<부>/<예제>/ 를 scratch/work/<캡처 이름>/ 에 통째로 베낀다
     (bin/·obj/ 는 빼고). ex/ 는 건드리지 않는다.
  2. 명령의 첫 낱말이 csrun 이면 tools/csrun 으로 바꾸고, 바로 뒤에
     -langversion:<v> 와 플래그를 넣는다(csrun 은 csproj 의 값 뒤에
     붙여 뒤가 이긴다). 명령 앞의 VAR=값 은 환경으로 옮긴다. 셸은
     쓰지 않는다.
  3. 표준 출력과 오류를 합쳐 받고 normalise() 로 이 실행의 우연을
     지운다.

dotnet 은 한 번에 하나만 돈다(§0.8). 서브에이전트 둘이 동시에 돌려도
scratch/dotnet.lock 의 flock 이 줄을 세운다. 실험 하나는 60초까지다.

    python3 tools/csver.py --check ex/02/a ex/02/b …
                                        # make examples-check

--check 는 예제마다 csproj 의 언어 버전으로 **컴파일만** 하고 경고가
하나도 없어야 통과다(EXPECT_FAIL 은 건너뛰고, EXPECT_WARN 은 경고를
허용한다). 결과는 소스·csproj·csrun 의 sha256 을 열쇠로
scratch/check/ 에 적어 둔다 — 예제가 천 개가 넘으면 매번 다시
컴파일하는 데 반 시간이 든다.

캡처 이름·첫 줄 규칙은 여기 없다 — deck/build_deck.py 의
csverslug()·csver_cmdline() 이 정하고 run_all.py 가 그것을 부른다.
한 규칙은 한 곳에.
"""
import fcntl
import hashlib
import io
import os
import re
import shlex
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SCRATCH = os.path.join(BASE, 'scratch')
CSRUN = os.path.join(HERE, 'csrun')
TIMEOUT = 60


def env_for(scratch, extra=None):
    """캡처가 기계·시각·사용자 설정에 기대지 않게 하는 환경."""
    env = {
        'PATH': os.environ.get('PATH', ''),
        'HOME': os.path.join(scratch, 'home'),
        'TMPDIR': os.path.join(scratch, 'tmp'),
        'DOTNET_GCHeapHardLimit': '0x30000000',
        'DOTNET_CLI_TELEMETRY_OPTOUT': '1', 'DOTNET_NOLOGO': '1',
        'DOTNET_SKIP_FIRST_TIME_EXPERIENCE': '1',
        'DOTNET_DbgEnableMiniDump': '0',
        'LANG': 'C', 'LC_ALL': 'C', 'TZ': 'UTC',
    }
    for k in ('HOME', 'TMPDIR'):
        os.makedirs(env[k], exist_ok=True)
    env.update(extra or {})
    return env


def csproj_props(src):
    """예제 디렉터리의 *.csproj 의 <PropertyGroup> 칸들 → {이름: 값}."""
    names = sorted(n for n in os.listdir(src) if n.endswith('.csproj'))
    if not names:
        raise ValueError('%s 에 csproj 가 없다' % src)
    with io.open(os.path.join(src, names[0]), encoding='utf-8') as f:
        text = f.read()
    return dict(re.findall(r'<(\w+)>([^<]*)</\1>', text))


def lang_version(src):
    """csproj 의 LangVersion. 없으면 오류 — 기본값(latest)에 기대면 SDK
    를
    올리는 날 캡처가 조용히 바뀐다."""
    v = csproj_props(src).get('LangVersion')
    if not v:
        raise ValueError('%s 의 csproj 에 LangVersion 이 없다' % src)
    return v


def split_cmd(cmd):
    """'A=1 csrun -- x' → ({'A': '1'}, ['csrun', '--', 'x']). 셸 기호는
    거절."""
    if re.search(r'[|&;<>`$]', cmd):
        raise ValueError('셸 기능은 쓰지 않는다: %r' % cmd)
    words = shlex.split(cmd)
    env = {}
    while words and re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', words[0]):
        k, v = words.pop(0).split('=', 1)
        env[k] = v
    return env, words


def build_argv(cmd, v=None, flags=None, env=None):
    """지시자의 cmd·v·flags·env → (환경 더하기, argv). 첫 줄 규칙
    (build_deck.csver_cmdline)과 같은 차례다."""
    extra, words = split_cmd(cmd)
    if env:
        e, _ = split_cmd(env + ' x')
        extra.update(e)
    if words and words[0] == 'csrun':
        words = ([CSRUN] + (['-langversion:' + v] if v else [])
                 + (shlex.split(flags) if flags else []) + words[1:])
    return extra, words


def prepare(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('bin',
    'obj'))


def normalise(text, work, scratch):
    """이 실행의 우연을 지운다 — 무엇을 지웠는지는 덱 0부가 밝힌다.

    경로(작업 사본 → /work, scratch → /scratch), 9자리 이상 16진 주소
    (0x… — 프로그램이 찍은 0xFF 같은 짧은 값은 증거라 남긴다), CRLF.
    스택 트레이스의 소스 경로는 csrun 의 -pathmap 이 이미 /work 로
    바꾼다. O(길이)."""
    text = text.replace('\r\n', '\n')
    for path, name in ((work, '/work'), (scratch, '/scratch')):
        text = re.sub(re.escape(path) + r'(?![\w.-])', name, text)
    text = re.sub(r'\b0x[0-9A-Fa-f]{9,}\b', '0x…', text)
    return text


def _run(argv, cwd, env):
    os.makedirs(SCRATCH, exist_ok=True)
    with open(os.path.join(SCRATCH, 'dotnet.lock'), 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)          # dotnet 은 한 번에
        하나
        return subprocess.run(argv, cwd=cwd, env=env,
                              stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=TIMEOUT)


def execute(src, cmd, v=None, flags=None, env=None, name=None,
            scratch=SCRATCH):
    """예제 src 에서 cmd 를 돌린다 → (종료 코드, 정규화한 출력)."""
    work = os.path.join(scratch, 'work', name or os.path.basename(src))
    prepare(src, work)
    extra, argv = build_argv(cmd, v, flags, env)
    p = _run(argv, work, env_for(scratch, extra))
    text = normalise(p.stdout.decode('utf-8', 'replace'), work, scratch)
    return p.returncode, text


# ---------------------------------------------------------------- 검사
def check_key(src):
    """예제의 소스·csproj·csrun 을 한데 묶은 sha256 — 검사 캐시의
    열쇠."""
    h = hashlib.sha256()
    for name in sorted(os.listdir(src)):
        p = os.path.join(src, name)
        if os.path.isfile(p) and (name.endswith('.cs') or
                                  name.endswith('.csproj') or
                                  name.startswith('EXPECT_')):
            h.update(name.encode() + b'\0')
            with open(p, 'rb') as f:
                h.update(f.read() + b'\0')
    with open(CSRUN, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()


def check(dirs):
    """예제마다 컴파일만 — 경고 0 이어야 통과. 실패한 것마다 한 줄."""
    cache = os.path.join(SCRATCH, 'check')
    os.makedirs(cache, exist_ok=True)
    bad, n, skipped, hit = [], 0, 0, 0
    for d in dirs:
        n += 1
        src = os.path.join(BASE, d)
        if os.path.exists(os.path.join(src, 'EXPECT_FAIL')):
            skipped += 1
            continue
        stamp = os.path.join(cache, check_key(src))
        if os.path.exists(stamp):
            hit += 1
            continue
        code, text = execute(src, 'CSRUN_COMPILE_ONLY=1 csrun',
                             name='check-' + d.replace('/', '-'))
        warn = re.search(r': warning CS\d+', text)
        allow = os.path.exists(os.path.join(src, 'EXPECT_WARN'))
        if code != 0:
            bad.append('%s: 컴파일 실패 (종료 %d)\n%s' % (d, code,
            text))
        elif warn and not allow:
            bad.append('%s: 경고가 있다\n%s' % (d, text))
        else:
            open(stamp, 'w').close()
    for b in bad:
        print('  ✗ ' + b)
    print('  예제 %d개 — 경고 0 컴파일 검사 (일부러 깨진 것 %d개 제외, '
          '캐시 %d개)' % (n, skipped, hit))
    return 1 if bad else 0


if __name__ == '__main__':
    if sys.argv[1:2] == ['--check']:
        sys.exit(check(sys.argv[2:]))
    print(__doc__)
