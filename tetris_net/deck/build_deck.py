# -*- coding: utf-8 -*-
"""build_deck.py — 섹션 조각들 + 실제 소스 파일 → 완성된 단일 HTML 덱.

2편(tetris_ai/deck/build_deck.py)과 같은 보증 두 가지를 그대로 지킨다:
  1) 슬라이드에 실린 코드는 tetris_net/ 의 실제 파일에서 잘라 온 것이다 (재입력 금지)
  2) 각 소스 파일의 모든 줄이 정확히 한 번씩 덱에 실렸는지 커버리지로 검증한다

3편에서 늘어난 것: 소스가 5개 언어(C++·JS·Go·파이썬·Makefile)로 흩어져 있고,
실제로 돌린 출력(logs/)을 그대로 인용하는 <!--RUN--> 지시자가 붙었다.
"""
import io, os, re, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl import highlight

HERE = os.path.dirname(os.path.abspath(__file__))          # tetris_net/deck
SRC  = os.path.dirname(HERE)                               # tetris_net
ROOT = os.path.dirname(SRC)                                # 저장소 루트
BASE = os.path.join(HERE, 'base')
SECD = os.path.join(HERE, 'sections')
OUT  = os.path.join(ROOT, 'C++_WASM_테트리스_8인_온라인.html')

TITLE = '🌐 C++ WASM 테트리스 3편 — 8인 온라인 대전과 두 개의 서버'
DESC  = ('1·2편에서 만든 C++ wasm 테트리스 코어와 유전 알고리즘 AI 위에 '
         '최대 8인(PC 1~8대, 한 PC 에 2명)이 붙는 온라인 대전을 얹는다. '
         'WebSocket(RFC 6455)을 직접 구현한 Go 서버와 파이썬 서버를 같은 프로토콜로 만들고, '
         '골든 벡터로 두 서버 + 브라우저 구현이 완전히 같음을 검증한다. '
         '같은 서버를 gorilla/websocket·websockets 라이브러리판으로도 다시 만들어 맞대어 본다. '
         '모든 코드는 실제로 빌드·실행·테스트했고 전문이 그대로 실려 있다. '
         '이 문서 안에서 8인 AI 대전이 직접 돌아간다.')
BRAND = '<i>🌐 8인 온라인</i> <small class="mut">C++ wasm · Go · 파이썬</small>'

LANGNAME = {'cpp': 'C++', 'js': 'JavaScript', 'go': 'Go', 'py': '파이썬',
            'make': 'Makefile', 'sh': 'shell', 'json': 'JSON', 'txt': '출력', 'md': '문서',
            'html': 'HTML'}
EXTLANG = {'cpp': 'cpp', 'h': 'cpp', 'go': 'go', 'py': 'py', 'js': 'js', 'mjs': 'js',
           'json': 'json', 'md': 'md', 'html': 'html', 'log': 'txt', 'txt': 'txt'}

_files, _cover, _partial = {}, {}, set()

def load(name):
    if name not in _files:
        p = os.path.join(SRC, name)
        _files[name] = io.open(p, encoding='utf-8').read().split('\n')
        _cover[name] = [0] * len(_files[name])
    return _files[name]

def nlines(name):
    lines = load(name)
    n = len(lines)
    if lines and lines[-1] == '':
        n -= 1
    return n

def lang_of(name, a):
    if a.get('lang'):
        return a['lang']
    base = os.path.basename(name)
    if base == 'Makefile':
        return 'make'
    return EXTLANG.get(base.rsplit('.', 1)[-1], 'txt')

def code_block(name, a, b, cap, lang, count=True):
    lines = load(name)
    n = len(lines)
    if lines and lines[-1] == '':
        n -= 1
    a = 1 if a is None else a
    b = n if b is None else b
    assert 1 <= a <= b <= n, '%s: 범위 %d-%d (총 %d줄)' % (name, a, b, n)
    if count:
        for i in range(a - 1, b):
            _cover[name][i] += 1
    body = '\n'.join(lines[a - 1:b]).rstrip('\n')
    meta = '%s · %d줄 (%d–%d)' % (LANGNAME.get(lang, lang), b - a + 1, a, b)
    return ('<div class="codewrap"><div class="codecap">%s<span>%s</span></div>'
            '<pre class="code %s"><code>%s</code></pre></div>'
            % (cap if cap else name, meta, lang, highlight(body, lang)))

# <!--BOARD rows="..|..|.." cap="…"--> → CSS 그리드 보드 도해
BOARD_RE = re.compile(r'<!--BOARD\s+(.*?)-->', re.S)
CLS = {'.': '', '#': 'f', 'o': 'p', 'g': 'g', 'c': 'c', 'x': 'x'}
def board_block(a):
    rows = a['rows'].split('|')
    w = max(len(r) for r in rows)
    cells = []
    for r in rows:
        r = r.ljust(w, '.')
        for ch in r:
            c = CLS.get(ch, '')
            cells.append('<i class="%s"></i>' % c if c else '<i></i>')
    grid = ('<div class="board" style="grid-template-columns:repeat(%d,auto)">%s</div>'
            % (w, ''.join(cells)))
    cap = a.get('cap')
    if cap:
        return ('<figure style="margin:.3em 0;display:inline-block">%s'
                '<figcaption class="small mut" style="text-align:center">%s</figcaption></figure>'
                % (grid, cap))
    return grid

