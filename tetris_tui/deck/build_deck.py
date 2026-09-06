# -*- coding: utf-8 -*-
"""build_deck.py — 섹션 조각들 + 실제 소스 파일 → 완성된 단일 HTML 덱.

1~4편(tetris_ai/deck, tetris_net/deck, tetris_ts/deck)에서 물려받은 보증 두 가지를
그대로 지킨다:

  1) 슬라이드에 실린 코드는 tetris_tui/ 의 실제 파일에서 잘라 온 것이다 (재입력 금지)
  2) 각 소스 파일의 모든 줄이 정확히 한 번씩 덱에 실렸는지 커버리지로 검증한다

이 덱에서 달라진 것: 브라우저에서 돌릴 wasm 이 없다. 대신 **터미널 화면 기록**이 있다.
tools/record 가 진짜 모델을 돌려 프레임을 남기고, tools/ansi2html 이 그걸 HTML 로
바꾸고, deck/player.js 가 덱 안에서 넘겨 보게 한다. 그래서 이 파일은 wasm 을
base64 로 싣던 자리에 프레임 묶음을 싣는다.

지시자:

    <!--CODE file=core/game.go lines=10-40 cap="락"-->   소스에서 잘라 온 코드
    <!--RUN file=out/make_test.txt lines=1-20 cap="…"-->  실제로 돌린 출력
    <!--CAP file=out/tmux_1p.html cap="…"-->             터미널 화면 한 장
    <!--PLAYER name=1p cap="…"-->                        넘겨 보는 기록
    <!--BOARD rows="..#|###" cap="…"-->                  판 도해
"""
import io, os, re, sys, json
import html as _html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hl import highlight

HERE = os.path.dirname(os.path.abspath(__file__))          # tetris_tui/deck
SRC  = os.path.dirname(HERE)                               # tetris_tui
ROOT = os.path.dirname(SRC)                                # 저장소 루트
BASE = os.path.join(HERE, 'base')
SECD = os.path.join(HERE, 'sections')
OUT  = os.path.join(ROOT, 'Go_Bubble_Tea_테트리스_만들기.html')

TITLE = '🍵 Go Bubble Tea 테트리스 — TUI 프레임워크 입문부터 AI 1:1 대전까지'
DESC  = ('Bubble Tea 를 처음 쓰는 사람을 위해 예제 7개로 Elm 아키텍처를 익힌 뒤, '
         '터미널 테트리스를 1인용 → 같은 키보드 2인용 → 8특징 AI 와의 1:1 대전까지 만든다. '
         '코어와 AI 는 기존 C++ wasm 덱의 골든 트레이스로 전 스텝 검증했고, '
         '화면은 전부 실제로 돌린 기록에서 뽑았다. 외부 의존성 0, 단일 HTML.')
BRAND = '<i>🍵 Go Bubble Tea</i> <small class="mut">터미널 테트리스</small>'

LANGNAME = {'go': 'Go', 'json': 'JSON', 'make': 'Makefile', 'mod': 'go.mod',
            'sh': 'shell', 'txt': '출력', 'md': '문서', 'html': 'HTML',
            'css': 'CSS', 'js': 'JavaScript', 'py': 'Python', 'cpp': 'C++',
            'ts': 'TypeScript'}
EXTLANG = {'go': 'go', 'json': 'json', 'md': 'md', 'html': 'html', 'css': 'css',
           'js': 'js', 'mjs': 'js', 'py': 'py', 'log': 'txt', 'txt': 'txt',
           'cpp': 'cpp', 'h': 'cpp', 'ts': 'ts', 'sum': 'txt', 'mod': 'mod'}

# 덱 안에서 넘겨 볼 기록들. 없으면 조용히 건너뛴다 — 뼈대 단계에서도 덱은 열려야 한다.
FRAME_FILES = ['out/frames_1p.html.json', 'out/frames_2p.html.json',
               'out/frames_ai.html.json', 'out/frames_aivai.html.json']

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
    if base == 'go.mod':
        return 'mod'
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


# <!--RUN file=out/x.txt lines=A-B cap="…"--> → 실제로 돌린 출력 그대로.
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


# <!--CAP file=out/tmux_1p.html cap="…"--> → 터미널 화면 한 장 (ansi2html 결과 그대로)
CAP_RE = re.compile(r'<!--CAP\s+(.*?)-->', re.S)


def cap_block(a):
    path = os.path.join(SRC, a['file'])
    if not os.path.exists(path):
        return ('<div class="warn">화면 %s 가 아직 없습니다 — <code>make tmux-smoke html</code></div>'
                % a['file'])
    body = io.open(path, encoding='utf-8').read().rstrip('\n')
    return ('<div class="codewrap"><div class="codecap">%s<span>실제 터미널 · 80×24</span></div>'
            '<pre class="term"><code>%s</code></pre></div>'
            % (a.get('cap', a['file']), body))


# <!--PLAYER name=1p cap="…"--> → 넘겨 보는 기록
PLAYER_RE = re.compile(r'<!--PLAYER\s+(.*?)-->', re.S)


def player_block(a):
    name = a['name']
    cap = a.get('cap', '')
    return ('<figure class="playerwrap"><div class="player" data-frames="%s"></div>'
            '<figcaption class="small mut">%s</figcaption></figure>' % (name, cap))


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
    text = CAP_RE.sub(lambda m: cap_block(parse_attrs(m.group(1))), text)
    text = PLAYER_RE.sub(lambda m: player_block(parse_attrs(m.group(1))), text)
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


