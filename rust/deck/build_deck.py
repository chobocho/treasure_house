#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""덱 조립기 — 조각 HTML + 진짜 예제 + 진짜 rustc 출력 → 단일 HTML 덱.

   원칙 하나: 덱 본문에 손으로 쓴 코드도, 손으로 적은 출력도, 손으로 적은
   릴리스 날짜도 없다. 모든 코드는 ex/ 의 진짜 파일에서 잘라 오고, 모든
   출력은 tools/rsrun.py 가 이 기계의 rustc 로 돌려 out/ 에 남긴 캡처이며,
   날짜는 data/releases.tsv 에서 온다. 조립기는 아무것도 돌리지 않는다.

   지시자 (조각 파일에 쓴다. RUN·CODE·OUT 은 한 줄에 하나, 나머지는 문장 안에):

     <!--RUN  file=ex/06/move.rs note=한 줄 설명-->      코드 + 그 캡처
     <!--CODE file=ex/06/move.rs lines=3-10 note=…-->    파일의 일부
     <!--OUT  file=out/06/move.txt lines=2-6 note=…-->   캡처의 일부
     <!--REL v=1.65-->          → 1.65(2022-11-03)
     <!--SINCE key=let-else-->  → 버전 배지
     <!--SRC key=rust-1.0-->    → 출처 링크
     <!--FACT id=first-release--> → 근거가 확인된 역사 주장의 출처 링크

   슬라이드를 통째로 만들어 내는 지시자(부록용 — <article> 밖에 둔다):

     <!--ECODES per=12-->    제목이 "— E0382" 로 끝나는 장을 모은 오류 번호 찾아보기
     <!--GLOSSARY per=9-->   deck/glossary.tsv (ko·en·desc·where) → 가나다순 용어집
     <!--SOURCES per=10-->   data/sources.tsv → 출처 목록

   검사는 build() 끝의 목록과 같다. 하나라도 걸리면 종료 코드 1.
   O(조각 글자 수 + 인용한 파일 크기) — 한 번 훑고 끝난다.