# <!--RUN file=logs/x.log lines=A-B cap="…"--> → 실제로 돌린 출력 그대로.
# 커버리지에 세지 않는다 — 로그는 "소스"가 아니라 "증거"다.
RUN_RE = re.compile(r'<!--RUN\s+(.*?)-->', re.S)
def run_block(a):
    rng = a.get('lines', '')
    lo = hi = None
    if '-' in rng:
        x, y = rng.split('-')
        lo = int(x) if x else None
        hi = int(y) if y else None
    elif rng:
        lo = hi = int(rng)
    name = a['file']
    lines = load(name)
    n = len(lines)
    if lines and lines[-1] == '':
        n -= 1
    lo = 1 if lo is None else lo
    hi = n if hi is None else hi
    _partial.add(name)
    body = '\n'.join(lines[lo - 1:hi]).rstrip('\n')
    import html as _h
    return ('<div class="codewrap"><div class="codecap">%s<span>실제 출력 · %d줄</span></div>'
            '<pre class="code txt"><code>%s</code></pre></div>'
            % (a.get('cap', name), hi - lo + 1, _h.escape(body)))

DIR_RE = re.compile(r'<!--CODE\s+(.*?)-->', re.S)
def parse_attrs(s):
    out = {}
    for m in re.finditer(r'(\w+)=(?:"([^"]*)"|(\S+))', s):
        out[m.group(1)] = m.group(2) if m.group(2) is not None else m.group(3)
    return out

def expand(text):
    def sub(m):
        a = parse_attrs(m.group(1))
        rng = a.get('lines', '')
        if '-' in rng:
            x, y = rng.split('-')
            lo = int(x) if x else None
            hi = int(y) if y else None
        elif rng:
            lo = hi = int(rng)
        else:
            lo = hi = None
        f = a['file']
        if a.get('partial'):
            _partial.add(f)
        return code_block(f, lo, hi, a.get('cap'), lang_of(f, a))
    text = RUN_RE.sub(lambda m: run_block(parse_attrs(m.group(1))), text)
    text = BOARD_RE.sub(lambda m: board_block(parse_attrs(m.group(1))), text)
    return DIR_RE.sub(sub, text)

SLIDE_RE = re.compile(r'<!--SLIDE\s+(.*?)-->', re.S)
def read_sections():
    slides = []
    for fn in sorted(os.listdir(SECD)):
        if not fn.endswith('.html'):
            continue
        raw = io.open(os.path.join(SECD, fn), encoding='utf-8').read()
        parts = SLIDE_RE.split(raw)
        if parts[0].strip():
            raise SystemExit('%s: 첫 <!--SLIDE--> 앞에 내용이 있다' % fn)
        for i in range(1, len(parts), 2):
            a = parse_attrs(parts[i])
            slides.append({'sec': a['sec'], 't': a['t'], 'html': parts[i + 1].strip(), 'src': fn})
    return slides

