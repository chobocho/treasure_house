# -*- coding: utf-8 -*-
"""덱 조립기 — 조각 HTML + 소스 파일 + 실행 출력 + 화면 캡처를 하나로 붙인다.

   원칙 하나: 덱 본문에 손으로 쓴 코드는 없다.
   모든 <pre><code> 는 data-src 로 진짜 파일의 진짜 줄을 가리키고, 여기서
   그 내용을 읽어 채운다. 그래서 소스를 고치면 덱이 자동으로 따라오고,
   verify_deck.py 가 둘이 어긋나지 않았음을 매번 다시 확인한다.

   사용법:  python3 deck/build_deck.py
"""
import base64
import html
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK = os.path.join(BASE, 'deck')
OUTDIR = os.path.join(BASE, 'out')
TARGET = os.path.join(os.path.dirname(BASE), '도스_RTS_전략게임_수학_해부.html')

sys.path.insert(0, DECK)
import chunks                                                  # noqa: E402

LANG_OF = {'.py': 'py', '.lua': 'lua', '.ts': 'ts', '.sh': 'sh', '.json': 'json'}

# 커버리지 집계: {파일: set(줄번호)}
covered = {}
errors = []


def read(p):
    return io.open(p, encoding='utf-8').read()


def esc(s):
    return html.escape(s, quote=False)


def src_lines(path):
    text = read(os.path.join(BASE, path))
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    return lines


def find_symbol(path, sym):
    """이름으로 함수/클래스/상수의 줄 범위를 찾는다 — 줄 번호를 손으로 세지 않기 위해서다.

       소스를 고치면 줄 번호가 전부 밀린다. 손으로 적어 두면 그때마다 덱이 조용히
       엉뚱한 코드를 보여 준다. 이름으로 가리키면 그 사고가 아예 생기지 않는다.
    """
    lines = src_lines(path)
    ext = os.path.splitext(path)[1]

    # "클래스.메서드" 는 클래스 범위 안에서만 찾는다 — __init__ 같은 이름이
    # 파일에 여럿 있어도 엉뚱한 것을 집지 않는다.
    lo, hi = 0, len(lines)
    if '.' in sym and ext in ('.py', '.ts'):
        cls, sym = sym.split('.', 1)
        ca, cb = find_symbol(path, cls)
        lo, hi = ca - 1, cb

    starts = []
    # 이름 뒤에 식별자 글자가 이어지면 다른 이름이다 — TERRAIN 을 찾다가
    # TERRAIN_MASK 를 집는 사고를 막는다.
    esc_sym = re.escape(sym)
    if ext == '.py':
        pat = re.compile(r'^(?:def|class)\s+%s\b|^%s\s*(?:[,:]|=)' % (esc_sym, esc_sym))
    elif ext == '.lua':
        pat = re.compile(r'^(?:local\s+)?function\s+%s\s*\(|^(?:local\s+)?%s\s*='
                         % (esc_sym, esc_sym))
    else:
        pat = re.compile(r'^(?:export\s+)?(?:function|class|interface|type|const|let|abstract)'
                         r'\s+%s\b|^(?:private|public|protected|get|set)?\s*%s\s*\('
                         % (esc_sym, esc_sym))
    for i in range(lo, hi):
        if pat.match(lines[i].strip()):
            starts.append(i)
    if not starts:
        errors.append('%s: 이름 %r 을 못 찾음' % (path, sym))
        return (1, 1)
    a = starts[0]
    indent = len(lines[a]) - len(lines[a].lstrip())

    # 바로 위의 주석·데코레이터도 함께 가져온다 — 설명이 코드와 붙어 있어야 한다
    top = a
    while top > 0:
        prev = lines[top - 1]
        st = prev.strip()
        if st.startswith('#') or st.startswith('--') or st.startswith('//') or st.startswith('@'):
            top -= 1
        else:
            break

    b = a
    if ext == '.lua':
        # 루아에는 중괄호가 없다. 대신 관례를 믿는다 — 함수를 닫는 end 는
        # function 과 같은 열에 있다. 키워드를 세는 것보다 훨씬 덜 틀린다.
        st0 = lines[a].strip()
        if not st0.startswith(('function', 'local function')):
            b = a
            while b + 1 < len(lines) and lines[b].rstrip().endswith((',', '{', '(')):
                b += 1
        else:
            b = len(lines) - 1
            pad = ' ' * indent
            for i in range(a + 1, len(lines)):
                if lines[i] == pad + 'end' or lines[i].rstrip() == pad + 'end':
                    b = i
                    break
    elif ext == '.py':
        b = len(lines) - 1
        header = lines[a].strip()
        if not (header.startswith('def ') or header.startswith('class ')):
            b = a                       # 상수 대입은 한 줄
            while b + 1 < len(lines) and lines[b].rstrip().endswith((',', '(', '[', '{')):
                b += 1
        else:
            for i in range(a + 1, len(lines)):
                ln = lines[i]
                if ln.strip() and (len(ln) - len(ln.lstrip())) <= indent:
                    b = i - 1
                    break
                b = i
    else:
        # 타입스크립트: 함수·클래스·인터페이스는 중괄호를 세고, 나머지는 세미콜론까지.
        head = lines[a].strip()
        blockish = any(head.startswith(k) for k in (
            'export function', 'function', 'export class', 'class',
            'export interface', 'interface', 'export abstract', 'constructor',
            'private ', 'public ', 'protected ', 'get ', 'set ')) or (
            head.endswith('{') or head.endswith('(') or head.endswith(','))
        if not blockish:
            b = a
            while b < len(lines) - 1 and not lines[b].rstrip().endswith(';'):
                b += 1
        else:
            depth = 0
            opened = False
            b = a
            for i in range(a, len(lines)):
                depth += lines[i].count('{') - lines[i].count('}')
                if '{' in lines[i]:
                    opened = True
                b = i
                if opened and depth <= 0:
                    break
                if not opened and lines[i].rstrip().endswith(';'):
                    break
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
CODE_RE = re.compile(
    r'<pre><code data-lang="(?P<lang>[a-z]+)" data-src="(?P<src>[^"]+)"'
    r'(?: data-lines="(?P<lines>[\d-]+)")?(?: data-sym="(?P<sym>[^"]+)")?></code></pre>')
