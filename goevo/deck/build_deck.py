# -*- coding: utf-8 -*-
"""덱 조립기 — 조각 HTML + 진짜 예제 + 진짜 go 출력 + 공식 문서 인용 → 단일 HTML 덱.

   원칙 하나: 덱 본문에 손으로 쓴 코드도, 손으로 적은 숫자도, 손으로 적은
   go 출력도, 손으로 적은 날짜도 없다. 모든 <pre><code> 는 data-src 로
   goevo/ 의 진짜 파일의 진짜 줄을 가리키고, 모든 캡처는 run_all.py 가
   이 기계의 go 1.27.1 을 돌려 out/ 에 남긴 것이며, 모든 릴리스 날짜는
   data/releases.tsv(공식 릴리스 페이지에서 만든 표)에서 오고, 모든 역사
   인용은 문서 키와 절 제목을 배지로 달고 나온다. verify_deck.py 가 덱과
   원본이 어긋나지 않았음을 매번 다시 확인한다.

   지시자 (조각 파일에 쓴다. REL·CITE 는 문장 안에, 나머지는 한 줄에 하나):

     <!--CODE file=ex/07/rangeint/main.go lines=1-30 note=한 줄 설명-->
     <!--CODE file=ex/07/rangeint/main.go sym=main note=main 함수-->
     <!--OUT  file=07-rangeint__go1.22.txt note=돌린 결과-->
     <!--GOVER v=1.21 file=ex/07/rangeint note=go.mod 를 1.21 로 내리면-->
     <!--GOVER godebug=asynctimerchan=1 file=ex/08/timer cmd="go run ."-->
     <!--FIG  file=cadence.svg cap=여섯 달마다 한 번-->
     <!--TABLE file=out/tbl_rel_1.22.html cap=Go 1.22 한눈에-->
     <!--CITE key=relnotes-1.22 sec="Changes to the language"-->
     <!--REL v=1.22-->   (그 버전이 나온 날짜로 바뀐다 — 날짜를 손으로 안 쓴다)
     <!--FULLSRC lang=go file=… prefix=… title=…-->
     <!--GLOSSARY-->  <!--QUIZINDEX-->  <!--SRCSTAT …-->

   GOVER 는 실행 지시자가 아니다. 조립기는 명령을 돌리지 않는다 — 돌리는
   것은 run_all.py 하나뿐이다(PLAN.md §1). GOVER 는 OUT 의 별칭으로,
   goverslug() 규칙의 out/<예제>__<변형>.txt 를 찾아 싣고, go.mod 의 go 줄과
   명령 줄을 캡처 위에 붙인다. 캡처 첫 줄('$ 명령')이 지시자와 글자까지
   같아야 한다 — 화면의 버전·명령과 캡처가 떨어질 수 없다.

   git/deck/build_deck.py 에서 그대로 물려받아 이 덱에 맞춘 것이다
   (PLAN.md §1). 바꾼 곳은 — 대상 파일 이름, 다루는 언어(Go 와 go.mod),
   커버리지를 세는 디렉터리(ex/), 상한 1000장과 부 예산 +10 % 오류,
   CITE 가 찾는 표(deck/cites.py — releases.tsv·cite_keys.tsv), 지시자 GIT 을
   빼고 GOVER·REL 을 더한 것. 나머지 규칙(폭 검사·근거 등급·커버리지)은
   손대지 않았다 — Keycloak·압축·무선·트랜스포머·Git 덱에서 실제로 결함을
   잡아 낸 검사들이다.
"""
import html
import io
import os
import re
import sys
import unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))    # goevo
DECK = os.path.join(BASE, 'deck')
OUTDIR = os.path.join(BASE, 'out')
TARGET = os.path.join(os.path.dirname(BASE), 'Go의_진화.html')

sys.path.insert(0, DECK)
import chunks                                                  # noqa: E402
import cites                                                   # noqa: E402
import gen_glossary                                            # noqa: E402

# 이 덱이 싣는 코드는 Go 하나다(PLAN.md §1). go.mod 는 '언어 버전' 을
# 보여 주는 증거라 따로 이름을 붙인다(강조 규칙은 없어 글자 그대로 나온다).
# 파이썬·셸은 도구를 인용할 때만, 자바스크립트는 데모뿐이다.
LANG_OF = {'.go': 'go', '.mod': 'mod', '.work': 'mod', '.sh': 'sh',
           '.py': 'py', '.js': 'js', '.json': 'json', '.tsv': 'text',
           '.txt': 'text', '.md': 'text', '.mk': 'make'}

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
    with io.open(p, encoding='utf-8') as f:
        return f.read()


