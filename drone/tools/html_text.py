# -*- coding: utf-8 -*-
"""html_text.py — 받은 문서를 인용할 수 있는 텍스트로 바꾼다.

    python3 tools/html_text.py 파일.html > 파일.txt
    python3 tools/html_text.py --ecfr part107.xml > part107.txt
    python3 tools/html_text.py --law 항공안전법.xml > law.txt

goevo/tools/html_text.py 에서 물려받아 넓혔다(PLAN.md §3.1). 드론
덱은 문서 사이트가 여럿이다 — docs.px4.io·mavlink.io(vitepress),
ardupilot.org·docs.blender.org(Sphinx), docs.skybrush.io(Antora),
faa.gov·easa.europa.eu(Drupal), 그리고 XML 둘(eCFR, 법제처 DRF).

  · 제목(h1–h6)과 <dt> 는 '§<TAB>제목' 한 줄이 된다. <!--CITE sec=…-->
    는 이 줄과 글자까지 같아야 한다(deck/cites.py). EASA 는 본문
    제목이 h5 라서 h5·h6 도 센다. Sphinx 의 필드 목록(<dl
    class="field-list"> 의 'Type:') 은 제목이 아니다.
  · 제목·<dt>·<section> 의 id 는 '§<TAB>#id' 줄이 된다 — 주소의
    조각(#HEARTBEAT, #bpy.types.Object.location)과 같아서, 긴 제목
    글자 대신 안정된 이름으로 가리킬 수 있다. <section id> 는 안에
    제목이 올 때만 남기고(본문이 먼저 오면 버린다), Drupal 블록
    id(block-…)는 버린다.
  · 문단·목록·표 행은 공백을 하나로 접은 한 줄. 목록은 '- ', 표의
    칸은 ' | ' 로 잇는다. <pre> 는 글자 그대로 둔다.
  · <main> 이 있으면 그 안만 읽고, script·style·nav·header·footer·
    aside·button 과 제목 옆 고리(¶, 폭 없는 공백)는 버린다. 단
    <main> 안의 <header> 는 글 머리라 남긴다(EASA 쪽 제목).

html.parser 로 한 번 훑는다. 시간 O(문서 길이), 공간 O(문서 길이).
"""
import html.parser
import re
import sys
import xml.etree.ElementTree as ET

HEAD = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'dt'}
BLOCK = {'p', 'div', 'li', 'dd', 'tr', 'blockquote', 'table', 'ul',
         'ol', 'dl', 'section', 'article', 'main', 'figure',
         'figcaption', 'caption', 'thead', 'tbody'} | HEAD
SKIP = {'script', 'style', 'nav', 'header', 'footer', 'noscript', 'svg',
        'button', 'form', 'template', 'aside', 'iframe'}
VOID = {'br', 'img', 'hr', 'meta', 'link', 'input', 'wbr', 'source'}
# 제목 옆에 붙는 고리 — 글자로 남으면 '§ 제목¶' 가 되어 인용이 어긋난다
ANCHOR_CLASS = {'headerlink', 'header-anchor', 'anchor'}
JUNK = str.maketrans('', '', '¶​﻿')


class _Text(html.parser.HTMLParser):
    def __init__(self, only_main):
        super().__init__(convert_charrefs=True)
        self.in_main = not only_main
        self.only_main = only_main
        self.skip = 0              # 버리는 요소의 깊이
        self.pre = 0
        self.buf = []              # 지금 쌓는 블록의 글자
        self.kind = None           # 'head' · 'li' · None
        self.out = []
        self.pending = []          # 제목을 기다리는 <section id>
        self.fields = []           # dl 이 필드 목록인가 (쌓기)

    def flush(self):
        text = ''.join(self.buf).translate(JUNK)
        self.buf = []
        kind, self.kind = self.kind, None
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'\s*\|\s*$', '', text)       # 표 행 끝의 칸 구분
        if not text:
            return
        if kind == 'head':
            self.out += ['§\t#' + i for i in self.pending]
            self.out.append('§\t' + text)
        else:
            self.out.append(('- ' if kind == 'li' else '') + text)
        self.pending = []

    def anchor(self, ident):
        if ident and not ident.startswith('block-'):
            self.pending.append(ident)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'main':
            self.in_main = True
        if not self.in_main:
            return
        cls = set((a.get('class') or '').split())
        # <main> 안의 <header> 는 글의 머리(EASA 의 쪽 제목)라 살린다
        drop = tag in SKIP and not (tag == 'header' and self.only_main)
        if self.skip or drop or (tag == 'a' and cls & ANCHOR_CLASS):
            if tag not in VOID:
                self.skip += 1
            return
        if tag == 'pre':
            self.flush()
            self.pre += 1
            return
        if self.pre:
            return
        if tag == 'dl':
            self.fields.append('field-list' in cls)
        if tag == 'br':
            self.buf.append(' ')
        elif tag in BLOCK:
            # li 안의 p 처럼 블록이 겹치면 바깥 앞글자를 먼저 내보낸다.
            # 목록 표시는 안쪽 첫 줄이 물려받는다.
            keep = (tag == 'p' and self.kind == 'li'
                    and not ''.join(self.buf).strip())
            self.flush()
            field = tag == 'dt' and self.fields and self.fields[-1]
            if tag in HEAD and not field:
                self.kind = 'head'
                self.anchor(a.get('id'))
            elif tag == 'li' or keep:
                self.kind = 'li'
            elif tag == 'section' or (tag == 'div'
                                      and 'section' in cls):
                self.anchor(a.get('id'))

    def handle_endtag(self, tag):
        if tag == 'main' and self.only_main:
            self.flush()
            self.in_main = False
            return
        if not self.in_main:
            return
        if self.skip:
            if tag not in VOID:
                self.skip -= 1
            return
        if tag == 'pre':
            self.pre -= 1
            text = ''.join(self.buf)
            self.buf = []
            self.out.append(text.strip('\n'))
            return
        if self.pre:
            return
        if tag == 'dl' and self.fields:
            self.fields.pop()
        if tag in ('td', 'th'):
            self.buf.append(' | ')
        elif tag in BLOCK:
            self.flush()

    def handle_data(self, data):
        if self.in_main and not self.skip:
            self.buf.append(data)


