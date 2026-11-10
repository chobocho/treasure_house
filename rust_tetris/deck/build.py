# -*- coding: utf-8 -*-
"""build.py — template.html 엔진 + deck/sections/*.html + 실제 소스·로그 → 단일 HTML 덱.

보증: 슬라이드의 코드·실행 결과·화면은 전부 저장소의 실물에서 잘라 온다(재입력 금지).

지시자 (sections/*.html 안에 HTML 주석으로):
  <!--CODE file=core/src/piece.rs anchor=kind-->        // ANCHOR: kind ~ ANCHOR_END 사이
  <!--CODE file=Cargo.toml lines=1-12 cap="..."-->      줄 범위(1부터, 양끝 포함)
  <!--RUN file=out/logs/test_core.txt pick="1-8,79"-->  명령 출력(첫 줄 $ 명령), pick 은 출력 줄
  <!--ANSI file=out/tui_play.ansi-->                    tmux 캡처(색 포함)
  <!--IMG file=out/gui_play.png alt="..." cap="..."-->  PNG 를 data: URI 로
  <!--TETRIS title="..."-->                             덱 안에서 돌아가는 진짜 WASM 테트리스
"""
import base64, html, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))     # rust_tetris/deck
SRC = os.path.dirname(HERE)                           # rust_tetris
ROOT = os.path.dirname(SRC)                           # 저장소 루트
SECD = os.path.join(HERE, 'sections')
OUT = os.path.join(ROOT, 'Rust_테트리스_만들기.html')

TITLE = 'Rust 테트리스 만들기 — TUI · GUI · WASM'
DESC = ('Go·Java·Python·JS 개발자를 위한 Rust 테트리스 가이드. 입출력 없는 규칙 코어 하나를 '
        '터미널(crossterm)·데스크톱 창(minifb)·브라우저(WASM, 손으로 쓴 JS 글루) 세 판이 같이 쓴다. '
        '코드·시험 결과·화면은 전부 실제로 돌린 것이고, 덱 안에서 WASM 판을 바로 해 볼 수 있다.')
BRAND = '🦀 Rust 테트리스 <small style="opacity:.7">TUI·GUI·WASM</small>'
MAX_COLS, MAX_LINES = 72, 45

errors = []


def err(msg):
    errors.append(msg)


def cols(s):
    """터미널 칸 수: 한글·전각 2칸, 나머지 1칸."""
    n = 0
    for ch in s:
        o = ord(ch)
        n += 2 if (0x1100 <= o <= 0x115F or 0x2E80 <= o <= 0xA4CF or 0xAC00 <= o <= 0xD7A3
                   or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFF60) else 1
    return n


def attrs(s):
    out = {}
    for m in re.finditer(r'(\w+)=(?:"([^"]*)"|(\S+))', s):
        out[m.group(1)] = m.group(2) if m.group(2) is not None else m.group(3)
    return out


def read(rel, mode='r'):
    p = os.path.join(SRC, rel)
    if not os.path.exists(p):
        err(f'파일 없음: {rel}')
        return b'' if 'b' in mode else ''
    if 'b' in mode:
        return open(p, 'rb').read()
    return io.open(p, encoding='utf-8').read()


LANG = {'.rs': 'rust', '.toml': 'toml', '.js': 'js', '.mjs': 'js', '.html': 'html',
        '.sh': 'sh', '.py': 'py', '.md': 'text', '.txt': 'text'}
ANCHOR = re.compile(r'^\s*(//|#|<!--)\s*ANCHOR(_END)?:\s*\w+.*$')