def esc(s):
    return html.escape(s, quote=False)


def src_lines(path):
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
    elif ext in ('.c', '.h', '.hpp', '.cpp', '.cc', '.java', '.ts', '.mts'):
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
    elif ext in ('.c', '.h', '.hpp', '.cpp', '.cc', '.java', '.ts', '.go'):
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
GOVER_RE = re.compile(r'^<!--GOVER (?P<args>.+?)-->$', re.M)
REL_RE = re.compile(r'<!--REL (?P<args>.+?)-->')
FIG_RE = re.compile(r'^<!--FIG (?P<args>.+?)-->$', re.M)
TABLE_RE = re.compile(r'^<!--TABLE (?P<args>.+?)-->$', re.M)
CITE_RE = re.compile(r'<!--CITE (?P<args>.+?)-->')
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
    """k=값 하나. 값에 공백이 있으면 큰따옴표로 감싼다(cmd="go vet ./...").

       문서 절 제목("Changes to the language")과 go 명령 줄은 공백을 품는다.
       따옴표 안에는 큰따옴표를 쓸 수 없다 — 그런 명령은 작은따옴표로 쓴다.
    """
    m = re.search(r'\b%s=(?:"([^"]*)"|(\S+))' % k, args)
    if not m:
        return None
    return m.group(1) if m.group(1) is not None else m.group(2)


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
    if not os.path.exists(os.path.join(BASE, path)):
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
    return ('%s<pre><code data-lang="%s" data-src="%s" data-lines="%d-%d">%s</code></pre>'
            % (label, lang, path, a, b, esc(body)))


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
    label = ''
    if note:
        label = ('<div class="src"><b>out/%s</b><span class="ln">%s</span>'
                 '<span>%s</span></div>\n' % (esc(name), span, esc(note)))
    return ('%s<pre class="term" data-out="%s"%s>%s</pre>'
            % (label, esc(name), attrs, esc(text)))


def _slug(s):
    """소문자로, 영숫자·점·밑줄이 아닌 것은 '-' 하나로."""
    return re.sub(r'[^a-z0-9._]+', '-', s.lower()).strip('-')


def goverslug(file, v=None, godebug=None, exp=None, tag=None):
    """예제 디렉터리 + 변형 → 캡처 파일 이름(확장자 뺀 것). run_all.py 도 이것을 쓴다.

       ex/07/rangeint, v=1.22            → 07-rangeint__go1.22
       ex/07/timer, godebug=x=1          → 07-timer__godebug-x-1
       ex/08/x, v=1.27, exp=a, tag=vet   → 08-x__go1.27-exp-a-vet

       변형은 go.mod 의 언어 버전 · GODEBUG · GOEXPERIMENT · 꼬리표 차례로
       잇는다(PLAN.md §3.3). 하나도 없으면 무엇을 증명하는 캡처인지 이름만
       보고 알 수 없으므로 거절한다. 같은 예제·변형에 명령이 둘이면 tag 로
       가른다. 겹치는 이름은 run_all.py 가 기록할 때 멈춘다.
    """
    if not file or not file.startswith('ex/'):
        raise ValueError('GOVER file= 는 ex/ 아래 예제 디렉터리다: %r' % file)
    parts = []
    if v:
        parts.append('go' + v)
    if godebug:
        parts.append('godebug-' + _slug(godebug))
    if exp:
        parts.append('exp-' + _slug(exp))
    if tag:
        parts.append(_slug(tag))
    if not parts:
        raise ValueError('GOVER 에 변형(v=·godebug=·exp=·tag=)이 없다: %r' % file)
    return '%s__%s' % (_slug(file[3:].rstrip('/')), '-'.join(parts))


def gover_cmdline(cmd, godebug=None, exp=None):
    """캡처 첫 줄에 적힐 명령 — 환경 변수 앞머리까지 보여야 증거가 된다."""
    pre = ''
    if godebug:
        pre += 'GODEBUG=%s ' % godebug
    if exp:
        pre += 'GOEXPERIMENT=%s ' % exp
    return pre + cmd


