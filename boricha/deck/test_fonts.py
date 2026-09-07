# -*- coding: utf-8 -*-
"""test_fonts.py — 덱에 내장하는 고정폭 글꼴 서브셋의 계약.

터미널 캡처는 "한글 = 2칸, 나머지 = 1칸"이라는 터미널의 칸 규칙 위에 그려진 그림이다.
보는 쪽 기기에 어떤 글꼴이 깔려 있든 그 규칙이 지켜져야 상자와 판이 안 깨진다.
그래서 글꼴을 덱에 넣고, 여기서 그 글꼴이 규칙을 지키는지 확인한다.

    python3 deck/test_fonts.py
"""
import base64, io, os, re, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def cells(ch):
    """check_deck.js 의 cells2 와 같은 규칙 — 한글·CJK 만 두 칸."""
    c = ord(ch)
    wide = (0x1100 <= c <= 0x115F) or (0x2E80 <= c <= 0x303E) or (0x3041 <= c <= 0x33FF) \
        or (0x3400 <= c <= 0x4DBF) or (0x4E00 <= c <= 0x9FFF) or (0xAC00 <= c <= 0xD7A3) \
        or (0xF900 <= c <= 0xFAFF) or (0xFF00 <= c <= 0xFF60)
    return 2 if wide else 1


class GenFonts(unittest.TestCase):
    def setUp(self):
        import gen_fonts
        self.gf = gen_fonts

    def _load(self, css):
        from fontTools.ttLib import TTFont
        m = re.search(r'url\(data:font/woff2;base64,([A-Za-z0-9+/=]+)\)', css)
        self.assertIsNotNone(m, 'woff2 data URI 가 없다')
        return TTFont(io.BytesIO(base64.b64decode(m.group(1))))

    def test_css_shape(self):
        css = self.gf.font_face_css('가')
        m = re.search(r'base64,([A-Za-z0-9+/=]{8})', css)
        self.assertEqual(base64.b64decode(m.group(1) + '==')[:4], b'wOF2', 'woff2 로 압축돼야 한다')
        self.assertIn('@font-face', css)
        self.assertIn('font-family:"DeckMono"', css)
        self.assertIn('format("woff2")', css)

    def test_covers_requested_and_fixed_ranges(self):
        text = '테트리스 ░█│─╭╮╯╰ ↑↓ ·×—… abc 09'
        ft = self._load(self.gf.font_face_css(text))
        cmap = ft.getBestCmap()
        for ch in text.replace(' ', '') + ' ':
            self.assertIn(ord(ch), cmap, '빠진 글자 %r' % ch)
        # 요청에 없어도 항상 실리는 것: ASCII 전체와 박스·블록 문자 전체
        for cp in list(range(0x20, 0x7F)) + list(range(0x2500, 0x25A0)):
            self.assertIn(cp, cmap, '기본 범위 누락 U+%04X' % cp)

    def test_advance_widths_follow_cell_rule(self):
        text = '가나다라 한글 ░█│─╭╮╯╰ ↑↓ ·×—… abc'
        ft = self._load(self.gf.font_face_css(text))
        cmap, hmtx, upm = ft.getBestCmap(), ft['hmtx'], ft['head'].unitsPerEm
        for ch in text.replace(' ', ''):
            adv = hmtx[cmap[ord(ch)]][0]
            self.assertEqual(adv * 2, upm * cells(ch), '%r 의 폭 %d (upm %d)' % (ch, adv, upm))

    def test_empty_text_still_builds(self):
        ft = self._load(self.gf.font_face_css(''))
        self.assertIn(ord('A'), ft.getBestCmap())

    def test_non_font_chars_are_ignored(self):
        # 글꼴에 없는 글자(변형 선택자·이모지)는 조용히 건너뛴다
        css = self.gf.font_face_css('︎🍵 가')
        self.assertIn(ord('가'), self._load(css).getBestCmap())

    def test_size_is_small(self):
        css = self.gf.font_face_css('가' * 1)
        self.assertLess(len(css), 60_000)


class BuiltDeck(unittest.TestCase):
    """조립된 덱이 글꼴을 싣고, 코드·터미널 글꼴 목록이 그것을 맨 앞에 두는지."""
    DECK = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'Go_Bubble_Tea_테트리스_만들기.html')

    def setUp(self):
        if not os.path.exists(self.DECK):
            self.skipTest('덱이 아직 없다')
        self.html = io.open(self.DECK, encoding='utf-8').read()

    def test_font_face_present_once(self):
        self.assertEqual(self.html.count('@font-face{font-family:"DeckMono"'), 1)

    def test_font_is_really_woff2(self):
        m = re.search(r'url\(data:font/woff2;base64,([A-Za-z0-9+/=]{8})', self.html)
        self.assertEqual(base64.b64decode(m.group(1) + '==')[:4], b'wOF2')

    def test_code_font_stacks_start_with_deckmono(self):
        style = self.html.split('</style>')[0]
        stacks = re.findall(r'font-family:([^;}]*monospace[^;}]*)', style)
        self.assertGreater(len(stacks), 3)
        for s in stacks:
            self.assertTrue(s.startswith('"DeckMono"'), s)

    def test_every_code_char_is_in_font(self):
        import html as H
        from fontTools.ttLib import TTFont
        m = re.search(r'url\(data:font/woff2;base64,([A-Za-z0-9+/=]+)\)', self.html)
        cmap = TTFont(io.BytesIO(base64.b64decode(m.group(1)))).getBestCmap()
        used = set()
        for m in re.finditer(r'<(?:code|pre)\b[^>]*>([\s\S]*?)</(?:code|pre)>', self.html):
            used |= set(H.unescape(re.sub(r'<[^>]+>', '', m.group(1))))
        for m in re.finditer(r'window\.__FRAMES=(\{.*?\});</script>', self.html):
            used |= set(H.unescape(re.sub(r'<[^>]+>', '', m.group(1))))
        # 원본 글꼴에 아예 없는 글자(이모지 등)만 빠져 있어야 한다
        import gen_fonts
        allowed = set(gen_fonts.unsupported(''.join(used)))
        missing = sorted(c for c in used if ord(c) > 0x20 and ord(c) not in cmap and c not in allowed)
        self.assertEqual(missing, [], '글꼴에 없는 글자: %r' % ''.join(missing))


if __name__ == '__main__':
    unittest.main()
