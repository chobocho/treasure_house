# -*- coding: utf-8 -*-
"""doc_text.py — 위키·마크다운 문서를 인용할 수 있는 글로 바꾼다.

    python3 tools/doc_text.py --all   # data/docs.tsv → sources/docs/
    python3 tools/doc_text.py --pin   # 빈 revid 를 지금 것으로 채움

문서를 근거로 쓴 장(b 등급)은 claims.md 에 "그 문서의 몇 절" 을
적는다. 절 번호가 기억이 아니라 같은 규칙에서 나와야 다음 사람이
되짚을 수 있다. 그래서 제목 줄은 전부 `절번호<TAB>제목` 한 줄이 되고,
나머지 꾸밈(굵게·링크·틀·각주)은 걷어 낸다. 코드 블록은 그대로 둔다.

두 가지 원천이 있다.
  mediawiki — wiki.termux.com. API 의 action=parse 에 oldid 를 주면
              **그 리비전** 이 온다. 그래서 revid 가 곧 핀이다.
  md        — GitHub 위키·README. 저장소를 data/repos.tsv 로 핀 고정해
              두고 그 커밋에서 읽는다(deck/srcpin.py).
받은 원문(JSON)은 sources/docs/raw/ 에 남겨 다시 묻지 않는다.

시간 O(문서 길이).
"""
import datetime
import hashlib
import html
import html.parser
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(BASE, 'sources', 'docs')
RAW = os.path.join(DOCS, 'raw')
WIKI_API = 'https://wiki.termux.com/api.php'
UA = 'treasure-house-termux-deck'


class Numberer(object):
    """제목 깊이 → '1.2.3'. 깊이를 건너뛰어도(## 다음 ####) 한 칸만
    내려간다 — 번호에 빈 자리(1.0.1)가 생기지 않게. 깊은 제목 뒤에
    얕은 제목이 와도(### 다음 ##) 같은 자리의 번호를 이어 받는다 —
    안 그러면 1.1 이 두 번 나온다(Build-environment.md 에서 실제로)."""

    def __init__(self):
        self.stack = []          # [(원래 깊이, 번호)]
        self.last = {}           # 자리(0부터) → 그 자리의 마지막 번호

    def next(self, level):
        while self.stack and self.stack[-1][0] > level:
            self.stack.pop()
        if self.stack and self.stack[-1][0] == level:
            d, n = self.stack.pop()
            self.stack.append((d, n + 1))
        else:
            pos = len(self.stack)
            self.stack.append((level, self.last.get(pos, 0) + 1))
        pos = len(self.stack) - 1
        self.last[pos] = self.stack[-1][1]
        # 이 자리가 바뀌었으니 더 깊은 자리의 기억은 버린다
        for deeper in [j for j in self.last if j > pos]:
            del self.last[deeper]
        return '.'.join(str(n) for _d, n in self.stack)


def _inline_wiki(s):
    s = re.sub(r'<ref[^>]*/>|<ref[^>]*>.*?</ref>', '', s)
    s = re.sub(r"'''(.*?)'''", r'\1', s)
    s = re.sub(r"''(.*?)''", r'\1', s)
    s = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', s)
    s = re.sub(r'\[(https?://\S+) ([^\]]+)\]', r'\2 (\1)', s)
    s = re.sub(r'\[(https?://[^\]\s]+)\]', r'\1', s)
    s = re.sub(r'<code>(.*?)</code>', r'\1', s)
    return s


def wikitext(text):
    """MediaWiki 원문 → 글. 틀({{…}})은 통째로 뺀다."""
    # 틀은 여러 줄에 걸칠 수 있다. 안쪽부터 반복해서 벗긴다.
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r'\{\{[^{}]*\}\}', '', text)
    out, num, code = [], Numberer(), False
    for line in text.split('\n'):
        if re.match(r'\s*<(syntaxhighlight|source|pre)\b', line):
            code = True
            rest = re.sub(r'.*?<(?:syntaxhighlight|source|pre)[^>]*>',
                          '', line, count=1)
            if rest.strip():
                out.append(rest)
            continue
        if code:
            if re.search(r'</(syntaxhighlight|source|pre)>', line):
                code = False
                rest = re.sub(r'</(?:syntaxhighlight|source|pre)>.*',
                              '', line)
                if rest.strip():
                    out.append(rest)
            else:
                out.append(line)
            continue
        m = re.match(r'^(=+)\s*(.*?)\s*\1\s*$', line)
        if m:
            out.append('%s\t%s' % (num.next(len(m.group(1))),
                                   _inline_wiki(m.group(2))))
            continue
        m = re.match(r'^([*#]+)\s*(.*)$', line)
        if m:
            out.append('  ' * (len(m.group(1)) - 1) + '- '
                       + _inline_wiki(m.group(2)))
            continue
        out.append(_inline_wiki(line))
    return '\n'.join(out).strip('\n')


