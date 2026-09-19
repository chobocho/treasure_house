# -*- coding: utf-8 -*-
"""run_all.py — 덱이 싣는 캡처를 전부, 차례로, 한 번에 하나씩 뜬다.

    python3 run_all.py                 # 전부 (있는 스냅샷은 건너뜀)
    python3 run_all.py --only ID …     # 몇 개만
    python3 run_all.py --resnap ID     # 스냅샷 하나를 날짜를 바꿔 다시
    python3 run_all.py --check         # 매니페스트·폭·개인정보만 검사
    python3 run_all.py --list          # 캡처 목록

캡처는 전부 tools/tmx.sh 를 거친다 — 호스트 Termux 로 가는 문은
그것 하나다(PLAN.md §2.1). 한 캡처는 여러 걸음(Step)이고, 걸음마다
'== N. 제목 ==' 절이 하나 생긴다. 덱의 <!--OUT sec=N--> 이 그 절을
통째로 가져가므로 캡처가 늘어나도 인용이 밀리지 않는다.

캡처는 두 종류다(PLAN.md §0.9).
  stable   — 세 번 떠서 바이트까지 같아야 한다. 매니페스트에 날짜를
             적지 않는다 — 적으면 같은 내용이 날마다 다른 파일이 된다.
  snapshot — 배터리·시간처럼 다시 뜨면 달라지는 것. 한 번 뜨고 첫 줄에
             '# snapshot 날짜' 를 박아 얼린다. 다음 실행은 건너뛴다.
             조용히 다시 뜨면 덱의 도장이 거짓말이 된다.

쓰기 전에 tools/scrub.py 의 fix() 를 거친다. 그래도 남은 개인정보는
--check 가 잡는다. 시간 O(캡처 수 × 명령 시간), 직렬.
"""
import datetime
import io
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'out')
# 같은 디렉터리의 두 이름. proot 의 /root 는 Termux 의 $HOME 을 묶어
# 둔 것이다. Termux 쪽 캡처는 Termux 가 부르는 이름으로 선다.
BASE_T = ('/data/data/com.termux/files/home/github/treasure_house'
          '/termux')
TMX = os.path.join(BASE, 'tools', 'tmx.sh')
sys.path.insert(0, os.path.join(BASE, 'tools'))
import anon                                        # noqa: E402
import scrub                                       # noqa: E402

# 덱의 캡처 폭 상한(build_deck.py MAX_TERM_COLS 와 같아야 한다)
MAX_COLS = 108
PROMPT = {'termux': '$', 'proot': '#', 'native': '$'}
SNAP_RE = re.compile(r'# snapshot (\d{4}-\d\d-\d\d)\n')


class Step(object):
    """캡처의 한 걸음 — 절 하나, 명령 하나."""

    def __init__(self, title, cmd, timeout=120, install=False):
        self.title, self.cmd = title, cmd
        self.timeout, self.install = timeout, install


class Capture(object):
    """out/<cid>.txt 하나. side 는 termux 또는 proot."""

    def __init__(self, cid, side, kind, steps, cwd=None):
        assert side in PROMPT and kind in ('stable', 'snapshot')
        self.cid, self.side, self.kind = cid, side, kind
        self.steps = steps
        self.cwd = cwd or (BASE_T if side == 'termux' else BASE)


class Import(object):
    """사용자가 네이티브 Termux 에서 뜬 파일을 캡처로 들여온다.

    proot 밖의 값(진짜 uid·커널·getprop·Termux:API 의 답)은 이 세션이
    뜰 수 없다. tools/native_facts.sh 가 만든 파일의 첫 줄
    '# native_facts 날짜' 가 곧 스냅샷 날짜다. 파일이 아직 없으면
    건너뛴다 — 그 캡처를 인용한 장이 있으면 조립기가 잡는다.
    """
    kind, side = 'snapshot', 'native'

    def __init__(self, cid, path, cmd='tools/native_facts.sh'):
        self.cid, self.path, self.cmd = cid, path, cmd


NATIVE_RE = re.compile(r'# native_facts (\d{4}-\d\d-\d\d)\n')


def tmx_runner(side, cmd, cwd, timeout, install):
    """진짜 runner — tmx.sh 를 부른다. (stdout+stderr, 종료 코드)."""
    args = ['sh', TMX, '--cwd', cwd, '--timeout', str(timeout)]
    if side == 'proot':
        args.append('--proot')
    if install:
        args.append('--allow-install')
    r = subprocess.run(args + ['--', cmd], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    return r.stdout.decode('utf-8', 'replace'), r.returncode


def cells(s):
    """화면 칸 수 — 한글·CJK 는 두 칸 (tools/width.py 와 같은 셈)."""
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(c) in ('W', 'F')
               else 1 for c in s)