def expand_gover(m):
    """<!--GOVER v=1.22 file=ex/07/rangeint [cmd="go run ."] note=…--> — OUT 의 별칭.

       캡처 첫 줄은 run_all.py(tools/gover.py)가 적은 '$ 명령' 이다. 그 줄이
       이 지시자로 만든 명령 줄과 글자까지 같아야 싣는다. v= 가 있으면
       go.mod 의 'go 1.N' 줄을 캡처 위 이름표에 적는다 — 옛 Go 를 돌릴 수
       없는 이 기계에서 '전과 후' 의 차이는 바로 그 한 줄이다(PLAN.md §0.6).
    """
    args = m.group('args')
    file, v = field(args, 'file'), field(args, 'v')
    godebug, exp = field(args, 'godebug'), field(args, 'exp')
    cmd = field(args, 'cmd') or 'go run .'
    try:
        name = goverslug(file, v=v, godebug=godebug, exp=exp,
                         tag=field(args, 'tag')) + '.txt'
    except ValueError as e:
        errors.append(str(e))
        return ''
    p = os.path.join(OUTDIR, name)
    if not os.path.exists(p):
        errors.append('캡처 없음: out/%s (run_all.py 에 %s 실험을 먼저)'
                      % (name, file))
        return ''
    want = '$ ' + gover_cmdline(cmd, godebug, exp)
    first = read(p).split('\n', 1)[0]
    if first != want:
        errors.append('out/%s 의 첫 줄 %r 이 지시자 명령 %r 과 다르다'
                      % (name, first, want))
    note = tail_field(args, 'note')
    head = '%s · go %s' % (file, v) if v else file
    label = ('<div class="src"><b>%s</b><span>%s</span></div>\n'
             % (esc(head), esc(note)))
    rest = ''.join(' %s=%s' % (k, field(args, k))
                   for k in ('lines', 'sec') if field(args, k))
    return label + expand_outdir(re.match(r'(?P<args>.*)', 'file=%s%s'
                                          % (name, rest)))


_REL = {}


def expand_rel(m):
    """<!--REL v=1.22--> → 그 버전이 나온 날(YYYY-MM-DD). 출처는 releases.tsv 하나.

       릴리스 페이지의 표기는 버전마다 다르다 — Go 1 은 'go1', 1.20 까지는
       'go1.20', 1.21 부터는 'go1.21.0'. 그래서 go<v> 와 go<v>.0 을 둘 다
       찾고, 1.0 은 go1 로 읽는다. 없으면 오류다. 날짜를 손으로 쓸 길을
       막는 것이 이 지시자의 요점이다(PLAN.md §3.4).
    """
    v = field(m.group('args'), 'v') or ''
    if not _REL:
        for row in _tsv_rows('releases.tsv'):
            if row.get('version') and row.get('date'):
                _REL[row['version']] = row['date']
    for cand in (['go1'] if v in ('1', '1.0') else []) + ['go' + v, 'go%s.0' % v]:
        if cand in _REL:
            return ('<span class="rel" data-rel="%s">%s</span>'
                    % (esc(v), esc(_REL[cand])))
    errors.append('REL v=%s — data/releases.tsv 에 그 버전이 없다' % v)
    return ''


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


_DOCS = {}
_CITE_USED = []


def _tsv_rows(name):
    """data/<name> 의 줄들을 {칸 이름: 값} 으로. 칸 차례는 첫 줄에서 읽는다."""
    p = os.path.join(BASE, 'data', name)
    if not os.path.exists(p):
        return []
    head, rows = None, []
    for line in read(p).split('\n'):
        if not line.strip() or line.startswith('#'):
            continue
        cols = [c.strip() for c in line.split('\t')]
        if head is None:
            head = cols
            continue
        rows.append(dict(zip(head, cols)))
    return rows


def docs_index():
    """인용할 수 있는 공식 문서 → 배지에 적을 이름 (deck/cites.py).

    <!--CITE--> 가 가리키는 키가 여기 없으면 오류다. 기억으로 적은
    "1.22 노트 어디쯤" 은 반드시 어딘가 틀린다 — 표에 올린 문서만 인용할
    수 있게 막는다. 키는 releases.tsv 의 큰 릴리스(relnotes-1.N, api-1.N)와
    cite_keys.tsv(spec, godebug, blog-… 등)에서 온다.
    """
    if not _DOCS:
        for k, ent in cites.index(BASE).items():
            _DOCS[k] = ent['name']
    return _DOCS


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


