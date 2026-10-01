# -*- coding: utf-8 -*-
"""html_text.py — go.dev 의 HTML 문서를 인용할 수 있는 텍스트로 바꾼다.

    python3 tools/html_text.py 파일.html > 파일.txt

git 덱의 adoc_text.py 자리다(PLAN.md §3.1). 규칙은 넷뿐이다.

  · 제목(h1–h6)과 릴리스 노트의 패키지 이름(<dt>)은 '§<TAB>제목' 한 줄이
    된다. <!--CITE sec=…--> 는 이 줄과 글자까지 같아야 한다(deck/cites.py).
    노트에는 번호가 없으므로 제목 글자로 가리킨다.
  · 문단·목록·표 행은 공백을 하나로 접어 한 줄로 만든다. 목록은 '- ',
    표의 칸은 ' | ' 로 잇는다. 그래야 "go1.22.1 (released …) includes …"
    같은 줄을 make_data.py 가 정규식 한 줄로 읽는다.
  · <pre> 는 글자 그대로 둔다 — 코드와 명령 출력은 공백이 뜻이다.
  · <main> 이 있으면 그 안만 읽고, script·style·nav·header·footer·
    주석은 버린다. 명세(go_spec.html)는 맨 앞의 JSON 주석에 제목과
    'Language version go1.N (날짜)' 가 있어 그것만은 살린다.

html.parser 하나로 한 번 훑는다. 시간 O(문서 길이), 공간 O(문서 길이).
"""
import html.parser
import json
import re
import sys

HEAD = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'dt'}
BLOCK = {'p', 'div', 'li', 'dd', 'tr', 'blockquote', 'table', 'ul', 'ol',
         'dl', 'section', 'article', 'main', 'figure', 'figcaption',
         'caption', 'thead', 'tbody'} | HEAD
SKIP = {'script', 'style', 'nav', 'header', 'footer', 'noscript', 'svg',
        'button', 'form', 'template'}
VOID = {'br', 'img', 'hr', 'meta', 'link', 'input', 'wbr', 'source'}


class _Text(html.parser.HTMLParser):
    def __init__(self, only_main):
        super().__init__(convert_charrefs=True)
        self.only_main = only_main
        self.in_main = not only_main
        self.skip = 0              # 버리는 요소의 깊이
        self.pre = 0
        self.buf = []              # 지금 쌓는 블록의 글자
        self.kind = None           # 'head' · 'li' · None
        self.out = []

    # -- 블록 하나를 닫아 줄로 내보낸다
    def flush(self):
        text = ''.join(self.buf)
        self.buf = []
        kind, self.kind = self.kind, None
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'\s*\|\s*$', '', text)          # 표 행 끝의 칸 구분
        if not text:
            return
        if kind == 'head':
            self.out.append('§\t' + text)
        elif kind == 'li':
            self.out.append('- ' + text)
        else:
            self.out.append(text)

    def handle_starttag(self, tag, attrs):
        if tag == 'main':
            self.in_main = True
        if not self.in_main:
            return
        if self.skip or tag in SKIP:
            if tag not in VOID:
                self.skip += 1
            return
        if tag == 'pre':
            self.flush()
            self.pre += 1
            return
        if self.pre:
            return
        if tag == 'br':
            self.buf.append(' ')
        elif tag in BLOCK:
            # li 안의 p 처럼 블록이 겹치면, 바깥 블록의 앞글자를 먼저 내보낸다.
            # 목록 표시는 안쪽 첫 줄이 물려받는다.
            keep = 'li' if (tag == 'p' and self.kind == 'li'
                            and not ''.join(self.buf).strip()) else None
            self.flush()
            if tag in HEAD:
                self.kind = 'head'
            elif tag == 'li' or keep:
                self.kind = 'li'
        elif tag in ('td', 'th'):
            pass

    def handle_endtag(self, tag):
        if tag == 'main' and self.only_main:
            self.flush()
            self.in_main = False
            return
        if not self.in_main:
            return
        if self.skip:
            if tag in SKIP or tag not in VOID:
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
        if tag in ('td', 'th'):
            self.buf.append(' | ')
        elif tag in BLOCK:
            self.flush()

    def handle_data(self, data):
        if self.in_main and not self.skip:
            self.buf.append(data)


def _spec_header(text):
    """go_spec.html 맨 앞의 <!--{ JSON }--> → (제목 줄들, 나머지 본문)."""
    m = re.match(r'\s*<!--(\{.*?\})-->', text, re.S)
    if not m:
        return [], text
    try:
        meta = json.loads(m.group(1))
    except ValueError:
        return [], text
    lines = []
    if meta.get('Title'):
        lines.append('§\t' + meta['Title'])
    if meta.get('Subtitle'):
        lines.append(meta['Subtitle'])
    return lines, text[m.end():]


def convert(text):
    """HTML 한 편 → 텍스트(줄 단위). 끝에 개행 하나."""
    head, body = _spec_header(text)
    p = _Text(only_main='<main' in body)
    p.feed(body)
    p.close()
    p.flush()
    lines = head + [l for l in p.out if l.strip()]
    return '\n'.join(lines) + '\n'


def convert_md(text):
    """마크다운(제안 저장소 README) → '#' 제목만 '§' 줄로 바꾼다."""
    out = []
    for line in text.split('\n'):
        m = re.match(r'^#{1,6}\s+(.*?)\s*#*\s*$', line)
        out.append('§\t' + m.group(1) if m else line.rstrip())
    return '\n'.join(out).rstrip('\n') + '\n'


if __name__ == '__main__':
    with open(sys.argv[1], encoding='utf-8') as f:
        src = f.read()
    sys.stdout.write(convert_md(src) if sys.argv[1].endswith('.md')
                     else convert(src))