def fold(line, limit=None):
    """한 줄을 limit 칸 이하 조각으로 — 이어지는 조각은 '↪ ' 로 연다.

    사람이 뜬 파일(Import)은 명령에 cut 을 걸 수 없어 여기서 접는다.
    자르지 않고 접는 까닭: uname 의 커널 판처럼 줄 끝이 곧 사실이다.
    공백에서 접으면 그 공백 하나만 줄바꿈으로 바뀐다.
    시간 O(글자 수), 공간 O(글자 수).
    """
    limit = limit or MAX_COLS
    if cells(line.expandtabs(4)) <= limit:
        return [line]
    line = line.expandtabs(4)
    parts, cur, w, head = [], '', 0, ''
    for c in line:
        cw = cells(c)
        if w + cw > limit:
            # 공백이 있으면 거기서 — 그 공백 하나는 줄바꿈이 대신한다
            sp = cur.rfind(' ')
            keep, cur = ((cur[:sp], cur[sp + 1:]) if sp > 0
                         else (cur, ''))
            parts.append(head + keep)
            head = '↪ '
            w = cells(head + cur)
        cur += c
        w += cw
    parts.append(head + cur)
    return parts


def render(cap, outputs):
    """걸음마다의 tmx 출력 → 캡처 파일 본문."""
    parts = []
    for k, (step, out) in enumerate(zip(cap.steps, outputs), 1):
        if out and not out.endswith('\n'):
            out += '\n'
        # tmx.sh 는 명령 출력 뒤에 끝줄을 붙인다. 명령이 줄바꿈 없이
        # 끝났으면 끝줄이 그 줄에 붙어 버리므로 떼어 낸다.
        out = re.sub(r'(?<=[^\n])(## tmx: )', r'\n\1', out)
        parts.append('== %d. %s ==\n%s %s\n%s'
                     % (k, step.title, PROMPT[cap.side], step.cmd, out))
    return '\n'.join(parts)


def load_manifest(outdir):
    p = os.path.join(outdir, 'manifest.json')
    if not os.path.exists(p):
        return {}
    return json.loads(io.open(p, encoding='utf-8').read())


def save_manifest(outdir, man):
    p = os.path.join(outdir, 'manifest.json')
    io.open(p, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(man, ensure_ascii=False, indent=1, sort_keys=True)
        + '\n')


def record(cap, outdir, date, runner, force=False):
    """캡처 하나를 떠서 쓰고, 매니페스트 항목을 돌려준다."""
    name = cap.cid + '.txt'
    path = os.path.join(outdir, name)
    if isinstance(cap, Import):
        if not os.path.exists(cap.path):
            return None
        raw = io.open(cap.path, encoding='utf-8').read()
        m = NATIVE_RE.match(raw)
        if not m:
            raise ValueError('%s: 첫 줄에 native_facts 날짜가 없다'
                             % cap.path)
        text, _n = scrub.fix(raw[m.end():].lstrip('\n'))
        # 공개 저장소에 올리므로 기기 식별값은 가짜로(tools/anon.py)
        text = anon.native(text)
        text = '\n'.join(p for ln in text.split('\n') for p in fold(ln))
        io.open(path, 'w', encoding='utf-8', newline='\n').write(
            '# snapshot %s\n' % m.group(1) + text)
        return {'kind': 'snapshot', 'side': 'native',
                'date': m.group(1), 'cmds': [cap.cmd]}
    entry = {'kind': cap.kind, 'side': cap.side,
             'cmds': [s.cmd for s in cap.steps]}
    if cap.kind == 'snapshot' and os.path.exists(path) and not force:
        m = SNAP_RE.match(io.open(path, encoding='utf-8').read())
        entry['date'] = m.group(1) if m else date
        return entry
    outs = [runner(cap.side, s.cmd, cap.cwd, s.timeout, s.install)[0]
            for s in cap.steps]
    text, _n = scrub.fix(render(cap, outs))
    text = anon.ids(text)      # 앱 번호·미러는 가짜로(tools/anon.py)
    if cap.kind == 'snapshot':
        text = '# snapshot %s\n' % date + text
        entry['date'] = date
    io.open(path, 'w', encoding='utf-8', newline='\n').write(text)
    return entry


# srcpin 의 경로 오류와 파이썬 예외. 의도한 실패(exit≠0)는 많아서
# 종료 코드로는 못 가리고, 이 도구들의 실패 문구로 가린다
TOOL_FAIL = ('에 맞는 파일이', '핀 커밋에 없다',
             'Traceback (most recent')


def check(outdir):
    """out/ 의 캡처가 매니페스트·폭·개인정보 규칙을 지키는가."""
    bad = []
    man = load_manifest(outdir)
    have = sorted(n for n in os.listdir(outdir) if n.endswith('.txt'))
    for n in have:
        if n not in man:
            bad.append('out/%s 가 manifest.json 에 없다' % n)
    for n in sorted(man):
        p = os.path.join(outdir, n)
        if not os.path.exists(p):
            bad.append('manifest 의 %s 가 out/ 에 없다' % n)
            continue
        text = io.open(p, encoding='utf-8').read()
        if man[n].get('kind') == 'snapshot' and not SNAP_RE.match(text):
            bad.append('out/%s: snapshot 인데 첫 줄 날짜가 없다' % n)
        for no, line in enumerate(text.split('\n'), 1):
            ctl = [c for c in line if ord(c) < 32 and c != '\t']
            if ctl:
                bad.append('out/%s:%d 제어 문자 %r — HTML 에 못 싣는다'
                           % (n, no, ctl[0]))
            # 도구가 실패한 채 캡처된 줄 — 덱에 오류 문구가 실린다
            if any(f in line for f in TOOL_FAIL):
                bad.append('out/%s:%d 도구 실패가 캡처됐다: %s'
                           % (n, no, line.strip()[:40]))
            w = cells(line.expandtabs(4))
            if w > MAX_COLS:
                bad.append('out/%s:%d %d칸 (최대 %d)'
                           % (n, no, w, MAX_COLS))
        for no, kind, shown in scrub.problems(text):
            bad.append('out/%s:%d %s %s' % (n, no, kind, shown))
    return bad