def expand_cite(m):
    """<!--CITE key=relnotes-1.22 sec="Changes to the language"-->

    이 덱이 가장 쉽게 틀릴 자리가 "몇 버전에 들어왔나" 다. 그래서 두 겹으로
    막는다. 여기서는 키가 표에 있는지 보고, make claims-check 가 그 절
    제목(API 목록이면 그 줄)이 진짜 받아 둔 문서 본문에 있는지 본다.
    """
    args = m.group('args')
    key = field(args, 'key')
    sec = field(args, 'sec') or ''
    if not key:
        errors.append('CITE 지시자에 key= 가 없다: %s' % args)
        return ''
    name = docs_index().get(key)
    if name is None:
        errors.append('data/releases.tsv·cite_keys.tsv 에 없는 문서 키: %s '
                      '(표에 먼저 넣을 것)' % key)
        name = key
    _CITE_USED.append((key, sec))
    tail = '<span class="cl">§%s</span>' % esc(sec) if sec else ''
    return ('<span class="cite" data-cite="%s" data-sec="%s">%s %s</span>'
            % (esc(key), esc(sec), esc(name), tail))


def write_cite_used():
    """이 덱이 실제로 인용한 (문서, 절) 목록을 남긴다 — claims-check 가 읽는다."""
    p = os.path.join(DECK, 'cite_used.txt')
    rows = sorted(set(_CITE_USED))
    io.open(p, 'w', encoding='utf-8', newline='\n').write(
        '# 조립기가 만든다 — 손으로 고치지 말 것.\n'
        '# 키\t절\n'
        + ''.join('%s\t%s\n' % r for r in rows))


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
            rows.append('<tr><td>%s</td><td>%s</td></tr>'
                        % (part_label(part), links))
        slides.append('<article class="card" id="p11-quiz-index-%d">\n'
                      '<h3>퀴즈 찾아보기 %d</h3>\n<div class="tblwrap">'
                      '<table class="kv">\n<tr><th>부</th><th>퀴즈</th></tr>\n'
                      '%s\n</table></div>\n<span class="tier ill">설명용</span>'
                      '\n</article>' % (k // 8 + 1, k // 8 + 1,
                                         '\n'.join(rows)))
    return '\n\n'.join(slides)


APPENDIX = 11     # 부록은 조각 11번이다(PLAN.md §4 의 A 줄)


def part_label(n):
    """조각 번호 → 사람이 읽는 이름. 11 은 '부록' 이다."""
    return '부록' if n == APPENDIX else '%d부' % n


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
    text = GOVER_RE.sub(expand_gover, text)
    text = FIG_RE.sub(expand_fig, text)
    text = TABLE_RE.sub(expand_table, text)
    text = CITE_RE.sub(expand_cite, text)
    text = REL_RE.sub(expand_rel, text)
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
COVER_DIRS = [('ex', ('.go',)),
              ('exps', ('.py',)),
              ('tools', ('.py', '.sh'))]
COVER_FILES = ['Makefile', 'run_all.py']
# 부분 인용만 하는 것들 — 빠진 줄이 있어도 오류가 아니다.
#
# 이 덱이 가르치는 것은 Go 의 역사지 이 저장소의 빌드 장치가 아니다
# (PLAN.md §0.13). 그래서 전부 실어야 하는 것은 ex/ 의 예제뿐이고,
# 실험 모듈(exps/)·도구(tools/·deck/)·Makefile·run_all.py 는 필요한 줄만
# 인용한다. 시험 파일(_test.go)은 발췌한다. data/*.tsv 는 <!--TABLE--> 로
# 실리고, docs/ 는 받아 둔 캐시, out/ 은 캡처라 여기 둔다.
PARTIAL = re.compile(r'_test\.(py|go)$|/tests?/|^tools/|^deck/|^exps/'
                     r'|^Makefile$|^run_all\.py$'
                     r'|^out/|^data/|^docs/|^scratch/')


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
# 2026-09-24 에 사용자가 1000 으로 못 박았다(PLAN.md 머리말). 목표 띠는
# 820~960 이고, 부마다 예산(budget.txt)의 10 % 를 넘으면 오류다(PLAN.md §4) —
# 한 부가 넘치면 뒤의 부가 상한에 눌리기 때문이다.
HARD_CAP = 1000
BUDGET_SLACK = 0.10


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
            term = 'class="term"' in pm.group(1)
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


