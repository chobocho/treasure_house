# -*- coding: utf-8 -*-
"""덱 조립기 — 조각 HTML + 진짜 소스 + 진짜 캡처 + 핀 고정 upstream 소스 → 단일 HTML 덱.

   원칙 하나: 덱 본문에 손으로 쓴 코드도, 손으로 적은 숫자도, 손으로 옮긴
   캡처도 없다. 모든 <pre><code> 는 data-src 로 termux/ 의 진짜 파일이나
   sources/ 의 핀 고정 커밋의 진짜 줄을 가리키고, 모든 캡처는 out/ 에서,
   모든 표는 data/*.tsv 나 out/ 에서 온다. 소스를 고치면 덱이 따라오고,
   verify_deck.py 가 둘이 어긋나지 않았음을 매번 다시 확인한다.

   지시자 (조각 파일에 한 줄로 쓴다):

     <!--CODE file=py/elf.py sym=read_dynamic note=한 줄 설명-->
     <!--CODE file=sources/termux-exec/src/exec/exec.c sha=… lines=1-30 note=…-->
     <!--OUT  file=env_termux.txt sec=2 note=Termux 쪽 환경 변수-->
     <!--FIG  file=sandbox.svg cap=앱마다 uid 가 하나-->
     <!--TABLE file=out/tbl_releases.html cap=termux-app 릴리스-->
     <!--SRC repo=termux-exec path=src/exec/exec.c sha=… lines=A-B-->
     <!--FULLSRC lang=py file=py/elf.py prefix=src-elf title=elf.py-->
     <!--GLOSSARY-->   (deck/glossary.txt 를 용어집 슬라이드로 펼친다)

   transformer/deck/build_deck.py 에서 그대로 물려받아 이 덱에 맞춘 것이다
   (PLAN.md §1). 바꾼 곳은 — 대상 파일 이름, 다루는 언어(sh·py·C99 에
   upstream 의 Java·Kotlin·XML 을 더했다), 커버리지를 세는 디렉터리,
   상한 3000장, 근거 등급(a·s·b·c·ill), 그리고 지시자 둘.
   논문 배지 CITE 는 소스 배지 SRC 가 되었고(저장소·커밋·경로·줄),
   CODE 는 sources/ 의 파일을 핀 커밋에서 읽는다(deck/srcpin.py).
   OUT 은 out/manifest.json 을 보고 어느 쪽(Termux/proot)에서 떴는지와
   스냅샷 날짜를 화면에 붙인다(PLAN.md §0.9).
   나머지 규칙(폭 검사·커버리지·예산)은 손대지 않았다 —
   Keycloak·압축·무선·트랜스포머 덱에서 실제로 결함을 잡아 낸 검사들이다.
"""
import html
import io
import json
import os
import re
import sys
import unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))    # termux
DECK = os.path.join(BASE, 'deck')
OUTDIR = os.path.join(BASE, 'out')
TARGET = os.path.join(os.path.dirname(BASE), 'Termux_대백과사전.html')

sys.path.insert(0, DECK)
import chunks                                                  # noqa: E402
import gen_glossary                                            # noqa: E402
import srcpin                                                  # noqa: E402

PINS = srcpin.Pins(BASE)

# 우리 코드는 셸·파이썬·C99 다(PLAN.md §1). upstream 인용에는 앱의
# Java·Kotlin·XML 과 termux-packages 의 셸·패치가 더해진다.
# 코틀린은 하이라이터에 따로 없어 Java 규칙으로 칠한다 — 키워드가 겹친다.
LANG_OF = {'.py': 'py', '.c': 'c', '.h': 'c', '.js': 'js', '.mjs': 'js',
           '.sh': 'sh', '.json': 'json', '.tsv': 'text',
           '.txt': 'text', '.md': 'text', '.mk': 'make',
           '.java': 'java', '.kt': 'java', '.kts': 'java',
           '.gradle': 'java', '.xml': 'xml', '.properties': 'sh',
           '.diff': 'text', '.patch': 'text'}

# 한 <pre> 가 넘으면 안 되는 선. 줄 수는 폴더블 접힘(374px)에서 한 화면,
# 칸 수는 가로 스크롤이 생기지 않는 폭이다. 둘 다 실제로 재서 정한 값이다.
MAX_PRE_LINES = 45
MAX_PRE_COLS = 72
# 진짜로 돌려서 받은 출력(<pre class="term">)은 우리가 다시 접을 수 없다.
# curl 의 Set-Cookie 한 줄이 106칸인 것은 curl 사정이지 우리 사정이 아니고,
# 그 줄을 잘라 내거나 고쳐 실으면 "출력은 진짜다" 라는 약속이 깨진다.
# 그래서 캡처만 상한을 늘리고(블록 안에서 가로로 스크롤된다), 그보다 긴 줄은
# 인용 범위에서 빼도록 여전히 오류로 잡는다.
MAX_TERM_COLS = 108
MAX_LI = 14

# 박스 그리기 문자는 <pre> 밖에서 쓰지 않는다. 내장 글꼴(DeckMono)은 고정폭
# 요소에만 걸리므로, 산문에 그린 표는 보는 기기의 글꼴에 따라 무너진다.
# <pre> 안(코드 주석의 ── 구분선 같은 것)은 DeckMono 가 반각으로 그려 안전하다.
BOXDRAW = re.compile(r'[\u2500-\u257f\u2580-\u259f]')
PRE_RE = re.compile(r'<pre[^>]*>.*?</pre>', re.S)

covered = {}
errors = []
warns = []


def read(p):
    return io.open(p, encoding='utf-8').read()


def esc(s):
    return html.escape(s, quote=False)


def src_lines(path):
    # sources/ 는 작업 트리가 아니라 data/repos.tsv 의 핀 커밋에서 읽는다
    if srcpin.split(path):
        got = PINS.lines(path)
        if got is None:
            errors.append('%s: 핀 커밋에 그 파일이 없다 (make sources?)'
                          % path)
            return ['']
        return list(got)
    lines = read(os.path.join(BASE, path)).split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    return lines