# ── 캡처 목록 (PLAN.md §3.3) ───────────────────────────────────────
# 걸음의 명령은 출력이 실행마다 같도록 고른다(stable). pid·시각처럼
# 흔들리는 값은 명령 안에서 걸러 내고, 걸러 낸 방법이 명령 줄에
# 그대로 보이게 둔다 — 캡처를 사람이 손보지 않는다.
S = Step
BB = 'scratch/build/bionic'
BG = 'scratch/build/glibc'
EXPS = ['hello', 'passwd', 'paths', 'bind_port', 'syscall_loop']
PROBE = '/tmp /bin/sh /usr/bin/env /etc/passwd /system/bin/sh'
# 소스 캡처(src_*)는 deck/srcpin.py 로 핀 커밋에서 읽는다
PD_UBUNTU = ('/data/data/com.termux/files/usr/var/lib/proot-distro/'
             'containers/ubuntu')
MANI = 'termux-app:app/src/main/AndroidManifest.xml'


def exp_steps(cc, out):
    """실험 바이너리를 짓는 걸음 + 돌리는 걸음. 두 쪽이 같은 모양."""
    return [
        S('짓기 — 경고 하나도 실패',
          'sh exp/build.sh %s %s' % (cc, out),
          timeout=300),
        S('같은 인사, 다른 libc', '%s/hello' % out),
        S('getpwuid 는 누구에게 묻나',
          '%s/passwd 0 1000 2000 10123' % out),
        S('자기 uid', '%s/passwd' % out),
        S('그 경로가 있는가',
          '%s/paths %s $PREFIX/bin/sh' % (out, PROBE)),
        S('1024 미만 포트 훑기', '%s/bind_port --scan 1 1100' % out),
        S('시스템 호출 1000번', '%s/syscall_loop 1000' % out),
    ]


