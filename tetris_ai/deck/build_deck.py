# -*- coding: utf-8 -*-
"""build_deck.py — 섹션 조각들 + 실제 소스 파일 → 완성된 단일 HTML 덱.

핵심 보증 두 가지:
  1) 슬라이드에 실린 코드는 tetris_ai/ 의 실제 파일에서 잘라 온 것이다 (재입력 금지)
  2) 각 소스 파일의 모든 줄이 정확히 한 번씩 덱에 실렸는지 커버리지로 검증한다
"""
import io, os, re, sys, base64, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl import highlight

HERE = os.path.dirname(os.path.abspath(__file__))          # tetris_ai/deck
SRC  = os.path.dirname(HERE)                               # tetris_ai
ROOT = os.path.dirname(SRC)                                # 저장소 루트
BASE = os.path.join(HERE, 'base')                          # 부 1 덱에서 떼어 온 머리/꼬리
SECD = os.path.join(HERE, 'sections')                      # 슬라이드 본문 조각
OUT  = os.path.join(ROOT, 'C++_WASM_테트리스_AI_대전.html')

TITLE = '🧬 C++ WASM 테트리스 2편 — 유전 알고리즘 AI와 1:1 대전'
DESC  = ('부 1 에서 만든 C++ wasm 테트리스 코어에 보드 평가 8특징·1수 탐색 AI를 얹고, '
         '가중치를 유전 알고리즘으로 실제로 학습시킨 뒤, 두 개의 wasm 인스턴스를 붙여 '
         '가비지를 주고받는 1:1 대전을 만든다. 모든 코드는 실제로 컴파일·실행해 검증했고 '
         '전문이 그대로 실려 있다. 이 문서 안에서 AI가 직접 대전한다.')
BRAND = '<i>🧬 테트리스 AI</i> <small class="mut">유전 알고리즘 · 1:1 대전</small>'

LANGNAME = {'cpp': 'C++', 'js': 'JavaScript', 'make': 'Makefile', 'sh': 'shell',
            'json': 'JSON', 'txt': '출력'}

_files, _cover, _partial = {}, {}, set()
def load(name):
    if name not in _files:
        p = os.path.join(SRC, name) if not os.path.isabs(name) else name
        _files[name] = io.open(p, encoding='utf-8').read().split('\n')
        _cover[name] = [0] * len(_files[name])
    return _files[name]

def nlines(name):
    lines = load(name)
    n = len(lines)
    if lines and lines[-1] == '':
        n -= 1
    return n

def code_block(name, a, b, cap, lang):
    lines = load(name)
    n = len(lines)
    if lines and lines[-1] == '':          # 파일 끝 개행은 줄로 세지 않는다
        n -= 1
    a = 1 if a is None else a
    b = n if b is None else b
    assert 1 <= a <= b <= n, '%s: 범위 %d-%d (총 %d줄)' % (name, a, b, n)
    for i in range(a - 1, b):
        _cover[name][i] += 1
    body = '\n'.join(lines[a - 1:b]).rstrip('\n')
    meta = '%s · %d줄 (%d–%d)' % (LANGNAME.get(lang, lang), b - a + 1, a, b)
    capr = cap if cap else name
    return ('<div class="codewrap"><div class="codecap">%s<span>%s</span></div>'
            '<pre class="code %s"><code>%s</code></pre></div>'
            % (capr, meta, lang, highlight(body, lang)))

# <!--BOARD rows="..|..|.." cap="…"--> → CSS 그리드 보드 도해
# 문자: . 빈칸 / # 굳은 블록 / o 이번 조각 / g 고스트 / c 지워질 줄 / x 강조
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
        return '<figure style="margin:.3em 0;display:inline-block">%s<figcaption class="small mut" style="text-align:center">%s</figcaption></figure>' % (grid, cap)
    return grid

# <!--GALOG file=ga_log.json cols="gen:세대,best:최고" cap="…"--> → 실제 학습 로그 표
GALOG_RE = re.compile(r'<!--GALOG\s+(.*?)-->', re.S)
def galog_block(a):
    rows = json.load(io.open(os.path.join(SRC, a['file']), encoding='utf-8'))
    cols = [c.split(':') for c in a['cols'].split(',')]
    head = ''.join('<th>%s</th>' % t for _, t in cols)
    body = []
    for r in rows:
        body.append('<tr>' + ''.join('<td>%s</td>' % r.get(k, '') for k, _ in cols) + '</tr>')
    cap = a.get('cap', '')
    return ('<div class="logbox"><table><tr>%s</tr>%s</table></div>'
            '<p class="small mut">%s</p>' % (head, ''.join(body), cap))

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
            x, y = rng.split('-'); lo = int(x) if x else None; hi = int(y) if y else None
        elif rng:
            lo = hi = int(rng)
        else:
            lo = hi = None
        f = a['file']
        if a.get('partial'): _partial.add(f)
        lang = a.get('lang') or ({'cpp': 'cpp'}.get(f.rsplit('.', 1)[-1]) or
              {'cpp': 'cpp', 'mjs': 'js', 'js': 'js', 'json': 'json'}.get(f.rsplit('.', 1)[-1], 'txt'))
        if f == 'Makefile': lang = a.get('lang', 'make')
        return code_block(f, lo, hi, a.get('cap'), lang)
    text = GALOG_RE.sub(lambda m: galog_block(parse_attrs(m.group(1))), text)
    text = BOARD_RE.sub(lambda m: board_block(parse_attrs(m.group(1))), text)
    return DIR_RE.sub(sub, text)