def build():
    head = io.open(os.path.join(BASE, 'deck_head.html'), encoding='utf-8').read()
    tail = io.open(os.path.join(BASE, 'deck_tail_scripts.html'), encoding='utf-8').read()
    slides = read_sections()
    total = len(slides)

    head = re.sub(r'<title>.*?</title>', '<title>%s (%d장)</title>' % (TITLE, total), head, flags=re.S)
    head = re.sub(r'<meta name="description" content=".*?">',
                  '<meta name="description" content="%s">' % DESC, head, flags=re.S)
    head = head.replace('<div class="brand"><i>🧱 C++ → wasm</i> <small class="mut">테트리스 완전정복</small></div>',
                        '<div class="brand">%s</div>' % BRAND)
    extra = io.open(os.path.join(HERE, 'extra.css'), encoding='utf-8').read()
    head = head.replace('</style>', extra + '</style>')

    # 1편에서 물려받은 데모 부트스트랩은 TetrisView 한 종류만 안다.
    # 이 덱은 데모가 7종이라 마운트를 demo.js 의 레지스트리에 위임한다.
    old = """    const p = loadCore(WASM_B64, (Math.random() * 0xffffffff) >>> 0)
      .then(core => {
        const v = new TetrisView(host, core, { bot });
        v.start();"""
    new = """    const p = window.__mountDemo(host)
      .then(v => {
        v.start();"""
    assert tail.count(old) == 1, '데모 부트스트랩을 찾지 못했다'
    tail = tail.replace(old, new)
    tail = tail.replace("    const bot = host.dataset.demo === 'bot';\n", '')

    body, toc, curseq = [], [], None
    for k, s in enumerate(slides, 1):
        secname = SECTIONS[s['sec']]
        label = '%s · %s' % (s['sec'], secname)
        html = expand(s['html'])
        html = html.replace('{{N}}', str(k)).replace('{{TOTAL}}', str(total))
        html = re.sub(r'\{\{LINES:([\w./]+)\}\}', lambda m: str(nlines(m.group(1))), html)
        body.append('<section class="slide" data-sec="%s" data-t="%s" id="s%d" data-n="%d">\n%s\n</section>'
                    % (label, s['t'], k, k, html))
        if s['sec'] != curseq:
            if curseq is not None:
                toc.append('</div>')
            toc.append('<div class="tocsec"><h4>%s</h4>' % label)
            curseq = s['sec']
        toc.append('<a href="#s%d" data-go="%d"><b>%d</b>%s</a>' % (k, k, k, s['t']))
    toc.append('</div>')

    nav = ('  </main>\n  <nav id="nav">\n'
           '    <button id="prev" aria-label="이전 슬라이드">◀</button>\n'
           '    <span id="counter">1 / %d</span>\n'
           '    <button id="next" aria-label="다음 슬라이드">▶</button>\n  </nav>\n'
           '  <div id="toc" role="dialog" aria-label="목차">\n'
           '    <h3>목차 — 전체 %d장</h3>\n%s\n'
           '    <button id="tocClose">닫기 ✕</button>\n  </div>\n</div>\n' % (total, total, ''.join(toc)))

    b64 = io.open(os.path.join(SRC, 'tetris_net.wasm.b64'), encoding='ascii').read().strip()
    weights = json.load(io.open(os.path.join(ROOT, 'tetris_ai', 'weights.json'), encoding='utf-8'))
    glue = ['<script>const WASM_B64 = "%s";\nconst NET_WEIGHTS = %s;</script>'
            % (b64, json.dumps(weights['levels'], ensure_ascii=False))]
    # room.mjs 는 서버 3구현 중 하나로 검증받은 원본 그대로다. 브라우저는 모듈이 아니라
    # 일반 스크립트로 읽으므로 각 줄 앞의 `export ` 만 기계적으로 떼어 낸다.
    rm = io.open(os.path.join(SRC, 'room.mjs'), encoding='utf-8').read()
    glue.append('<script>\n' + re.sub(r'^export ', '', rm, flags=re.M) + '\n</script>')
    for f in ('netcore_browser.js', 'net_client.js', 'seats.js', 'arena.js', 'match.js', 'demo.js'):
        glue.append('<script>\n' + io.open(os.path.join(SRC, f), encoding='utf-8').read() + '\n</script>')

    out = head + '\n' + '\n'.join(body) + '\n' + nav + '\n'.join(glue) + '\n' + tail
    io.open(OUT, 'w', encoding='utf-8', newline='').write(out)
    return total, out

SECTIONS = {}
def ranges(nums):
    out, s, p = [], nums[0], nums[0]
    for n in nums[1:]:
        if n == p + 1:
            p = n
            continue
        out.append('%d' % s if s == p else '%d-%d' % (s, p))
        s = p = n
    out.append('%d' % s if s == p else '%d-%d' % (s, p))
    return ','.join(out)

def main():
    global SECTIONS
    SECTIONS = json.load(io.open(os.path.join(SECD, 'sections.json'), encoding='utf-8'))
    total, out = build()
    print('슬라이드 %d장 · %.0f KB → %s' % (total, len(out.encode('utf-8')) / 1024, os.path.basename(OUT)))
    print('\n── 소스 커버리지 (덱에 실린 줄 / 전체 줄)')
    bad, tot_l, tot_c = 0, 0, 0
    for name in sorted(_cover):
        c = _cover[name]
        n = len(load(name))
        if _files[name] and _files[name][-1] == '':
            n -= 1
        c = c[:n]
        miss = [i + 1 for i, v in enumerate(c) if v == 0]
        dup = [i + 1 for i, v in enumerate(c) if v > 1]
        if name not in _partial:
            tot_l += n
            tot_c += sum(1 for v in c if v)
        flag = '' if (not miss or name in _partial) and not dup else '  ⚠'
        print('  %-26s %5d/%-5d%s' % (name, sum(1 for v in c if v), n, flag))
        if miss and name not in _partial:
            print('      빠진 줄: %s' % ranges(miss))
            bad += 1
        if dup:
            print('      중복 줄: %s' % ranges(dup))
    print('  %-26s %5d/%-5d' % ('── 합계(로그 제외)', tot_c, tot_l))
    print('\n── 오버플로 점검 (한 <pre> 45줄 초과 / 한 슬라이드 <li> 14개 초과)')
    warn = 0
    for sec in re.findall(r'<section class="slide".*?</section>', out, re.S):
        sid = re.search(r'id="(s\d+)"', sec).group(1)
        t = re.search(r'data-t="([^"]*)"', sec).group(1)
        for pre in re.findall(r'<pre class="code[^"]*"><code>(.*?)</code></pre>', sec, re.S):
            n = pre.count('\n') + 1
            if n > 45:
                print('  %s %s — 코드 %d줄' % (sid, t, n))
                warn += 1
        li = sec.count('<li>')
        if li > 14:
            print('  %s %s — <li> %d개' % (sid, t, li))
            warn += 1
    if not warn:
        print('  (없음)')
    if bad:
        print('\n⚠ 덱에 실리지 않은 소스 줄이 있다')

if __name__ == '__main__':
    main()