CAPTURES = [
    Capture('env_termux', 'termux', 'stable', [
        S('환경 변수', 'env | sort'),
        S('신원 — proot 가 보여 주는 값', "id | tr ' ' '\\n'"),
        S('커널 — proot 가 보여 주는 값', 'uname -srm'),
        S('이 셸의 실행 파일',
          'x=$(readlink /proc/$$/exe); echo "$x"'),
        S('추적자가 있는가',
          "awk '/^TracerPid/{print $1, ($2>0?\"(0 아님)\":0)}' "
          '/proc/self/status'),
        S('SELinux 문맥 — proot 도 못 꾸민다',
          "tr -d '\\0' < /proc/self/attr/current; echo"),
    ]),
    Capture('env_proot', 'proot', 'stable', [
        S('환경 변수', 'env | sort'),
        S('신원', "id | tr ' ' '\\n'"),
        S('커널 — proot 가 보여 주는 값', 'uname -srm'),
        S('배포판', 'head -n 3 /etc/os-release'),
        S('이 셸의 실행 파일',
          'x=$(readlink /proc/$$/exe); echo "$x"'),
        S('추적자가 있는가',
          "awk '/^TracerPid/{print $1, ($2>0?\"(0 아님)\":0)}' "
          '/proc/self/status'),
    ]),
    Capture('prefix_tree', 'termux', 'stable', [
        S('앱 데이터 디렉터리', 'ls -F /data/data/com.termux/files'),
        S('$PREFIX 의 첫 층', 'ls -F $PREFIX'),
        S('$PREFIX/etc', 'ls -F $PREFIX/etc'),
        S('$PREFIX/etc/termux', 'ls -F $PREFIX/etc/termux'),
        S('bin 에 있는 실행 파일 수', 'ls $PREFIX/bin | wc -l'),
        S('termux-* 명령 수', 'ls $PREFIX/bin | grep -c ^termux-'),
    ]),
    Capture('prefix_du', 'termux', 'snapshot', [
        # proot-distro 컨테이너 안의 바인드 경로에서 du 가 넘어진다 —
        # 컨테이너는 빼고 잰다(9부에서 따로)
        S('$PREFIX 의 크기 — proot-distro 컨테이너 뺌',
          'du -sh --exclude=proot-distro $PREFIX', timeout=300),
        S('큰 하위 디렉터리',
          'du -sh $PREFIX/lib $PREFIX/share $PREFIX/bin '
          '$PREFIX/include', timeout=300),
    ]),
    Capture('linker_termux', 'termux', 'stable', [
        S('bash · ls · termux-api 가 부르는 것',
          'python3 py/elf.py $PREFIX/bin/bash $PREFIX/bin/ls '
          '$PREFIX/libexec/termux-api'),
        S('ls 는 무엇인가', 'readlink $PREFIX/bin/ls'),
    ]),
    Capture('linker_proot', 'proot', 'stable', [
        S('우분투의 bash · ls', 'python3 py/elf.py /bin/bash /bin/ls'),
    ]),
    Capture('exp_bionic', 'termux', 'stable', exp_steps('clang', BB)),
    Capture('exp_glibc', 'proot', 'stable', exp_steps('gcc', BG)),
    Capture('shebang', 'termux', 'stable', [
        S('셔뱅 셋 — proot 안에서', 'sh exp/shebang/run.sh'),
        S('termux-exec 를 LD_PRELOAD 로 얹어서',
          'LD_PRELOAD=$PREFIX/lib/libtermux-exec-ld-preload.so '
          'sh exp/shebang/run.sh'),
        S('termux-exec 라이브러리들',
          "ls $PREFIX/lib | grep '^libtermux-exec'"),
        S('고칠 사본',
          'mkdir -p scratch/fix && '
          'cp exp/shebang/*_sh.sh scratch/fix/'),
        S('termux-fix-shebang', 'termux-fix-shebang scratch/fix/*.sh'),
        S('고친 첫 줄', 'head -qn 1 scratch/fix/*.sh'),
    ]),
    Capture('dpkg_stats', 'termux', 'stable', [
        S('설치된 패키지 수', "dpkg -l | grep -c '^ii'"),
        S('크기로 본 설치 패키지',
          'python3 py/pkgstat.py $PREFIX/var/lib/dpkg/status'),
        S('termux-* 명령은 어느 패키지 것인가',
          'dpkg -S $PREFIX/bin/termux-* | sort'),
        S('패키지마다 몇 개',
          'dpkg -S $PREFIX/bin/termux-* | cut -d: -f1 | sort | '
          'uniq -c | sort -rn'),
    ]),
    Capture('apt_sources', 'termux', 'stable', [
        S('sources.list', 'cat $PREFIX/etc/apt/sources.list'),
        S('sources.list.d', 'ls $PREFIX/etc/apt/sources.list.d'),
        S('TUR 한 줄', 'cat $PREFIX/etc/apt/sources.list.d/*.list'),
        S('믿는 키 파일', 'ls $PREFIX/etc/apt/trusted.gpg.d'),
        S('apt 를 root 로', 'apt list --installed 2>&1 | head -n 3'),
    ]),
    Capture('apt_policy', 'termux', 'snapshot', [
        S('저장소 우선순위',
          'apt-cache policy 2>&1 | head -n 20 | cut -c1-100'),
    ]),
    Capture('pkg_script', 'termux', 'stable', [
        S('pkg 는 셸 스크립트다', 'head -n 12 $PREFIX/bin/pkg'),
        S('설치된 termux-tools',
          "dpkg -s termux-tools | grep '^Version'"),
        S('설치된 termux-exec·termux-core',
          'dpkg -s termux-exec termux-core | '
          "grep -E '^(Package|Version)'"),
        S('핀 고정 소스(pkg.in @v1.45.0)와 설치본',
          'sh exp/pkg_diff.sh sources/termux-tools/scripts/pkg.in '
          '$PREFIX/bin/pkg 1.45.0'),
    ]),
    Capture('deb_by_hand', 'termux', 'stable', [
        S('짓기', 'sh exp/mkdeb/build.sh scratch/deb'),
        S('control 보기',
          'dpkg-deb -f scratch/deb/treasure-hello_1.0_all.deb'),
        S('안에 든 파일',
          'dpkg-deb -c scratch/deb/treasure-hello_1.0_all.deb | '
          "awk '{print $1, $2, $6}'"),
        S('dpkg 로 설치',
          'dpkg -i scratch/deb/treasure-hello_1.0_all.deb 2>&1',
          install=True),
        S('설치된 것 돌리기', 'treasure-hello'),
        S('dpkg -L', 'dpkg -L treasure-hello'),
        S('지우기', 'dpkg -r treasure-hello 2>&1'),
        S('지운 뒤', 'command -v treasure-hello; echo "종료 $?"'),
    ]),
    Capture('termux_info', 'termux', 'stable', [
        S('termux-info — proot 안에서', 'termux-info 2>&1'),
    ]),
    Capture('api_mechanism', 'termux', 'stable', [
        S('termux-battery-status 의 몸통',
          'cat $PREFIX/bin/termux-battery-status'),
        S('termux-api 실행 파일',
          "stat -c '%A %s %n' $PREFIX/libexec/termux-api"),
        S('명령 스크립트 중 termux-api 를 부르는 것',
          'grep -l libexec/termux-api $PREFIX/bin/termux-* | wc -l'),
        S('그 이름들',
          'grep -l libexec/termux-api $PREFIX/bin/termux-* | '
          'xargs -n1 basename'),
    ]),
    Capture('api_proot', 'termux', 'snapshot', [
        S('proot 안에서 부르면',
          'timeout 15 termux-battery-status; echo "종료 $?"',
          timeout=60),
    ]),
    Capture('proot_probe', 'proot', 'stable', [
        S('getprop', '/system/bin/getprop ro.build.version.sdk 2>&1; '
          'echo "종료 $?"'),
        S('proot 안에서 proot-distro',
          '/data/data/com.termux/files/usr/bin/proot-distro list 2>&1 '
          '| head -n 2 | cut -c1-100'),
        S('마운트 줄 수', 'grep -c . /proc/mounts'),
    ]),
    Capture('proot_cost', 'termux', 'snapshot', [
        S('bionic: getpid 20만 번 ×3',
          'python3 exp/timeit_exp.py -n 3 -- '
          '%s/syscall_loop 200000' % BB, timeout=600),
        S('bionic: getcwd 20만 번 ×3 — proot 가 가로채는 호출',
          'python3 exp/timeit_exp.py -n 3 -- '
          '%s/syscall_loop 200000 getcwd' % BB, timeout=600),
        S('true 100번 ×3',
          'python3 exp/timeit_exp.py -n 3 -- sh exp/fork_loop.sh 100',
          timeout=600),
    ]),
    Capture('limits', 'termux', 'stable', [
        S('pid_max', 'cat /proc/sys/kernel/pid_max'),
        S('ulimit -a', 'ulimit -a'),
    ]),
    Capture('storage', 'termux', 'stable', [
        S('~/storage 의 링크', "find ~/storage -maxdepth 1 -type l "
          "-printf '%f -> %l\\n' 2>&1 | sort"),
        S('공유 저장소 마운트 줄',
          "grep ' /storage/emulated ' /proc/mounts | cut -d' ' -f1-4"),
    ]),
    Capture('sshd', 'termux', 'stable', [
        S('ssh 판', 'ssh -V 2>&1'),
        S('설정 디렉터리', 'ls $PREFIX/etc/ssh'),
        S('sshd_config 의 켜진 줄',
          "grep -v '^#' $PREFIX/etc/ssh/sshd_config | grep ."),
    ]),
    Capture('toolchains', 'termux', 'snapshot', [
        S('판', 'clang --version | head -n 1; python3 --version; '
          'node --version; go version; rustc --version; git --version'),
    ]),
    Capture('x11', 'termux', 'stable', [
        S('X11 관련 패키지',
          "dpkg -l | awk '/^ii/{print $2}' | "
          "grep -E 'x11|xfce|vnc|xorg' || echo '(없음)'"),
    ]),
    # 12부 — 이 proot 세션의 /tmp 는 Termux 의 /tmp 와 같은 곳인가.
    # termux-x11 은 --shared-tmp 를 요구한다(README 1.6)
    Capture('x11_proot', 'proot', 'stable', [
        S('두 /tmp 의 inode', "stat -c '%i %n' /tmp "
          '/data/data/com.termux/files/usr/tmp'),
        S('X 소켓 디렉터리', 'ls -A /tmp/.X11-unix 2>&1 | head -n 3'),
    ]),
    Capture('signals', 'termux', 'stable', [
        S('SIGKILL 의 137', 'sh exp/signals.sh | tail -n 1'),
    ]),
    Capture('session_self', 'proot', 'snapshot', [
        S('메모리', 'free -m'),
        S('RSS 가 큰 프로세스',
          'ps -eo rss,comm --sort=-rss | head -n 8'),
    ]),
    # 핀 커밋의 소스에서 필요한 줄만 뽑는다 — 줄이 72칸을 넘어
    # 코드 블록에 못 싣는 파일(XML 등)을 위해서다.
    Capture('src_manifest', 'termux', 'stable', [
        S('termux-app 이 요청하는 권한',
          'python3 deck/srcpin.py grep %s \'use.*permission\\.[A-Z_]+\''
          % MANI),
        S('sharedUserId', 'python3 deck/srcpin.py grep %s '
          '\'sharedUserId="[^"]*"\'' % MANI),
        S('저장소 옛 방식', 'python3 deck/srcpin.py grep %s '
          '\'requestLegacy[A-Za-z]*="[a-z]*"\'' % MANI),
    ]),
    Capture('src_app', 'termux', 'stable', [
        S('termux.properties 의 키',
          "python3 deck/srcpin.py grep 'termux-app:*/TermuxPropertyCons"
          "tants.java' 'KEY_[A-Z_]+ += +\"[a-z0-9-]+\"'"),
        S('allow-external-apps',
          "python3 deck/srcpin.py grep "
          "'termux-app:*/TermuxConstants.java'"
          " 'PROP_ALLOW_EXTERNAL_APPS = \"[a-z-]+\"'"),
        S('RUN_COMMAND 권한', 'python3 deck/srcpin.py grep %s '
          "'permission.RUN_COMMAND'" % MANI),
        S('셸을 못 찾으면', "python3 deck/srcpin.py grep "
          "'termux-app:*/TermuxSession.java' "
          "'Fall back.*|login shell|\"/system/bin/sh\"'"),
        S('설치기 머리 주석의 걸음',
          "python3 deck/srcpin.py grep "
          "'termux-app:*/TermuxInstaller.java'"
          " '[(][0-9.]+[)] .*' | cut -c1-100"),
        S('스테이징을 접두사로',
          "python3 deck/srcpin.py grep "
          "'termux-app:*/TermuxInstaller.java'"
          " 'STAGING_PREFIX_DIR.renameTo[(][A-Z_]+[)]'"),
        S('웨이크락의 종류', "python3 deck/srcpin.py grep "
          "'termux-app:*/TermuxService.java' "
          "'[a-zA-Z]+Manager\\.[A-Z_]+_(LOCK|PERF)'"),
    ]),
    Capture('src_pkgs', 'termux', 'stable', [
        S('massage 단계가 셔뱅을 고치는 줄',
          "python3 deck/srcpin.py grep "
          "'termux-packages:*/termux_step_massage.sh' "
          "'# Fix shebang.*|sed --follow.*'"),
        S('apt 패치가 root 검사를 넣는 곳',
          "python3 deck/srcpin.py grep "
          "'termux-packages:packages/apt/0010-*.patch' "
          "'^.   if .getuid.. == 0. .'"),
    ]),
    # 개인정보 명령은 실행하지 않는다(§0.8) — 무엇이 나오는지는 앱
    # 소스의 JSON 칸 이름으로 보인다
    Capture('src_api', 'termux', 'stable', [
        S('앱이 받는 메서드 수', "python3 deck/srcpin.py grep "
          "'termux-api:*/TermuxApiReceiver.java' "
          "'case \"[A-Za-z]+\"' | wc -l"),
        S('termux-sms-list 가 내는 칸', "python3 deck/srcpin.py grep "
          "'termux-api:*/SmsInboxAPI.java' 'name[(]\"[a-z_]+\"[)]'"),
        S('termux-location 이 내는 칸', "python3 deck/srcpin.py grep "
          "'termux-api:*/LocationAPI.java' 'name[(]\"[a-z_]+\"[)]'"),
        S('termux-battery-status 가 내는 칸',
          "python3 deck/srcpin.py grep "
          "'termux-api:*/BatteryStatusAPI.java' "
          "'put[A-Za-z]*[(]out, \"[a-z_]+\"'"),
    ]),
    # 거부 목록이 실행 **전에** 막는지 — 안쪽 tmx.sh 는 명령을 받자마자
    # 거부하고 99 로 끝난다. 개인정보 명령은 한 번도 돌지 않는다(§0.8)
    Capture('tmx_deny', 'proot', 'stable', [
        S('개인정보 명령을 건네 보면',
          'sh tools/tmx.sh termux-sms-list; echo "exit=$?"'),
        S('카메라도',
          'sh tools/tmx.sh termux-camera-photo a.jpg; echo "exit=$?"'),
    ]),
    # 8부 — 지금 이 앱의 프로세스들(팬텀 프로세스 한도 32 와 견준다).
    # ps 는 같은 uid 의 것만 보인다. 수는 그때그때라 스냅샷이다
    Capture('procs_now', 'proot', 'snapshot', [
        S('이름별 개수', 'ps -e -o comm= | sort | uniq -c | sort -rn'),
        S('모두 몇 개', 'ps -e -o pid= | wc -l'),
        S('부모가 init 인 것', "ps -e -o ppid=,comm= | awk '$1 == 1'"),
    ]),
    # 8부 — bionic 에 맞추느라 붙은 패치의 양. 고정 커밋의 트리만 본다
    Capture('porting', 'termux', 'stable', [
        S('고정 커밋의 packages/', 'sh tools/patch_stats.sh '
          'sources/termux-packages 7d5b4d3'),
    ]),
    Capture('libandroid', 'termux', 'stable', [
        S('bionic 에 없는 것을 채우는 패키지',
          "dpkg -l | awk '/^ii/ && $2 ~ /^libandroid-/ "
          "{print $2, $3}'"),
    ]),
    Capture('src_limits', 'termux', 'stable', [
        S('wake lock 을 잡을 때', "python3 deck/srcpin.py grep "
          "'termux-app:*/TermuxService.java' "
          "'.*BatteryOptimizations.*'"),
        S('매니페스트의 권한', "python3 deck/srcpin.py grep "
          "'termux-app:app/src/main/AndroidManifest.xml' "
          "'.*IGNORE_BATTERY.*'"),
    ]),
    # 10부 — 도구마다 자기가 어디서 도는 줄 아는가. 판이 바뀌면
    # 달라지는 줄이 있어 toolchains 와 같이 스냅샷이다
    Capture('dev_termux', 'termux', 'snapshot', [
        S('파이썬', 'python3 -c "import sys, sysconfig; '
          'print(sys.platform, sysconfig.get_platform())"'),
        S('Node.js',
          "node -p 'process.platform + \" \" + process.arch'"),
        S('clang 의 대상', 'clang -dumpmachine'),
        S('rustc 의 호스트', 'rustc -vV | grep host'),
        S('Go', 'go env GOOS GOARCH'),
        S('없는 도구', 'for c in vim nano tmux git make ssh sshd rsync '
          'emacs; do command -v $c >/dev/null || echo "$c 없음"; done'),
    ]),
    Capture('dev_proot', 'proot', 'stable', [
        S('파이썬', 'python3 -c "import sys, sysconfig; '
          'print(sys.platform, sysconfig.get_platform())"'),
        S('gcc 의 대상', 'gcc -dumpmachine'),
        S('node 는', "command -v node || echo '(우분투 쪽에는 없다)'"),
        S('git 은', "command -v git || echo '(우분투 쪽에는 없다)'"),
    ]),
    # 11부 — Termux:Boot 가 부팅 때 하는 일(소스)과, 폰에 띄운 작은
    # 웹 서버. 서버는 127.0.0.1 에만 붙이고 한 번 묻고 끈다
    Capture('src_boot', 'termux', 'stable', [
        S('부팅 방송을 받고 파일을 이름순으로',
          "python3 deck/srcpin.py grep "
          "'termux-boot:*/BootReceiver.java' '.*(ACTION_BOOT|sort).*'"),
        S('3초 안에 돌 작업으로, 실행 권한도 챙긴다',
          "python3 deck/srcpin.py grep "
          "'termux-boot:*/BootReceiver.java' "
          "'.*(Deadline|set(Read|Exec)).*'"),
    ]),
    Capture('serve_local', 'termux', 'stable', [
        S('exp/ 를 8080 에 내놓고 hello.c 를 한 번 받는다',
          'sh exp/serve_once.sh 8080 exp hello.c'),
    ]),
    # 14부 — 매니페스트가 남에게 여는 문과 그 자물쇠
    Capture('src_security', 'termux', 'stable', [
        S('권한·authority 줄', "python3 deck/srcpin.py grep "
          "'%s' '.*(ission=|ities=|Level).*'" % MANI),
    ]),
    # 14부 — 이 덱의 개인정보 검사가 무엇을 바꾸고 무엇을 막는가.
    # 예시는 문서의 예시값(공개 DNS·가짜 번호)만 쓴다
    Capture('scrub_demo', 'proot', 'stable', [
        # 명령 줄 자체가 검사에 걸리지 않도록 값을 printf 로 조립한다
        S('세 줄을 쓴다', "printf 'inet 121.130.%s.42\\n"
          "dns 8.8.8.8\\npkg 14.0.0.11-1\\n' 7 > scratch/f.txt"),
        S('고친다', 'python3 tools/scrub.py --fix scratch/f.txt'),
        S('바뀐 것은 공인 IP 하나', 'cat scratch/f.txt'),
        S('막는 것 — 값은 가리고 종류만', "printf 'call 010-%s-5678\\n'"
          ' 1234 > scratch/c.txt; python3 tools/scrub.py --check '
          'scratch/c.txt'),
        S('시험', 'python3 -m unittest tools.tests.test_scrub 2>&1'
          " | grep -E '^(Ran|OK)' | cut -d' ' -f1-3"),
    ]),
    # 15부 — 실험 12: 라이브러리를 지운 실행 파일. 두 링커의 말
    Capture('missing_termux', 'termux', 'stable', [
        S('bionic — Termux 의 clang', 'sh exp/missing_lib.sh clang '
          'scratch/missing_b'),
    ]),
    Capture('missing_proot', 'proot', 'stable', [
        S('glibc — 우분투의 gcc', 'sh exp/missing_lib.sh gcc '
          'scratch/missing_g | cut -c1-100'),
    ]),
    # 13부 — 이 저장소 자신. 커밋·덱 수는 날마다 늘어 스냅샷이다
    Capture('repo_self', 'termux', 'snapshot', [
        S('저장소의 커밋 수', 'git -C .. log --oneline | wc -l'),
        S('맨 위의 HTML 문서 수', 'ls ../*.html | wc -l'),
        S('달마다 커밋', 'git -C .. log --format=%ad '
          "--date=format:%Y-%m | sort | uniq -c | tail -n 4"),
        S('저장소 CLAUDE.md 의 절', "grep '^## ' ../CLAUDE.md"),
    ]),
    Capture('src_pd_claude', 'termux', 'stable', [
        S('proot-distro 의 CLAUDE.md 절 제목', "python3 deck/srcpin.py "
          "grep 'proot-distro:CLAUDE.md' '^## .*' | head -n 12"),
        S('빈 줄이 아닌 줄 수', "python3 deck/srcpin.py grep "
          "'proot-distro:CLAUDE.md' '.+' | wc -l"),
    ]),
    # 9부 — 이 세션을 띄운 proot 명령줄. 추적자(TracerPid)의
    # cmdline 을 읽는다. 세션을 다시 띄우면 바뀔 수 있어 스냅샷이다
    Capture('proot_session', 'proot', 'snapshot', [
        S('추적자의 이름', "t=$(awk '/^TracerPid/{print $2}' "
          "/proc/self/status); awk '/^Name/' /proc/$t/status"),
        # 줄이 길어 둘로 나눈다 — sysdata 가짜 파일 바인드는 따로
        S('추적자의 명령줄',
          "t=$(awk '/^Tr/{print$2}' /proc/self/status); "
          "tr '\\0' '\\n' </proc/$t/cmdline | grep -v sysdata"
          " | cut -c-100"),
        S('그중 sysdata 바인드', "t=$(awk '/^Tr/{print $2}' "
          "/proc/self/status); tr '\\0' '\\n' < /proc/$t/cmdline"
          " | grep -o 'sysdata/.*'"),
        S('가짜 /proc/version', 'cat /proc/version | cut -c1-100'),
        S('빈 /sys/fs/selinux', 'ls -A /sys/fs/selinux | wc -l'),
    ]),
    # --link2symlink — 하드 링크를 심볼릭 링크 둘로 흉내 낸다(9부).
    # /.l2s 의 개수는 설치한 패키지에 따라 늘어 스냅샷이다
    Capture('proot_l2s', 'proot', 'snapshot', [
        S('하드 링크를 만들면', 'mkdir -p scratch/l2s && cd scratch/l2s'
          " && echo hi >x && ln -f x y && stat -c '%n %h %F' x y"),
        S('실제로 생긴 것', "cd /.l2s && stat -c '%n  %F' .l2s.x0*"),
        S('/.l2s 에 쌓인 항목 수', 'ls -A /.l2s | wc -l'),
        S('지우면 함께 사라진다', 'rm scratch/l2s/x scratch/l2s/y; '
          "ls -A /.l2s | grep -c '^\\.l2s\\.x0'"),
    ]),
    # 이 세션의 컨테이너 — proot-distro 가 설치 때 남긴 것(9부)
    Capture('proot_container', 'proot', 'stable', [
        S('컨테이너 디렉터리', 'ls'),
        S('어느 이미지인가', "grep -o '\"image_ref\": \"[^\"]*\"\\|"
          "\"arch\": \"[^\"]*\"' manifest.json"),
        S('안드로이드 사용자를 등록해 둔 줄', 'grep aid_ /etc/passwd; '
          'grep -c aid_ /etc/group'),
        S('DNS', 'cat /etc/resolv.conf'),
    ], cwd=PD_UBUNTU),
    Capture('src_proot', 'termux', 'stable', [
        S('proot 가 멈추는 호출의 수', "python3 deck/srcpin.py grep "
          "'proot:src/syscall/seccomp.c' '^\\s+\\{ PR_' | wc -l"),
        S('그 목록에 getpid 는', "python3 deck/srcpin.py grep "
          "'proot:src/syscall/seccomp.c' 'PR_getpid' | wc -l"),
        S('proot-distro 가 붙이는 옵션', "python3 deck/srcpin.py grep "
          "'proot-distro:*/proot_cmd.py' 'append\\(\"-.*'"),
        S('가짜 커널 판', "python3 deck/srcpin.py grep "
          "'proot-distro:proot_distro/constants.py' "
          "'KERNEL_RELEASE =.*'"),
        S('proot 옵션의 한 줄 설명', "python3 deck/srcpin.py grep "
          "'proot:src/cli/proot.h' 'description = .*'"),
        S('-p 가 포트를 옮기는 규칙', "python3 deck/srcpin.py grep "
          "'proot:*/port_switch.c' '#define PORT_.*'"),
    ]),
    # 사용자 설정 디렉터리는 이름만 본다 — 내용은 사용자의 것이다(§3.3)
    Capture('dot_termux', 'termux', 'stable', [
        S('~/.termux 에 있는 이름', 'ls -A ~/.termux'),
    ]),
    Import('native_device', os.path.join(BASE, 'data', 'device.txt')),
]