def find_symbol(path, sym):
    """이름으로 함수·타입·상수의 줄 범위를 찾는다 — 줄 번호를 손으로 세지 않기 위해서다.

       소스를 고치면 줄 번호가 전부 밀린다. 손으로 적어 두면 그때마다 덱이
       조용히 엉뚱한 코드를 보여 준다. 이름으로 가리키면 그 사고가 안 생긴다.
       Go 는 중괄호가 열에 맞춰 닫히므로 '같은 열의 }' 를 찾으면 끝이다. O(파일 줄 수).
    """
    lines = src_lines(path)
    ext = os.path.splitext(path)[1]
    e = re.escape(sym)

    if ext == '.go':
        pat = re.compile(r'^func\s+(?:\([^)]*\)\s*)?%s\b|^(?:type|var|const)\s+%s\b' % (e, e))
    elif ext == '.py':
        # 메서드는 들여쓰기 안에 있다 — 열 0 만 보면 못 찾는다.
        pat = re.compile(r'^\s*(?:def|class)\s+%s\b|^%s\s*(?:[,:]|=)'
                         % (e, e))
    elif ext == '.sh':
        pat = re.compile(r'^%s\s*\(\)|^%s=' % (e, e))
    elif ext in ('.yaml', '.yml'):
        pat = re.compile(r'^\s*(?:name|kind):\s*%s\s*$' % e)
    elif ext == '.ldif':
        pat = re.compile(r'^dn:\s*.*\b%s\b' % e)
    elif ext in ('.c', '.h', '.hpp', '.cpp', '.cc', '.java', '.kt', '.ts',
                 '.mts'):
        # 클래스·구조체·함수·메서드를 한 판에 잡는다. 이름 앞에는 공백이나
        # * 가 온다(C 의 `float *tfs_tensor(`). 이름 뒤에 여는
        # 괄호가 오거나(함수), 선언 낱말이 앞에 오거나(형) 둘 중 하나다.
        pat = re.compile(
            r'^\s*(?:(?:export|public|private|protected|static|final|'
            r'inline|template|abstract|constexpr)\s+)*'
            r'(?:class|struct|interface|enum|namespace|function)\s+%s\b'
            r'|^\s*(?:[\w:<>,&*\[\]\s]+[\s*])?%s\s*\(' % (e, e))
    else:
        pat = re.compile(r'^\s*"%s"\s*:' % e)

    starts = [i for i, ln in enumerate(lines) if pat.match(ln)]
    if not starts:
        errors.append('%s: 이름 %r 을 못 찾음' % (path, sym))
        return (1, 1)
    a = starts[0]

    # 바로 위에 붙은 주석도 함께 가져온다 — 설명이 코드에서 떨어지면 안 된다
    top = a
    while top > 0:
        st = lines[top - 1].strip()
        if st.startswith('//') or st.startswith('#') or st.startswith('--'):
            top -= 1
        else:
            break

    b = a
    head = lines[a].rstrip()
    if ext == '.py':
        # 파이썬은 들여쓰기가 몸통이다. 중괄호 규칙을 쓰면 def 줄
        # 하나만 잘려 나온다 — 실제로 그렇게 한 장이 나왔다가 잡혔다.
        indent = len(lines[a]) - len(lines[a].lstrip())
        b = len(lines) - 1
        for i in range(a + 1, len(lines)):
            ln = lines[i]
            if ln.strip() and (len(ln) - len(ln.lstrip())) <= indent:
                b = i - 1
                break
            b = i
    elif head.endswith('{') or head.endswith('('):
        opener, closer = ('{', '}') if head.endswith('{') else ('(', ')')
        depth = 0
        for i in range(a, len(lines)):
            depth += lines[i].count(opener) - lines[i].count(closer)
            b = i
            if depth <= 0:
                break
    elif ext in ('.c', '.h', '.hpp', '.cpp', '.cc', '.java', '.kt', '.ts',
                 '.go'):
        # 여러 줄로 접힌 서명 — 72칸 규칙 때문에 이 덱에는 흔하다.
        # 몸통을 여는 { 를 먼저 찾고 거기서부터 짝을 맞춘다.
        opened = None
        for i in range(a, min(a + 8, len(lines))):
            if '{' in lines[i]:
                opened = i
                break
        if opened is None:
            b = a
        else:
            depth = 0
            for i in range(opened, len(lines)):
                depth += lines[i].count('{') - lines[i].count('}')
                b = i
                if depth <= 0:
                    break
    elif ext in ('.yaml', '.yml', '.json', '.ldif'):
        # 들여쓰기가 구조다 — 같은 깊이 이상으로 돌아오는 줄 직전까지
        indent = len(lines[a]) - len(lines[a].lstrip())
        b = len(lines) - 1
        for i in range(a + 1, len(lines)):
            ln = lines[i]
            if ln.strip() and (len(ln) - len(ln.lstrip())) <= indent:
                b = i - 1
                break
            b = i
    while b > a and not lines[b].strip():
        b -= 1
    return (top + 1, b + 1)


def cut(path, spec):
    lines = src_lines(path)
    if spec:
        a, b = (int(x) for x in spec.split('-'))
    else:
        a, b = 1, len(lines)
    if b > len(lines):
        errors.append('%s: %s 는 파일 끝(%d줄)을 넘는다' % (path, spec, len(lines)))
        b = len(lines)
    cov = covered.setdefault(path, {})
    for i in range(a, b + 1):
        cov[i] = cov.get(i, 0) + 1
    return '\n'.join(lines[a - 1:b])