def code_block(a, where):
    rel = a.get('file', '')
    text = read(rel)
    lines = text.split('\n')
    if 'anchor' in a:
        name = a['anchor']
        start = [i for i, l in enumerate(lines) if re.search(r'ANCHOR:\s*' + name + r'\b', l)]
        end = [i for i, l in enumerate(lines) if re.search(r'ANCHOR_END:\s*' + name + r'\b', l)]
        if len(start) != 1 or len(end) != 1:
            err(f'{where}: {rel} 의 앵커 {name} 이 {len(start)}/{len(end)}개')
            return ''
        body = lines[start[0] + 1:end[0]]
    elif 'lines' in a:
        x, y = (int(v) for v in a['lines'].split('-'))
        body = lines[x - 1:y]
    else:
        body = lines[:-1] if lines and lines[-1] == '' else lines
    body = [l for l in body if not ANCHOR.match(l)]
    ind = min((len(l) - len(l.lstrip(' ')) for l in body if l.strip()), default=0)
    body = [l[ind:] for l in body]
    for i, l in enumerate(body):
        if cols(l) > MAX_COLS:
            err(f'{where}: {rel} 줄 {cols(l)}칸 > {MAX_COLS}: {l.strip()[:40]}')
    if len(body) > MAX_LINES:
        err(f'{where}: {rel} {a.get("anchor", "")} {len(body)}줄 > {MAX_LINES}')
    base = os.path.basename(rel)
    lang = a.get('lang') or ('make' if base == 'Makefile' else LANG.get(os.path.splitext(rel)[1], 'text'))
    cap = a.get('cap', rel)
    return (f'<p class="fname">{html.escape(cap)}</p>\n'
            f'<pre><code data-lang="{lang}">{html.escape(chr(10).join(body))}</code></pre>')


def pick_lines(out, spec):
    """'1-8,79' → 고른 줄 + 건너뛴 곳에 생략 표시."""
    want = []
    for part in spec.split(','):
        if part.strip() == 'last':
            want.append(len(out))
            continue
        x, _, y = part.partition('-')
        want.extend(range(int(x), int(y or x) + 1))
    res, prev = [], 0
    for n in want:
        if not 1 <= n <= len(out):
            err(f'pick 범위 밖: {n} > {len(out)}')
            continue
        if n != prev + 1:
            res.append(('skip', n - prev - 1))
        res.append(('line', out[n - 1]))
        prev = n
    if prev < len(out):
        res.append(('skip', len(out) - prev))
    return res


def run_block(a, where):
    text = read(a.get('file', '')).rstrip('\n')
    if not text.startswith('$ '):
        err(f'{where}: {a.get("file")} 첫 줄이 $ 명령이 아니다')
        return ''
    first, _, rest = text.partition('\n')
    out = rest.split('\n') if rest else []
    items = pick_lines(out, a['pick']) if 'pick' in a else [('line', l) for l in out]
    rows = ['<span class="p">$</span> ' + html.escape(first[2:])]
    for kind, v in items:
        if kind == 'skip':
            rows.append(f'<span class="c">… ({v}줄 생략)</span>')
        else:
            esc = html.escape(v)
            if re.match(r'\s*(error|thread .* panicked|FAIL)', v):
                esc = f'<span class="r">{esc}</span>'
            elif re.match(r'\s*(test result: ok|ok  |\d+ passed)', v):
                esc = f'<span class="g">{esc}</span>'
            rows.append(esc)
    cap = f'<p class="cap">{html.escape(a["cap"])}</p>\n' if 'cap' in a else ''
    return cap + '<div class="term">' + '\n'.join(rows) + '</div>'


BASIC = ['#000000', '#cd3131', '#0dbc79', '#e5e510', '#2472c8', '#bc3fbc', '#11a8cd', '#e5e5e5',
         '#666666', '#f14c4c', '#23d18b', '#f5f543', '#3b8eea', '#d670d6', '#29b8db', '#ffffff']


