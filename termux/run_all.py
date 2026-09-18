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
import scrub                                       # noqa: E402

# 덱의 캡처 폭 상한(build_deck.py MAX_TERM_COLS 와 같아야 한다)
MAX_COLS = 108
PROMPT = {'termux': '$', 'proot': '#'}
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
    entry = {'kind': cap.kind, 'side': cap.side,
             'cmds': [s.cmd for s in cap.steps]}
    if cap.kind == 'snapshot' and os.path.exists(path) and not force:
        m = SNAP_RE.match(io.open(path, encoding='utf-8').read())
        entry['date'] = m.group(1) if m else date
        return entry
    outs = [runner(cap.side, s.cmd, cap.cwd, s.timeout, s.install)[0]
            for s in cap.steps]
    text, _n = scrub.fix(render(cap, outs))
    if cap.kind == 'snapshot':
        text = '# snapshot %s\n' % date + text
        entry['date'] = date
    io.open(path, 'w', encoding='utf-8', newline='\n').write(text)
    return entry


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
    ]),
]


def main(argv):
    if '--list' in argv:
        for c in CAPTURES:
            print('%-16s %-7s %-8s %d걸음'
                  % (c.cid, c.side, c.kind, len(c.steps)))
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
        man[c.cid + '.txt'] = record(c, OUT, date, tmx_runner,
                                     force=force and c.cid in only)
    save_manifest(OUT, man)
    bad = check(OUT)
    for line in bad:
        print('  ✗ ' + line)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
