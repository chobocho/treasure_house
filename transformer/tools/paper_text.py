# -*- coding: utf-8 -*-
"""논문 본문 받기 — ar5iv HTML 을 절 제목 줄이 박힌 텍스트로.

    python3 tools/paper_text.py --fetch-all data/papers.tsv
    python3 tools/paper_text.py --fetch vaswani2017 1706.03762
    python3 tools/paper_text.py --grep vaswani2017 'warmup'

왜 받아 두는가: 논문에서 옮긴 숫자(d_model 512, 워밍업 4000)는
기억으로 적으면 반드시 어딘가 틀린다. 원문을 papers/<키>.txt 로
받아 두고 거기서 인용한다. 받은 파일은 캐시라 커밋하지 않는다.

출력 꼴 — check_claims.py 가 이 꼴에 기댄다:

    # key<TAB>arxiv-id<TAB>제목<TAB>v1 날짜
    3.2.1<TAB>Scaled Dot-Product Attention     ← 절 제목 줄
    본문 문단 한 줄                              ← 문단 하나 = 한 줄
    | N | d_model | ...                         ← 표의 행
    수식은 $…$ 안에 LaTeX 원문(alttext) 그대로

arXiv 에 없는 문서(OpenAI 의 GPT-1·2 보고서 같은 것)는 여기서 받지
않는다. papers.tsv 의 arxiv-id 칸이 '-' 이면 건너뛰고, 그 문서의
주장은 claims.md 에 URL 과 확인 방법을 따로 적는다.
시간·공간 O(HTML 크기).
"""
import html.parser
import io
import os
import re
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS = os.path.join(BASE, 'papers')
UA = 'treasure_house-deck/1.0 (+github.com/chobocho/treasure_house)'
HEADS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')


def get(url):
    """한 번 받는다. 실패하면 쉬었다가 두 번 더 — 서버 탓이 흔하다."""
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for n in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode('utf-8', 'replace')
        except OSError:
            if n == 2:
                raise
            time.sleep(3 * (n + 1))
    return ''


