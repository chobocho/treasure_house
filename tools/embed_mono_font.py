#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""embed_mono_font.py — 덱 HTML에 고정폭 글꼴(DeckMono) 서브셋을 내장한다.

왜 글꼴을 싣나: 아스키 표·터미널 캡처·트리 도해는 "한글 = 2칸, 나머지 = 1칸"이라는
칸 규칙 위에 그려진 그림이다. 보는 쪽 기기에 그 규칙을 지키는 글꼴이 없으면
(안드로이드·iOS 에는 없다, 윈도·맥에서도 D2Coding 을 따로 깔아야 있다) 한글은
비례폭 글꼴에서, 박스 문자는 또 다른 글꼴에서 오게 되어 표의 선과 열이 어긋난다.
그래서 D2Coding(네이버, SIL OFL 1.1)에서 덱의 고정폭 요소가 실제로 쓰는 글자만 잘라
base64 woff2 로 <style> 앞머리에 싣는다. 덱마다 수십 KB 로 끝난다.

D2Coding 이 이 용도에 맞는 이유: 라틴·박스·블록·음영(░)·화살표가 전부 반각(500),
한글이 정확히 그 두 배(1000)라 터미널 칸과 1:1 로 맞는다. 다른 한글 고정폭 글꼴
(Noto Sans Mono CJK)은 박스 문자를 전각으로 그려 오히려 깨진다.

    python3 tools/embed_mono_font.py 덱.html [덱2.html ...]   # 제자리 내장·교체
    python3 tools/embed_mono_font.py --check 덱.html           # 검사만 (어긋나면 종료 코드 1)
    python3 tools/embed_mono_font.py --css '가나다'            # @font-face 를 표준 출력으로