def ansi_block(a, where):
    text = read(a.get('file', '')).rstrip('\n')
    fg = bg = None
    out = []
    for line in text.split('\n'):
        parts = re.split(r'\x1b\[([0-9;]*)m', line)
        buf = ''
        for i, p in enumerate(parts):
            if i % 2 == 1:
                nums = [int(x) if x else 0 for x in p.split(';')]
                j = 0
                while j < len(nums):
                    n = nums[j]
                    if n == 0: fg = bg = None
                    elif n == 39: fg = None
                    elif n == 49: bg = None
                    elif n in (38, 48) and j + 1 < len(nums):
                        if nums[j + 1] == 2:
                            c = '#%02x%02x%02x' % tuple(nums[j + 2:j + 5]); j += 4
                        else:
                            c = BASIC[nums[j + 2]] if nums[j + 2] < 16 else '#888888'; j += 2
                        if n == 38: fg = c
                        else: bg = c
                    elif 30 <= n <= 37: fg = BASIC[n - 30]
                    elif 90 <= n <= 97: fg = BASIC[n - 82]
                    elif 40 <= n <= 47: bg = BASIC[n - 40]
                    j += 1
            elif p:
                style = ';'.join(s for s in [f'color:{fg}' if fg else '',
                                             f'background:{bg}' if bg else ''] if s)
                t = html.escape(p)
                buf += f'<span style="{style}">{t}</span>' if style else t
        out.append(buf)
    cap = f'<p class="cap">{html.escape(a["cap"])}</p>\n' if 'cap' in a else ''
    return cap + '<pre class="tui">' + '\n'.join(out) + '</pre>'


def img_block(a, where):
    data = read(a.get('file', ''), 'rb')
    b64 = base64.b64encode(data).decode()
    cap = f'<figcaption>{html.escape(a["cap"])}</figcaption>' if 'cap' in a else ''
    alt = html.escape(a.get('alt', ''))
    return (f'<figure class="shot"><img src="data:image/png;base64,{b64}" alt="{alt}">'
            f'{cap}</figure>')


def tetris_block(a, where):
    title = html.escape(a.get('title', 'Rust → WASM 테트리스'))
    pad = ''.join(f'<button class="sec" data-a="{k}" aria-label="{lbl}">{t}</button>'
                  for k, t, lbl in [('left', '◀', '왼쪽'), ('soft', '▼', '소프트 드롭'),
                                    ('right', '▶', '오른쪽'), ('ccw', '⟲', '반시계 회전'),
                                    ('cw', '⟳', '시계 회전'), ('hard', '⤓', '하드 드롭'),
                                    ('hold', 'H', '홀드'), ('pause', 'Ⅱ', '일시정지'),
                                    ('restart', '↻', '다시 시작')])
    return f'''<div class="demo tt" data-demo="tetris">
<h5>{title}</h5>
<div class="tt-wrap">
<canvas class="tt-canvas" tabindex="0" aria-label="테트리스 판"></canvas>
<div class="tt-side">
<div class="row"><button data-start>▶ 시작</button><button class="sec" data-stop>■ 그만</button></div>
<div class="tt-pad">{pad}</div>
<div class="out"></div>
<p class="cap">시작하면 키·게임패드가 게임으로 갑니다 — ← → ↓ 이동 · ↑/X 회전 · Z 반대 회전 · Space 드롭 · C 홀드 · P 멈춤 · Q 나가기(슬라이드 넘기기로 돌아감)</p>
</div>
</div>
</div>'''


DIRECTIVES = {'CODE': code_block, 'RUN': run_block, 'ANSI': ansi_block,
              'IMG': img_block, 'TETRIS': tetris_block}


def expand(text, where):
    def sub(m):
        return DIRECTIVES[m.group(1)](attrs(m.group(2) or ''), where)
    return re.sub(r'<!--(' + '|'.join(DIRECTIVES) + r')\b(.*?)-->', sub, text, flags=re.S)


def nav_options(body):
    opts = ['<option value="top">챕터 이동…</option>']
    for m in re.finditer(r'<article class="card section" id="([^"]+)">\s*<p class="chnum">([^<]+)</p>\s*<h2>([^<]+)</h2>'
                         r'|<article class="card" id="([^"]+)">\s*<p class="chnum">(\d+장)</p>\s*<h2>([^<]+)</h2>', body):
        if m.group(1):
            opts.append(f'<option value="{m.group(1)}">{m.group(2)} · {m.group(3)}</option>')
        else:
            opts.append(f'<option value="{m.group(4)}">· {m.group(6)}</option>')
    return '\n    '.join(opts)