"""
import html
import io
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                   # rust/
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import rsrun  # noqa: E402

TARGET_NAME = 'Rust_기초_문법집.html'
HARD_CAP = 1000            # 사용자가 정한 상한(PLAN.md §6)
# 접힌 폴더블(374px)에서 한 화면·가로 스크롤 없는 폭. 다른 덱들에서 재서 정한 값.
MAX_PRE_LINES = 45
MAX_PRE_COLS = 72
# 캡처는 우리가 다시 접을 수 없다(rustc 진단 한 줄이 길다). 108칸까지는 가로로
# 밀어 보고, 그보다 길면 화면에서만 접는다(바이트는 그대로). 200칸은 오류.
MAX_TERM_COLS = 108
MAX_WRAP_COLS = 200
PLACEHOLDER = '준비 중입니다'
# 역사 부는 연도·주장마다 근거를 요구한다(PLAN.md §0.5).
HISTORY_PARTS = (1,)
YEAR = re.compile(r'(?<![\d.#-])(19[5-9]\d|20[0-4]\d)(?![\d.])')
LANG_OF = {'.rs': 'rust', '.toml': 'toml', '.txt': 'text', '.md': 'text', '.sh': 'sh'}

# 값에는 > 가 올 수 있다(note=-> () , Option<u8>). 지시자의 끝은 --> 뿐이다.
# 따옴표 없는 값은 "--> 가 아닌 글자들" 이고, 다음 key= 앞의 공백에서 끝난다.
_WORD = r'(?:(?!-->)\S)+'
_VALUE = r'(?:"[^"]*"|%s(?:\s+(?![a-z]+=)%s)*)?' % (_WORD, _WORD)
DIRECTIVE = re.compile(r'<!--([A-Z]+)((?:\s+[a-z]+=%s)*)\s*-->' % _VALUE)
ATTR = re.compile(r'([a-z]+)=(?:"([^"]*)"|(%s(?:\s+(?![a-z]+=)%s)*)?)' % (_WORD, _WORD))
ARTICLE = re.compile(r'<article\b([^>]*)>(.*?)</article>', re.S)
PRE = re.compile(r'<pre\b([^>]*)>(.*?)</pre>', re.S)
# 박스 그리기 문자는 <pre> 밖에서 쓰지 않는다 — 내장 글꼴(DeckMono)은 고정폭
# 요소에만 걸려, 산문에 그린 표는 보는 기기의 글꼴에 따라 무너진다.
BOXDRAW = re.compile(r'[─-╿▀-▟]')


def read(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()


def esc(s):
    return html.escape(s, quote=False)


def width(s):
    """화면 칸 수. 한글·전각은 2칸, 탭은 다음 8칸 자리까지."""
    n = 0
    for ch in s:
        if ch == '\t':
            n += 8 - n % 8
        elif unicodedata.combining(ch):
            continue
        else:
            n += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return n


def tsv(path, key):
    """첫 줄이 머리인 TSV → {key 열: 행 dict}. 파일이 없으면 빈 표."""
    rows = {}
    if not os.path.isfile(path):
        return rows
    lines = [ln for ln in read(path).split('\n') if ln and not ln.startswith('#')]
    if not lines:
        return rows
    head = lines[0].split('\t')
    for ln in lines[1:]:
        f = ln.split('\t')
        row = dict(zip(head, f + [''] * (len(head) - len(f))))
        rows[row[key]] = row
    return rows


class Result(object):
    def __init__(self):
        self.html = ''
        self.errors = []
        self.warns = []
        self.slides = 0
        self.per_part = {}


class Builder(object):
    def __init__(self, root, skel):
        self.root = root
        self.skel = skel
        self.r = Result()
        self.releases = tsv(os.path.join(root, 'data', 'releases.tsv'), 'version')
        self.features = tsv(os.path.join(root, 'data', 'features.tsv'), 'key')
        self.sources = tsv(os.path.join(root, 'data', 'sources.tsv'), 'key')
        self.evidence = tsv(os.path.join(root, 'data', 'evidence.tsv'), 'id')
        self.manifest = rsrun.manifest_load(root)
        self.used = set()           # 슬라이드가 인용한 예제
        self.where = ''             # 오류 문구에 붙일 "조각:줄"

    def err(self, msg):
        self.r.errors.append('%s — %s' % (self.where, msg) if self.where else msg)

    # ── 인용 ───────────────────────────────────────────────────────
    def lines_of(self, rel, strip_directives):
        p = os.path.join(self.root, rel)
        if not os.path.isfile(p):
            self.err('파일이 없다: %s' % rel)
            return None
        text = read(p)
        if strip_directives:
            try:
                text, _ = rsrun.parse_directives(text)
            except rsrun.RsrunError as e:
                self.err('%s: %s' % (rel, e))
                return None
        lines = text.split('\n')
        if lines and lines[-1] == '':
            lines.pop()
        return lines

    def slice(self, rel, lines, spec):
        if not spec:
            return 1, len(lines)
        m = re.match(r'^(\d+)-(\d+)$', spec)
        a, b = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
        if not m or a < 1 or b < a or b > len(lines):
            self.err('%s: lines=%s 가 범위(1-%d) 밖이다' % (rel, spec, len(lines)))
            return 1, len(lines)
        return a, b

    def measure(self, rel, lines, max_cols, what):
        if len(lines) > MAX_PRE_LINES:
            self.err('%s: %s %d줄 — 한 블록은 %d줄까지(lines= 로 나누거나 예제를 줄인다)'
                     % (rel, what, len(lines), MAX_PRE_LINES))
        wide = [(i, width(ln)) for i, ln in enumerate(lines, 1) if width(ln) > max_cols]
        if wide:
            self.err('%s: %s %d번째 줄이 %d칸 — %d칸까지' % (rel, what, wide[0][0], wide[0][1], max_cols))

    def balanced(self, rel, part, spec):
        """잘라 온 Rust 코드의 중괄호가 맞는가 — 함수 가운데서 끊긴 인용을 잡는다.

           문자열·문자·주석 안의 중괄호는 세지 않는다. 한 번 훑는다, O(글자 수).
        """
        text = '\n'.join(part)
        text = re.sub(r'//[^\n]*', '', text)
        text = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
        text = re.sub(r"'(?:\\.|[^'\\])'", "''", text)
        depth = text.count('{') - text.count('}')
        if depth:
            self.err('%s: lines=%s 가 블록 경계에 맞지 않는다(중괄호 %+d) — 함수·블록 단위로 자른다'
                     % (rel, spec, depth))

    def check_fresh(self, ex):
        self.used.add(ex)
        why = rsrun.stale(self.root, ex, self.manifest)
        if why:
            self.err('%s: 캡처가 낡았다(%s) — python3 tools/rsrun.py %s' % (ex, why, ex))

    def code(self, a):
        rel = a.get('file', '')
        if not rel.startswith('ex/'):
            self.err('CODE 는 ex/ 아래 파일만 싣는다: %s' % rel)
            return ''
        ext = os.path.splitext(rel)[1]
        base = os.path.basename(rel)
        lines = self.lines_of(rel, ext == '.rs')
        if lines is None:
            return ''
        self.used.add(rsrun.example_of(rel))
        lo, hi = self.slice(rel, lines, a.get('lines'))
        part = lines[lo - 1:hi]
        self.measure(rel, part, MAX_PRE_COLS, '코드')
        if ext == '.rs' and a.get('lines'):
            self.balanced(rel, part, a['lines'])
        lang = 'text' if base == 'RUN' else LANG_OF.get(ext, 'text')
        label = rel + (' · ' + a['note'] if a.get('note') else '')
        return ('<p class="fname">%s</p>\n<pre data-src="%s" data-lines="%d-%d">'
                '<code data-lang="%s">%s\n</code></pre>'
                % (esc(label), rel, lo, hi, lang, esc('\n'.join(part))))

    def out(self, a):
        rel = a.get('file', '')
        if not rel.startswith('out/') or not rel.endswith('.txt'):
            self.err('OUT 은 out/….txt 캡처만 싣는다: %s' % rel)
            return ''
        lines = self.lines_of(rel, False)
        if lines is None:
            return ''
        ex = 'ex/' + rel[4:-4]
        if os.path.isfile(os.path.join(self.root, ex + '.rs')):
            ex += '.rs'
        self.check_fresh(ex)
        lo, hi = self.slice(rel, lines, a.get('lines'))
        part = lines[lo - 1:hi]
        cols = max([width(ln) for ln in part] or [0])
        cls = 'term'
        if cols > MAX_WRAP_COLS:
            self.err('%s: 캡처 한 줄이 %d칸 — %d칸까지(그 줄을 lines= 로 뺀다)' % (rel, cols, MAX_WRAP_COLS))
        elif cols > MAX_TERM_COLS:
            cls = 'term wrap'
        if len(part) > MAX_PRE_LINES:
            self.err('%s: 캡처 %d줄 — 한 블록은 %d줄까지' % (rel, len(part), MAX_PRE_LINES))
        body = '\n'.join('<span class="p">%s</span>' % esc(ln) if ln.startswith('$ ') else esc(ln)
                         for ln in part)
        note = '<p class="cap">%s</p>\n' % esc(a['note']) if a.get('note') else ''
        return '%s<pre class="%s" data-src="%s" data-lines="%d-%d">%s\n</pre>' % (note, cls, rel, lo, hi, body)

    def run(self, a):
        rel = a.get('file', '')
        if not rel.endswith('.rs'):
            self.err('RUN 은 파일 하나짜리 예제(ex/NN/name.rs)에 쓴다 — 디렉터리 예제는 CODE·OUT 으로: %s' % rel)
            return ''
        code = self.code(a)
        if not code:
            return ''
        return code + '\n' + self.out({'file': rsrun.capture_path(rel)})

    def inline(self, name, a):
        if name == 'REL':
            v = a.get('v', '')
            if v not in self.releases:
                self.err('REL: data/releases.tsv 에 없는 버전 %s' % v)
                return v
            return '%s(%s)' % (v, self.releases[v]['date'])
        if name == 'SINCE':
            f = self.features.get(a.get('key', ''))
            if not f:
                self.err('SINCE: data/features.tsv 에 없는 키 %s' % a.get('key'))
                return ''
            return '<span class="vt" title="%s">%s</span>' % (html.escape(f['label']), f['version'])
        if name == 'SRC':
            s = self.sources.get(a.get('key', ''))
            if not s:
                self.err('SRC: data/sources.tsv 에 없는 키 %s' % a.get('key'))
                return ''
            return ('<a class="src" href="%s" title="%s">출처</a>'
                    % (html.escape(s['url']), html.escape(s['title'])))
        if name == 'FACT':
            e = self.evidence.get(a.get('id', ''))
            s = self.sources.get(e['source']) if e else None
            if not e or not s:
                self.err('FACT: data/evidence.tsv 에 없는 주장 %s (facts.tsv 에 적고 make data)' % a.get('id'))
                return ''
            title = '%s — %s' % (s['title'], e['matched'])
            if len(title) > 160:
                title = title[:159] + '…'
            return '<a class="src" href="%s" title="%s">출처</a>' % (html.escape(s['url']), html.escape(title))
        return None

    def history_check(self, fname, text):
        """역사 부의 장마다 — 근거 지시자가 하나는 있고, 적힌 연도가 그 근거 안에 있는가."""
        for n, m in enumerate(ARTICLE.finditer(text), 1):
            attrs, inner = m.group(1), m.group(2)
            self.where = '%s:%d' % (fname, text.count('\n', 0, m.start()) + 1)
            if 'section' in attrs or 'class="chnum"' in inner or 'quiz' in attrs:
                continue
            allowed, cited = set(), 0
            for d in DIRECTIVE.finditer(inner):
                a = {k: (q if q else u).strip() for k, q, u in ATTR.findall(d.group(2))}
                name = d.group(1)
                if name == 'FACT' and a.get('id') in self.evidence:
                    e = self.evidence[a['id']]
                    allowed.update(YEAR.findall(e['matched']))
                    allowed.update(YEAR.findall(self.sources.get(e['source'], {}).get('date', '')))
                elif name == 'SRC' and a.get('key') in self.sources:
                    allowed.update(YEAR.findall(self.sources[a['key']].get('date', '')))
                elif name == 'REL' and a.get('v') in self.releases:
                    allowed.update(YEAR.findall(self.releases[a['v']]['date']))
                if name in ('FACT', 'SRC', 'REL', 'SINCE', 'RUN', 'OUT'):
                    cited += 1
            if not cited:
                self.err('근거 없는 역사 슬라이드 — FACT·SRC·REL 가운데 하나는 단다')
            prose = re.sub(r'<[^>]+>', ' ', DIRECTIVE.sub(' ', inner))
            for y in sorted(set(YEAR.findall(prose)) - allowed):
                self.err('%s년 — 이 장의 근거(FACT·SRC 날짜·REL) 어디에도 없는 연도' % y)

    # ── 슬라이드를 만들어 내는 지시자 ─────────────────────────────
    def pages(self, slug, title, head, rows, per):
        """표의 행들을 per 개씩 끊어 슬라이드 여러 장으로. 장수는 예산에 그대로 잡힌다."""
        per = max(1, per)
        chunks = [rows[i:i + per] for i in range(0, len(rows), per)] or [[]]
        out = []
        for n, chunk in enumerate(chunks, 1):
            out.append('<article class="card" id="p%02d-%s-%d">\n<h3>%s (%d/%d)</h3>\n'
                       '<div class="tblwrap">\n<table class="kv">\n<tr>%s</tr>\n%s\n</table>\n</div>\n</article>'
                       % (self.part, slug, n, title, n, len(chunks),
                          ''.join('<th>%s</th>' % h for h in head),
                          '\n'.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % c for c in r) for r in chunk)))
        return '\n\n'.join(out)

    def generated(self, name, a):
        per = int(a['per']) if a.get('per', '').isdigit() else 12
        if name == 'ECODES':
            rows = [('<code>%s</code>' % code,
                     ' · '.join('<a href="#%s">%s</a>' % (sid, t) for sid, t in self.ecodes[code]))
                    for code in sorted(self.ecodes)]
            return self.pages('ecodes', '오류 번호 찾아보기', ('번호', '나오는 곳'), rows, per)
        if name == 'GLOSSARY':
            terms = tsv(os.path.join(self.root, 'deck', 'glossary.tsv'), 'ko')
            rows = []
            for ko in sorted(terms):
                t = terms[ko]
                head = '<a href="#%s">%s</a>' % (t['where'], esc(ko)) if t.get('where') else esc(ko)
                rows.append((head + '<br><span class="en">%s</span>' % esc(t['en']), t['desc']))
            return self.pages('glossary', '용어집', ('용어', '뜻'), rows, per)
        rows = [('<a href="%s">%s</a>' % (html.escape(x['url']), esc(x['title'])), x.get('date', ''))
                for x in self.sources.values()]
        return self.pages('sources', '출처', ('글', '나온 날'), rows, per)

    def expand(self, m):
        name = m.group(1)
        a = {k: (q if q else u).strip() for k, q, u in ATTR.findall(m.group(2))}
        if name in ('ECODES', 'GLOSSARY', 'SOURCES'):
            before = m.string[:m.start()]
            if before.count('<article') != before.count('</article>'):
                self.err('%s 는 슬라이드를 만들어 낸다 — <article> 밖에 둔다' % name)
                return ''
            return self.generated(name, a)
        if name == 'RUN':
            return self.run(a)
        if name == 'CODE':
            return self.code(a)
        if name == 'OUT':
            return self.out(a)
        got = self.inline(name, a)
        if got is None:
            self.err('모르는 지시자 <!--%s-->' % name)
            return ''
        return got

    # ── 조각 하나 ──────────────────────────────────────────────────
    def fragment(self, fname):
        part = self.part = int(fname[:2])
        text = read(os.path.join(self.root, 'deck', 'sections', fname))
        # 손으로 쓴 <pre> 는 지시자를 펴기 전에 본다(편 뒤에는 구별할 수 없다).
        for m in PRE.finditer(text):
            self.where = '%s:%d' % (fname, text.count('\n', 0, m.start()) + 1)
            if not re.search(r'class="fig"', m.group(1)):
                self.err('손으로 쓴 <pre> — 코드·출력은 RUN/CODE/OUT 으로만 싣는다'
                         '(그림은 <pre class="fig">)')
            else:
                body = html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip('\n').split('\n')
                self.measure(fname, body, MAX_PRE_COLS, '그림')
        if part in HISTORY_PARTS:
            self.history_check(fname, text)
        out = []
        pos = 0
        for m in DIRECTIVE.finditer(text):
            self.where = '%s:%d' % (fname, text.count('\n', 0, m.start()) + 1)
            out.append(text[pos:m.start()])
            out.append(self.expand(m))
            pos = m.end()
        out.append(text[pos:])
        body = ''.join(out)
        self.where = fname
        left = re.search(r'<!--\s*[A-Z]{2,}\b.*?-->', body, re.S)
        if left:
            self.err('펴지지 않은 지시자: %s' % left.group(0)[:60])
        if BOXDRAW.search(PRE.sub('', body)):
            self.err('박스 그리기 문자가 <pre> 밖에 있다')
        if PLACEHOLDER in body and not self.skel:
            self.err('"%s" 플레이스홀더가 남았다' % PLACEHOLDER)
        n = 0
        for m in ARTICLE.finditer(body):
            n += 1
            idm = re.search(r'\bid="([^"]+)"', m.group(1))
            if not idm:
                self.err('%d번째 슬라이드에 id 가 없다' % n)
                continue
            sid = idm.group(1)
            if sid in self.ids:
                self.err('id 가 겹친다: %s' % sid)
            self.ids.add(sid)
            if sid != 'top' and not re.match(r'^p%02d(-|$)' % part, sid):
                self.err('id 는 p%02d 로 시작한다: %s' % (part, sid))
            self.subids.update(re.findall(r'\bid="([^"]+)"', m.group(2)))
            self.links += [(fname, h) for h in re.findall(r'href="#([^"]+)"', m.group(2))]
            self.nav_item(part, sid, m.group(1), m.group(2))
        if body.count('<article') != n or body.count('</article>') != n:
            self.err('<article> 열고 닫는 수가 맞지 않는다')
        self.r.per_part[part] = self.r.per_part.get(part, 0) + n
        return body

    def nav_item(self, part, sid, attrs, inner):
        h = re.search(r'<h[12][^>]*>(.*?)</h[12]>', inner, re.S)
        title = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h.group(1))).strip() if h else ''
        num = re.search(r'<p class="chnum">(.*?)</p>', inner)
        if 'cover' in attrs:
            return
        if re.search(r'class="[^"]*\bsection\b', attrs):
            label = (re.sub(r'<[^>]+>', '', num.group(1)) + ' · ' if num else '') + title
            self.nav.append('    <option value="%s">%s</option>' % (sid, label))
        elif num:
            self.nav.append('    <option value="%s">· %s</option>' % (sid, title))

    # ── 전체 ───────────────────────────────────────────────────────
    def build(self):
        d = os.path.join(self.root, 'deck')
        order = [ln.strip() for ln in read(os.path.join(d, 'order.txt')).split('\n')
                 if ln.strip() and not ln.startswith('#')]
        self.ids, self.subids, self.links = set(), set(), []
        self.nav = ['    <option value="top">챕터 이동…</option>']
        # 오류 번호 찾아보기는 모든 조각의 제목을 봐야 한다 — 먼저 한 번 훑는다.
        self.ecodes = {}
        for f in order:
            for m in ARTICLE.finditer(read(os.path.join(d, 'sections', f))):
                h = re.search(r'<h3[^>]*>(.*?)</h3>', m.group(2), re.S)
                sid = re.search(r'\bid="([^"]+)"', m.group(1))
                if not h or not sid:
                    continue
                title = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', DIRECTIVE.sub('', h.group(1)))).strip()
                short = re.sub(r'\s*—\s*E0\d{3}.*$', '', title)
                for code in sorted(set(re.findall(r'\bE0\d{3}\b', title))):
                    self.ecodes.setdefault(code, []).append((sid.group(1), short))
        bodies = [self.fragment(f) for f in order]
        self.where = ''
        for fname, h in self.links:
            if h not in self.ids and h not in self.subids:
                self.err('%s — 없는 자리로 가는 링크 #%s' % (fname, h))
        self.budget()
        self.coverage()
        head = read(os.path.join(d, 'base', 'head.html'))
        tail = read(os.path.join(d, 'base', 'tail.html'))
        if '<!--NAV-->' not in head:
            self.err('head.html 에 <!--NAV--> 자리가 없다')
        head = head.replace('<!--NAV-->', '\n'.join(self.nav))
        demos = os.path.join(d, 'demos.js')
        tail = tail.replace('<!--DEMOS-->', '<script>\n%s</script>' % read(demos)
                            if os.path.isfile(demos) else '')
        self.r.slides = sum(self.r.per_part.values())
        self.r.html = head + '\n'.join(bodies) + tail
        return self.r

    def budget(self):
        total = sum(self.r.per_part.values())
        if total > HARD_CAP:
            self.err('전체 %d장 — 상한은 %d장이다' % (total, HARD_CAP))
        want = {}
        for ln in read(os.path.join(self.root, 'deck', 'budget.txt')).split('\n'):
            f = ln.split()
            if len(f) == 2 and f[0].isdigit():
                want[int(f[0])] = int(f[1])
        for part in sorted(self.r.per_part):
            n, w = self.r.per_part[part], want.get(part)
            if w is None:
                self.err('%d부의 예산이 budget.txt 에 없다' % part)
            elif n > w * 1.1:
                self.err('%d부 %d장 — 예산 %d장을 10 %% 넘게 넘었다' % (part, n, w))
            elif n < w * 0.8 and not self.skel:
                self.r.warns.append('%d부 %d장 — 예산 %d장에 20 %% 넘게 모자란다' % (part, n, w))

    def coverage(self):
        for ex in rsrun.examples(self.root):
            if ex not in self.used:
                msg = '어느 슬라이드도 싣지 않는 예제: %s' % ex
                (self.r.warns if self.skel else self.r.errors).append(msg)


def build(root=ROOT, skel=False):
    return Builder(root, skel).build()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    skel = '--skeleton' in argv
    r = build(ROOT, skel)
    target = os.path.join(os.path.dirname(ROOT), TARGET_NAME)
    with io.open(target, 'w', encoding='utf-8', newline='') as f:
        f.write(r.html)
    for w in r.warns:
        print('  ! ' + w)
    for e in r.errors:
        print('  ✗ ' + e)
    parts = ' '.join('%d:%d' % (p, n) for p, n in sorted(r.per_part.items()))
    print('  부별 장수 %s' % parts)
    print('  %s — %d장, 오류 %d건, 알림 %d건' % (TARGET_NAME, r.slides, len(r.errors), len(r.warns)))
    return 1 if r.errors else 0


if __name__ == '__main__':
    sys.exit(main())