TERM_RE = re.compile(r'<pre class="term" data-out="(?P<out>[^"]+)"'
                     r'(?: data-lines="(?P<lines>[\d-]+)")?></pre>')
SHOT_RE = re.compile(r'<img class="shot" data-shot="(?P<shot>[^"]+)"(?P<rest>[^>]*)>')
SVG_RE = re.compile(r'<div class="fig" data-svg="(?P<svg>[^"]+)"></div>')
FULL_RE = re.compile(r'^<!--FULLSRC (?P<args>[^>]+)-->$', re.M)
# <!--CODE file=... (sym=... | lines=A-B) note=자유 문장--> 한 줄이
# '파일·줄번호 라벨 + 코드 블록' 으로 펼쳐진다. 줄 번호를 손으로 쓰지 않기 위한 장치.
CODEDIR_RE = re.compile(r'^<!--CODE (?P<args>.+?)-->$', re.M)
# <!--OUT file=... [lines=A-B] [note=...]--> 실행 출력 블록. 라벨의 줄 번호도 자동.
OUTDIR_RE = re.compile(r'^<!--OUT (?P<args>.+?)-->$', re.M)


def expand_code(m):
    spec = m.group('lines')
    if m.group('sym'):
        name = m.group('sym')
        if '..' in name:            # "첫 이름..끝 이름" — 여러 함수를 한 덩어리로
            n1, n2 = name.split('..')
            a = find_symbol(m.group('src'), n1)[0]
            b = find_symbol(m.group('src'), n2)[1]
        else:
            a, b = find_symbol(m.group('src'), name)
        spec = '%d-%d' % (a, b)
    body = cut(m.group('src'), spec)
    attrs = ' data-lines="%s"' % spec if spec else ''
    return ('<pre><code data-lang="%s" data-src="%s"%s>%s</code></pre>'
            % (m.group('lang'), m.group('src'), attrs, esc(body)))


