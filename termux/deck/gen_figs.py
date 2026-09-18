#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""덱에 실을 그림(SVG)을 만든다. 손으로 그리지 않는다.

    python3 deck/gen_figs.py            # deck/figs/*.svg 를 다시 만든다
    python3 deck/gen_figs.py --check    # 지금 것과 같은지만 본다

구조도(샌드박스·앱 구조·API 경로·패키지 흐름·proot 고리)는 설명용이다.
그 안의 이름(클래스·경로·저장소 주소)은 핀 고정한 소스나 data/*.tsv
에서 확인한 것만 쓴다. 숫자가 들어가는 그림(릴리스 수·SDK 변화·
패키지 크기·포트 훑기)은 data/ 나 out/ 을 읽어 그린다 — 그림 안에
숫자를 손으로 적지 않는다.

만든 뒤에는 **눈으로 본다**. `make figs-png` 가 검정 바탕 PNG 를
.svgrender/ 에 뽑는다. 글자가 겹치거나 잘리는 것은 기계가 못 잡는다.
(transformer/deck/gen_figs.py 의 틀을 물려받았다.)
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
FIGS = os.path.join(HERE, 'figs')
OUT = os.path.join(BASE, 'out')
DATA = os.path.join(BASE, 'data')
sys.path.insert(0, HERE)

import svgkit as sk                                    # noqa: E402
from svgkit import Fig                                 # noqa: E402

FIGURES = {}


def fig(name):
    def deco(fn):
        FIGURES[name] = fn
        return fn
    return deco


def tsv(name):
    """data/<name> → 칸 이름을 열쇠로 한 dict 목록."""
    head, rows = None, []
    for line in io.open(os.path.join(DATA, name), encoding='utf-8'):
        line = line.rstrip('\n')
        if not line.strip() or line.startswith('#'):
            continue
        cols = line.split('\t')
        if head is None:
            head = cols
        else:
            rows.append(dict(zip(head, cols + [''] * len(head))))
    return rows


def section(name, title_part):
    """out/<name> 에서 제목에 title_part 가 든 절의 본문(명령·끝줄 뺌)."""
    text = io.open(os.path.join(OUT, name), encoding='utf-8').read()
    lines, on = [], False
    for line in text.split('\n'):
        if line.startswith('== '):
            on = title_part in line
            continue
        if on:
            lines.append(line)
    lines = [l for l in lines[1:] if not l.startswith('## tmx:')]
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def arrow(f, x1, y1, x2, y2, hot=False, head=5):
    """선 + 끝의 삼각형. 방향은 (x1,y1) → (x2,y2)."""
    cls = 'arw hot' if hot else 'arw'
    f.line(x1, y1, x2, y2, cls=cls)
    dx, dy = x2 - x1, y2 - y1
    n = max(1e-9, (dx * dx + dy * dy) ** 0.5)
    ux, uy = dx / n, dy / n
    bx, by = x2 - ux * head, y2 - uy * head
    f.poly([(x2, y2), (bx - uy * head * .6, by + ux * head * .6),
            (bx + uy * head * .6, by - ux * head * .6)],
           cls='dot2' if hot else 'dotn', extra=' style="opacity:1"')


def box(f, x, y, w, h, g, title, sub=None):
    """층 색 g(g1…g6)의 상자. 제목 한 줄, 필요하면 아래에 작은 줄."""
    f.rect(x, y, w, h, cls='box %s' % g if g else 'box')
    if sub:
        f.text(x + w / 2, y + h / 2 - 2, title, cls='key')
        f.text(x + w / 2, y + h / 2 + 10, sub, cls='cap')
    else:
        f.text(x + w / 2, y + h / 2 + 3, title, cls='key')


# ── 3부: 안드로이드 앱 샌드박스 ──────────────────────────────────────
@fig('sandbox')
def f_sandbox():
    f = Fig(h=210, title='앱마다 uid 하나, 데이터 디렉터리 하나')
    box(f, 10, 170, 320, 30, 'g1', '리눅스 커널 (안드로이드)',
        'uid·SELinux·seccomp 로 가른다')
    apps = [('다른 앱', 'u0_a101', '/data/data/<패키지>', 'g6'),
            ('Termux', 'u0_aNNN', '/data/data/com.termux', 'g2'),
            ('또 다른 앱', 'u0_a205', '/data/data/<패키지>', 'g6')]
    for k, (name, uid, d, g) in enumerate(apps):
        x = 10 + k * 108
        box(f, x, 60, 100, 44, g, name, uid)
        f.rect(x, 110, 100, 34, cls='box off')
        f.text(x + 50, 124, '/data/data/', cls='cap')
        f.text(x + 50, 136, d.split('/data/data/')[1], cls='cap')
        arrow(f, x + 50, 146, x + 50, 168)
    box(f, 10, 12, 320, 34, 'g1', 'Zygote → 앱 프로세스',
        '앱은 전부 같은 뿌리에서 갈라져 나온다')
    for k in range(3):
        arrow(f, 60 + k * 108, 46, 60 + k * 108, 58)
    return f.render()


# ── 4부: termux-app 의 구조 ─────────────────────────────────────────
@fig('app_arch')
def f_app_arch():
    f = Fig(h=236, title='화면에서 셸까지 — termux-app 의 층')
    rows = [('TermuxActivity', '화면·키보드·서랍', 'g2'),
            ('TerminalView', 'terminal-view: 글자를 그린다', 'g2'),
            ('TermuxService', '포그라운드 서비스: 세션을 붙든다', 'g2'),
            ('TerminalSession', 'terminal-emulator: PTY 를 연다', 'g2'),
            ('PTY  →  $PREFIX/bin/login  →  bash', '커널의 가상 터미널',
             'g1')]
    y = 8
    for k, (a, b, g) in enumerate(rows):
        box(f, 30, y, 280, 34, g, a, b)
        if k < len(rows) - 1:
            arrow(f, 170, y + 34, 170, y + 46)
        y += 46
    return f.render()


# ── 7부: Termux:API 의 경로 ─────────────────────────────────────────
@fig('api_path')
def f_api_path():
    f = Fig(h=250, title='termux-battery-status 한 줄이 가는 길')
    steps = [('termux-battery-status', '셸 스크립트 — 인자 검사', 'g2'),
             ('$PREFIX/libexec/termux-api', 'C 프로그램 — 메서드 이름 전달',
              'g2'),
             ('유닉스 소켓 · 없으면 am broadcast', '앱을 깨워 부탁한다',
              'g1'),
             ('Termux:API 앱 (com.termux.api)',
              'TermuxApiReceiver → 안드로이드 API', 'g6'),
             ('JSON 출력', '소켓으로 돌아와 표준 출력으로', 'g2')]
    y = 6
    for k, (a, b, g) in enumerate(steps):
        box(f, 30, y, 280, 38, g, a, b)
        if k < len(steps) - 1:
            arrow(f, 170, y + 38, 170, y + 50, hot=(k == 2))
        y += 50
    return f.render()


# ── 5부: 셔뱅과 termux-exec ─────────────────────────────────────────
@fig('execve_path')
def f_execve_path():
    f = Fig(h=200, title='#!/bin/sh 는 어디로 가나')
    f.text(85, 14, 'termux-exec 없이', cls='key')
    f.text(255, 14, 'termux-exec 를 LD_PRELOAD 로', cls='key')
    for x, hot in ((10, False), (180, True)):
        box(f, x, 24, 150, 34, 'g2', 'execve("./a.sh")', '셔뱅 #!/bin/sh')
        arrow(f, x + 75, 58, x + 75, 76, hot=hot)
    box(f, 10, 78, 150, 40, 'g1', '커널이 /bin/sh 를 연다',
        '안드로이드에는 없다')
    box(f, 10, 132, 150, 34, 'g5', 'ENOENT', 'No such file')
    arrow(f, 85, 118, 85, 130)
    box(f, 180, 78, 150, 40, 'g2', '가로채서 고쳐 쓴다',
        '/bin/sh → $PREFIX/bin/sh')
    box(f, 180, 132, 150, 34, 'g2', '실행된다', '$PREFIX/bin/sh a.sh')
    arrow(f, 255, 118, 255, 130, hot=True)
    f.text(170, 190, '그림은 설명용 — 실제 동작은 5부의 캡처와 소스',
           cls='cap')
    return f.render()


# ── 6부: 패키지가 폰까지 오는 길 ─────────────────────────────────────
@fig('package_flow')
def f_package_flow():
    main = [r for r in tsv('repos_apt.tsv') if r['apt-repo'] == 'main']
    host = main[0]['url'].split('/')[2] if main else '?'
    f = Fig(h=270, title='소스에서 $PREFIX 까지')
    steps = [('termux/termux-packages', 'packages/<이름>/build.sh', 'g3'),
             ('build-package.sh + NDK', 'x86-64 에서 교차 컴파일', 'g3'),
             ('.deb 파일', '경로는 /data/data/com.termux/…', 'g3'),
             (host, '기본 저장소 — 미러가 따라 복제', 'g3'),
             ('pkg → apt → dpkg', '이 폰에서', 'g2'),
             ('$PREFIX', '/data/data/com.termux/files/usr', 'g2')]
    y = 4
    for k, (a, b, g) in enumerate(steps):
        box(f, 40, y, 260, 34, g, a, b)
        if k < len(steps) - 1:
            arrow(f, 170, y + 34, 170, y + 45)
        y += 45
    return f.render()


# ── 4부: 부트스트랩 설치 순서 (TermuxInstaller 의 머리 주석 1–5) ──────
@fig('bootstrap_seq')
def f_bootstrap_seq():
    f = Fig(h=250, title='첫 실행 — TermuxInstaller 의 다섯 걸음')
    steps = [('(1) $PREFIX 가 있나?', '있으면 끝 — 없을 때만 설치', 'g2'),
             ('(2) "Installing…" 창', '진행 표시', 'g2'),
             ('(3) $STAGING_PREFIX 비우기', '지난번에 깨진 것 치우기',
              'g2'),
             ('(4) zip 을 공유 라이브러리에서', 'APK 안에 실려 온 부트스트랩',
              'g3'),
             ('(5) 풀기 · SYMLINKS.txt', '실행 권한 · 심볼릭 링크 세우기',
              'g3')]
    y = 6
    for k, (a, b, g) in enumerate(steps):
        box(f, 30, y, 280, 38, g, a, b)
        if k < len(steps) - 1:
            arrow(f, 170, y + 38, 170, y + 49)
        y += 49
    return f.render()


# ── 9부: proot 의 고리 ──────────────────────────────────────────────
@fig('proot_loop')
def f_proot_loop():
    f = Fig(h=220, title='경로를 쓰는 시스템 호출에 proot 가 끼어든다')
    box(f, 10, 20, 130, 40, 'g4', '추적되는 프로그램', 'open("/etc/os-release")')
    box(f, 200, 20, 130, 40, 'g4', 'proot (추적자)', 'ptrace 로 멈춰 세움')
    box(f, 200, 100, 130, 40, 'g4', '경로 번역',
        '…/rootfs/etc/os-release')
    box(f, 10, 170, 320, 36, 'g1', '커널', '바뀐 인자로 진짜 호출')
    arrow(f, 140, 34, 198, 34, hot=True)
    arrow(f, 265, 60, 265, 98)
    arrow(f, 265, 140, 265, 168)
    arrow(f, 120, 168, 75, 62)
    f.text(170, 28, '① 들어갈 때', cls='cap')
    f.text(96, 120, '② 결과를 돌려준다', cls='cap')
    return f.render()


# ── 8부: 팬텀 프로세스 킬러를 끄는 법 (data/android.tsv 12~14) ─────────
@fig('phantom_steps')
def f_phantom_steps():
    rows = [r for r in tsv('android.tsv')
            if r['short'] and r['android-version'] in ('12', '12L', '14')
            and ('팬텀' in r['behaviour'] or 'phantom' in r['behaviour']
                 or 'child process' in r['behaviour'])]
    f = Fig(h=40 + 58 * len(rows), title='판마다 다른 끄는 법')
    y = 8
    for r in rows:
        box(f, 10, y, 60, 46, 'g1', 'Android', r['android-version'])
        # 요약은 data/android.tsv 의 short 칸 — '|' 가 줄바꿈 자리
        first, _, second = r['short'].partition('|')
        f.rect(80, y, 250, 46, cls='box g5')
        f.text(205, y + 19, first, cls='cap')
        f.text(205, y + 33, second, cls='cap')
        y += 58
    f.text(170, y + 10, '자세한 명령과 출처는 8부 · data/android.tsv',
           cls='cap')
    return f.render()


# ── 1부: 어디서 설치하나 (README 1.3) ────────────────────────────────
@fig('install_tree')
def f_install_tree():
    f = Fig(h=250, title='설치처 고르기')
    box(f, 110, 6, 120, 34, 'g1', '안드로이드 판은?')
    box(f, 6, 70, 100, 44, 'g6', '5·6', 'GitHub apt-android-5')
    box(f, 120, 70, 100, 44, 'g2', '7 이상', 'F-Droid 또는 GitHub')
    box(f, 234, 70, 100, 44, 'g3', '11 이상', 'Google Play(실험판)')
    for x in (56, 170, 284):
        arrow(f, 170, 40, x, 68)
    f.rect(6, 140, 328, 56, cls='box g5')
    f.text(170, 158, '설치처를 섞지 않는다', cls='key')
    f.text(170, 172, '앱·플러그인은 sharedUserId com.termux —', cls='cap')
    f.text(170, 184, '같은 키로 서명된 것끼리만 함께 돈다', cls='cap')
    f.text(170, 220, '패키지 갱신은 7 이상만(5·6 은 앱만)', cls='cap')
    return f.render()


# ── 7·11부: 플러그인이 스크립트를 부르는 자리 (각 README) ─────────────
@fig('plugin_dirs')
def f_plugin_dirs():
    f = Fig(h=200, title='플러그인마다 스크립트를 두는 디렉터리')
    rows = [('Termux:Boot', '기기가 켜지면', '~/.termux/boot/',
             '안의 스크립트를 이름 차례로'),
            ('Termux:Widget', '홈 화면 위젯을 누르면', '~/.shortcuts/',
             '위젯에서 고른 스크립트'),
            ('Termux:Tasker', 'Tasker 작업이 부르면', '~/.termux/tasker/',
             '작업이 이름을 댄 스크립트')]
    y = 10
    for name, when, d, what in rows:
        box(f, 6, y, 110, 46, 'g6', name, when)
        arrow(f, 116, y + 23, 150, y + 23)
        box(f, 152, y, 182, 46, 'g2', d, what)
        y += 60
    return f.render()


# ── 10·11부: 폰의 sshd 에 PC 가 붙는다 (위키 Remote Access) ───────────
@fig('ssh_topology')
def f_ssh_topology():
    f = Fig(h=170, title='폰이 서버, PC 가 손님')
    box(f, 6, 40, 130, 70, 'g6', 'PC', 'ssh -p 8022 폰의주소')
    box(f, 204, 40, 130, 70, 'g2', '폰의 Termux', 'sshd · 포트 8022')
    arrow(f, 136, 64, 202, 64, hot=True)
    arrow(f, 202, 88, 136, 88)
    f.text(170, 58, '같은 Wi-Fi', cls='cap')
    f.text(170, 104, '키로 로그인', cls='cap')
    f.text(170, 140, '8022 는 위키가 적은 기본값 — 이 기기의 설정은',
           cls='cap')
    f.text(170, 152, '10부의 sshd_config 캡처', cls='cap')
    return f.render()


# ── 10부: termux-backup 이 담는 것과 안 담는 것 ───────────────────────
@fig('backup_scope')
def f_backup_scope():
    f = Fig(h=170, title='termux-backup 은 $PREFIX 만 담는다')
    box(f, 10, 10, 320, 30, 'g6', '/data/data/com.termux/files')
    box(f, 10, 56, 150, 50, 'g2', 'usr ($PREFIX)', '백업에 들어간다')
    box(f, 180, 56, 150, 50, 'g5', 'home ($HOME)', '들어가지 않는다')
    arrow(f, 85, 40, 85, 54)
    arrow(f, 255, 40, 255, 54)
    f.text(170, 130, 'termux-tools 의 termux-backup 스크립트 머리 주석',
           cls='cap')
    f.text(170, 144, '— $HOME 관리는 사용자의 몫', cls='cap')
    return f.render()


# ── 14부: 위협 모델 ─────────────────────────────────────────────────
@fig('threat_model')
def f_threat_model():
    f = Fig(h=250, title='무엇을, 누구에게서 지키나')
    box(f, 110, 90, 120, 60, 'g2', '지킬 것', '$HOME · 키 · 토큰')
    threats = [(6, 6, '같은 키의 다른 앱', 'sharedUserId'),
               (234, 6, '네트워크', '열어 둔 sshd'),
               (6, 180, '내려받은 스크립트', '읽지 않고 실행'),
               (234, 180, '다른 앱', '공유 저장소의 파일')]
    for x, y, a, b in threats:
        box(f, x, y, 100, 50, 'g5', a, b)
        arrow(f, x + 50, y + (50 if y < 90 else 0), 170,
              90 if y < 90 else 150)
    return f.render()


# ── 6부: 저장소 계층 (data/repos_apt.tsv) ────────────────────────────
@fig('repo_tiers')
def f_repo_tiers():
    rows = tsv('repos_apt.tsv')
    f = Fig(h=24 + 44 * len(rows), title='저장소 다섯 층')
    y = 6
    for r in rows:
        g = 'g3' if r['apt-repo'] != 'tur' else 'g6'
        box(f, 6, y, 80, 36, g, r['apt-repo'], r['package'][:14])
        f.rect(92, y, 242, 36, cls='box off')
        u = r['url'].split()[0].replace('https://', '')
        f.text(213, y + 22, u[:40], cls='cap')
        y += 44
    return f.render()


# ── 2부: 해마다 나온 termux-app 릴리스 (data/releases.tsv) ─────────────
@fig('release_bars')
def f_release_bars():
    years = {}
    for r in tsv('releases.tsv'):
        if r['repo'] == 'termux-app':
            years[r['date'][:4]] = years.get(r['date'][:4], 0) + 1
    lo, hi = int(min(years)), int(max(years))
    # 릴리스가 없는 해도 막대 자리를 둔다 — 빼면 빈 해가 안 보인다
    ys = [str(y) for y in range(lo, hi + 1)]
    for y in ys:
        years.setdefault(y, 0)
    top = max(years.values())
    f = Fig(h=190, title='termux-app GitHub 릴리스 — 해마다')
    bw = 300.0 / len(ys)
    for k, y in enumerate(ys):
        h = 130.0 * years[y] / top
        x = 24 + k * bw
        f.rect(x + 2, 150 - h, bw - 4, h, cls='box g2')
        f.text(x + bw / 2, 146 - h, str(years[y]), cls='tick')
        f.text(x + bw / 2, 164, "'" + y[2:], cls='tick')
    f.line(20, 150, 330, 150, cls='ax')
    f.text(170, 184, 'data/releases.tsv (사전 릴리스 포함)', cls='cap')
    return f.render()


# ── 2·4부: minSdk·targetSdk 의 걸음 (data/app_sdk.tsv) ────────────────
@fig('sdk_steps')
def f_sdk_steps():
    rows = [r for r in tsv('app_sdk.tsv')
            if r['min-sdk'].isdigit() and r['target-sdk'].isdigit()
            and 'beta' not in r['tag']]
    f = Fig(h=210, title='termux-app 태그마다의 SDK 수준')
    lo, hi = 20, 30
    x0, x1, y0, y1 = 30, 330, 20, 170
    n = len(rows)

    def px(i):
        return x0 + (x1 - x0) * i / max(1, n - 1)

    def py(v):
        return y1 - (y1 - y0) * (v - lo) / (hi - lo)
    for v in (21, 24, 28):
        f.line(x0, py(v), x1, py(v), cls='grid')
        f.text(x0 - 4, py(v) + 3, str(v), cls='tick', anchor='end')
    f.path([(px(i), py(int(r['target-sdk']))) for i, r in
            enumerate(rows)], cls='cv3')
    f.path([(px(i), py(int(r['min-sdk']))) for i, r in
            enumerate(rows)], cls='cv5')
    f.text(px(0), y1 + 14, rows[0]['tag'], cls='tick', anchor='start')
    f.text(px(n - 1), y1 + 14, rows[-1]['tag'], cls='tick', anchor='end')
    sk.legend(f, 40, 30, [('targetSdk', 'cv3'), ('minSdk', 'cv5')])
    f.text(170, 202, 'data/app_sdk.tsv — 안정판 태그만', cls='cap')
    return f.render()


# ── 6부: 이 기기의 패키지 크기 분포 (out/dpkg_stats.txt) ───────────────
@fig('pkg_sizes')
def f_pkg_sizes():
    rows = []
    on = False
    for line in section('dpkg_stats.txt', '크기로 본'):
        if '크기 분포' in line:
            on = True
            continue
        if on:
            m = re.match(r'^\s{4}(.+?)\s+(\d+)$', line)
            if not m:
                break
            rows.append((m.group(1), int(m.group(2))))
    top = max(n for _k, n in rows)
    f = Fig(h=34 + 30 * len(rows), title='설치 크기로 나눈 패키지 수')
    y = 8
    for name, n in rows:
        f.text(92, y + 15, name, cls='tick', anchor='end')
        w = 200.0 * n / top
        f.rect(98, y + 4, w, 16, cls='box g3')
        f.text(102 + w, y + 16, str(n), cls='tick', anchor='start')
        y += 30
    f.text(170, y + 12, 'out/dpkg_stats.txt — 이 기기, proot 에서 읽음',
           cls='cap')
    return f.render()


# ── 8부: 1024 미만 포트 훑기 (out/exp_bionic.txt) ─────────────────────
@fig('port_scan')
def f_port_scan():
    spans = []
    for line in section('exp_bionic.txt', '포트 훑기'):
        m = re.match(r'^(\d+)(?:-(\d+))?: (\S+)$', line)
        if m:
            a = int(m.group(1))
            spans.append((a, int(m.group(2) or a), m.group(3)))
    f = Fig(h=150, title='127.0.0.1 에 bind — 1 부터 1100 까지')
    x0, x1 = 10, 330

    def px(p):
        return x0 + (x1 - x0) * (p - 1) / 1100.0
    for a, b, res in spans:
        cls = 'box g2' if res == 'ok' else 'box g5'
        w = max(1.5, px(b + 1) - px(a))
        f.rect(px(a), 30, w, 40, cls=cls)
    oks = [(a, b) for a, b, r in spans if r == 'ok' and a < 1024]
    for k, (a, b) in enumerate(oks):
        lab = str(a) if a == b else '%d–%d' % (a, b)
        f.text(px(a), 84 + (k % 3) * 11, lab, cls='tick', anchor='start')
    f.line(px(1024), 24, px(1024), 76, cls='cvd')
    f.text(px(1024) - 2, 20, '1024', cls='tick', anchor='end')
    sk.legend(f, 20, 128, [('bind 됨', 'cv2'), ('EACCES', 'cv5')])
    f.text(250, 142, 'out/exp_bionic.txt · 이 기기', cls='cap')
    return f.render()


def render_all():
    made = {}
    for name, fn in sorted(FIGURES.items()):
        made[name + '.svg'] = fn() + '\n'
    return made


def main(argv):
    made = render_all()
    if '--check' in argv:
        bad = []
        for name, want in sorted(made.items()):
            p = os.path.join(FIGS, name)
            cur = (io.open(p, encoding='utf-8').read()
                   if os.path.exists(p) else '')
            if cur != want:
                bad.append(name)
        for name in bad:
            print('  ✗ %s 가 소스와 어긋난다' % name)
        print('그림 %d장 — 어긋남 %d건' % (len(made), len(bad)))
        return 1 if bad else 0
    if not os.path.isdir(FIGS):
        os.makedirs(FIGS)
    for name, text in sorted(made.items()):
        io.open(os.path.join(FIGS, name), 'w', encoding='utf-8',
                newline='\n').write(text)
    print('그림 %d장 → deck/figs/' % len(made))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
