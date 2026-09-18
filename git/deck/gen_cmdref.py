# -*- coding: utf-8 -*-
"""17부(명령어 사전) 조각을 만든다 — deck/sections/17_cmdref.html.

    cd git && python3 deck/gen_cmdref.py

읽는 것: data/commands.tsv(명령·분류·NAME 줄)·data/commands_ko.tsv(한국어
한 줄)·out/cmdref*(-h 와 실행 예 캡처)·deck/sections/*.html(다른 부의
캡처에서 그 명령을 부른 곳). 손으로 적는 것은 이 파일의 표(분류 이름,
돌릴 수 없는 명령의 까닭)뿐이다.

"이 덱에서 돌린 곳" 은 캡처마다 처음 실린 부 하나만 센다 — 18·19부처럼
앞 부의 캡처를 다시 보인 곳은 넣지 않는다. OUT·GIT 지시자를 모두 보고,
cat 으로 보인 스크립트는 그 안의 명령까지 센다. O(조각 크기 + 캡처 수).
"""
import io, os, re, sys, glob, html
sys.path.insert(0, '.')
from exps.cmdref import EXAMPLES
from deck.build_deck import gitslug

CAT = {'mainporcelain': '주 명령', 'ancillarymanipulators': '보조 — 조작',
       'ancillaryinterrogators': '보조 — 조회',
       'foreignscminterface': '다른 SCM 과의 연결',
       'plumbingmanipulators': '배관 — 조작',
       'plumbinginterrogators': '배관 — 조회',
       'synchingrepositories': '저장소 동기화',
       'synchelpers': '동기화 도우미', 'purehelpers': '내부 도우미',
       'complete': '완성 목록 전용', 'guide': '안내서',
       'userinterfaces': '사용자 설명서',
       'developerinterfaces': '개발자 설명서(형식·프로토콜)'}
rows = []
for line in io.open('data/commands.tsv', encoding='utf-8'):
    if line.startswith('#') or line.startswith('command\t'):
        continue
    c = line.rstrip('\n').split('\t')
    rows.append(c)
ko = {}
for line in io.open('data/commands_ko.tsv', encoding='utf-8'):
    if line.startswith('#') or line.startswith('command\t'):
        continue
    a, b = line.rstrip('\n').split('\t')[:2]
    ko[a] = b
# -h 캡처: 첫 줄의 명령에서 이름을 읽는다
helpcap = {}
for f in glob.glob('out/cmdref__*.txt'):
    first = io.open(f, encoding='utf-8').readline()
    m = re.match(r'\$ (?:git )?(\S+) (?:-h|sync --help) ', first)
    assert m, f
    helpcap[m.group(1)] = os.path.basename(f)
excap = {}
for name, cmd in EXAMPLES.items():
    fn = 'cmdref_ex__%s.txt' % gitslug(cmd)
    assert os.path.exists('out/' + fn), fn
    excap[name] = fn
# 이 덱의 다른 부에서 그 명령을 실제로 돌린 캡처
used = {}
first_seen = set()
TOK = re.compile(r'(?:^|[\s;&|(`$])git((?:\s+-[Cc]\s+\S+)*)\s+([a-z][a-z0-9-]*)')
for sec in sorted(glob.glob('deck/sections/*.html')):
    part = int(os.path.basename(sec)[:2])
    if part in (17,):
        continue
    stext = io.open(sec, encoding='utf-8').read()
    files = re.findall(r'<!--OUT file=(\S+)', stext)
    # GIT 지시자(repo= cmd=)로 실은 캡처도 같은 파일 이름으로 푼다
    files += ['%s__%s.txt' % (r, gitslug(c)) for r, c in
              re.findall(r'<!--GIT repo=(\S+) cmd="([^"]*)"', stext)]
    for fn in files:
        # 같은 캡처를 뒤의 부가 다시 보이면(18·19부) 처음 실린 부만 센다
        if fn in first_seen:
            continue
        first_seen.add(fn)
        p = 'out/' + fn
        if not os.path.exists(p):
            continue
        text = io.open(p, encoding='utf-8').read()
        cmd = text.split('\n', 1)[0][2:]
        # cat 으로 보인 스크립트는 그 안의 명령도 센다(11부의 cgi.sh 같은 것)
        scan = text if cmd.startswith('cat ') else cmd
        for _, sub in TOK.findall(scan):
            used.setdefault(sub, set()).add(part)
ABS = {'gitk': '설치되지 않음', 'git-gui': '설치되지 않음',
       'git-citool': 'git gui 의 일부라 같이 없음',
       'git-svn': '설치되지 않음',
       'git-cvsserver': '스크립트는 있지만 펄 DBI 모듈이 없어 시작하지 못함',
       'gitweb': 'share/gitweb/gitweb.cgi 로 깔려 있지만 웹 서버가 부르는 CGI 라 명령줄 캡처가 없음'}