# ---------------------------------------------------------------- 지시자 확장
CODEDIR_RE = re.compile(r'^<!--CODE (?P<args>.+?)-->$', re.M)
OUTDIR_RE = re.compile(r'^<!--OUT (?P<args>.+?)-->$', re.M)
FIG_RE = re.compile(r'^<!--FIG (?P<args>.+?)-->$', re.M)
TABLE_RE = re.compile(r'^<!--TABLE (?P<args>.+?)-->$', re.M)
SRC_RE = re.compile(r'<!--SRC (?P<args>.+?)-->')
FULL_RE = re.compile(r'^<!--FULLSRC (?P<args>[^>]+)-->$', re.M)
_FULLSRC_CACHE = []
GLOSS_RE = re.compile(r'^<!--GLOSSARY-->$', re.M)
# 퀴즈 찾아보기 — 조각 파일의 퀴즈를 훑어 부마다 링크를 만든다.
QUIZ_RE = re.compile(r'^<!--QUIZINDEX-->$', re.M)
# 부록 표지의 파일 수·줄 수. 손으로 적으면 소스가 한 줄만 늘어도 어긋난다 —
# 3차 리뷰에서 실제로 그랬다. 세는 일은 조립기가 한다.
SRCSTAT_RE = re.compile(r'<!--SRCSTAT (total-files|total-lines|files)-->')
# 조각 안에 직접 쓴 <pre><code data-lang data-src> 도 채워 준다 (3단 비교처럼 라벨이 이미 있는 자리용)
CODE_RE = re.compile(
    r'<pre><code data-lang="(?P<lang>[a-z]+)" data-src="(?P<src>[^"]+)"'
    r'(?: data-lines="(?P<lines>[\d-]+)")?(?: data-sym="(?P<sym>[^"]+)")?></code></pre>')


def field(args, k):
    m = re.search(r'\b%s=(\S+)' % k, args)
    return m.group(1) if m else None


def tail_field(args, k):
    """note=/cap= 처럼 공백을 품은 자유 문장. 반드시 지시자의 맨 끝에 온다."""
    m = re.search(r'\b%s=(.+)$' % k, args)
    return m.group(1).strip() if m else ''


def resolve_range(path, args):
    if field(args, 'sym'):
        name = field(args, 'sym')
        if '..' in name:                      # "첫 이름..끝 이름" — 여러 정의를 한 덩어리로
            n1, n2 = name.split('..')
            return find_symbol(path, n1)[0], find_symbol(path, n2)[1]
        return find_symbol(path, name)
    if field(args, 'lines'):
        return (int(x) for x in field(args, 'lines').split('-'))
    return 1, len(src_lines(path))


def expand_codedir(m):
    args = m.group('args')
    path = field(args, 'file')
    if not path:
        errors.append('CODE 지시자에 file 이 없다: %s' % args)
        return ''
    sp = srcpin.split(path)
    shattr = ''
    if sp:
        # upstream 인용 — sha= 가 반드시 있어야 하고 핀과 같아야 한다.
        # 없으면 "어느 커밋의 줄인가" 를 독자가 알 길이 없다.
        why = PINS.check(sp[0], field(args, 'sha'))
        if why:
            errors.append('CODE %s: %s' % (path, why))
            return ''
        if not PINS.exists(path):
            errors.append('소스 파일 없음(핀 커밋): %s' % path)
            return ''
        shattr = ' data-sha="%s"' % PINS.sha(sp[0])
    elif not os.path.exists(os.path.join(BASE, path)):
        errors.append('소스 파일 없음: %s' % path)
        return ''
    lang = field(args, 'lang') or LANG_OF.get(os.path.splitext(path)[1], 'text')
    a, b = resolve_range(path, args)
    body = cut(path, '%d-%d' % (a, b))
    note = tail_field(args, 'note')
    label = ''
    if note:
        label = ('<div class="src"><b>%s</b><span class="ln">%d–%d</span>'
                 '<span>%s</span></div>\n' % (esc(path), a, b, esc(note)))
    return ('%s<pre><code data-lang="%s" data-src="%s" data-lines="%d-%d"%s>'
            '%s</code></pre>'
            % (label, lang, path, a, b, shattr, esc(body)))


def expand_code(m):
    spec = m.group('lines')
    src = m.group('src')
    if m.group('sym'):
        a, b = find_symbol(src, m.group('sym'))
        spec = '%d-%d' % (a, b)
    body = cut(src, spec)
    attrs = ' data-lines="%s"' % spec if spec else ''
    return ('<pre><code data-lang="%s" data-src="%s"%s>%s</code></pre>'
            % (m.group('lang'), src, attrs, esc(body)))


def expand_outdir(m):
    """실제로 돌려서 out/ 에 남긴 출력. 커버리지에 세지 않는다 — 증거지 소스가 아니다."""
    args = m.group('args')
    name = field(args, 'file')
    if not name:
        errors.append('OUT 지시자에 file 이 없다: %s' % args)
        return ''
    p = os.path.join(OUTDIR, name)
    if not os.path.exists(p):
        errors.append('출력 파일 없음: out/%s' % name)
        return ''
    text = read(p).rstrip('\n')
    total = len(text.split('\n'))
    ln = field(args, 'lines')
    sec = field(args, 'sec')
    if sec:
        # '== N. 제목 ==' 로 시작하는 절 하나를 통째로. 파일이 늘어나도 안 밀린다.
        rows = text.split('\n')
        a = b = None
        for i, row in enumerate(rows):
            if row.startswith('== %s.' % sec):
                a = i + 1
            elif a is not None and row.startswith('== '):
                b = i
                break
        if a is None:
            errors.append('out/%s 에 %s번 절이 없다' % (name, sec))
            return ''
        b = b or len(rows)
        while b > a and not rows[b - 1].strip():
            b -= 1
        text = '\n'.join(rows[a - 1:b])
        attrs, span = ' data-lines="%d-%d"' % (a, b), '%d–%d' % (a, b)
    elif ln:
        a, b = (int(x) for x in ln.split('-'))
        text = '\n'.join(text.split('\n')[a - 1:b])
        attrs, span = ' data-lines="%d-%d"' % (a, b), '%d–%d' % (a, b)
    else:
        attrs, span = '', '전체 %d줄' % total
    note = tail_field(args, 'note')
    info = capture_info(name)
    side = info.get('side', '')
    tag = ''
    if side in SIDES:
        tag = '<span class="side %s">%s</span>' % (side, SIDES[side])
    label = ''
    if note or tag:
        label = ('<div class="src"><b>out/%s</b><span class="ln">%s</span>'
                 '<span>%s</span>%s</div>\n'
                 % (esc(name), span, esc(note), tag))
    stamp = ''
    if info.get('kind') == 'snapshot':
        # 다시 뜨면 달라지는 값이다. 날짜를 숨기면 독자는 그 숫자를
        # "Termux 의 성질" 로 읽는다(PLAN.md §0.9).
        stamp = ('<p class="stamp" data-snap="%s">이 기기 · %s 캡처</p>\n'
                 % (esc(info.get('date', '')), esc(info.get('date', '')[:7])))
    return ('%s%s<pre class="term" data-out="%s"%s>%s</pre>'
            % (stamp, label, esc(name), attrs, esc(text)))


