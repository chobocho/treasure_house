# -*- coding: utf-8 -*-
"""build_deck.py — 섹션 조각들 + 실제 소스 파일 → 완성된 단일 HTML 덱.

1~3편(tetris_ai/deck, tetris_net/deck)에서 물려받은 보증 두 가지를 그대로 지킨다:
  1) 슬라이드에 실린 코드는 tetris_ts/ 의 실제 파일에서 잘라 온 것이다 (재입력 금지)
  2) 각 소스 파일의 모든 줄이 정확히 한 번씩 덱에 실렸는지 커버리지로 검증한다

이 덱에서 달라진 것: 소스가 전부 TypeScript 한 언어다. 그래서 wasm 을 base64 로
싣던 자리가 없어졌고, 대신 tsc 가 뽑은 **컴파일된 JS**(web/js/)를 인라인해서
덱 안의 데모를 돌린다. 슬라이드는 TS 원문을 보여 주고 데모는 그 컴파일 결과를
돌린다 — 같은 코드지만 같은 파일은 아니라는 걸 덱 본문에도 밝혀 둔다.
"""
import io, os, re, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl import highlight

HERE = os.path.dirname(os.path.abspath(__file__))          # tetris_ts/deck
SRC  = os.path.dirname(HERE)                               # tetris_ts
ROOT = os.path.dirname(SRC)                                # 저장소 루트
BASE = os.path.join(HERE, 'base')
SECD = os.path.join(HERE, 'sections')
OUT  = os.path.join(ROOT, 'TypeScript_테트리스_AI_8인_대전.html')

TITLE = '🟦 TypeScript 테트리스 — 코어부터 8인 온라인 대전까지'
DESC  = ('C++ wasm 3부작을 타입스크립트 한 언어로 다시 만든다. 코어 엔진은 C++ wasm 의 '
         '골든 트레이스를 그대로 재현하고, 8특징 AI 를 유전 알고리즘으로 실제로 학습시키며, '
         'RFC 6455 를 직접 구현한 서버로 8인 온라인 대전까지 간다. 런타임 의존성 0, '
         'strict 타입체크, 모든 코드는 실제로 컴파일·실행·테스트했고 전문이 그대로 실려 있다.')
BRAND = '<i>🟦 TypeScript</i> <small class="mut">테트리스 · AI · 8인 대전</small>'

LANGNAME = {'ts': 'TypeScript', 'js': 'JavaScript', 'json': 'JSON', 'make': 'Makefile',
            'sh': 'shell', 'txt': '출력', 'md': '문서', 'html': 'HTML', 'css': 'CSS',
            'cpp': 'C++'}
EXTLANG = {'ts': 'ts', 'mts': 'ts', 'tsx': 'ts', 'js': 'js', 'mjs': 'js', 'json': 'json',
           'md': 'md', 'html': 'html', 'css': 'css', 'log': 'txt', 'txt': 'txt',
           'cpp': 'cpp', 'h': 'cpp'}

# 덱 안에서 도는 데모용 스크립트. tsc 가 뽑은 결과를 `make web` 이 여기로 모은다.
# 아직 없으면 건너뛴다 — 뼈대 단계에서도 덱은 열려야 하기 때문이다.
DEMO_JS = ['web/js/core.js', 'web/js/ai.js', 'web/js/ga.js', 'web/js/battle.js',
           'web/js/protocol.js', 'web/js/room.js',
           'web/js/view.js', 'web/js/ga_view.js',
           'web/js/arena_view.js', 'web/js/demo.js']   # 전부 make web 생성물 (원본은 src/*.ts)

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
    n = nlines(name)
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
def parse_range(rng):
    if '-' in rng:
        x, y = rng.split('-')
        return (int(x) if x else None), (int(y) if y else None)
    if rng:
        return int(rng), int(rng)
    return None, None