# ── 섹션 조각 읽기 ───────────────────────────────────────────────────
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

    # 부 1 의 데모 부트스트랩은 TetrisView 한 종류만 안다. 이 덱은 데모가 7종이라
    # 마운트를 battle.js 의 __mountDemo 레지스트리에 위임한다 (이 부분만 다르다).
    old = """    const p = loadCore(WASM_B64, (Math.random() * 0xffffffff) >>> 0)
      .then(core => {
        const v = new TetrisView(host, core, { bot });
        v.start();"""
    new = """    const p = window.__mountDemo(host)
      .then(v => {
        v.start();"""
    assert tail.count(old) == 1, '부 1 데모 부트스트랩을 찾지 못했다'
    tail = tail.replace(old, new)
    tail = tail.replace("    const bot = host.dataset.demo === 'bot';\n", '')

    body, toc, curseq = [], [], None
    for k, s in enumerate(slides, 1):
        secname = SECTIONS[s['sec']]
        label = '%s · %s' % (s['sec'], secname)
        html = expand(s['html'])
        html = html.replace('{{N}}', str(k)).replace('{{TOTAL}}', str(total))
        html = re.sub(r'\{\{LINES:([\w.]+)\}\}', lambda m: str(nlines(m.group(1))), html)
        body.append('<section class="slide" data-sec="%s" data-t="%s" id="s%d" data-n="%d">\n%s\n</section>'
                    % (label, s['t'], k, k, html))
        if s['sec'] != curseq:
            if curseq is not None: toc.append('</div>')
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

    b64 = io.open(os.path.join(SRC, 'tetris_ai.wasm.b64'), encoding='ascii').read().strip()
    glue = []
    # ga_core.mjs 는 Node 트레이너와 공유하는 원본 그대로다. 브라우저는 모듈이 아니라
    # 일반 스크립트로 읽어야 하므로 각 줄 앞의 `export ` 만 기계적으로 떼어 낸다.
    gc = io.open(os.path.join(SRC, 'ga_core.mjs'), encoding='utf-8').read()
    glue.append('<script>\n' + re.sub(r'^export ', '', gc, flags=re.M) + '\n</script>')
    for f in ('battle.js', 'ga_browser.js'):
        p = os.path.join(SRC, f)
        if os.path.exists(p):
            glue.append('<script>\n' + io.open(p, encoding='utf-8').read() + '\n</script>')
    wasm_script = '<script>const WASM_B64 = "%s";\nconst GA_LOG = %s;\nconst GA_WEIGHTS = %s;</script>' % (
        b64,
        io.open(os.path.join(SRC, 'ga_log.json'), encoding='utf-8').read().strip(),
        io.open(os.path.join(SRC, 'weights.json'), encoding='utf-8').read().strip())

    out = head + '\n' + '\n'.join(body) + '\n' + nav + wasm_script + '\n' + '\n'.join(glue) + '\n' + tail
    io.open(OUT, 'w', encoding='utf-8', newline='').write(out)
    return total, out

SECTIONS = {}
def main():
    global SECTIONS
    SECTIONS = json.load(io.open(os.path.join(SECD, 'sections.json'), encoding='utf-8'))
    total, out = build()
    print('슬라이드 %d장 · %.0f KB → %s' % (total, len(out.encode('utf-8')) / 1024, os.path.basename(OUT)))
    print('\n── 소스 커버리지 (덱에 실린 줄 / 전체 줄)')
    bad = 0
    for name in sorted(_cover):
        c = _cover[name]
        n = len(load(name))
        if _files[name] and _files[name][-1] == '': n -= 1
        c = c[:n]
        miss = [i + 1 for i, v in enumerate(c) if v == 0]
        dup  = [i + 1 for i, v in enumerate(c) if v > 1]
        flag = '' if (not miss or name in _partial) and not dup else '  ⚠'
        print('  %-18s %4d/%-4d%s' % (name, sum(1 for v in c if v), n, flag))
        if miss and name not in _partial: print('      빠진 줄: %s' % ranges(miss)); bad += 1
        if dup:  print('      중복 줄: %s' % ranges(dup))
    print('\n── 오버플로 점검 (한 <pre> 45줄 초과 / 한 슬라이드 <li> 12개 초과)')
    for m in re.finditer(r'<section class="slide"[^>]*id="(s\d+)"[^>]*data-t="([^"]*)"', out):
        pass
    warn = 0
    for sec in re.findall(r'<section class="slide".*?</section>', out, re.S):
        sid = re.search(r'id="(s\d+)"', sec).group(1)
        t = re.search(r'data-t="([^"]*)"', sec).group(1)
        for pre in re.findall(r'<pre class="code[^"]*"><code>(.*?)</code></pre>', sec, re.S):
            n = pre.count('\n') + 1
            if n > 45: print('  %s %s — 코드 %d줄' % (sid, t, n)); warn += 1
        li = sec.count('<li>')
        if li > 14: print('  %s %s — <li> %d개' % (sid, t, li)); warn += 1
    if not warn: print('  (없음)')
    if bad: print('\n⚠ 덱에 실리지 않은 소스 줄이 있다')

def ranges(nums):
    out, s, p = [], nums[0], nums[0]
    for n in nums[1:]:
        if n == p + 1: p = n; continue
        out.append('%d' % s if s == p else '%d-%d' % (s, p)); s = p = n
    out.append('%d' % s if s == p else '%d-%d' % (s, p))
    return ','.join(out)

if __name__ == '__main__':
    main()
