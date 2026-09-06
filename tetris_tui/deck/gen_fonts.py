# -*- coding: utf-8 -*-
"""gen_fonts.py — 덱에 내장할 고정폭 글꼴 서브셋을 만든다.

왜 글꼴을 싣나: 터미널 캡처와 재생기 화면은 "한글 = 2칸, 나머지 = 1칸"이라는
터미널의 칸 규칙 위에 그려진 그림이다. 보는 쪽 기기에 그 규칙을 지키는 글꼴이
없으면(안드로이드·iOS 에는 없다, 윈도에서도 D2Coding 을 따로 깔아야 있다)
한글은 비례폭 글꼴에서, 박스 문자는 또 다른 글꼴에서 오게 되어 상자와 판이 깨진다.
그래서 D2Coding(OFL) 에서 덱이 실제로 쓰는 글자만 잘라 base64 로 싣는다.

D2Coding 이 이 용도에 맞는 이유: 라틴·박스·블록·음영(░)·화살표가 전부 반각(500),
한글이 정확히 그 두 배(1000)라 터미널 칸과 1:1 로 맞는다. 다른 한글 고정폭 글꼴
(Noto Sans Mono CJK)은 박스 문자를 전각으로 그려 오히려 깨진다.

    python3 deck/gen_fonts.py '가나다'   →  @font-face 를 표준 출력으로
"""
import base64, io, os, sys

FAMILY = 'DeckMono'

# 설치된 파일 이름이 배포판마다 다르다. 처음 있는 것을 쓴다.
CANDIDATES = [
    '/usr/share/fonts/truetype/nanum/D2Coding-Ver1.3.2-20180524-ligature.ttf',
    '/usr/share/fonts/truetype/nanum/D2Coding-Ver1.3.2-20180524.ttf',
    '/usr/share/fonts/truetype/D2Coding/D2Coding-Ver1.3.2-20180524.ttf',
    os.path.expanduser('~/.fonts/D2Coding.ttf'),
]

# 요청 글자에 더해 항상 싣는 범위 — ASCII 전체, 박스 그리기, 블록·음영, 화살표.
# 기록이 바뀌어 새 박스 모양이 나와도 글꼴을 다시 만들 필요가 없게 한다.
ALWAYS = list(range(0x20, 0x7F)) + list(range(0x2500, 0x25A0)) + \
         list(range(0x2190, 0x2194)) + [0x25B6, 0x25C0, 0x00B7, 0x00D7, 0x2014, 0x2026]


def source_path():
    for p in CANDIDATES:
        if os.path.exists(p):
            return p
    raise SystemExit('D2Coding 글꼴 파일이 없다 — apt install fonts-nanum-coding 또는 CANDIDATES 를 고칠 것')


def _cells(cp):
    """check_deck.js 의 cells2 와 같은 규칙. 한글·CJK 만 두 칸."""
    wide = (0x1100 <= cp <= 0x115F) or (0x2E80 <= cp <= 0x303E) or (0x3041 <= cp <= 0x33FF) \
        or (0x3400 <= cp <= 0x4DBF) or (0x4E00 <= cp <= 0x9FFF) or (0xAC00 <= cp <= 0xD7A3) \
        or (0xF900 <= cp <= 0xFAFF) or (0xFF00 <= cp <= 0xFF60)
    return 2 if wide else 1


def unsupported(text):
    """원본 글꼴에 아예 없는 글자들 — 이모지·변형 선택자 따위. 빌드가 경고로만 남긴다."""
    from fontTools.ttLib import TTFont
    cmap = TTFont(source_path(), lazy=True).getBestCmap()
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
    # 계약 검사: 반각 500 · 전각 1000 (upm 1000). 하나라도 어긋나면 상자가 깨진다.
    hmtx, upm = font['hmtx'], font['head'].unitsPerEm
    sub_cmap = font.getBestCmap()
    for cp, g in sub_cmap.items():
        adv = hmtx[g][0]
        if adv * 2 != upm * _cells(cp):
            raise SystemExit('U+%04X 의 폭 %d 이 칸 규칙(%d칸)과 다르다' % (cp, adv, _cells(cp)))
    font.flavor = 'woff2'          # opt.flavor 는 save_font 전용이라 여기서 다시 지정해야 woff2 로 압축된다
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def font_face_css(text):
    b64 = base64.b64encode(subset_woff2(text)).decode('ascii')
    return ('  /* D2Coding (네이버, SIL OFL 1.1) 서브셋 — 이 덱의 코드·캡처에 쓰인 글자만 담았다 */\n'
            '  @font-face{font-family:"%s"; font-style:normal; font-weight:400; font-display:block;\n'
            '    src:url(data:font/woff2;base64,%s) format("woff2")}\n' % (FAMILY, b64))


if __name__ == '__main__':
    sys.stdout.write(font_face_css(' '.join(sys.argv[1:])))