파일은 @font-face 블록 외에는 바이트 하나 건드리지 않는다 — 줄바꿈(LF/CRLF)·BOM·들여쓰기 그대로.
tetris_tui/deck/gen_fonts.py 를 일반화한 것이라 글꼴 계약(폭 규칙·ALWAYS 범위)은 그쪽과 같다.
"""
import base64, html as htmlmod, io, os, re, sys

FAMILY = 'DeckMono'

# 설치된 파일 이름이 배포판마다 다르다. 처음 있는 것을 쓴다.
CANDIDATES = [
    '/usr/share/fonts/truetype/nanum/D2Coding-Ver1.3.2-20180524-ligature.ttf',
    '/usr/share/fonts/truetype/nanum/D2Coding-Ver1.3.2-20180524.ttf',
    '/usr/share/fonts/truetype/D2Coding/D2Coding-Ver1.3.2-20180524.ttf',
    os.path.expanduser('~/.fonts/D2Coding.ttf'),
]

# 덱의 글자에 더해 항상 싣는 범위 — ASCII 전체, 박스 그리기, 블록·음영, 화살표.
# 표 모양이 조금 바뀌어도 글꼴을 다시 만들 필요가 없게 한다.
ALWAYS = list(range(0x20, 0x7F)) + list(range(0x2500, 0x25A0)) + \
         list(range(0x2190, 0x2194)) + [0x25B6, 0x25C0, 0x00B7, 0x00D7, 0x2014, 0x2026]

# 고정폭으로 그리는 요소들. <pre>·<code> 와, 덱 CSS 에서 monospace 를 받는 클래스들.
MONO_CLASSES = ('term', 'cerr', 'sig', 'pkgtree', 'fname', 'out')
_RE_PRE = re.compile(r'<(pre|code)\b[^>]*>(.*?)</\1>', re.S | re.I)
_RE_CLS = re.compile(r'<(div|p|span|td|th)\b[^>]*\bclass="[^"]*\b(?:%s)\b[^"]*"[^>]*>(.*?)</\1>'
                     % '|'.join(MONO_CLASSES), re.S | re.I)
_RE_TAG = re.compile(r'<[^>]+>')
_RE_FACE = re.compile(r'(?:[ \t]*/\*[^*]*\*/\r?\n)?[ \t]*@font-face\{font-family:"%s";[^}]*\}\r?\n?' % FAMILY)
_RE_STYLE = re.compile(r'<style\b[^>]*>', re.I)
_RE_STACK = re.compile(r'font-family:\s*([^;}]*monospace[^;}]*)')


def source_path():
    for p in CANDIDATES:
        if os.path.exists(p):
            return p
    raise SystemExit('D2Coding 글꼴 파일이 없다 — apt install fonts-nanum-coding 또는 CANDIDATES 를 고칠 것')


def _cells(cp):
    """터미널 칸 규칙. 한글·CJK 만 두 칸 — tetris_tui/deck/check_deck.js 의 cells2 와 같다."""
    wide = (0x1100 <= cp <= 0x115F) or (0x2E80 <= cp <= 0x303E) or (0x3041 <= cp <= 0x33FF) \
        or (0x3400 <= cp <= 0x4DBF) or (0x4E00 <= cp <= 0x9FFF) or (0xAC00 <= cp <= 0xD7A3) \
        or (0xF900 <= cp <= 0xFAFF) or (0xFF00 <= cp <= 0xFF60)
    return 2 if wide else 1


def mono_text(html):
    """고정폭 요소 안의 글자만 모은다. 산문의 한글은 싣지 않아야 서브셋이 작게 남는다.
    태그를 벗기고 엔티티(&lt; 등)를 되돌린 실제 글자다. O(n)."""
    parts = [m.group(2) for m in _RE_PRE.finditer(html)] + [m.group(2) for m in _RE_CLS.finditer(html)]
    return ''.join(htmlmod.unescape(_RE_TAG.sub('', p)) for p in parts)


_SOURCE_CMAP = None


def _source_cmap():
    """원본 D2Coding 의 cmap. check() 가 파일마다 부르므로 한 번만 읽어 둔다."""
    global _SOURCE_CMAP
    if _SOURCE_CMAP is None:
        from fontTools.ttLib import TTFont
        f = TTFont(source_path(), lazy=True)
        _SOURCE_CMAP = f.getBestCmap()
        f.close()
    return _SOURCE_CMAP


# 칸 규칙을 어겼지만 죽이지 않고 넘긴 글자들. main() 이 경고로 보여 준다.
ambiguous_warnings = []


def _is_ambiguous(cp):
    """East_Asian_Width 가 A(모호)인가.

    모호 글자는 유니코드가 "문맥에 따라 1칸도 2칸도 된다" 고 못박아 둔 것들이다
    (동그라미 숫자, é, 박스 그리기 일부). 그러니 글꼴이 우리 표와 다르게 그리는 것은
    글꼴의 잘못이 아니라 그 글자의 성질이다. 여기서 빌드를 죽이면 안 된다 —
    대신 경고로 남겨서, 정말 칸이 맞아야 하는 자리(터미널 캡처)에 그런 글자를
    쓰지 않았는지 사람이 확인하게 한다. boricha/deck/gen_fonts.py 와 같은 계약이다.
    """
    import unicodedata
    try:
        return unicodedata.east_asian_width(chr(cp)) == 'A'
    except ValueError:
        return False


def unsupported(text):
    """원본 글꼴에 아예 없는 글자들 — 이모지·변형 선택자 따위. 실을 수 없으니 경고로만 남긴다."""
    cmap = _source_cmap()
    return sorted(set(c for c in text if ord(c) > 0x20 and ord(c) not in cmap))


def subset_woff2(text):
    """text 의 글자 + ALWAYS 범위를 담은 woff2 바이트. 폭 규칙을 어기면 여기서 죽는다."""
    from fontTools.ttLib import TTFont
    from fontTools import subset
    font = TTFont(source_path())
    cmap = font.getBestCmap()
    want = set(ALWAYS) | set(ord(c) for c in text)
    want = set(cp for cp in want if cp in cmap)
    opt = subset.Options()
    opt.flavor = 'woff2'
    opt.hinting = False            # 힌트를 빼면 크기가 반으로 준다. 화면용이라 손해가 없다.
    opt.layout_features = []       # 합자(->, ==)를 끈다. 코드는 한 글자 한 칸이어야 한다.
    opt.name_IDs = [1, 2, 6]
    opt.notdef_outline = True
    sub = subset.Subsetter(opt)
    sub.populate(unicodes=want)
    sub.subset(font)
    # 계약 검사: 반각 500 · 전각 1000 (upm 1000). 하나라도 어긋나면 표가 깨진다.
    hmtx, upm = font['hmtx'], font['head'].unitsPerEm
    del ambiguous_warnings[:]
    for cp, g in font.getBestCmap().items():
        adv = hmtx[g][0]
        if adv * 2 == upm * _cells(cp):
            continue
        if _is_ambiguous(cp):
            ambiguous_warnings.append((cp, adv))   # 모호 글자. 갈리는 것이 정상이다
            continue
        raise SystemExit('U+%04X 의 폭 %d 이 칸 규칙(%d칸)과 다르다' % (cp, adv, _cells(cp)))
    font.flavor = 'woff2'          # opt.flavor 는 save_font 전용이라 여기서 다시 지정해야 woff2 로 압축된다
    font.recalcTimestamp = False   # 저장 시각을 안 찍어야 언제 돌려도 같은 바이트 — 덱 diff 가 조용하다
    buf = io.BytesIO()
    font.save(buf)
    font.close()
    return buf.getvalue()


def font_face_css(text):
    b64 = base64.b64encode(subset_woff2(text)).decode('ascii')
    return ('  /* D2Coding (네이버, SIL OFL 1.1) 서브셋 — 이 덱의 코드·표·캡처에 쓰인 글자만 담았다.'
            ' 갱신: python3 tools/embed_mono_font.py 이파일.html */\n'
            '  @font-face{font-family:"%s"; font-style:normal; font-weight:400; font-display:block;\n'
            '    src:url(data:font/woff2;base64,%s) format("woff2")}\n' % (FAMILY, b64))


def embed(html):
    """@font-face 블록만 제자리 교체(없으면 첫 <style> 바로 뒤에 삽입)한 새 문자열.
    줄바꿈은 파일이 쓰는 것을 따른다 — 그 외 바이트는 그대로다."""
    nl = '\r\n' if '\r\n' in html else '\n'
    css = font_face_css(mono_text(html)).replace('\n', nl)
    if _RE_FACE.search(html):
        return _RE_FACE.sub(lambda m: css, html, count=1)
    m = _RE_STYLE.search(html)
    if not m:
        raise ValueError('<style> 이 없다 — 글꼴을 넣을 자리가 없다')
    at = m.end()
    if html.startswith(nl, at):
        at += len(nl)
    return html[:at] + css + html[at:]


def _embedded_cmap(style_head):
    from fontTools.ttLib import TTFont
    m = re.search(r'url\(data:font/woff2;base64,([A-Za-z0-9+/=]+)\)', style_head)
    if not m:
        return None
    f = TTFont(io.BytesIO(base64.b64decode(m.group(1))))
    cmap = f.getBestCmap()
    f.close()
    return cmap


def check(html):
    """어긋난 점의 목록. 비어 있으면 통과. 검사 셋 — 글꼴이 딱 하나 woff2 로 있는가,
    고정폭 목록이 전부 DeckMono 로 시작하는가, 고정폭 요소의 글자를 글꼴이 다 덮는가."""
    probs = []
    style_head = html.split('</style>')[0]
    faces = style_head.count('@font-face{font-family:"%s"' % FAMILY)
    if faces != 1:
        probs.append('내장 글꼴 @font-face 가 %d개 — 정확히 1개여야 한다' % faces)
    elif 'base64,d09GMg' not in style_head:   # 'wOF2' 의 base64
        probs.append('내장 글꼴이 woff2 가 아니다')
    stacks = [s.strip() for s in _RE_STACK.findall(style_head)]
    bad = [s for s in stacks if not s.startswith('"%s"' % FAMILY)]
    if bad:
        probs.append('%s 로 시작하지 않는 고정폭 글꼴 목록 %d개: %s' % (FAMILY, len(bad), '; '.join(b[:40] for b in bad)))
    cmap = _embedded_cmap(style_head) if faces == 1 else None
    if cmap is not None:
        src = _source_cmap()
        missing = sorted(set(c for c in mono_text(html) if ord(c) > 0x20 and ord(c) in src and ord(c) not in cmap))
        if missing:
            probs.append('내장 글꼴에 없는 고정폭 글자 %d개: %s' % (len(missing), ''.join(missing)[:60]))
    return probs


def _read(path):
    with open(path, 'rb') as f:
        return f.read().decode('utf-8')


def main(argv):
    if '--css' in argv:
        i = argv.index('--css')
        sys.stdout.write(font_face_css(' '.join(argv[i + 1:])))
        return 0
    check_only = '--check' in argv
    paths = [a for a in argv if not a.startswith('--')]
    if not paths:
        sys.stderr.write(__doc__)
        return 2
    rc = 0
    for path in paths:
        html = _read(path)
        if check_only:
            probs = check(html)
            for p in probs:
                print('%s: %s' % (path, p))
            print('%s: %s' % (path, '통과' if not probs else '어긋남 %d건' % len(probs)))
            rc = rc or (1 if probs else 0)
            continue
        out = embed(html)
        with open(path, 'wb') as f:
            f.write(out.encode('utf-8'))
        text = mono_text(out)
        bad = unsupported(text)
        m = re.search(r'base64,([A-Za-z0-9+/=]+)', out.split('</style>')[0])
        print('%s: 고정폭 글자 %d종 → DeckMono %d KB' % (path, len(set(text)), len(m.group(1)) * 3 // 4 // 1024))
        if bad:
            print('  경고: D2Coding 에 없는 글자 %d개는 못 실었다 — %s' % (len(bad), ''.join(bad)[:40]))
        if ambiguous_warnings:
            chars = ''.join(chr(cp) for cp, _ in ambiguous_warnings)
            print('  경고: 모호(A) 폭이라 글꼴과 칸 규칙이 갈리는 글자 %d개 — %s'
                  ' · 칸이 맞아야 하는 캡처에는 쓰지 말 것' % (len(ambiguous_warnings), chars))
        left = check(out)
        for p in left:
            print('  ' + p)
        rc = rc or (1 if left else 0)
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