def _inline_md(s):
    s = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'\1', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', r'\1 (\2)', s)
    s = re.sub(r'\*\*(.*?)\*\*|__(.*?)__',
               lambda m: m.group(1) or m.group(2), s)
    s = re.sub(r'`([^`]*)`', r'\1', s)
    return s


def markdown(text):
    """마크다운 → 글. 울타리 코드 안의 # 은 제목이 아니다."""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    out, num, fence = [], Numberer(), None
    for line in text.split('\n'):
        f = re.match(r'^\s*(```|~~~)', line)
        if f:
            if fence is None:
                fence = f.group(1)
            elif f.group(1) == fence:
                fence = None
            continue
        if fence is not None:
            out.append(line)
            continue
        m = re.match(r'^(#{1,6})\s+(.*?)\s*#*\s*$', line)
        if m:
            out.append('%s\t%s' % (num.next(len(m.group(1))),
                                   _inline_md(m.group(2))))
            continue
        out.append(_inline_md(line))
    text = '\n'.join(out)
    return re.sub(r'\n{3,}', '\n\n', text).strip('\n')


class _HtmlText(html.parser.HTMLParser):
    """HTML → 줄 목록. 머리글은 제목 줄, 나머지는 글."""
    SKIP = {'script', 'style', 'nav', 'header', 'footer', 'noscript',
            'svg', 'template'}
    BLOCK = {'p', 'div', 'li', 'br', 'tr', 'table', 'section',
             'article', 'dt', 'dd', 'ul', 'ol', 'pre', 'blockquote'}

    def __init__(self):
        html.parser.HTMLParser.__init__(self, convert_charrefs=True)
        self.out, self.buf = [], []
        self.skip = 0
        self.pre = 0
        self.head = None
        self.num = Numberer()

    def flush(self):
        text = ''.join(self.buf)
        self.buf = []
        if self.pre:
            self.out.extend(text.strip('\n').split('\n'))
            return
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            self.out.append(text)

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        if self.skip:
            return
        if re.match(r'h[1-6]$', tag):
            self.flush()
            self.head = int(tag[1])
        elif tag in self.BLOCK:
            self.flush()
            if tag == 'pre':
                self.pre += 1
            if tag == 'li':
                self.buf.append('- ')

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if self.head and tag == 'h%d' % self.head:
            t = re.sub(r'\s+', ' ', ''.join(self.buf)).strip()
            self.buf = []
            if t:
                n = self.num.next(self.head)
                self.out.append('%s\t%s' % (n, t))
            self.head = None
        elif tag in self.BLOCK:
            self.flush()
            if tag == 'pre':
                self.pre = max(0, self.pre - 1)

    def handle_data(self, data):
        if not self.skip:
            self.buf.append(data)


def html_text(text):
    """HTML 문서 → 글. 스크립트·스타일·메뉴는 버린다."""
    p = _HtmlText()
    p.feed(text)
    p.close()
    p.flush()
    return '\n'.join(p.out)


def slug(s):
    return re.sub(r'[^A-Za-z0-9]+', '_', s).strip('_').lower()


def raw_name(key, revid):
    return '%s@%s.json' % (slug(key), revid)


def query(page, revid):
    """API 물음. revid 가 있으면 그 리비전, 없으면 지금 것(넘겨주기
    를 따라간다 — 위키의 이름 여럿이 넘겨주기다)."""
    q = {'action': 'parse', 'prop': 'wikitext|revid', 'format': 'json'}
    if revid:
        q['oldid'] = str(revid)
    else:
        q['page'] = page
        q['redirects'] = '1'
    return q