cmds = [r for r in rows if r[0].startswith('git-') or r[0] in ('gitk', 'gitweb', 'scalar')]
docs = [r for r in rows if r not in cmds]
o = []
w = o.append
w('''<article class="card section" id="p17">
<p class="chnum">17부</p>
<h2>명령어 사전</h2>
<p class="chsub">한 장에 명령 하나, 알파벳순</p>
</article>

<article class="card" id="p17-intro">
<h2>이 부를 읽는 법</h2>
<p class="lead">git 2.55.0 의 명령 목록(command-list.txt)에 있는 명령 %d개를 알파벳순으로 한 장씩 싣습니다.</p>
<ul>
<li><b>한 줄 설명</b> — 그 명령 설명서의 NAME 줄을 옮긴 것, 원문을 아래에 같이 둡니다.</li>
<li><b>분류</b> — command-list.txt 의 분류. porcelain(사람용)과 plumbing(스크립트용 배관)의 구분은 6부.</li>
<li><b>사용법</b> — 이 기계에서 <code>git 명령 -h</code> 를 돌린 앞 여섯 줄.</li>
<li><b>실행 예</b> — 자주 쓰는 명령은 표본 저장소(main·topic, 태그 v1, 커밋 넷)에서 한 번 돌린 캡처.</li>
<li><b>이 덱에서 돌린 곳</b> — 다른 부의 캡처 가운데 그 명령을 부른 부.</li>
</ul>
<span class="tier ill">설명용</span>
</article>

<article class="card" id="p17-cats">
<h3>분류별 개수</h3>
<!--TABLE file=out/tbl_cmdref.html cap=이 기계에서 -h 를 돌린 결과 — 없는 명령은 없다고 적었다-->
<span class="tier a">실행 검증</span>
</article>
''' % len(cmds))
RANGES = [('a', 'c'), ('d', 'f'), ('g', 'l'), ('m', 'p'), ('q', 'r'), ('s', 's'), ('t', 'z')]
def key(r):
    return r[0][4:] if r[0].startswith('git-') else r[0]
cmds.sort(key=key)
nslides = 0
for ci, (lo, hi) in enumerate(RANGES, 1):
    group = [r for r in cmds if lo <= key(r)[0] <= hi]
    w('<article class="card" id="p17-ch%d"><p class="chnum">%d장</p><h2>%s ~ %s</h2><p class="chsub">%d개</p></article>\n'
      % (ci, ci, lo.upper(), hi.upper(), len(group)))
    for r in group:
        name, cat, kind, nl = r[0], r[1], r[2], r[3]
        short = key(r)
        shown = 'git ' + short if name.startswith('git-') else name
        w('<article class="card" id="p17-c-%s">' % short)
        w('<h3><code>%s</code></h3>' % shown)
        w('<p class="lead">%s</p>' % html.escape(ko[name], quote=False))
        w('<p class="cap">원문: %s · 분류: %s</p>' % (html.escape(nl, quote=False), CAT[cat]))
        hc = helpcap.get(short) or helpcap.get(name)
        ex = excap.get(short)
        if hc:
            w('<!--OUT file=%s note=%s-->' % (hc, '사용법 — -h 를 몰라 sync --help 의 앞 여섯 줄' if short == 'p4' else '사용법 — -h 의 앞 여섯 줄'))
        if ex:
            w('<!--OUT file=%s note=표본 저장소에서 한 번-->' % ex)
        parts = sorted(used.get(short, ()))
        if parts:
            w('<p>이 덱에서 돌린 곳: %s부</p>' % '·'.join(str(p) for p in parts))
        if not hc:
            why = ABS.get(name)
            if short in ('sh-i18n', 'sh-setup'):
                w('<p>셸 스크립트가 <code>.</code> 으로 읽어 들이는 라이브러리라 직접 부르지 않습니다.</p>')
            else:
                w('<p>이 덱의 git 에서는 돌릴 수 없습니다%s. 없는 출력은 싣지 않습니다.</p>' % ('(%s)' % why if why else ''))
            w('<span class="tier ill">설명용</span>')
        else:
            w('<span class="tier a">실행 검증</span>')
        w('</article>\n')
        nslides += 1
w('<article class="card" id="p17-docs">\n<h3>명령이 아닌 설명서 %d편</h3>' % len(docs))
w('<p>명령 목록에는 개념·형식을 다룬 설명서도 들어 있습니다. <code>git help 이름</code> 으로 읽습니다(예: <code>git help gitrevisions</code>).</p>')
w('<div class="tblwrap"><table class="kv">\n<tr><th>이름</th><th>분류</th><th>내용</th></tr>')
for r in sorted(docs):
    w('<tr><td><code>%s</code></td><td>%s</td><td>%s</td></tr>' % (r[0], CAT[r[1]], html.escape(ko[r[0]], quote=False)))
w('</table></div>\n<span class="tier ill">설명용</span>\n</article>\n')
io.open('deck/sections/17_cmdref.html', 'w', encoding='utf-8', newline='\n').write('\n'.join(o))
print('commands', len(cmds), 'slides', nslides, 'help', len(helpcap), 'ex', len(excap), 'docs', len(docs))
missing = [key(r) for r in cmds if not (helpcap.get(key(r)) or helpcap.get(r[0]))]
print('no -h:', missing)