def expand_codedir(m):
    args = m.group('args')
    def field(k):
        mm = re.search(r'\b%s=(\S+)' % k, args)
        return mm.group(1) if mm else None
    path = field('file')
    if not path:
        errors.append('CODE 지시자에 file 이 없다: %s' % args)
        return ''
    note = re.search(r'\bnote=(.+)$', args)
    note = note.group(1).strip() if note else ''
    lang = field('lang') or LANG_OF.get(os.path.splitext(path)[1], 'text')
    if field('sym'):
        name = field('sym')
        if '..' in name:
            n1, n2 = name.split('..')
            a = find_symbol(path, n1)[0]
            b = find_symbol(path, n2)[1]
        else:
            a, b = find_symbol(path, name)
    elif field('lines'):
        a, b = (int(x) for x in field('lines').split('-'))
    else:
        a, b = 1, len(src_lines(path))
    body = cut(path, '%d-%d' % (a, b))
    # note 를 주지 않으면 라벨을 붙이지 않는다 — 3단 비교처럼 이미 제목이 있는 자리용
    label = ''
    if note:
        label = ('<div class="src"><b>%s</b><span class="ln">%d–%d</span>'
                 '<span>%s</span></div>\n' % (esc(path), a, b, esc(note)))
    return ('%s<pre><code data-lang="%s" data-src="%s" data-lines="%d-%d">%s</code></pre>'
            % (label, lang, path, a, b, esc(body)))


def expand_outdir(m):
    args = m.group('args')
    mm = re.search(r'\bfile=(\S+)', args)
    if not mm:
        errors.append('OUT 지시자에 file 이 없다: %s' % args)
        return ''
    name = mm.group(1)
    ln = re.search(r'\blines=([\d-]+)', args)
    sec = re.search(r'\bsec=(\d+)', args)
    note = re.search(r'\bnote=(.+)$', args)
    note = note.group(1).strip() if note else ''
    p = os.path.join(OUTDIR, name)
    if not os.path.exists(p):
        errors.append('출력 파일 없음: out/%s' % name)
        return ''
    text = read(p).rstrip('\n')
    total = len(text.split('\n'))
    if sec:
        # '== N. 제목 ==' 로 시작하는 절 하나를 통째로. 파일이 늘어나도 안 밀린다.
        rows = text.split('\n')
        a = b = None
        for i, row in enumerate(rows):
            if row.startswith('== %s.' % sec.group(1)):
                a = i + 1
            elif a is not None and row.startswith('== '):
                b = i
                break
        if a is None:
            errors.append('out/%s 에 %s번 절이 없다' % (name, sec.group(1)))
            return ''
        b = b or len(rows)
        while b > a and not rows[b - 1].strip():
            b -= 1
        ln = None
        text = '\n'.join(rows[a - 1:b])
        attrs = ' data-lines="%d-%d"' % (a, b)
        span = '%d–%d' % (a, b)
    elif ln:
        a, b = (int(x) for x in ln.group(1).split('-'))
        text = '\n'.join(text.split('\n')[a - 1:b])
        attrs = ' data-lines="%d-%d"' % (a, b)
        span = '%d–%d' % (a, b)
    else:
        attrs = ''
        span = '전체 %d줄' % total
    label = ''
    if note:
        label = ('<div class="src"><b>out/%s</b><span class="ln">%s</span>'
                 '<span>%s</span></div>\n' % (esc(name), span, esc(note)))
    return ('%s<pre class="term" data-out="%s"%s>%s</pre>'
            % (label, esc(name), attrs, esc(text)))


def expand_term(m):
    p = os.path.join(OUTDIR, m.group('out'))
    if not os.path.exists(p):
        errors.append('출력 파일 없음: out/%s' % m.group('out'))
        return '<pre class="term">(없음)</pre>'
    text = read(p).rstrip('\n')
    if m.group('lines'):
        a, b = (int(x) for x in m.group('lines').split('-'))
        text = '\n'.join(text.split('\n')[a - 1:b])
    attrs = ' data-lines="%s"' % m.group('lines') if m.group('lines') else ''
    return ('<pre class="term" data-out="%s"%s>%s</pre>'
            % (m.group('out'), attrs, esc(text)))


def expand_shot(m):
    p = os.path.join(OUTDIR, m.group('shot'))
    if not os.path.exists(p):
        errors.append('캡처 파일 없음: out/%s' % m.group('shot'))
        return ''
    b64 = base64.b64encode(io.open(p, 'rb').read()).decode('ascii')
    return ('<img class="shot" data-shot="%s"%s src="data:image/png;base64,%s">'
            % (m.group('shot'), m.group('rest'), b64))