def mediawiki(page, revid, cache_dir=RAW, offline=False):
    """(글, revid). revid 가 있으면 그 리비전을, 없으면 지금 것을."""
    if revid:
        p = os.path.join(cache_dir, raw_name(page, revid))
        if os.path.exists(p):
            raw = json.loads(io.open(p, encoding='utf-8').read())
            return (wikitext(raw['parse']['wikitext']['*']),
                    raw['parse']['revid'])
    if offline:
        raise LookupError('캐시에 없다: %s@%s' % (page, revid))
    req = urllib.request.Request(
        WIKI_API + '?' + urllib.parse.urlencode(query(page, revid)),
        headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode('utf-8')
    raw = json.loads(body)
    if 'parse' not in raw:
        raise LookupError('%s: %s' % (page, raw.get('error')))
    rev = raw['parse']['revid']
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)
    io.open(os.path.join(cache_dir, raw_name(page, rev)), 'w',
            encoding='utf-8', newline='\n').write(body)
    return wikitext(raw['parse']['wikitext']['*']), rev


def header(source, pin, fetched):
    return ('# source: %s\n# pin: %s\n# fetched: %s\n'
            % (source, pin, fetched))


# ── data/docs.tsv 전부 ─────────────────────────────────────────────
def _table():
    p = os.path.join(BASE, 'data', 'docs.tsv')
    rows, head, notes = [], None, []
    for line in io.open(p, encoding='utf-8').read().split('\n'):
        if line.startswith('#'):
            notes.append(line)       # 머리 주석은 다시 쓸 때 살린다
            continue
        if not line.strip():
            continue
        cols = line.split('\t')
        if head is None:
            head = cols
            continue
        rows.append(dict(zip(head, cols + [''] * len(head))))
    return p, head, rows, notes


def run_all(pin_only=False):
    sys.path.insert(0, os.path.join(BASE, 'deck'))
    import srcpin
    pins = srcpin.Pins(BASE)
    p, head, rows, notes = _table()
    today = datetime.date.today().isoformat()
    if not os.path.isdir(DOCS):
        os.makedirs(DOCS)
    changed = False
    for row in rows:
        if row['kind'] == 'mediawiki':
            rev = row.get('revid') or None
            if pin_only and rev:
                continue
            text, got = mediawiki(row['source'], rev)
            if not rev:
                row['revid'] = str(got)
                changed = True
            src = '%s?oldid=%s' % (WIKI_API.replace('api.php',
                                                    'index.php'), got)
            pin = 'revid %s' % got
        elif row['kind'] == 'html':
            if pin_only:
                continue
            # 리비전이 없는 쪽이다. 처음 받은 원문을 캐시에 얼리고,
            # 그 원문의 SHA-256 앞자리를 핀으로 적는다.
            raw = os.path.join(RAW, row['key'] + '.html')
            if not os.path.exists(raw):
                req = urllib.request.Request(
                    row['source'],
                    headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = r.read()
                if not os.path.isdir(RAW):
                    os.makedirs(RAW)
                io.open(raw, 'wb').write(body)
            body = io.open(raw, 'rb').read()
            text = html_text(body.decode('utf-8', 'replace'))
            src = row['source']
            pin = 'sha256 %s' % hashlib.sha256(body).hexdigest()[:12]
        else:
            if pin_only:
                continue
            repo, _, path = row['source'].partition(':')
            lines = pins.lines('sources/%s/%s' % (repo, path))
            if lines is None:
                print('  ✗ %s: sources/%s/%s 가 없다' % (row['key'],
                                                        repo, path))
                continue
            text = markdown('\n'.join(lines))
            src = row['source']
            pin = '%s@%s' % (repo, (pins.sha(repo) or '')[:12])
        out = os.path.join(DOCS, row['key'] + '.txt')
        io.open(out, 'w', encoding='utf-8', newline='\n').write(
            header(src, pin, today) + text + '\n')
        print('  %-28s %s' % (row['key'], pin))
    if changed:
        io.open(p, 'w', encoding='utf-8', newline='\n').write(
            ''.join(n + '\n' for n in notes)
            + '\t'.join(head) + '\n' + ''.join(
                '\t'.join(r.get(h, '') for h in head) + '\n'
                for r in rows))
    return 0


def main(argv):
    if '--all' in argv:
        return run_all()
    if '--pin' in argv:
        return run_all(pin_only=True)
    print('사용법: doc_text.py --all | --pin')
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