# 캡처가 뜬 쪽. 프롬프트 기호도 같은 약속이다 — Termux 는 $, proot(uid 0) 는 #
# (PLAN.md §9 결정 12). proot 캡처를 Termux 것처럼 보이게 두지 않는다.
# native 는 사용자가 proot 밖(네이티브 Termux)에서 뜬 것이다 —
# tools/native_facts.sh, run_all.Import.
SIDES = {'termux': 'Termux $', 'proot': 'proot #',
         'both': 'Termux $ · proot #', 'native': '네이티브 Termux $'}
_MANIFEST = []


def capture_info(name):
    """out/manifest.json 의 그 캡처 항목. 매니페스트가 있는데 없으면 오류.

    형식(§5 6단계의 run_all.py 가 쓴다):
      {"env_termux.txt": {"kind": "stable"|"snapshot",
                          "side": "termux"|"proot"|"both",
                          "date": "2026-09-18", ...}, ...}
    매니페스트가 아직 없는 뼈대 단계에서는 빈 항목을 돌려준다.
    """
    if not _MANIFEST:
        p = os.path.join(OUTDIR, 'manifest.json')
        _MANIFEST.append(json.loads(read(p)) if os.path.exists(p) else None)
    man = _MANIFEST[0]
    if man is None:
        return {}
    info = man.get(name)
    if not isinstance(info, dict):
        errors.append('out/%s 가 manifest.json 에 없다 — run_all.py 가 '
                      '만든 캡처만 싣는다' % name)
        return {}
    if info.get('kind') not in ('stable', 'snapshot'):
        errors.append('out/%s: kind 가 stable/snapshot 이 아니다' % name)
    if info.get('side') not in SIDES:
        errors.append('out/%s: side 가 termux/proot/both/native 가 아니다'
                      % name)
    if info.get('kind') == 'snapshot' and not re.match(
            r'\d{4}-\d\d-\d\d$', info.get('date', '')):
        errors.append('out/%s: 스냅샷인데 date 가 없다' % name)
    return info


def expand_fig(m):
    """deck/figs/*.svg 를 그대로 인라인한다. 외부 이미지를 쓰지 않는다는 계약."""
    args = m.group('args')
    name = field(args, 'file')
    p = os.path.join(DECK, 'figs', name or '')
    if not name or not os.path.exists(p):
        errors.append('도해 파일 없음: deck/figs/%s' % name)
        return ''
    svg = read(p).strip()
    # 폴더블 접힘은 374px 이다. viewBox 가 그보다 넓으면 그림이 줄어들어
    # 글자가 못 읽을 크기가 된다 — 그럴 바에는 그림을 둘로 쪼개야 한다.
    vb = re.search(r'viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ', svg)
    if vb and float(vb.group(1)) > 360:
        errors.append('deck/figs/%s: viewBox 폭 %s — 340 으로 그릴 것' % (name, vb.group(1)))
    cap = tail_field(args, 'cap')
    if cap:
        return '%s\n<p class="cap">%s</p>' % (svg, esc(cap))
    return svg


_SRC_USED = []


def expand_table(m):
    """<!--TABLE file=out/xxx.html cap=...--> — 만들어진 표를 그대로 싣는다.

    표의 내용은 deck/gen_tables.py 가 data/*.tsv 와 out/manifest.json 에서
    만든다. 여기서는 그 결과를 끼워 넣기만 한다. 손으로 적은 숫자 표가
    덱에 들어올 길을 아예 막아 두는 것이 요점이다.
    """
    args = m.group('args')
    rel = field(args, 'file')
    if not rel:
        errors.append('TABLE 지시자에 file 이 없다: %s' % args)
        return ''
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        errors.append('표 파일 없음: %s (make tables 먼저)' % rel)
        return ''
    cap = tail_field(args, 'cap')
    body = read(p).strip()
    capline = '\n<p class="cap">%s</p>' % esc(cap) if cap else ''
    return '<div class="gtbl" data-table="%s">\n%s%s\n</div>' % (esc(rel), body, capline)


def expand_src(m):
    """<!--SRC repo=termux-exec path=src/… sha=… lines=A-B--> — 소스 배지.

    "이 설명은 저 저장소, 저 커밋, 저 파일의 저 줄이다" 를 화면에 박는다.
    세 겹으로 막는다. 여기서는 저장소가 data/repos.tsv 에 있고 sha= 가
    핀과 같은지 보고, main() 이 같은 장에 그 파일의 발췌(CODE)나 캡처가
    있는지 보고("보여 주는 것을 인용하라"), make claims-check 가 그 줄이
    그 커밋에 진짜 있는지 본다. 배지 글자는 repo@sha7 · path:A–B 다.
    """
    args = m.group('args')
    repo, path = field(args, 'repo'), field(args, 'path')
    sha, ln = field(args, 'sha'), field(args, 'lines') or ''
    if not repo or not path:
        errors.append('SRC 지시자에 repo=·path= 가 없다: %s' % args)
        return ''
    why = PINS.check(repo, sha)
    if why:
        errors.append('SRC: %s' % why)
        return ''
    _SRC_USED.append((repo, PINS.sha(repo), path, ln))
    where = '%s:%s' % (path, ln.replace('-', '–')) if ln else path
    return ('<span class="srcb" data-repo="%s" data-path="%s" data-sha="%s"'
            ' data-lines="%s">%s@%s <span class="sl">· %s</span></span>'
            % (esc(repo), esc(path), esc(PINS.sha(repo)), esc(ln),
               esc(repo), esc(PINS.sha(repo)[:7]), esc(where)))