def expand_fullsrc(m):
    """<!--FULLSRC lang=py file=... prefix=... title=...--> 를 슬라이드 여러 장으로."""
    args = dict(re.findall(r'(\w+)=(\S+)', m.group('args')))
    path = args['file']
    lang = args.get('lang') or LANG_OF.get(os.path.splitext(path)[1], 'py')
    prefix = args['prefix']
    title = args.get('title', os.path.basename(path)).replace('_', ' ')
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


def expand_svg(m):
    p = os.path.join(DECK, 'figs', m.group('svg'))
    if not os.path.exists(p):
        errors.append('도해 파일 없음: deck/figs/%s' % m.group('svg'))
        return ''
    return read(p).strip()


def expand(text):
    text = FULL_RE.sub(expand_fullsrc, text)
    text = CODEDIR_RE.sub(expand_codedir, text)
    text = OUTDIR_RE.sub(expand_outdir, text)
    text = CODE_RE.sub(expand_code, text)
    text = TERM_RE.sub(expand_term, text)
    text = SHOT_RE.sub(expand_shot, text)
    text = SVG_RE.sub(expand_svg, text)
    return text


# --------------------------------------------------------------------- 조립
ART_RE = re.compile(r'<article([^>]*)id="([^"]+)"([^>]*)>(.*?)</article>', re.S)


def build_nav(body):
    opts = ['    <option value="top">챕터 이동…</option>']
    for m in ART_RE.finditer(body):
        cls = m.group(1) + m.group(3)
        aid, inner = m.group(2), m.group(4)
        if 'section' in cls and 'cover' not in cls:
            num = re.search(r'<p class="chnum">([^<]+)</p>', inner)
            h = re.search(r'<h2>(.*?)</h2>', inner, re.S)
            if h:
                opts.append('    <option value="%s">%s · %s</option>'
                            % (aid, esc(re.sub('<[^>]+>', '', num.group(1))) if num else '',
                               esc(re.sub('<[^>]+>', '', h.group(1)))))
        elif re.search(r'<p class="chnum">\d+장</p>', inner):
            h = re.search(r'<h2>(.*?)</h2>', inner, re.S)
            if h:
                opts.append('    <option value="%s">· %s</option>'
                            % (aid, esc(re.sub('<[^>]+>', '', h.group(1)))))
    return '\n'.join(opts)


def coverage_report():
    files = sorted(covered)
    rows = []
    total_have = total_all = 0
    for f in files:
        n = len(src_lines(f))
        have = len(covered[f] & set(range(1, n + 1)))
        total_have += have
        total_all += n
        missing = sorted(set(range(1, n + 1)) - covered[f])
        rows.append((f, have, n, missing))
    return rows, total_have, total_all


def main():
    order = [l.strip() for l in read(os.path.join(DECK, 'order.txt')).split('\n')
             if l.strip() and not l.strip().startswith('#')]
    body_parts = []
    for fn in order:
        p = os.path.join(DECK, 'sections', fn)
        if not os.path.exists(p):
            errors.append('조각 없음: %s' % fn)
            continue
        body_parts.append('<!-- ===== %s ===== -->\n%s' % (fn, expand(read(p)).rstrip()))
    body = '\n\n'.join(body_parts)

    ids = ART_RE.findall(body)
    seen, dup = set(), []
    for _a, aid, _b, _c in ids:
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
    # 엔진 번들이 먼저다 — 데모가 window.__isorpg 를 쓴다.
    for name in ('engine.js', 'demos.js'):
        p = os.path.join(DECK, name)
        if os.path.exists(p):
            tail = tail.replace(
                '</body>', '<script>\n%s\n</script>\n</body>' % read(p).rstrip())

    doc = head.rstrip('\n') + '\n\n<main class="prose">\n\n' + body + '\n\n' + tail
    io.open(TARGET, 'w', encoding='utf-8').write(doc)

    rows, have, all_ = coverage_report()
    print('슬라이드 %d장 · 고유 id %d개 · %.0f KB'
          % (len(ids), len(seen), os.path.getsize(TARGET) / 1024))
    print('소스 커버리지 %d/%d줄 (%.1f%%)' % (have, all_, 100.0 * have / max(1, all_)))
    for f, h, n, missing in rows:
        if h != n:
            print('  %-28s %4d/%-4d  빠진 줄: %s' % (f, h, n, missing[:14]))
    if errors:
        print('\n오류 %d건' % len(errors))
        for e in errors[:20]:
            print('  ' + e)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