def main():
    tpl = io.open(os.path.join(ROOT, 'template.html'), encoding='utf-8').read()
    head, _, rest = tpl.partition('<main class="prose">')
    _, _, tail = rest.partition('</main>')

    files = sorted(f for f in os.listdir(SECD) if f.endswith('.html'))
    body = '\n'.join(expand(io.open(os.path.join(SECD, f), encoding='utf-8').read(), f)
                     for f in files)

    ids = re.findall(r'<article[^>]*\bid="([^"]+)"', body)
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        err('겹치는 id: ' + ', '.join(dup))
    all_ids = set(re.findall(r'\bid="([^"]+)"', body))
    for ref in re.findall(r'href="#([^"]+)"', body):
        if ref not in all_ids:
            err(f'없는 링크 대상: #{ref}')
    for f in files:
        if 'TODO' in io.open(os.path.join(SECD, f), encoding='utf-8').read():
            err(f'{f}: TODO 남음')

    head = re.sub(r'<title>.*?</title>', f'<title>{html.escape(TITLE)}</title>', head)
    head = re.sub(r'<meta name="description" content="[^"]*">',
                  f'<meta name="description" content="{html.escape(DESC)}">', head)
    head = re.sub(r'<span class="brand">.*?</span>', f'<span class="brand">{BRAND}</span>', head)
    head = re.sub(r'(<select id="nav"[^>]*>).*?(</select>)',
                  lambda m: m.group(1) + '\n    ' + nav_options(body) + '\n  ' + m.group(2),
                  head, flags=re.S)
    extra = io.open(os.path.join(HERE, 'extra.css'), encoding='utf-8').read()
    head = head.replace('</style>', extra + '</style>', 1)

    # 게임패드: 게임이 패드를 쥐고 있으면 덱 셸은 페이지를 넘기지 않는다
    pad_hook = '    raf = requestAnimationFrame(poll);\n'
    if tail.count(pad_hook) != 1:
        err('게임패드 셸의 고정점을 못 찾았다')
    tail = tail.replace(pad_hook, pad_hook + '    if (window.__deckPadOwner) return;   // 덱 안의 게임이 패드를 쓰는 중\n')
    # Rust 수명('a, '_)을 문자열로 칠하지 않게
    lt_hook = r"""    p.push('"(?:\\\\.|[^"\\\\\\n])*"');""" + '\n'
    lt_rule = r"""    if (lang === 'rust') p.push("'[A-Za-z_]\\w*\\b(?!')");   // 수명""" + '\n'
    if tail.count(lt_hook) != 1:
        err('하이라이터 고정점을 못 찾았다')
    tail = tail.replace(lt_hook, lt_rule + lt_hook)

    # 템플릿의 예시 데모를 이 덱의 데모로 바꾼다
    demo_re = re.compile(r'<!-- ===== 덱마다 다른 부분: 데모 함수들.*?</script>\n', re.S)
    if len(demo_re.findall(tail)) != 1:
        err('예시 데모 블록을 못 찾았다')
    wasm = base64.b64encode(read('out/tetris_wasm.wasm', 'rb')).decode()
    glue = read('wasm/web/tetris.js')
    demo = io.open(os.path.join(HERE, 'demo.js'), encoding='utf-8').read()
    block = ('<!-- ===== 이 덱의 데모: Rust 가 만든 WASM + 손글루 (rust_tetris/wasm) ===== -->\n'
             f'<script>\n{glue}</script>\n<script>window.__TT_WASM = "{wasm}";</script>\n'
             f'<script>\n{demo}</script>\n')
    tail = demo_re.sub(lambda m: block, tail, count=1)

    doc = head + '<main class="prose">\n' + body + '\n</main>' + tail
    n = len(re.findall(r'<article\b', body))
    if errors:
        print('\n'.join('  ✘ ' + e for e in errors))
    io.open(OUT, 'w', encoding='utf-8', newline='\n').write(doc)
    print(f'{os.path.basename(OUT)}: {n}장, {len(doc) // 1024} KB, wasm {len(wasm) * 3 // 4 // 1024} KB')
    print(f'오류 {len(errors)}건')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