def run_block(a):
    lo, hi = parse_range(a.get('lines', ''))
    name = a['file']
    lines = load(name)
    n = nlines(name)
    lo = 1 if lo is None else lo
    hi = n if hi is None else hi
    _partial.add(name)
    body = '\n'.join(lines[lo - 1:hi]).rstrip('\n')
    import html as _h
    return ('<div class="codewrap"><div class="codecap">%s<span>실제 출력 · %d줄</span></div>'
            '<pre class="code txt"><code>%s</code></pre></div>'
            % (a.get('cap', name), hi - lo + 1, _h.escape(body)))

# <!--CHART file=ga_log.json x=gen y=best,mean cap="…"--> → 실측 로그를 그대로 그린 SVG.
# 차트도 "지어내지 않는다"는 규칙을 따른다. 눈금과 점이 전부 파일에서 온다.
CHART_RE = re.compile(r'<!--CHART\s+(.*?)-->', re.S)
SERIES_COLOR = {'best': 'var(--acc)', 'mean': 'var(--acc2)', 'worst': 'var(--mut)'}
SERIES_KO = {'best': '최고', 'mean': '평균', 'worst': '최저'}

def chart_block(a):
    """세로 눈금은 로그의 최대값에서 뽑는다 — 보기 좋은 수로 반올림하면 그 순간
    화면의 수와 파일의 수가 달라진다. 축에 적히는 값이 곧 실측값이어야 한다."""
    name = a['file']
    _partial.add(name)  # 데이터 파일은 커버리지 대상이 아니다
    rows = json.load(io.open(os.path.join(SRC, name), encoding='utf-8'))
    xk = a.get('x', 'gen')
    keys = a.get('y', 'best,mean').split(',')
    W_, H_, PAD = 640, 260, 34
    xs = [float(r[xk]) for r in rows]
    ys = [float(r[k]) for k in keys for r in rows]
    x0, x1 = min(xs), max(xs)
    y1 = max(ys)
    sx = lambda v: PAD + (v - x0) / ((x1 - x0) or 1) * (W_ - PAD * 2)
    sy = lambda v: H_ - PAD - (v / (y1 or 1)) * (H_ - PAD * 2)
    out = ['<figure class="chart" style="margin:.4em 0">',
           '<svg viewBox="0 0 %d %d" width="100%%" role="img" aria-label="%s" '
           'style="max-width:100%%;height:auto">' % (W_, H_, a.get('cap', '차트'))]
    # 가로 눈금선 넷 + 값
    for i in range(5):
        v = y1 * i / 4
        y = sy(v)
        out.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="var(--line2)" stroke-width="1"/>'
                   % (PAD, y, W_ - PAD, y))
        out.append('<text x="%d" y="%.1f" fill="var(--mut)" font-size="11" text-anchor="end">%s</text>'
                   % (PAD - 4, y + 4, ('%g' % round(v, 1))))
    for k in keys:
        pts = ' '.join('%.1f,%.1f' % (sx(float(r[xk])), sy(float(r[k]))) for r in rows)
        out.append('<polyline data-series="%s" points="%s" fill="none" stroke="%s" stroke-width="2"/>'
                   % (k, pts, SERIES_COLOR.get(k, 'var(--acc)')))
    # 가로축 양 끝과 범례
    out.append('<text x="%d" y="%d" fill="var(--mut)" font-size="11">%s</text>' % (PAD, H_ - 8, '%g' % x0))
    out.append('<text x="%d" y="%d" fill="var(--mut)" font-size="11" text-anchor="end">%s</text>'
               % (W_ - PAD, H_ - 8, '%g' % x1))
    for i, k in enumerate(keys):
        out.append('<rect x="%d" y="10" width="14" height="3" fill="%s"/>' % (PAD + i * 78, SERIES_COLOR.get(k, 'var(--acc)')))
        out.append('<text x="%d" y="15" fill="var(--mut)" font-size="11">%s</text>'
                   % (PAD + i * 78 + 18, SERIES_KO.get(k, k)))
    out.append('</svg>')
    if a.get('cap'):
        out.append('<figcaption class="small mut" style="text-align:center">%s</figcaption>' % a['cap'])
    out.append('</figure>')
    return ''.join(out)