def main(argv):
    if '--list' in argv:
        for c in CAPTURES:
            print('%-16s %-7s %-8s %s'
                  % (c.cid, c.side, c.kind,
                     '%d걸음' % len(c.steps) if hasattr(c, 'steps')
                     else c.path))
        return 0
    if '--check' in argv:
        bad = check(OUT)
        for line in bad:
            print('  ✗ ' + line)
        print('캡처 검사 — 걸린 것 %d건' % len(bad))
        return 1 if bad else 0
    only = set(a for a in argv if not a.startswith('--'))
    force = '--resnap' in argv
    known = set(c.cid for c in CAPTURES)
    if only - known:
        print('모르는 캡처: %s' % ', '.join(sorted(only - known)))
        return 2
    date = datetime.date.today().isoformat()
    man = load_manifest(OUT)
    for c in CAPTURES:
        if only and c.cid not in only:
            continue
        print('  %-16s %s …' % (c.cid, c.side), flush=True)
        e = record(c, OUT, date, tmx_runner,
                   force=force and c.cid in only)
        if e is None:
            print('    (원본이 아직 없다 — 건너뜀)')
            continue
        man[c.cid + '.txt'] = e
    save_manifest(OUT, man)
    bad = check(OUT)
    for line in bad:
        print('  ✗ ' + line)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