def write_src_used():
    """이 덱이 실제로 인용한 (저장소, 커밋, 경로, 줄) — claims-check 가 읽는다."""
    p = os.path.join(DECK, 'src_used.txt')
    rows = sorted(set(_SRC_USED))
    io.open(p, 'w', encoding='utf-8', newline='\n').write(
        '# 조립기가 만든다 — 손으로 고치지 말 것.\n'
        '# 저장소\t커밋\t경로\t줄\n'
        + ''.join('%s\t%s\t%s\t%s\n' % r for r in rows))


def src_shown_check(doc):
    """소스 배지가 붙은 장에 그 파일의 발췌나 캡처가 있는가 (PLAN.md §3.2 c).

    배지만 있고 코드가 없으면 독자는 배지를 믿을 수밖에 없다. 배지는
    "여기 보이는 줄의 출처" 여야지 "어딘가에 있다는 주장" 이면 안 된다.
    """
    for m in ART_RE.finditer(doc):
        aid, inner = m.group(2), m.group(4)
        for b in re.finditer(r'<span class="srcb" data-repo="([^"]+)" '
                             r'data-path="([^"]+)"', inner):
            src = 'data-src="sources/%s/%s"' % (b.group(1), b.group(2))
            if src not in inner and 'class="term"' not in inner:
                errors.append('%s: 소스 배지 %s/%s 인데 그 발췌도 캡처도 '
                              '화면에 없다' % (aid, b.group(1), b.group(2)))


def expand_fullsrc(m):
    """<!--FULLSRC lang=go file=… prefix=… title=…--> 를 슬라이드 여러 장으로 펼친다."""
    args = m.group('args')
    path = field(args, 'file')
    lang = field(args, 'lang') or LANG_OF.get(os.path.splitext(path)[1], 'text')
    prefix = field(args, 'prefix')
    title = (field(args, 'title') or os.path.basename(path)).replace('_', ' ')
    lines = src_lines(path)
    parts = chunks.split('\n'.join(lines), lang)
    out = []
    for k, (a, b) in enumerate(parts):
        label = chunks.label_for(lines, a, b, lang)
        # 전문 인용 슬라이드에도 근거 등급을 붙인다. 이 파일들은 시험이
        # 통과하는 실물이므로 A 다 — 배지를 안 붙이면 조립기가 오류로 잡는다.
        out.append(
            '<article class="card" id="%s-%d">\n'
            '<h3>%s <span class="badge">%d/%d</span></h3>\n'
            '<div class="src"><b>%s</b><span class="ln">%d–%d</span>'
            '<span>%s</span></div>\n'
            '<pre><code data-lang="%s" data-src="%s" data-lines="%d-%d">%s</code></pre>\n'
            '<span class="tier a">실행 검증</span>\n'
            '</article>'
            % (prefix, k + 1, esc(title), k + 1, len(parts), esc(path), a, b,
               esc(label), lang, path, a, b, esc(cut(path, '%d-%d' % (a, b)))))
    return '\n\n'.join(out)


def expand_glossary(m):
    """용어집을 펼친다 — 그리고 낱말이 가리키는 자리가 실재하는지 검사한다.

    용어집은 손으로 적은 목록이라 본문이 바뀌면 조용히 어긋난다. 뜻까지
    기계가 맞출 수는 없지만, "어디를 보라" 는 화살표만은 맞출 수 있다.
    없는 id 를 가리키면 여기서 오류로 잡혀 덱이 안 나온다.
    """
    rows = gen_glossary.entries()
    for line in gen_glossary.check(rows, gen_glossary.slide_ids()):
        errors.append('용어집: %s' % line)
    return gen_glossary.render(rows)


def expand_quizindex(m):
    """<!--QUIZINDEX--> — 모든 퀴즈로 가는 링크를 부마다 한 줄씩.

    손으로 적으면 퀴즈를 하나 더할 때마다 잊는다. 조각 파일에서 id 와
    제목을 읽어 만든다. 한 장에 부 여덟까지 — 접힌 화면에 들게.
    """
    parts = {}
    for name in sorted(os.listdir(os.path.join(DECK, 'sections'))):
        if not name.endswith('.html') or not name[:2].isdigit():
            continue
        text = read(os.path.join(DECK, 'sections', name))
        for qm in re.finditer(r'<article class="card quiz" id="([^"]+)"'
                              r'[^>]*>\s*<h3>(.*?)</h3>', text, re.S):
            parts.setdefault(int(name[:2]), []).append(
                (qm.group(1), re.sub('<[^>]+>', '', qm.group(2))))
    keys = sorted(parts)
    slides = []
    for k in range(0, len(keys), 8):
        rows = []
        for part in keys[k:k + 8]:
            links = ' · '.join('<a href="#%s">%s</a>' % (qid, esc(t))
                               for qid, t in parts[part])
            rows.append('<tr><td>%d부</td><td>%s</td></tr>' % (part, links))
        slides.append('<article class="card" id="p17-quiz-index-%d">\n'
                      '<h3>퀴즈 찾아보기 %d</h3>\n<div class="tblwrap">'
                      '<table class="kv">\n<tr><th>부</th><th>퀴즈</th></tr>\n'
                      '%s\n</table></div>\n<span class="tier ill">설명용</span>'
                      '\n</article>' % (k // 8 + 1, k // 8 + 1,
                                         '\n'.join(rows)))
    return '\n\n'.join(slides)


def all_fullsrc():
    """부록에 전문이 실리는 파일 전부. 조각 파일을 한 번만 훑어 외워 둔다."""
    if not _FULLSRC_CACHE:
        paths = []
        for name in sorted(os.listdir(os.path.join(DECK, 'sections'))):
            if not name.endswith('.html'):
                continue
            text = read(os.path.join(DECK, 'sections', name))
            paths += re.findall(r'^<!--FULLSRC file=(\S+)', text, re.M)
        _FULLSRC_CACHE.extend(paths)
    return _FULLSRC_CACHE


