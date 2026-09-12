# -*- coding: utf-8 -*-
"""덱 조립기 — 조각 HTML + 진짜 소스 파일 + 진짜 실행 출력 → 단일 HTML 덱.

   원칙 하나: 덱 본문에 손으로 쓴 코드는 없다.
   모든 <pre><code> 는 data-src 로 keycloak_ad/ 의 진짜 파일의 진짜 줄을 가리키고,
   여기서 그 내용을 읽어 채운다. 그래서 소스를 고치면 덱이 따라오고,
   verify_deck.py 가 둘이 어긋나지 않았음을 매번 다시 확인한다.

   지시자 (조각 파일에 한 줄로 쓴다):

     <!--CODE file=web/01_hello/main.go lines=1-30 note=한 줄 설명-->
     <!--CODE file=oidc/jwt/jwt.go sym=Verify note=서명 검증-->
     <!--OUT  file=kc_e2e_03.txt lines=1-20 note=토큰 응답-->
     <!--FIG  file=system_part4.svg cap=4부까지 켜진 그림-->
     <!--FULLSRC lang=go file=ldap/ber/ber.go prefix=src-ber title=ber.go-->
     <!--GLOSSARY-->   (deck/glossary.txt 를 용어집 슬라이드로 펼친다)

   keycloak_ad/deck/build_deck.py 에서 그대로 물려받아 이 덱에 맞춘 것뿐이다.
   바꾼 곳은 넷 — 대상 파일 이름, 다루는 언어(다섯 언어 + 헤더), 장수 상한 3000,
   커버리지를 세는 디렉터리(src/ cli/ bench/ interop/ corpus/ tools/).
   나머지 규칙(폭 검사·근거 등급·커버리지·예산)은 손대지 않았다 —
   Keycloak 덱에서 실제로 결함을 잡아 낸 검사들이라 그대로 쓰는 편이 낫다.
"""
import html
import io
import os
import re
import sys
import unicodedata

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))    # compress
DECK = os.path.join(BASE, 'deck')
OUTDIR = os.path.join(BASE, 'out')
TARGET = os.path.join(os.path.dirname(BASE), '압축_대백과사전.html')

sys.path.insert(0, DECK)
import chunks                                                  # noqa: E402
import gen_glossary                                            # noqa: E402

# 이 덱은 한 알고리즘을 다섯 언어로 쓴다. 확장자 표가 곧 그 목록이다.
LANG_OF = {'.py': 'py', '.go': 'go', '.mod': 'go',
           '.cpp': 'cpp', '.cc': 'cpp', '.h': 'cpp', '.hpp': 'cpp',
           '.java': 'java', '.ts': 'ts', '.mts': 'ts', '.mjs': 'js', '.js': 'js',
           '.sh': 'sh', '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml',
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
    return io.open(p, encoding='utf-8').read()


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
        pat = re.compile(r'^(?:def|class)\s+%s\b|^%s\s*(?:[,:]|=)' % (e, e))
    elif ext == '.sh':
        pat = re.compile(r'^%s\s*\(\)|^%s=' % (e, e))
    elif ext in ('.yaml', '.yml'):
        pat = re.compile(r'^\s*(?:name|kind):\s*%s\s*$' % e)
    elif ext == '.ldif':
        pat = re.compile(r'^dn:\s*.*\b%s\b' % e)
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
    if head.endswith('{') or head.endswith('('):
        opener, closer = ('{', '}') if head.endswith('{') else ('(', ')')
        depth = 0
        for i in range(a, len(lines)):
            depth += lines[i].count(opener) - lines[i].count(closer)
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
FULL_RE = re.compile(r'^<!--FULLSRC (?P<args>[^>]+)-->$', re.M)
GLOSS_RE = re.compile(r'^<!--GLOSSARY-->$', re.M)
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


def expand_fig(m):
    """deck/figs/*.svg 를 그대로 인라인한다. 외부 이미지를 쓰지 않는다는 계약."""
    args = m.group('args')
    name = field(args, 'file')
    p = os.path.join(DECK, 'figs', name or '')
    if not name or not os.path.exists(p):
        errors.append('도해 파일 없음: deck/figs/%s' % name)
        return ''
    svg = read(p).strip()
    cap = tail_field(args, 'cap')
    if cap:
        return '%s\n<p class="cap">%s</p>' % (svg, esc(cap))
    return svg


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


def expand(text):
    text = GLOSS_RE.sub(expand_glossary, text)
    text = FULL_RE.sub(expand_fullsrc, text)
    text = CODEDIR_RE.sub(expand_codedir, text)
    text = OUTDIR_RE.sub(expand_outdir, text)
    text = FIG_RE.sub(expand_fig, text)
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
COVER_DIRS = [('src', ('.py', '.go', '.cpp', '.h', '.hpp', '.java', '.ts')),
              ('cli', ('.py', '.go', '.cpp', '.java', '.ts')),
              ('corpus', ('.py',)), ('bench', ('.py',)), ('interop', ('.py', '.sh'))]
COVER_FILES = ['Makefile']
# 부분 인용만 하는 것들 — 빠진 줄이 있어도 오류가 아니다
#
# 시험 코드는 부분 인용만 한다 — 전문을 실으면 덱이 시험 코드로 가득 찬다.
# realm-campus.json 도 여기 든다. 그 파일은 **사람이 쓴 소스가 아니라
# Keycloak 이 뽑아 준 3,200줄짜리 내보내기**라, 전문을 실으면 덱이 80장쯤
# JSON 낭독이 된다. 우리가 정한 칸들은 keycloak/json/*.json 에 따로 있고
# 그쪽은 전문이 실린다 — 배울 것은 거기 다 있다.
# 부분 인용만 하는 것들 — 빠진 줄이 있어도 오류가 아니다.
#
# 시험 코드는 발췌만 싣는다. 다섯 언어 × 17모듈의 시험을 전문으로 실으면
# 덱의 절반이 시험 코드가 된다. 도구(tools/·deck/)와 캡처(out/)도 같다 —
# 덱이 가르치는 대상은 압축 알고리즘이지 이 저장소의 빌드 장치가 아니다.
PARTIAL = re.compile(r'_test\.go$|_test\.py$|Tests?\.java$|\.test\.ts$'
                     r'|/tests/|^tools/|^deck/|^out/|^golden/|^scratch/'
                     r'|/node_modules/')


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
# 2026-09-12 에 사용자가 3000 으로 못 박았다(PLAN.md §9). 목표 띠는 2,200~2,600 이고,
# 2,900 에 닿으면 본문을 조이되 부록(다섯 언어 전문)과 증거는 건드리지 않는다.
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
        aid, inner = m.group(2), m.group(4)
        if '<pre' not in inner:
            continue
        total += 1
        t = re.search(r'<span class="tier (a|b|c|ill)\b', inner)
        if not t:
            none += 1
            errors.append('%s: 코드·출력이 있는데 근거 등급 배지가 없다' % aid)
        elif t.group(1) == 'c':
            c += 1
        elif t.group(1) == 'ill':
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