DIR_RE = re.compile(r'<!--CODE\s+(.*?)-->', re.S)
def parse_attrs(s):
    out = {}
    for m in re.finditer(r'(\w+)=(?:"([^"]*)"|(\S+))', s):
        out[m.group(1)] = m.group(2) if m.group(2) is not None else m.group(3)
    return out

def expand(text):
    def sub(m):
        a = parse_attrs(m.group(1))
        lo, hi = parse_range(a.get('lines', ''))
        f = a['file']
        if a.get('partial'):
            _partial.add(f)
        return code_block(f, lo, hi, a.get('cap'), lang_of(f, a))
    text = RUN_RE.sub(lambda m: run_block(parse_attrs(m.group(1))), text)
    text = CHART_RE.sub(lambda m: chart_block(parse_attrs(m.group(1))), text)
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

def demo_glue():
    """덱 안에서 도는 데모 스크립트를 인라인한다.

    wasm 이 없으니 base64 덩어리도 없다. tsc 결과(web/js/*.js)를 그대로 <script> 로
    넣을 뿐이다. 아직 안 만든 파일은 조용히 건너뛴다 — 뼈대 단계에서도 덱은 열려야 한다.
    """
    glue, missing = [], []
    wp = os.path.join(SRC, 'weights.json')
    if os.path.exists(wp):
        w = json.load(io.open(wp, encoding='utf-8'))
        glue.append('<script>const TS_WEIGHTS = %s;</script>'
                    % json.dumps(w.get('levels', {}), ensure_ascii=False))
    for f in DEMO_JS:
        p = os.path.join(SRC, f)
        if not os.path.exists(p):
            missing.append(f)
            continue
        glue.append('<script>\n' + io.open(p, encoding='utf-8').read() + '\n</script>')
    return glue, missing

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

    # 1편에서 물려받은 데모 부트스트랩은 wasm 을 올려 TetrisView 하나를 띄우는 물건이다.
    # 이 덱은 wasm 이 없고 데모도 여러 종이라 마운트를 demo.js 의 레지스트리에 넘긴다.
    # 레지스트리가 아직 없으면(뼈대 단계) 자리만 안내 문구로 채운다 — 덱은 그래도 열린다.
    old = """    const p = loadCore(WASM_B64, (Math.random() * 0xffffffff) >>> 0)
      .then(core => {
        const v = new TetrisView(host, core, { bot });
        v.start();"""
    new = """    const p = (window.__mountDemo
        ? window.__mountDemo(host)
        : Promise.reject(new Error('이 데모는 아직 준비 중입니다')))
      .then(v => {
        v.start();"""
    assert tail.count(old) == 1, '데모 부트스트랩을 찾지 못했다'
    tail = tail.replace(old, new)
    tail = tail.replace("    const bot = host.dataset.demo === 'bot';\n", '')
    tail = tail.replace("host.innerHTML = '<div class=\"warn\"><b>wasm 로드 실패</b>' + String(err) + '</div>';",
                        "host.innerHTML = '<div class=\"warn\"><b>데모를 띄우지 못했습니다</b> ' + String(err) + '</div>';")

    body, toc, curseq = [], [], None
    for k, s in enumerate(slides, 1):
        if s['sec'] not in SECTIONS:
            raise SystemExit('%s: sections.json 에 없는 파트 "%s"' % (s['src'], s['sec']))
        label = '%s · %s' % (s['sec'], SECTIONS[s['sec']])
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

    glue, missing = demo_glue()
    out = head + '\n' + '\n'.join(body) + '\n' + nav + '\n'.join(glue) + '\n' + tail
    io.open(OUT, 'w', encoding='utf-8', newline='').write(out)
    return total, out, missing

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
    total, out, missing = build()
    print('슬라이드 %d장 · %.0f KB → %s' % (total, len(out.encode('utf-8')) / 1024, os.path.basename(OUT)))
    if missing:
        print('  (데모 스크립트 %d개 미생성: %s)' % (len(missing), ', '.join(missing)))
    print('\n── 소스 커버리지 (덱에 실린 줄 / 전체 줄)')
    bad, tot_l, tot_c = 0, 0, 0
    for name in sorted(_cover):
        c = _cover[name][:nlines(name)]
        n = nlines(name)
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