def expand_srcstat(text):
    """<!--SRCSTAT ...--> 를 실제로 센 수로 바꾼다.

    total-files · total-lines 는 부록 전체, files 는 다음 files 표식까지의
    절(節) 하나다. 절 표지 바로 아래에 그 절의 <!--FULLSRC--> 들이 오는
    구조라 이렇게 세면 맞는다. O(조각 파일 크기).
    """
    here = [(m.start(), m.group(1))
            for m in re.finditer(r'^<!--FULLSRC file=(\S+)', text, re.M)]

    def repl(m):
        kind = m.group(1)
        if kind == 'total-files':
            return '%d' % len(all_fullsrc())
        if kind == 'total-lines':
            n = sum(len(src_lines(p)) for p in all_fullsrc())
            return '{:,}'.format(n)
        nxt = text.find('<!--SRCSTAT files-->', m.end())
        end = nxt if nxt >= 0 else len(text)
        n = sum(1 for pos, _p in here if m.end() < pos < end)
        if not n:
            errors.append('SRCSTAT files: 뒤따르는 <!--FULLSRC--> 가 없다')
        return '%d' % n

    return SRCSTAT_RE.sub(repl, text)


def expand(text):
    text = expand_srcstat(text)
    text = GLOSS_RE.sub(expand_glossary, text)
    text = QUIZ_RE.sub(expand_quizindex, text)
    text = FULL_RE.sub(expand_fullsrc, text)
    text = CODEDIR_RE.sub(expand_codedir, text)
    text = OUTDIR_RE.sub(expand_outdir, text)
    text = FIG_RE.sub(expand_fig, text)
    text = TABLE_RE.sub(expand_table, text)
    text = SRC_RE.sub(expand_src, text)
    text = CODE_RE.sub(expand_code, text)
    return text


# --------------------------------------------------------------------- 조립
ART_RE = re.compile(r'<article([^>]*)id="([^"]+)"([^>]*)>(.*?)</article>', re.S)


def build_nav(body):
    """상단 챕터 이동 목록을 부 표지에서 뽑는다 — 손으로 적으면 반드시 어긋난다."""
    opts = ['    <option value="top">챕터 이동…</option>']
    for m in ART_RE.finditer(body):
        cls = m.group(1) + m.group(3)
        aid, inner = m.group(2), m.group(4)
        if 'section' in cls and 'cover' not in cls:
            num = re.search(r'<p class="chnum">([^<]+)</p>', inner)
            h = re.search(r'<h2>(.*?)</h2>', inner, re.S)
            if h:
                opts.append('    <option value="%s">%s · %s</option>'
                            % (aid,
                               esc(re.sub('<[^>]+>', '', num.group(1))) if num else '',
                               esc(re.sub('<[^>]+>', '', h.group(1)))))
        elif re.search(r'<p class="chnum">\d+장</p>', inner):
            h = re.search(r'<h2>(.*?)</h2>', inner, re.S)
            if h:
                opts.append('    <option value="%s">· %s</option>'
                            % (aid, esc(re.sub('<[^>]+>', '', h.group(1)))))
    return '\n'.join(opts)


# 커버리지를 세는 대상. 덱에 한 번도 안 나온 파일은 covered 에 없으므로,
# covered 만 보면 통째로 빠진 모듈이 100 % 로 보인다. 그래서 디렉터리를 직접 훑는다.
COVER_DIRS = [('py', ('.py',)),
              ('exp', ('.c', '.h', '.sh', '.py')),
              ('tools', ('.py', '.sh'))]
COVER_FILES = ['Makefile', 'run_all.py', 'exp/mkdeb/control',
               'exp/mkdeb/postinst', 'exp/mkdeb/treasure-hello']
# 부분 인용만 하는 것들 — 빠진 줄이 있어도 오류가 아니다.
#
# 커버리지 100 % 는 **우리 코드**(tools/·py/·exp/·run_all.py)에만 건다
# (PLAN.md §1). upstream 소스(sources/)는 45줄 이하로 발췌만 하고,
# 시험 코드도 발췌만 싣는다. 조립 장치(deck/)와 캡처(out/)는 이 덱이
# 가르치는 대상이 아니다. data/*.tsv 는 <!--TABLE--> 로 실리므로 여기 둔다.
PARTIAL = re.compile(r'_test\.py$|/tests/|^deck/|^out/|^data/'
                     r'|^sources/|^scratch/')