def tier_report(doc):
    """근거 등급이 빠진 화면과 C 등급 비율을 센다 (PLAN.md §5 10단계 계약).

    등급은 넷이다. a 돌려 봤다 · b 도구로 문법만 봤다 · c 문서에서 읽었다 ·
    ill 설명하려고 그린 조각(돌아가는 코드가 아니다). 배지가 아예 없는 화면은
    "확인했는지 안 했는지 모르겠다" 는 뜻이라, 그 자체가 결함이다.
    """
    total = c = none = ill = 0
    for m in ART_RE.finditer(doc):
        attrs, aid, inner = m.group(1) + m.group(3), m.group(2), m.group(4)
        # 배지는 장의 **마지막** tier 태그다. 앞쪽에 나오는 것은 등급표를
        # 설명하는 장(howto-tier)처럼 본문이 배지를 예시로 그린 것이라,
        # 첫 번째를 집으면 그 장의 등급을 잘못 읽는다.
        found = re.findall(r'<span class="tier (a|b|c|ill)\b', inner)
        t = found[-1] if found else None

        # **거꾸로도 본다** — a(실행 검증)는 "이 화면의 숫자가 돌려서
        # 나왔다" 는 뜻이다. 그런데 1차 전수 리뷰에서 코드도 출력도 그림도
        # 없는 장 열 개가 a 를 달고 있었다. 배지는 얻는 것이지 붙이는 것이
        # 아니므로, 근거가 화면에 없으면 여기서 막는다.
        # 퀴즈는 뺀다 — 답이 앞 장의 표를 인용하는 꼴이라 화면에 증거가
        # 없는 것이 정상이다. 대신 퀴즈의 등급은 사람이 정독으로 본다.
        if t == 'a' and 'quiz' not in attrs:
            proof = ('<pre' in inner or 'data-demo=' in inner
                     or 'data-table=' in inner
                     or '<svg class="diag"' in inner)
            if not proof:
                errors.append('%s: 실행 검증 배지인데 화면에 코드·출력·'
                              '그림·자동 생성 표가 없다' % aid)

        if '<pre' not in inner:
            continue
        total += 1
        if not t:
            none += 1
            errors.append('%s: 코드·출력이 있는데 근거 등급 배지가 없다' % aid)
        elif t == 'c':
            c += 1
        elif t == 'ill':
            ill += 1
    return total, c, none, ill


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
    write_cite_used()
    io.open(TARGET, 'w', encoding='utf-8', newline='\n').write(doc)

    n_slides = len(ART_RE.findall(body))
    print('슬라이드 %d장 · 고유 id %d개 · %.0f KB → %s'
          % (n_slides, len(seen), os.path.getsize(TARGET) / 1024,
             os.path.basename(TARGET)))

    want = budget()
    got = budget_report(body)
    if want:
        done = sorted(got)
        line = ' · '.join('%s %d/%d' % (part_label(k), got[k], want.get(k, 0))
                          for k in done if got[k] > 1)
        left = sum(v for k, v in want.items() if k not in got or got[k] <= 1)
        print('장수 예산: %s' % (line or '(아직 없음)'))
        print('  쓴 것 %d장 · 남은 부 목표 합 %d장 · 예상 합계 %d장 (상한 %d)'
              % (n_slides, left, n_slides + left, HARD_CAP))
        for k in done:
            if got[k] > 1 and got[k] > want.get(k, 0) * (1 + BUDGET_SLACK):
                errors.append('%s가 예산 +10%%를 넘었다 (%d/%d)'
                              % (part_label(k), got[k], want.get(k, 0)))
            elif got[k] > 1 and got[k] > want.get(k, 0):
                warns.append('%s가 목표보다 %d장 많다 (%d/%d)'
                             % (part_label(k), got[k] - want.get(k, 0),
                                got[k], want.get(k, 0)))
    if n_slides > HARD_CAP:
        errors.append('슬라이드 %d장 — 상한 %d장을 넘었다' % (n_slides, HARD_CAP))
    tot, tc, tnone, till = tier_report(doc)
    if tot:
        # C 등급 비율은 '검증할 수 있었던 것' 중에서 센다 — 설명용 그림은
        # 애초에 검증 대상이 아니므로 분모에서 뺀다.
        base = max(1, tot - till)
        print('근거 등급: 코드·출력 %d장 (설명용 %d장 제외 %d장 중 '
              'C등급 %d장 = %.0f%%) · 배지 없음 %d장'
              % (tot, till, base, tc, 100.0 * tc / base, tnone))
        if 100.0 * tc / base > 10.0:
            warns.append('C등급이 %.0f%% — 10%% 아래로 두기로 했다'
                         % (100.0 * tc / base))

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

