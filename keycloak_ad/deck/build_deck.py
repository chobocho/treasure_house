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

   rts/deck/build_deck.py 에서 물려받았다. 다른 점 셋:
     · 화면 캡처(PNG)가 없다 — 이 덱의 증거는 텍스트 출력과 SVG 도해다
     · 근거 등급 배지(A/B/C) 를 화면마다 세어 비율을 보고한다
     · 폴더블 폭 검사(<pre> 72칸)를 조립 때 같이 한다
"""
import html
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))    # keycloak_ad
DECK = os.path.join(BASE, 'deck')
OUTDIR = os.path.join(BASE, 'out')
TARGET = os.path.join(os.path.dirname(BASE), 'Keycloak_AD_연동_쉽게_배우기.html')

sys.path.insert(0, DECK)
import chunks                                                  # noqa: E402

LANG_OF = {'.go': 'go', '.yaml': 'yaml', '.yml': 'yaml', '.json': 'json',
           '.sh': 'sh', '.py': 'py', '.ldif': 'ldif', '.mod': 'go',
           '.txt': 'text', '.md': 'text', '.conf': 'text', '.crt': 'text'}

# 한 <pre> 가 넘으면 안 되는 선. 줄 수는 폴더블 접힘(374px)에서 한 화면,
# 칸 수는 가로 스크롤이 생기지 않는 폭이다. 둘 다 실제로 재서 정한 값이다.
MAX_PRE_LINES = 45
MAX_PRE_COLS = 72
MAX_LI = 14

# 박스 그리기 문자는 쓰지 않는다 — 폰·태블릿에서 글꼴이 갈리면 표가 무너진다.
# (DeckMono 를 실어도 <pre> 밖의 산문에는 적용되지 않는 자리가 있다.)
BOXDRAW = re.compile(r'[─-╿▀-▟]')

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
    covered.setdefault(path, set()).update(range(a, b + 1))
    return '\n'.join(lines[a - 1:b])


# ---------------------------------------------------------------- 지시자 확장
CODEDIR_RE = re.compile(r'^<!--CODE (?P<args>.+?)-->$', re.M)
OUTDIR_RE = re.compile(r'^<!--OUT (?P<args>.+?)-->$', re.M)
FIG_RE = re.compile(r'^<!--FIG (?P<args>.+?)-->$', re.M)
FULL_RE = re.compile(r'^<!--FULLSRC (?P<args>[^>]+)-->$', re.M)
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
        out.append(
            '<article class="card" id="%s-%d">\n'
            '<h3>%s <span class="badge">%d/%d</span></h3>\n'
            '<div class="src"><b>%s</b><span class="ln">%d–%d</span>'
            '<span>%s</span></div>\n'
            '<pre><code data-lang="%s" data-src="%s" data-lines="%d-%d">%s</code></pre>\n'
            '</article>'
            % (prefix, k + 1, esc(title), k + 1, len(parts), esc(path), a, b,
               esc(label), lang, path, a, b, esc(cut(path, '%d-%d' % (a, b)))))
    return '\n\n'.join(out)


def expand(text):
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
COVER_DIRS = [('web', ('.go',)), ('ldap', ('.go',)), ('oidc', ('.go',)),
              ('k8s', ('.yaml',)), ('keycloak', ('.json', '.sh')),
              ('certs', ('.sh',)), ('data', ('.ldif',))]
COVER_FILES = ['Makefile', 'go.mod']
# 부분 인용만 하는 것들 — 빠진 줄이 있어도 오류가 아니다
# 시험 코드는 부분 인용만 한다 — 전문을 실으면 덱이 시험 코드로 가득 찬다
PARTIAL = re.compile(r'_test\.go$|/check_\w+\.sh$|^tools/|^deck/|^bin/|^kc/|^out/')


def cover_files():
    out = list(COVER_FILES)
    for d, exts in COVER_DIRS:
        full = os.path.join(BASE, d)
        for root, dirs, names in os.walk(full):
            dirs[:] = [x for x in dirs if not x.startswith(('.', '__'))]
            for name in sorted(names):
                if name.endswith(exts):
                    rel = os.path.relpath(os.path.join(root, name), BASE)
                    out.append(rel.replace(os.sep, '/'))
    return sorted(set(x for x in out if os.path.exists(os.path.join(BASE, x))))


def coverage_report():
    files = sorted(set(covered) | set(cover_files()))
    rows, have_t, all_t = [], 0, 0
    for f in files:
        if not os.path.exists(os.path.join(BASE, f)):
            continue
        n = len(src_lines(f))
        got = covered.get(f, set()) & set(range(1, n + 1))
        partial = bool(PARTIAL.search(f))
        if not partial:
            have_t += len(got)
            all_t += n
        rows.append((f, len(got), n, sorted(set(range(1, n + 1)) - got), partial))
    return rows, have_t, all_t


def overflow_check(doc):
    """폴더블에서 잘리는 화면을 조립 때 잡는다. 사람 눈보다 자가 정확하다."""
    for m in ART_RE.finditer(doc):
        aid, inner = m.group(2), m.group(4)
        for pm in re.finditer(r'<pre[^>]*>(.*?)</pre>', inner, re.S):
            body = html.unescape(re.sub(r'<[^>]+>', '', pm.group(1)))
            rows = body.split('\n')
            if len(rows) > MAX_PRE_LINES:
                errors.append('%s: <pre> 가 %d줄 (최대 %d)' % (aid, len(rows), MAX_PRE_LINES))
            wide = max((len(r) for r in rows), default=0)
            if wide > MAX_PRE_COLS:
                errors.append('%s: <pre> 가 %d칸 (최대 %d)' % (aid, wide, MAX_PRE_COLS))
        li = inner.count('<li>')
        if li > MAX_LI:
            errors.append('%s: <li> 가 %d개 (최대 %d)' % (aid, li, MAX_LI))
        box = BOXDRAW.search(re.sub(r'<[^>]+>', '', inner))
        if box:
            errors.append('%s: 박스 그리기 문자 %r — 표는 <table> 로' % (aid, box.group()))


def tier_report(doc):
    """근거 등급이 빠진 화면과 C 등급 비율을 센다 (§2.2 계약)."""
    total = c = none = 0
    for m in ART_RE.finditer(doc):
        inner = m.group(4)
        if '<pre' not in inner:
            continue
        total += 1
        t = re.search(r'<span class="tier (a|b|c)\b', inner)
        if not t:
            none += 1
        elif t.group(1) == 'c':
            c += 1
    return total, c, none


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
    tot, tc, tnone = tier_report(doc)
    if tot:
        print('근거 등급: 코드·출력이 있는 %d장 중 C등급 %d장 (%.0f%%) · 배지 없음 %d장'
              % (tot, tc, 100.0 * tc / tot, tnone))

    rows, have, all_ = coverage_report()
    print('소스 커버리지 %d/%d줄 (%.1f%%)' % (have, all_, 100.0 * have / max(1, all_)))
    for f, h, n, missing, partial in rows:
        if h != n and not partial:
            print('  %-34s %5d/%-5d  빠진 줄: %s'
                  % (f, h, n, ','.join(str(x) for x in missing[:14])
                     + (' …' if len(missing) > 14 else '')))
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