def budget():
    """부마다 목표한 장수 (PLAN.md §6). 없으면 빈 표."""
    p = os.path.join(DECK, 'budget.txt')
    if not os.path.exists(p):
        return {}
    out = {}
    for line in read(p).split('\n'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        part, n = line.split()
        out[int(part)] = int(n)
    return out


# 사용자가 못 박은 상한. 넘기면 조립을 실패시킨다.
# 2026-09-18 에 사용자가 3000 으로 못 박았다(PLAN.md §9). 목표 띠는 1,800~2,600 이고,
# 2,900 에 닿으면 10·11부의 산문을 조이되 부록과 증거는 건드리지 않는다.
HARD_CAP = 3000


def budget_report(body):
    """조각 파일 이름의 앞 두 자리를 부 번호로 보고 장수를 센다.

    왜 세는가: 한 부를 쓰는 동안에는 그 부만 보이고 전체가 안 보인다.
    1부가 목표보다 24장 많다는 사실을 12부에서 알면 이미 늦다.
    """
    counts = {}
    for chunk in body.split('<!-- ===== '):
        name = chunk.split(' =====')[0]
        if not name[:2].isdigit():
            continue
        counts[int(name[:2])] = chunk.count('<article')
    return counts


def pending_files():
    """아직 그 부(部)를 안 써서 인용되지 않은 파일들.

    비어 있는 것이 목표다. 부가 하나씩 들어올 때마다 여기서 한 줄씩 지운다.
    이 명단이 없으면 아직 안 쓴 부의 소스가 통째로 '빠진 줄' 오류가 되어
    빌드가 늘 빨간불이고, 그러면 진짜 오류를 아무도 안 보게 된다.
    """
    p = os.path.join(DECK, 'pending.txt')
    if not os.path.exists(p):
        return set()
    return set(l.split('#')[0].strip() for l in read(p).split('\n')
               if l.split('#')[0].strip())


def cover_files():
    out = list(COVER_FILES)
    for d, exts in COVER_DIRS:
        full = os.path.join(BASE, d)
        for root, dirs, names in os.walk(full):
            # node_modules 는 남의 코드다. make deps 로 받는 것이라
            # 커버리지에 세면 덱이 영원히 빨간불이 된다.
            dirs[:] = [x for x in dirs
                       if not x.startswith(('.', '__'))
                       and x != 'node_modules']
            for name in sorted(names):
                if name.endswith(exts):
                    rel = os.path.relpath(os.path.join(root, name), BASE)
                    out.append(rel.replace(os.sep, '/'))
    return sorted(set(x for x in out if os.path.exists(os.path.join(BASE, x))))


def coverage_report():
    """파일마다 (빠진 줄, 두 번 이상 실린 줄) 을 센다.

    빠진 줄은 오류다 — "이 저장소의 모든 줄이 덱에 있다" 는 약속이 깨진다.
    두 번 실린 줄은 오류가 아니라 알림이다. 가르치는 글에서는 같은 함수를
    맥락에서 한 번, 전문에서 한 번 보여 주는 편이 낫다. 다만 의도한 것인지
    사람이 볼 수 있어야 하므로 개수를 남긴다.
    """
    files = sorted(set(covered) | set(cover_files()))
    rows, have_t, all_t = [], 0, 0
    for f in files:
        if not os.path.exists(os.path.join(BASE, f)):
            continue
        n = len(src_lines(f))
        cov = covered.get(f, {})
        got = [i for i in range(1, n + 1) if cov.get(i)]
        dup = [i for i in range(1, n + 1) if cov.get(i, 0) > 1]
        partial = bool(PARTIAL.search(f))
        if not partial:
            have_t += len(got)
            all_t += n
        missing = [i for i in range(1, n + 1) if not cov.get(i)]
        rows.append((f, len(got), n, missing, partial, dup))
    return rows, have_t, all_t


def cells(s):
    """화면 칸 수. 한글·CJK 는 두 칸이다.

    글자 수로 세면 안 된다 — 한글 주석 40글자는 80칸이라 폴더블 접힘에서
    가로 스크롤이 생긴다. 고정폭 글꼴의 '한글 = 반각 두 배' 계약이 곧 이 계산이다.
    """
    n = 0
    for ch in s:
        n += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return n


def overflow_check(doc):
    """폴더블에서 잘리는 화면을 조립 때 잡는다. 사람 눈보다 자가 정확하다."""
    for m in ART_RE.finditer(doc):
        aid, inner = m.group(2), m.group(4)
        for pm in re.finditer(r'<pre([^>]*)>(.*?)</pre>', inner, re.S):
            # upstream 소스(sources/)의 발췌도 캡처와 같은 처지다 — 남의
            # 코드를 72칸으로 다시 접으면 "진짜 코드" 가 아니게 된다.
            # 108칸까지 두고(블록 안에서 가로로 민다) 더 긴 줄은 인용
            # 범위에서 빼도록 여전히 오류로 잡는다(PLAN.md 진행 기록 5부).
            upstream = 'data-src="sources/' in pm.group(2)[:300]
            term = 'class="term"' in pm.group(1) or upstream
            body = html.unescape(re.sub(r'<[^>]+>', '', pm.group(2)))
            rows = body.split('\n')
            if len(rows) > MAX_PRE_LINES:
                errors.append('%s: <pre> 가 %d줄 (최대 %d)'
                              % (aid, len(rows), MAX_PRE_LINES))
            limit = MAX_TERM_COLS if term else MAX_PRE_COLS
            wide = max((cells(r.expandtabs(4)) for r in rows), default=0)
            if wide > limit:
                errors.append('%s: %s 가 %d칸 (최대 %d)'
                              % (aid, '캡처' if term else '<pre>', wide, limit))
        li = inner.count('<li>')
        if li > MAX_LI:
            errors.append('%s: <li> 가 %d개 (최대 %d)' % (aid, li, MAX_LI))
        # 박스 그리기는 <pre> 밖에서만 잡는다 (위 BOXDRAW 주석 참고)
        prose = re.sub(r'<[^>]+>', '', PRE_RE.sub('', inner))
        box = BOXDRAW.search(prose)
        if box:
            errors.append('%s: 산문에 박스 그리기 문자 %r — 표는 <table> 로'
                          % (aid, box.group()))


TIERS = ('a', 's', 'b', 'c', 'ill')


def tier_report(doc):
    """근거 등급을 부마다 센다 (PLAN.md §6 "Evidence badges").

    등급은 다섯이다. a 이 기기에서 뜬 캡처 · s upstream 소스 발췌 ·
    b 공식 문서·이슈 · c 역사·뉴스 자료 · ill 설명하려고 그린 것.
    배지가 없는 장은 "어디서 온 말인지 모르겠다" 는 뜻이라 그 자체가
    결함이다. 부 표지·덱 표지·퀴즈만 뺀다 — 앞 장을 되묻는 장이다.

    돌려주는 것: {부 번호: {등급: 장수}}. O(덱 크기).
    """
    per = {}
    part = 0
    for m in ART_RE.finditer(doc):
        attrs, aid, inner = m.group(1) + m.group(3), m.group(2), m.group(4)
        pm = re.match(r'p(\d+)', aid)
        if pm:
            part = int(pm.group(1))
        if 'section' in attrs or 'cover' in attrs or 'quiz' in attrs:
            continue
        # 배지는 장의 **마지막** tier 태그다. 앞쪽에 나오는 것은 등급표를
        # 설명하는 장처럼 본문이 배지를 예시로 그린 것이다.
        found = re.findall(r'<span class="tier (a|s|b|c|ill)\b', inner)
        t = found[-1] if found else None
        if not t:
            errors.append('%s: 근거 등급 배지가 없다' % aid)
            continue
        per.setdefault(part, {}).setdefault(t, 0)
        per[part][t] += 1

        # **거꾸로도 본다** — 배지는 얻는 것이지 붙이는 것이 아니다.
        # a 는 "이 화면의 것이 이 기기에서 떴다" 는 뜻이므로 캡처·생성 표·
        # 그림·데모 중 하나가 화면에 있어야 한다(트랜스포머 덱 1차 리뷰에서
        # 근거 없는 a 가 열 장 나왔다). s 는 소스 배지가 있어야 한다.
        if t == 'a':
            proof = ('class="term"' in inner or 'data-demo=' in inner
                     or 'data-table=' in inner
                     or '<svg class="diag"' in inner)
            if not proof:
                errors.append('%s: 캡처 등급(a)인데 화면에 캡처·생성 표·'
                              '그림·데모가 없다' % aid)
        elif t == 's' and 'class="srcb"' not in inner:
            errors.append('%s: 소스 등급(s)인데 소스 배지(SRC)가 없다' % aid)
    return per


def main():
    order = [l.strip() for l in read(os.path.join(DECK, 'order.txt')).split('\n')
             if l.strip() and not l.strip().startswith('#')]
    parts = []
    for fn in order:
        p = os.path.join(DECK, 'sections', fn)
        if not os.path.exists(p):
            errors.append('조각 없음: %s' % fn)
            continue
        parts.append('<!-- ===== %s ===== -->\n%s' % (fn, expand(read(p)).rstrip()))
    body = '\n\n'.join(parts)

    seen, dup = set(), []
    for _a, aid, _b, _c in ART_RE.findall(body):
        if aid in seen:
            dup.append(aid)
        seen.add(aid)
    if dup:
        errors.append('중복 id: %s' % dup[:10])
    if body.count('<article') != body.count('</article>'):
        errors.append('article 열림/닫힘 불일치 %d/%d'
                      % (body.count('<article'), body.count('</article>')))

    head = read(os.path.join(DECK, 'base', 'head.html')).replace('<!--NAV-->', build_nav(body))
    tail = read(os.path.join(DECK, 'base', 'tail.html'))
    # 이 덱의 데모 함수들. 아직 없으면 자리만 비운다 — 뼈대 단계에서도 덱은 열려야 한다.
    demos = os.path.join(DECK, 'demos.js')
    glue = '<script>\n%s\n</script>' % read(demos).rstrip() if os.path.exists(demos) else ''
    tail = tail.replace('<!--DEMOS-->', glue)

    doc = head.rstrip('\n') + '\n\n<main class="prose">\n\n' + body + '\n\n' + tail
    overflow_check(doc)
    src_shown_check(doc)
    write_src_used()
    io.open(TARGET, 'w', encoding='utf-8', newline='\n').write(doc)

    n_slides = len(ART_RE.findall(body))
    print('슬라이드 %d장 · 고유 id %d개 · %.0f KB → %s'
          % (n_slides, len(seen), os.path.getsize(TARGET) / 1024,
             os.path.basename(TARGET)))

    want = budget()
    got = budget_report(body)
    if want:
        done = sorted(got)
        line = ' · '.join('%d부 %d/%d' % (k, got[k], want.get(k, 0))
                          for k in done if got[k] > 1)
        left = sum(v for k, v in want.items() if k not in got or got[k] <= 1)
        print('장수 예산: %s' % (line or '(아직 없음)'))
        print('  쓴 것 %d장 · 남은 부 목표 합 %d장 · 예상 합계 %d장 (상한 %d)'
              % (n_slides, left, n_slides + left, HARD_CAP))
        for k in done:
            if got[k] > 1 and got[k] > want.get(k, 0):
                warns.append('%d부가 목표보다 %d장 많다 (%d/%d)'
                             % (k, got[k] - want.get(k, 0), got[k], want.get(k, 0)))
    if n_slides > HARD_CAP:
        errors.append('슬라이드 %d장 — 상한 %d장을 넘었다' % (n_slides, HARD_CAP))
    per = tier_report(doc)
    if per:
        tot = {}
        for k in per:
            for t, n in per[k].items():
                tot[t] = tot.get(t, 0) + n
        print('근거 등급: ' + ' · '.join('%s %d장' % (t, tot.get(t, 0))
                                          for t in TIERS))
        # 설명용 그림만 가득한 부는 "원리를 보였다" 가 아니라 "원리를
        # 말했다" 다. 0부(읽는 법)는 덱 자체의 설명이라 뺀다.
        for k in sorted(per):
            n = sum(per[k].values())
            ev = n - per[k].get('ill', 0)
            if k != 0 and n >= 10 and ev < 0.6 * n:
                warns.append('%d부의 근거 등급 a+s+b+c 가 %d/%d (%.0f%%) — '
                             '60%% 아래' % (k, ev, n, 100.0 * ev / n))
    rows, have, all_ = coverage_report()
    print('소스 커버리지 %d/%d줄 (%.1f%%)' % (have, all_, 100.0 * have / max(1, all_)))
    dups = 0
    pending = pending_files()
    for f, h, n, missing, partial, dup in rows:
        dups += len(dup)
        if f in pending:
            if h == n:
                warns.append('%s 는 이제 다 실렸다 — deck/pending.txt 에서 뺄 것'
                             % f)
            continue
        if h != n and not partial:
            errors.append('%s: 덱에 안 실린 줄 %d개 (%s%s)'
                          % (f, len(missing),
                             ','.join(str(x) for x in missing[:10]),
                             ' …' if len(missing) > 10 else ''))
            print('  %-34s %5d/%-5d  빠진 줄: %s'
                  % (f, h, n, ','.join(str(x) for x in missing[:14])
                     + (' …' if len(missing) > 14 else '')))
    if dups:
        print('  (두 번 이상 실린 줄 %d개 — 맥락과 전문에 겹쳐 실은 것)' % dups)
    if pending:
        print('  (아직 그 부를 안 써서 인용 대기 중인 파일 %d개: %s)'
              % (len(pending), ', '.join(sorted(pending)[:4])
                 + (' …' if len(pending) > 4 else '')))
    for w in warns:
        print('  (경고) %s' % w)
    if errors:
        print('\n오류 %d건' % len(errors))
        for e in errors[:25]:
            print('  ' + e)
        return 1
    print('\n오류 0건')
    return 0


if __name__ == '__main__':
    sys.exit(main())