def frame_glue():
    """기록 묶음과 재생기를 인라인한다.

    프레임은 "앞 프레임과 달라진 줄"만 담고 있어서, 네 모드를 다 실어도
    500 KB 남짓이다. 통째로 담았다면 1.2 MB 였다.
    """
    frames, missing = {}, []
    for f in FRAME_FILES:
        p = os.path.join(SRC, f)
        if not os.path.exists(p):
            missing.append(f)
            continue
        rec = json.load(io.open(p, encoding='utf-8'))
        frames[rec['name']] = rec
    glue = []
    if frames:
        glue.append('<script>window.__FRAMES=%s;</script>'
                    % json.dumps(frames, ensure_ascii=False, separators=(',', ':')))
    pj = os.path.join(HERE, 'player.js')
    if os.path.exists(pj):
        glue.append('<script>\n' + io.open(pj, encoding='utf-8').read() + '\n</script>')
    return glue, missing


# 1편에서 물려받은 데모 부트스트랩은 wasm 을 올려 TetrisView 하나를 띄우는 물건이다.
# 이 덱에는 wasm 이 없다 — 화면은 미리 뽑아 둔 기록이고, 재생기가 따로 있다.
# 그래서 그 자리를 아무 일도 안 하는 코드로 바꾼다. 그냥 두면 죽은 코드가
# 정의된 적 없는 이름(loadCore, WASM_B64)을 가리키게 된다.
OLD_DEMO = """    const bot = host.dataset.demo === 'bot';
    if (demos.has(host)) { demos.get(host).then(v => v && v.start()); return; }
    const p = loadCore(WASM_B64, (Math.random() * 0xffffffff) >>> 0)
      .then(core => {
        const v = new TetrisView(host, core, { bot });
        v.start();
        // 자동 포커스는 하지 않는다. 슬라이드에 들어서자마자 방향키를 게임이 가져가면
        // 사용자가 슬라이드를 넘길 방법을 잃는다. 클릭/탭이 곧 "조작권 인수" 신호다.
        return v;
      })
      .catch(err => {
        host.innerHTML = '<div class="warn"><b>wasm 로드 실패</b>' + String(err) + '</div>';
        return null;
      });
    demos.set(host, p);"""
NEW_DEMO = """    // 이 덱에는 살아 도는 데모가 없다. 화면은 전부 미리 뽑아 둔 기록이고,
    // 넘겨 보는 일은 deck/player.js 가 맡는다.
    return;"""


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

    assert tail.count(OLD_DEMO) == 1, '데모 부트스트랩을 찾지 못했다'
    tail = tail.replace(OLD_DEMO, NEW_DEMO)

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

    glue, missing = frame_glue()
    out = head + '\n' + '\n'.join(body) + '\n' + nav + '\n'.join(glue) + '\n' + tail
    out, font_warn = embed_font(out)
    io.open(OUT, 'w', encoding='utf-8', newline='').write(out)
    return total, out, missing, font_warn


def embed_font(out):
    """코드·터미널에 쓰이는 글자만 담은 D2Coding 서브셋을 <style> 맨 앞에 싣고,
    고정폭 글꼴 목록의 맨 앞에 그 이름을 둔다.

    보는 쪽 기기에 한글 고정폭 글꼴이 없으면(폰·태블릿이 그렇다) 한글이 비례폭으로,
    박스 문자가 다른 글꼴로 와서 터미널 캡처의 상자와 판이 어긋난다. 글꼴을 싣는 것이
    "어디서 열어도 같은 그림"을 지키는 유일한 길이다. 글자 집합은 조립이 끝난 덱에서
    직접 뽑으므로 새 화면·새 주석이 생겨도 따로 손댈 것이 없다.
    """
    import gen_fonts
    used = set()
    for m in re.finditer(r'<(?:code|pre)\b[^>]*>([\s\S]*?)</(?:code|pre)>', out):
        used |= set(_html.unescape(re.sub(r'<[^>]+>', '', m.group(1))))
    for m in re.finditer(r'window\.__FRAMES=(\{.*?\});</script>', out):
        used |= set(_html.unescape(re.sub(r'<[^>]+>', '', m.group(1))))
    text = ''.join(sorted(used))
    css = gen_fonts.font_face_css(text)
    # 머리의 첫 <style> 이 덱 전체의 CSS 다. 그 맨 앞에 두어야 뒤의 글꼴 목록이 참조할 수 있다.
    assert '<style>' in out, '<style> 을 찾지 못했다'
    out = out.replace('<style>', '<style>\n' + css, 1)
    n = out.count('font-family:"D2Coding",')
    assert n >= 4, '고정폭 글꼴 목록을 찾지 못했다'
    out = out.replace('font-family:"D2Coding",', 'font-family:"%s","D2Coding",' % gen_fonts.FAMILY)
    warn = []
    skipped = gen_fonts.unsupported(text)
    if skipped:
        warn.append('글꼴에 없어 시스템 글꼴로 남는 글자 %d개: %s' % (len(skipped), ''.join(skipped)))
    return out, warn


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
    total, out, missing, font_warn = build()
    print('슬라이드 %d장 · %.0f KB → %s' % (total, len(out.encode('utf-8')) / 1024, os.path.basename(OUT)))
    if missing:
        print('  (기록 %d개 미생성: %s)' % (len(missing), ', '.join(missing)))
    for w in font_warn:
        print('  (글꼴: %s)' % w)
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
        print('  %-30s %5d/%-5d%s' % (name, sum(1 for v in c if v), n, flag))
        if miss and name not in _partial:
            print('      빠진 줄: %s' % ranges(miss))
            bad += 1
        if dup:
            print('      중복 줄: %s' % ranges(dup))
            bad += 1
    print('  %-30s %5d/%-5d' % ('── 합계(로그 제외)', tot_c, tot_l))

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
    print('\n오류 %d건' % (bad + warn))


if __name__ == '__main__':
    main()