class Text(html.parser.HTMLParser):
    """ar5iv 의 LaTeXML 마크업만 안다. 다른 HTML 에는 쓰지 말 것."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []          # 완성된 줄
        self.buf = []          # 지금 모으는 줄
        self.skip = 0          # <script>·<math> 안쪽 깊이
        self.head = None       # 제목을 모으는 중이면 태그 이름
        self.tag_num = None    # 제목의 절 번호
        self.in_tag = False
        self.row = None        # 표의 한 행
        self.cell = None

    def flush(self):
        s = re.sub(r'\s+', ' ', ''.join(self.buf)).strip()
        if s:
            self.out.append(s)
        self.buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get('class') or ''
        if self.skip:
            if tag in ('math', 'script', 'style'):
                self.skip += 1
            return
        if tag in ('script', 'style', 'nav', 'footer'):
            self.skip = 1
            return
        if tag == 'math':
            alt = a.get('alttext', '')
            self.target().append(' $%s$ ' % alt)
            self.skip = 1
            return
        if tag in HEADS and 'ltx_title' in cls:
            self.flush()
            self.head, self.tag_num = tag, None
            return
        if tag == 'span' and 'ltx_tag' in cls and self.head:
            self.in_tag = True
            self.tag_num = ''
            return
        if tag == 'tr' and 'ltx_equation' not in cls:
            self.flush()
            self.row = []
            return
        if tag in ('td', 'th') and self.row is not None:
            self.cell = []
            return
        if tag in ('p', 'figcaption', 'li', 'br', 'div'):
            if self.row is None:
                self.flush()

    def handle_endtag(self, tag):
        if self.skip:
            if tag in ('math', 'script', 'style', 'nav', 'footer'):
                self.skip -= 1
            return
        if tag == 'span' and self.in_tag:
            self.in_tag = False
            return
        if self.head and tag == self.head:
            title = re.sub(r'\s+', ' ', ''.join(self.buf)).strip()
            num = (self.tag_num or '').strip().rstrip('.')
            num = re.sub(r'^(Appendix|Section)\s+', '', num)
            self.out.append('%s\t%s' % (num or '-', title))
            self.buf, self.head = [], None
            return
        if tag in ('td', 'th') and self.cell is not None:
            cell = re.sub(r'\s+', ' ', ''.join(self.cell)).strip()
            self.row.append(cell)
            self.cell = None
            return
        if tag == 'tr' and self.row is not None:
            if any(self.row):
                self.out.append('| ' + ' | '.join(self.row) + ' |')
            self.row = None
            return
        if tag in ('p', 'figcaption', 'li') and self.row is None:
            self.flush()

    def target(self):
        if self.cell is not None:
            return self.cell
        return self.buf

    def handle_data(self, data):
        if self.skip:
            return
        if self.in_tag:
            self.tag_num += data
            return
        self.target().append(data)


def to_text(page):
    art = re.search(r'<article.*?</article>', page, re.S)
    p = Text()
    p.feed(art.group(0) if art else page)
    p.flush()
    return p.out


def meta(arxiv):
    """arXiv API 에서 (제목, 첫 판 v1 이 올라온 날).

    제목을 본문에서 줍지 않는 까닭: ar5iv 의 첫 제목 줄이 각주나
    'Abstract' 인 논문이 여럿 있었다(3단계 조사에서 9편).
    """
    xml = get('http://export.arxiv.org/api/query?id_list=%s' % arxiv)
    ent = re.search(r'<entry>(.*?)</entry>', xml, re.S)
    body = ent.group(1) if ent else ''
    t = re.search(r'<title>(.*?)</title>', body, re.S)
    d = re.search(r'<published>(\d{4}-\d\d-\d\d)', body)
    title = re.sub(r'\s+', ' ', t.group(1)).strip() if t else '?'
    return title, d.group(1) if d else '?'


def fetch(key, arxiv, force=False):
    dst = os.path.join(PAPERS, key + '.txt')
    if os.path.exists(dst) and not force:
        return dst, False
    lines = to_text(get('https://ar5iv.labs.arxiv.org/html/%s' % arxiv))
    title, date = meta(arxiv)
    head = '# %s\t%s\t%s\t%s' % (key, arxiv, title, date)
    if not os.path.isdir(PAPERS):
        os.makedirs(PAPERS)
    with io.open(dst, 'w', encoding='utf-8', newline='\n') as f:
        f.write(head + '\n' + '\n'.join(lines) + '\n')
    return dst, True


def rows(tsv):
    head = None
    for line in io.open(tsv, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line.strip() or line.startswith('#'):
            continue
        cols = line.split('\t')
        if head is None:
            head = cols
            continue
        yield dict(zip(head, cols))


def main(argv):
    if argv[:1] == ['--fetch'] and len(argv) >= 3:
        dst, new = fetch(argv[1], argv[2], force='--force' in argv)
        print('%s %s' % ('받음' if new else '있음', dst))
        return 0
    if argv[:1] == ['--fetch-all'] and len(argv) >= 2:
        bad = 0
        for r in rows(argv[1]):
            aid = r.get('arxiv-id', '-').strip()
            if not aid or aid == '-':
                continue
            try:
                dst, new = fetch(r['key'], aid)
                if new:
                    print('  받음 %s' % dst)
                    time.sleep(2)         # 서버에 예의를 지킨다
            except OSError as e:
                bad += 1
                print('  ✗ %s (%s): %s' % (r['key'], aid, e))
        print('논문 본문 — 실패 %d건' % bad)
        return 1 if bad else 0
    if argv[:1] == ['--grep'] and len(argv) >= 3:
        p = os.path.join(PAPERS, argv[1] + '.txt')
        sec = '-'
        for line in io.open(p, encoding='utf-8'):
            # '-' 는 번호 없는 문단 제목(Residual Dropout 같은 것)이다.
            # 그 줄에서 절을 바꾸면 5.4 의 문단이 '-' 로 보인다.
            if re.match(r'^[\w.]+\t', line):
                sec = line.split('\t')[0]
            if re.search(argv[2], line, re.I):
                print('[%s] %s' % (sec, line.rstrip()[:300]))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
