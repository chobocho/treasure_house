# -*- coding: utf-8 -*-
"""test_embed_mono_font.py — 덱에 내장하는 고정폭 글꼴(DeckMono)의 계약.

아스키 표·터미널 캡처는 "한글 = 2칸, 나머지 = 1칸"이라는 칸 규칙 위에 그려진 그림이다.
보는 쪽 기기에 어떤 글꼴이 있든 그 규칙이 지켜져야 표가 안 깨진다. 그래서 덱마다
D2Coding 서브셋을 싣고, 여기서 스크립트가 그 규칙과 파일 보존 약속을 지키는지 확인한다.

    python3 tools/test_embed_mono_font.py
"""
import base64, io, os, re, sys, unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import embed_mono_font as em

STACK = '"DeckMono","D2Coding",monospace'
# 실제 덱의 최소 골격 — <style> 하나, 고정폭 목록 둘, 산문 한글과 코드 한글이 다르다.
DOC = ('<!DOCTYPE html>\n<html><head><meta charset="utf-8">\n<style>\n'
       'body{font-family:sans-serif}\n'
       'pre{font-family:%s}\n'
       'code{font-family:%s}\n'
       '</style></head><body>\n'
       '<p>산문에만 나오는 글자 — 뷁</p>\n'
       '<pre><code data-lang="c">int a; /* 코드 &lt;주석&gt; */</code></pre>\n'
       '<div class="term"><span class="p">$</span> 실행 ┌─┐</div>\n'
       '</body></html>\n') % (STACK, STACK)


def _font(css):
    from fontTools.ttLib import TTFont
    m = re.search(r'url\(data:font/woff2;base64,([A-Za-z0-9+/=]+)\)', css)
    assert m, 'woff2 data URI 가 없다'
    return TTFont(io.BytesIO(base64.b64decode(m.group(1))))


class MonoText(unittest.TestCase):
    def test_collects_only_monospace_elements(self):
        t = em.mono_text(DOC)
        self.assertIn('코드', t)
        self.assertIn('실행', t)
        self.assertIn('┌', t)
        self.assertNotIn('뷁', t, '산문의 글자는 싣지 않는다')

    def test_unescapes_entities_and_strips_tags(self):
        t = em.mono_text(DOC)
        self.assertIn('<주석>', t)
        self.assertNotIn('&lt;', t)
        self.assertNotIn('span', t)

    def test_empty(self):
        self.assertEqual(em.mono_text(''), '')
        self.assertEqual(em.mono_text('<p>글</p>'), '')


class Subset(unittest.TestCase):
    def test_woff2_and_always_ranges(self):
        data = em.subset_woff2('')
        self.assertEqual(data[:4], b'wOF2')
        from fontTools.ttLib import TTFont
        cmap = TTFont(io.BytesIO(data)).getBestCmap()
        for cp in list(range(0x20, 0x7F)) + [0x2500, 0x2502, 0x250C, 0x2588, 0x2591, 0x2192]:
            self.assertIn(cp, cmap, 'U+%04X 는 항상 실어야 한다' % cp)
        self.assertNotIn(0xAC00, cmap, '요청하지 않은 한글은 싣지 않는다')

    def test_width_contract(self):
        from fontTools.ttLib import TTFont
        f = TTFont(io.BytesIO(em.subset_woff2('가')))
        cmap, hmtx, upm = f.getBestCmap(), f['hmtx'], f['head'].unitsPerEm
        self.assertEqual(hmtx[cmap[ord('A')]][0] * 2, upm)        # 반각
        self.assertEqual(hmtx[cmap[ord('가')]][0], upm)           # 전각
        self.assertEqual(hmtx[cmap[0x2502]][0] * 2, upm)          # 박스 문자도 반각

    def test_width_violation_aborts(self):
        # 칸 규칙 함수를 망가뜨리면 검사가 잡아야 한다 — 실제 D2Coding 은 어기지 않으므로 이렇게 흉내낸다.
        with mock.patch.object(em, '_cells', lambda cp: 1):
            with self.assertRaises(SystemExit):
                em.subset_woff2('가')

    def test_unsupported_chars(self):
        self.assertEqual(em.unsupported('가A😀'), ['😀'])
        self.assertEqual(em.unsupported(''), [])

    def test_font_face_css_shape(self):
        css = em.font_face_css('가')
        self.assertIn('@font-face{font-family:"DeckMono"', css)
        self.assertIn('format("woff2")', css)
        self.assertIn(ord('가'), _font(css).getBestCmap())


class Embed(unittest.TestCase):
    def test_inserts_after_style_when_missing(self):
        out = em.embed(DOC)
        self.assertEqual(out.count('@font-face{font-family:"DeckMono"'), 1)
        self.assertTrue(out.startswith(DOC.split('<style>\n')[0] + '<style>\n'))
        self.assertTrue(out.endswith('body{font-family:sans-serif}\n' + DOC.split('body{font-family:sans-serif}\n')[1]),
                        '@font-face 외에는 바이트 하나 바뀌면 안 된다')
        self.assertIn(ord('코'), _font(out).getBestCmap())

    def test_replaces_existing_and_is_idempotent(self):
        once = em.embed(DOC)
        twice = em.embed(once)
        self.assertEqual(once, twice)
        self.assertEqual(twice.count('@font-face'), 1)

    def test_no_build_timestamp(self):
        # 다른 날 다시 돌려도 바이트가 같아야 diff 가 조용하다 — 저장 시각을 head 에 새로 찍으면 안 된다.
        from fontTools.ttLib import TTFont
        src = TTFont(em.source_path(), lazy=True)
        self.assertEqual(_font(em.embed(DOC))['head'].modified, src['head'].modified)
        src.close()

    def test_replace_tracks_new_glyphs(self):
        old = em.embed(DOC)
        new = em.embed(old.replace('코드', '코드 새글자'))
        cmap = _font(new).getBestCmap()
        self.assertIn(ord('새'), cmap)
        self.assertEqual(new.count('@font-face'), 1)

    def test_preserves_crlf(self):
        crlf = DOC.replace('\n', '\r\n')
        out = em.embed(crlf)
        self.assertNotIn('\n', out.replace('\r\n', ''), 'LF 가 새로 섞이면 안 된다')
        self.assertEqual(out.count('\r\n'), crlf.count('\r\n') + out.count('@font-face') * 3)

    def test_no_style_raises(self):
        with self.assertRaises(ValueError):
            em.embed('<html><body><pre>x</pre></body></html>')


class Check(unittest.TestCase):
    def test_ok_after_embed(self):
        self.assertEqual(em.check(em.embed(DOC)), [])

    def test_missing_font(self):
        probs = em.check(DOC)
        self.assertTrue(any('@font-face' in p for p in probs), probs)

    def test_missing_glyph(self):
        out = em.embed(DOC).replace('코드', '코드 낯선')
        probs = em.check(out)
        self.assertTrue(any('낯' in p and '선' in p for p in probs), probs)

    def test_bad_stack(self):
        out = em.embed(DOC).replace('code{font-family:%s}' % STACK, 'code{font-family:Consolas,monospace}')
        probs = em.check(out)
        self.assertTrue(any('DeckMono' in p and '1' in p for p in probs), probs)

    def test_unsupported_is_not_a_problem(self):
        # 이모지는 D2Coding 에 없다 — 실을 수 없으니 오류가 아니라 경고 대상이다.
        out = em.embed(DOC.replace('실행', '실행 😀'))
        self.assertEqual(em.check(out), [])


if __name__ == '__main__':
    unittest.main(verbosity=1)