def convert(text):
    """HTML 한 편 → 텍스트(줄 단위). 끝에 개행 하나."""
    p = _Text(only_main='<main' in text)
    p.feed(text)
    p.close()
    p.flush()
    return '\n'.join(l for l in p.out if l.strip()) + '\n'


def convert_md(text):
    """마크다운(README) → '#' 제목만 '§' 줄로 바꾼다."""
    out = []
    for line in text.split('\n'):
        m = re.match(r'^#{1,6}\s+(.*?)\s*#*\s*$', line)
        out.append('§\t' + m.group(1) if m else line.rstrip())
    return '\n'.join(out).rstrip('\n') + '\n'


def _flat(s):
    return re.sub(r'\s+', ' ', s or '').strip()


# eCFR XML(versioner API)의 요소 — 대문자 태그를 html.parser 가
# 소문자로 바꿔 준다. HEAD 는 부·절·조의 제목, DIV8 의 N 은 조 번호.
_ECFR_BLOCK = {'p', 'fp', 'auth', 'source', 'cita', 'note', 'extract',
               'ednote', 'secauth', 'appro', 'div5', 'div6', 'div7',
               'div8', 'div9'}


class _Ecfr(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.buf, self.out, self.head = [], [], False

    def flush(self):
        text = _flat(''.join(self.buf))
        self.buf = []
        if text:
            self.out.append(('§\t' if self.head else '') + text)
        self.head = False

    def handle_starttag(self, tag, attrs):
        if tag == 'head' or tag in _ECFR_BLOCK:
            self.flush()
        if tag == 'head':
            self.head = True
        if tag == 'div8' and dict(attrs).get('n'):
            self.out.append('§\t#' + dict(attrs)['n'])

    def handle_endtag(self, tag):
        if tag == 'head' or tag in _ECFR_BLOCK:
            self.flush()
        elif tag == 'hed':
            self.buf.append(' ')       # 'Authority:' 와 본문 사이

    def handle_data(self, data):
        self.buf.append(data)


def convert_ecfr(text):
    """eCFR 조문 XML → '§ 107.29 …' 제목 줄 + '#107.29' 절 줄 + 문단."""
    p = _Ecfr()
    p.feed(re.sub(r'^<\?xml[^>]*\?>', '', text))
    p.close()
    p.flush()
    return '\n'.join(p.out) + '\n'


_ARTICLE = re.compile(r'^(제\d+조(?:의\d+)?)(\([^)]*\))?\s*(.*)$', re.S)


def _ymd(s):
    s = (s or '').strip()
    return '%s-%s-%s' % (s[:4], s[4:6], s[6:8]) if len(s) == 8 else s


def convert_law(text):
    """법제처 DRF lawService XML → 장·조문 절 줄 + 항·호·목 줄.

    조문 하나는 '§ 제129조' 와 '§ 제129조(제목)' 두 줄로 연다 — 번호
    만으로도, 제목까지로도 인용할 수 있다. 부칙·별표는 싣지 않는다
    (덱은 본문 조문만 인용한다). O(조문 수).
    """
    root = ET.fromstring(text.encode('utf-8'))
    info = root.find('기본정보')
    out = ['§\t' + _flat(info.findtext('법령명_한글'))]
    out.append('공포 %s · 공포번호 제%s호 · 시행 %s' % (
        _ymd(info.findtext('공포일자')),
        _flat(info.findtext('공포번호')),
        _ymd(info.findtext('시행일자'))))
    for unit in root.iter('조문단위'):
        body = _flat(unit.findtext('조문내용'))
        if unit.findtext('조문여부') == '전문':
            # 장·절 제목. 끝의 '<개정 2023.4.18>' 같은 꼬리는 뗀다.
            out.append('§\t' + re.sub(r'\s*<[^>]*>$', '', body))
            continue
        m = _ARTICLE.match(body)
        if m:
            out.append('§\t' + m.group(1))
            if m.group(2):
                out.append('§\t' + m.group(1) + m.group(2))
            body = m.group(3)
        if body:
            out.append(body)
        for el in unit.iter():
            if el.tag in ('항내용', '호내용', '목내용', '조문참고자료'):
                t = _flat(el.text)
                if t:
                    out.append(t)
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    args = sys.argv[1:]
    mode = args.pop(0) if args and args[0].startswith('--') else ''
    with open(args[0], encoding='utf-8') as f:
        src = f.read()
    fn = {'--ecfr': convert_ecfr, '--law': convert_law,
          '--md': convert_md}.get(mode, convert)
    sys.stdout.write(fn(src))
