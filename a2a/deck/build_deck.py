#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""덱 조립기 — 조각 HTML + 진짜 예제 + 진짜 캡처 → 단일 HTML 덱.

   원칙 하나: 덱 본문에 손으로 쓴 코드도, 손으로 적은 출력·JSON·HTTP 주고받음도 없다.
   모든 코드는 ex/ 의 진짜 파일에서 잘라 오고, 모든 출력은 tools/a2arun.py 가 이 기계에서
   돌려 out/ 에 남긴 캡처다. 조립기는 아무것도 돌리지 않는다.
   (../rust/deck/build_deck.py 를 옮겨 와 세 언어·구역·캡처 구역에 맞게 고쳤다.)

   지시자 (조각 파일에 쓴다. RUN·CODE·OUT·SPEC 은 한 줄에 하나, 나머지는 문장 안에):

     <!--RUN  file=ex/py/02/x.py note=…-->              코드 + 그 캡처(파일 하나짜리 예제)
     <!--CODE file=ex/… [lines=A-B | region=이름] note=…-->  파일의 일부
     <!--OUT  file=out/….txt [part=터미널 3 | server=bus | wire=bus-wire [ex=N | ex=N-M]]
              [lines=A-B] [grep=정규식] note=…-->        캡처의 한 구역
     <!--SPEC file=ex/run/11/push.run-->                 명세 파일 그 자체(드물게)
     <!--REL v=v1.0.1-->        → v1.0.1(2026-05-28)  (data/releases.tsv)
     <!--SRC key=…-->           → 출처 링크           (data/sources.tsv)
     <!--FACT id=…-->           → 근거가 확인된 주장의 출처 링크 (data/evidence.tsv)

   구역 표시: `# region: 이름` … `# endregion` (ts·go 는 //). 표시 줄과 파일 끝의 지시자 줄
   (# @ · //@)은 화면에 절대 나오지 않는다. 줄 번호는 밀리므로 lines= 보다 region= 을 쓴다.
   화면에 실은 원본 줄 번호는 data-lines="3-5,9-9" 처럼 적어 verify_deck.py 가 되짚는다.

   슬라이드를 통째로 만들어 내는 지시자(부록용 — <article> 밖에 둔다):
     <!--GLOSSARY per=9-->   deck/glossary.tsv (ko·en·desc·where) → 가나다순 용어집
     <!--SOURCES per=10-->   data/sources.tsv → 출처 목록
     <!--FIELDS per=18-->    deck/fields.tsv(tools/appendix.py 가 proto 에서) → 필드 사전.
                             블록(메시지·enum)을 쪼개지 않고, deck/proto_where.tsv 가 가리키는
                             슬라이드로 블록 이름을 잇는다
     <!--INDEX per=20-->     deck/index.tsv(tools/appendix.py 가 조각에서) → 찾아보기, 쪽 번호로
     <!--QUIZZES per=10-->   앞 부들의 퀴즈 슬라이드 → 부마다 한 줄, 장마다 링크

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
ROOT = os.path.dirname(HERE)                                   # a2a/
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import a2arun  # noqa: E402

TARGET_NAME = 'A2A_프로토콜_완전_가이드.html'
HARD_CAP = 2000            # 사용자가 정한 상한(PLAN.md §0.11, 2026-10-16)
# 접힌 폴더블(374px)에서 한 화면·가로 스크롤 없는 폭. 다른 덱들에서 재서 정한 값.
MAX_PRE_LINES = 45
MAX_PRE_COLS = 72
# 캡처는 우리가 다시 접을 수 없다(와이어 기록의 JSON 한 줄이 길다). 108칸까지는 가로로
# 밀어 보고, 그보다 길면 화면에서만 접는다(바이트는 그대로). 200칸은 오류.
MAX_TERM_COLS = 108
MAX_WRAP_COLS = 200
PLACEHOLDER = '준비 중입니다'
# 역사 부는 연도·주장마다 근거를 요구한다(PLAN.md §0.7).
HISTORY_PARTS = (1,)
YEAR = re.compile(r'(?<![\d.#-])(19[5-9]\d|20[0-4]\d)(?![\d.])')
# data-lang 은 template 하이라이터의 이름(ALIAS 가 python·typescript 를 받는다).
LANG_OF = {'.py': 'python', '.ts': 'typescript', '.go': 'go', '.json': 'json',
           '.http': 'http', '.txt': 'text', '.run': 'text'}
DIRECTIVE_MARK = {'.py': '#@', '.ts': '//@', '.go': '//@'}
COMMENT = {'.py': '#', '.ts': '//', '.go': '//'}
TAB = {'.go': 4}           # Go 의 탭은 화면에서 4칸 공백으로 편다(gofmt 는 탭으로 들여 쓴다)

# 값에는 > 가 올 수 있다(note=-> dict, list<int>). 지시자의 끝은 --> 뿐이다.
# 따옴표 없는 값은 "--> 가 아닌 글자들" 이고, 다음 key= 앞의 공백에서 끝난다.
_WORD = r'(?:(?!-->)\S)+'
# 따옴표로 감싼 값은 닫는 따옴표 바로 뒤가 다음 key= 이거나 지시자의 끝일 때만
# 그렇게 읽는다 — note="role" 을 세 가지로 … 처럼 따옴표로 "시작" 할 뿐인 값이
# 첫 낱말에서 끊기지 않게 하기 위해서다.
_QUOTED = r'"[^"]*"(?=\s+[a-z]+=|\s*(?:-->|$))'
_VALUE = r'(?:%s|%s(?:\s+(?![a-z]+=)%s)*)?' % (_QUOTED, _WORD, _WORD)
DIRECTIVE = re.compile(r'<!--([A-Z]+)((?:\s+[a-z]+=%s)*)\s*-->' % _VALUE)
ATTR = re.compile(r'([a-z]+)=(?:"([^"]*)"(?=\s+[a-z]+=|\s*$)|(%s(?:\s+(?![a-z]+=)%s)*)?)'
                  % (_WORD, _WORD))
ARTICLE = re.compile(r'<article\b([^>]*)>(.*?)</article>', re.S)
PRE = re.compile(r'<pre\b([^>]*)>(.*?)</pre>', re.S)
# 박스 그리기 문자는 <pre> 밖에서 쓰지 않는다 — 내장 글꼴(DeckMono)은 고정폭
# 요소에만 걸려, 산문에 그린 표는 보는 기기의 글꼴에 따라 무너진다.
BOXDRAW = re.compile(r'[─-╿▀-▟]')
# 그림(<pre class="fig">)에 손으로 쓴 코드·JSON·HTTP 가 숨어 들어오는 것을 막는 얼개.
CODELIKE = re.compile(r'"[A-Za-z_$][\w$-]*"\s*:|^\s*(?:def|func|import|from|const|let|var|class|'
                      r'package|return|async|await)\b|\bfunction\b|=>|;\s*$|^\s*\$ |'
                      r'^\s*(?:GET|POST|PUT|PATCH|DELETE) /|^\s*HTTP/\d', re.M)


GENERATORS = ('GLOSSARY', 'SOURCES', 'FIELDS', 'INDEX', 'QUIZZES')


def ticks(s):
    """proto 주석의 `이름` → <code>이름</code>. 나머지는 이스케이프."""
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', esc(s))


def read(p):
    with io.open(p, encoding='utf-8') as f:
        return f.read()


def esc(s):
    return html.escape(s, quote=False)


def width(s, tab=8):
    """화면 칸 수. 한글·전각은 2칸, 탭은 다음 tab 칸 자리까지."""
    n = 0
    for ch in s:
        if ch == '\t':
            n += tab - n % tab
        elif unicodedata.combining(ch):
            continue
        else:
            n += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return n


def display_line(s, ext):
    """원본 줄 → 화면 줄. Go 만 탭을 4칸 공백으로 편다. verify_deck 도 이것을 쓴다."""
    return s.expandtabs(TAB[ext]) if ext in TAB else s


def display_width(s, ext):
    return width(display_line(s, ext))


def ranges(nums):
    """[3, 4, 5, 9] → '3-5,9-9'. 화면에 실은 원본 줄 번호의 압축."""
    out, start, prev = [], None, None
    for n in nums:
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append('%d-%d' % (start, prev))
            start = prev = n
    if start is not None:
        out.append('%d-%d' % (start, prev))
    return ','.join(out)


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


def file_lines(text):
    lines = text.split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    return lines


class Result(object):
    def __init__(self):
        self.html = ''
        self.errors = []
        self.warns = []
        self.slides = 0
        self.placeholders = 0
        self.per_part = {}
        self.holes_per_part = {}


class Builder(object):
    def __init__(self, root, skel):
        self.root = root
        self.skel = skel
        self.r = Result()
        self.releases = tsv(os.path.join(root, 'data', 'releases.tsv'), 'version')
        self.sources = tsv(os.path.join(root, 'data', 'sources.tsv'), 'key')
        self.evidence = tsv(os.path.join(root, 'data', 'evidence.tsv'), 'id')
        self.manifest = a2arun.manifest_load(root)
        self.used = set()           # 슬라이드가 실은 예제(a2arun.sources 의 이름)
        self.where = ''             # 오류 문구에 붙일 "조각:줄"

    def err(self, msg):
        self.r.errors.append('%s — %s' % (self.where, msg) if self.where else msg)

    # ── 원본 파일 ──────────────────────────────────────────────────
    def source_lines(self, rel):
        """(화면에 실을 수 있는 원본 줄 번호들, 전체 줄) — 지시자·구역 표시 줄은 뺀다."""
        p = os.path.join(self.root, rel)
        if not os.path.isfile(p):
            self.err('파일이 없다: %s' % rel)
            return None, None
        text = read(p)
        lines = file_lines(text)
        ext = os.path.splitext(rel)[1]
        body = len(lines)
        if ext in DIRECTIVE_MARK and rel.startswith('ex/'):
            try:
                body, _ = a2arun.parse_directives(text, {'.py': 'py', '.ts': 'ts', '.go': 'go'}[ext])
            except a2arun.RunError as e:
                self.err('%s: %s' % (rel, e))
                return None, None
        marker = self.marker(ext)
        keep = [i for i in range(1, body + 1) if not (marker and marker.match(lines[i - 1]))]
        return keep, lines

    @staticmethod
    def marker(ext):
        c = COMMENT.get(ext)
        if not c:
            return None
        return re.compile(r'^\s*%s\s*(?:region:\s*\S+|endregion)\s*$' % re.escape(c))

    def region(self, rel, lines, keep, name):
        ext = os.path.splitext(rel)[1]
        c = COMMENT.get(ext)
        if not c:
            self.err('%s: region= 은 .py·.ts·.go 에만 쓴다' % rel)
            return keep
        start = re.compile(r'^\s*%s\s*region:\s*(\S+)\s*$' % re.escape(c))
        end = re.compile(r'^\s*%s\s*endregion\s*$' % re.escape(c))
        for i, ln in enumerate(lines, 1):
            m = start.match(ln)
            if m and m.group(1) == name:
                depth = 0
                for j in range(i + 1, len(lines) + 1):
                    if start.match(lines[j - 1]):
                        depth += 1
                    elif end.match(lines[j - 1]):
                        if depth == 0:
                            return [k for k in keep if i < k < j]
                        depth -= 1
                self.err('%s: region=%s 를 닫는 endregion 이 없다' % (rel, name))
                return keep
        self.err('%s: region=%s 가 없다 (%s region: %s 표시를 단다)' % (rel, name, c, name))
        return keep

    def measure(self, rel, shown, max_cols, what):
        if len(shown) > MAX_PRE_LINES:
            self.err('%s: %s %d줄 — 한 블록은 %d줄까지(region= 으로 나누거나 예제를 줄인다)'
                     % (rel, what, len(shown), MAX_PRE_LINES))
        wide = [(i, width(ln)) for i, ln in enumerate(shown, 1) if width(ln) > max_cols]
        if wide:
            self.err('%s: %s %d번째 줄이 %d칸 — %d칸까지' % (rel, what, wide[0][0], wide[0][1], max_cols))

    def balanced(self, rel, shown, spec):
        """잘라 온 ts·go 코드의 중괄호가 맞는가 — 함수 가운데서 끊긴 인용을 잡는다.

           문자열을 먼저 지우고(주석 속 따옴표 하나는 그 줄에서 짝이 없어 안 걸린다) 그다음
           주석을 지운다. 한 번 훑는다, O(글자 수).
        """
        text = '\n'.join(shown)
        text = re.sub(r'"(?:\\.|[^"\\\n])*"', '""', text)
        text = re.sub(r"'(?:\\.|[^'\\\n])*'", "''", text)
        text = re.sub(r'`[^`]*`', '``', text)
        text = re.sub(r'//[^\n]*', '', text)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
        depth = text.count('{') - text.count('}')
        if depth:
            self.err('%s: %s 가 블록 경계에 맞지 않는다(중괄호 %+d) — 함수·블록 단위로 자른다'
                     % (rel, spec, depth))

    def mark_used(self, rel):
        ex = a2arun.example_of(rel)
        if ex:
            self.used.add(ex)

    def check_fresh(self, ex):
        self.used.add(ex)
        why = a2arun.stale(self.root, ex, self.manifest)
        if why:
            self.err('%s: 캡처가 낡았다(%s) — python3 tools/a2arun.py %s' % (ex, why, ex))

    # ── 지시자 ────────────────────────────────────────────────────
    def code(self, a, label_rel=None):
        rel = a.get('file', '').rstrip('/')
        if not rel.startswith('ex/'):
            self.err('CODE 는 ex/ 아래 파일만 싣는다: %s' % rel)
            return ''
        if os.path.isdir(os.path.join(self.root, rel)) and os.path.isfile(
                os.path.join(self.root, rel, 'main.go')):
            rel += '/main.go'                     # Go 예제 디렉터리 → main.go
        keep, lines = self.source_lines(rel)
        if keep is None:
            return ''
        self.mark_used(rel)
        ext = os.path.splitext(rel)[1]
        spec = None
        if a.get('lines') and a.get('region'):
            self.err('%s: lines= 와 region= 은 함께 쓰지 않는다' % rel)
        elif a.get('lines'):
            spec = 'lines=' + a['lines']
            m = re.match(r'^(\d+)-(\d+)$', a['lines'])
            lo, hi = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
            if not m or lo < 1 or hi < lo or hi > (keep[-1] if keep else 0):
                self.err('%s: lines=%s 가 범위(1-%d) 밖이다' % (rel, a['lines'], keep[-1] if keep else 0))
            else:
                keep = [k for k in keep if lo <= k <= hi]
        elif a.get('region'):
            spec = 'region=' + a['region']
            keep = self.region(rel, lines, keep, a['region'])
        shown = [display_line(lines[k - 1], ext) for k in keep]
        if not shown:
            self.err('%s: 보일 줄이 없다' % rel)
            return ''
        self.measure(rel, shown, MAX_PRE_COLS, '코드')
        if spec and ext in ('.ts', '.go'):
            self.balanced(rel, shown, spec)
        lang = LANG_OF.get(ext, 'text')
        label = (label_rel or rel) + (' · ' + a['note'] if a.get('note') else '')
        return ('<p class="fname">%s</p>\n<pre data-src="%s" data-lines="%s">'
                '<code data-lang="%s">%s\n</code></pre>'
                % (esc(label), rel, ranges(keep), lang, esc('\n'.join(shown))))

    def section_of(self, rel, lines, a):
        """캡처 줄 → (고른 줄 번호들, 이름표). 구역 고르기 → lines= → grep= 차례."""
        n = len(lines)
        heads = [i for i in range(1, n + 1) if lines[i - 1].startswith('── ')]
        first_head = heads[0] if heads else n + 1
        label = ''

        def after(i):           # 머리줄 i 다음부터 다음 머리줄 앞까지
            nxt = [h for h in heads if h > i]
            return list(range(i + 1, (nxt[0] if nxt else n + 1)))
        picked = list(range(1, n + 1))
        keys = [k for k in ('part', 'server', 'wire') if a.get(k)]
        if len(keys) > 1:
            self.err('%s: part·server·wire 는 하나만 쓴다' % rel)
            return None, ''
        if a.get('ex') and not a.get('wire'):
            self.err('%s: ex= 는 wire= 와 함께 쓴다' % rel)
            return None, ''
        if a.get('part'):
            m = re.match(r'^터미널 (\d+)$', a['part'])
            if not m:
                self.err('%s: part= 는 "터미널 N" 꼴이다: %s' % (rel, a['part']))
                return None, ''
            tag = '[터미널 %s] ' % m.group(1)
            picked, on = [], False
            for i in range(1, first_head):
                ln = lines[i - 1]
                if ln.startswith('[터미널 '):
                    on = ln.startswith(tag)
                if on:
                    picked.append(i)
            label = a['part']
        elif a.get('server'):
            h = [i for i in heads if re.match(r'^── 터미널 \d+ \(%s\) 출력 ──$' % re.escape(a['server']),
                                               lines[i - 1])]
            if not h:
                self.err('%s: server=%s 구역이 없다' % (rel, a['server']))
                return None, ''
            picked = after(h[0])
            label = lines[h[0] - 1].strip('─ ')
        elif a.get('wire'):
            h = [i for i in heads if re.match(r'^── 와이어 \(%s\)( \(정렬됨\))? ──$' % re.escape(a['wire']),
                                               lines[i - 1])]
            if not h:
                self.err('%s: wire=%s 구역이 없다' % (rel, a['wire']))
                return None, ''
            picked = after(h[0])
            label = lines[h[0] - 1].strip('─ ')
            if a.get('ex'):
                starts = [i for i in picked if lines[i - 1].startswith('→ ')]
                m = re.match(r'^(\d+)(?:-(\d+))?$', a['ex'])
                lo = int(m.group(1)) if m else 0
                hi = int(m.group(2) or lo) if m else 0
                if not m or lo < 1 or hi < lo or hi > len(starts):
                    self.err('%s: ex=%s — 주고받음은 %d개다' % (rel, a['ex'], len(starts)))
                    return None, ''
                end = starts[hi] if hi < len(starts) else picked[-1] + 1
                picked = [i for i in picked if starts[lo - 1] <= i < end]
                label += ' · 주고받음 %s' % a['ex']
        if a.get('lines'):
            m = re.match(r'^(\d+)-(\d+)$', a['lines'])
            lo, hi = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
            if not m or lo < 1 or hi < lo or hi > len(picked):
                self.err('%s: lines=%s 가 구역(1-%d) 밖이다' % (rel, a['lines'], len(picked)))
                return None, ''
            picked = picked[lo - 1:hi]
        if a.get('grep'):
            try:
                rx = re.compile(a['grep'])
            except re.error as e:
                self.err('%s: grep= 정규식이 틀렸다: %s' % (rel, e))
                return None, ''
            picked = [i for i in picked if rx.search(lines[i - 1])]
        if not picked:
            self.err('%s: 고른 구역이 비었다' % rel)
            return None, ''
        return picked, label

    def out(self, a):
        rel = a.get('file', '')
        if not rel.startswith('out/') or not rel.endswith('.txt') or rel.count('/') != 2:
            self.err('OUT 은 out/NN/….txt 캡처만 싣는다: %s' % rel)
            return ''
        p = os.path.join(self.root, rel)
        if not os.path.isfile(p):
            self.err('캡처가 없다: %s (python3 tools/a2arun.py %s)' % (rel, a2arun.source_of(rel)))
            return ''
        self.check_fresh(a2arun.source_of(rel))
        lines = file_lines(read(p))
        picked, label = self.section_of(rel, lines, a)
        if picked is None:
            return ''
        part = [lines[i - 1] for i in picked]
        cols = max([width(ln) for ln in part] or [0])
        cls = 'term'
        if cols > MAX_WRAP_COLS:
            self.err('%s: 캡처 한 줄이 %d칸 — %d칸까지(그 줄을 lines=·grep= 로 뺀다)' % (rel, cols, MAX_WRAP_COLS))
        elif cols > MAX_TERM_COLS:
            cls = 'term wrap'
        if len(part) > MAX_PRE_LINES:
            self.err('%s: 캡처 %d줄 — 한 블록은 %d줄까지' % (rel, len(part), MAX_PRE_LINES))
        body = '\n'.join('<span class="p">%s</span>' % esc(ln)
                         if re.match(r'^(?:\[터미널 \d+\] )?\$ ', ln) else esc(ln) for ln in part)
        cap = a.get('note') or label
        note = '<p class="cap">%s</p>\n' % esc(cap) if cap else ''
        return '%s<pre class="%s" data-src="%s" data-lines="%s">%s\n</pre>' % (
            note, cls, rel, ranges(picked), body)

    def run(self, a):
        rel = a.get('file', '').rstrip('/')
        ex = a2arun.example_of(rel)
        if not ex or a2arun.kind_of(ex) == 'run':
            self.err('RUN 은 파일 하나짜리 예제(ex/py|ts/NN/x, ex/go/NN/name)에 쓴다 — 명세는 SPEC·OUT 으로: %s'
                     % rel)
            return ''
        main = os.path.join(self.root, ex, 'main.go') if a2arun.kind_of(ex) == 'go' else \
            os.path.join(self.root, ex)
        if os.path.isfile(main):
            try:
                _, d = a2arun.parse_directives(read(main), a2arun.kind_of(ex))
            except a2arun.RunError:
                d = {'norun': False}
            if d['norun']:
                self.err('%s 는 norun 이라 캡처가 없다 — CODE 로 싣는다' % ex)
                return ''
        code = self.code(dict(a, file=ex))
        if not code:
            return ''
        return code + '\n' + self.out({'file': a2arun.capture_path(ex)})

    def spec(self, a):
        rel = a.get('file', '')
        if not (rel.startswith('ex/run/') and rel.endswith('.run')):
            self.err('SPEC 은 ex/run/NN/….run 에 쓴다: %s' % rel)
            return ''
        self.used.add(rel)
        return self.code(a)

    def inline(self, name, a):
        if name == 'REL':
            v = a.get('v', '')
            if v not in self.releases:
                self.err('REL: data/releases.tsv 에 없는 판 %s' % v)
                return v
            return '%s(%s)' % (v, self.releases[v]['date'])
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
        for m in ARTICLE.finditer(text):
            attrs, inner = m.group(1), m.group(2)
            self.where = '%s:%d' % (fname, text.count('\n', 0, m.start()) + 1)
            if ('section' in attrs or 'class="chnum"' in inner or 'quiz' in attrs
                    or PLACEHOLDER in inner):
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
                if name in ('FACT', 'SRC', 'REL', 'RUN', 'OUT'):
                    cited += 1
            if not cited:
                self.err('근거 없는 역사 슬라이드 — FACT·SRC·REL 가운데 하나는 단다')
            prose = re.sub(r'<[^>]+>', ' ', DIRECTIVE.sub(' ', inner))
            for y in sorted(set(YEAR.findall(prose)) - allowed):
                self.err('%s년 — 이 장의 근거(FACT·SRC 날짜·REL) 어디에도 없는 연도' % y)

    # ── 슬라이드를 만들어 내는 지시자 ─────────────────────────────
    def pages(self, slug, title, head, rows, per, keys=None):
        """표의 행들을 per 개씩 끊어 슬라이드 여러 장으로. 장수는 예산에 그대로 잡힌다.
           keys(행마다 이름)를 주면 제목에 그 쪽의 첫 이름 ~ 끝 이름을 붙인다."""
        per = max(1, per)
        chunks = [rows[i:i + per] for i in range(0, len(rows), per)] or [[]]
        out = []
        for n, chunk in enumerate(chunks, 1):
            what = ''
            if keys:
                k = keys[(n - 1) * per:(n - 1) * per + len(chunk)]
                what = ' — ' + esc(k[0] if len(k) == 1 or k[0] == k[-1] else '%s ~ %s' % (k[0], k[-1]))
            out.append('<article class="card" id="p%02d-%s-%d">\n<h3>%s (%d/%d)%s</h3>\n'
                       '<div class="tblwrap">\n<table class="kv">\n<tr>%s</tr>\n%s\n</table>\n</div>\n</article>'
                       % (self.part, slug, n, title, n, len(chunks), what,
                          ''.join('<th>%s</th>' % h for h in head),
                          '\n'.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % c for c in r) for r in chunk)))
        return '\n\n'.join(out)

    def grouped_pages(self, slug, title, head, groups, per):
        """[(블록 이름, 머리 행 html, [행 html …])] → 슬라이드들. 블록은 한 쪽에 들어가면
           쪼개지 않고, 한 쪽보다 길면 다음 쪽에서 머리 행을 "(이어서)" 로 다시 단다.
           O(행 수)."""
        per = max(2, per)
        pages, cur, names = [], [], []
        for name, top, rows in groups:
            if cur and len(cur) + 1 + len(rows) > per:
                pages.append((names, cur))
                cur, names = [], []
            cur.append(top % '')
            names.append(name)
            for r in rows:
                if len(cur) >= per:
                    pages.append((names, cur))
                    cur, names = [top % ' (이어서)'], []
                cur.append(r)
        if cur:
            pages.append((names, cur))
        out = []
        for n, (names, rows) in enumerate(pages, 1):
            what = (' — ' + (names[0] if len(names) == 1 else '%s ~ %s' % (names[0], names[-1]))
                    if names else '')
            out.append('<article class="card" id="p%02d-%s-%d">\n<h3>%s (%d/%d)%s</h3>\n'
                       '<div class="tblwrap">\n<table class="kv">\n<tr>%s</tr>\n%s\n</table>\n</div>\n</article>'
                       % (self.part, slug, n, title, n, len(pages), esc(what),
                          ''.join('<th>%s</th>' % h for h in head), '\n'.join(rows)))
        return '\n\n'.join(out)

    def fields(self, per):
        path = os.path.join(self.root, 'deck', 'fields.tsv')
        if not os.path.isfile(path):
            self.err('FIELDS: deck/fields.tsv 가 없다 (python3 tools/appendix.py)')
            return ''
        lines = [ln.split('\t') for ln in read(path).split('\n')[1:] if ln]
        where = tsv(os.path.join(self.root, 'deck', 'proto_where.tsv'), 'name')
        groups = []
        for f in lines:
            f = f + [''] * (9 - len(f))
            block, kind, name, json, typ, num, rule, oneof, comment = f[:9]
            if kind in ('message', 'enum'):
                w = where.get(block, {}).get('where')
                label = '<a href="#%s">%s</a>' % (w, esc(block)) if w else esc(block)
                top = ('<tr><th colspan="4">%s%%s <span class="en">%s%s</span></th></tr>'
                       % (label, kind + ' — ' if kind == 'enum' else '', ticks(comment)))
                groups.append((block, top, []))
            elif kind in ('field', 'value') and groups:
                mark = {'REQUIRED': ' <b>필수</b>', 'DEPRECATED': ' <b>폐기</b>'}.get(rule, '')
                sub = '<br><span class="en">oneof %s</span>' % esc(oneof) if oneof else ''
                groups[-1][2].append('<tr><td><code>%s</code>%s%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                                     % (esc(json), mark, sub, '<code>%s</code>' % esc(typ) if typ else '',
                                        esc(num), ticks(comment)))
        return self.grouped_pages('fields', '필드 사전', ('필드(JSON)', '타입', '#', '뜻(proto 주석)'),
                                  groups, per)

    def index(self, per):
        path = os.path.join(self.root, 'deck', 'index.tsv')
        if not os.path.isfile(path):
            self.err('INDEX: deck/index.tsv 가 없다 (python3 tools/appendix.py)')
            return ''
        rows, keys = [], []
        for ln in read(path).split('\n')[1:]:
            if not ln:
                continue
            ident, kind, where = (ln.split('\t') + ['', ''])[:3]
            links = []
            for sid in [w for w in where.split(',') if w]:
                if sid not in self.pageno:
                    self.err('INDEX: %s 의 슬라이드 %s 가 앞 부에 없다 — 찾아보기가 낡았다 '
                             '(python3 tools/appendix.py)' % (ident, sid))
                    continue
                links.append('<a href="#%s">%d</a>' % (sid, self.pageno[sid]))
            rows.append(('<code>%s</code>' % esc(ident), esc(kind), ' · '.join(links)))
            keys.append(ident)
        return self.pages('index', '찾아보기', ('이름', '종류', '쪽'), rows, per, keys)

    def quizzes(self, per):
        parts = []
        for part, sid, chap in self.quiz_list:
            if not parts or parts[-1][0] != part:
                parts.append((part, []))
            parts[-1][1].append('<a href="#%s">%s</a>' % (sid, esc(chap)))
        rows = [('<a href="#p%02d">%d부</a> %s' % (p, p, esc(self.part_title.get(p, ''))), ' · '.join(links))
                for p, links in parts]
        return self.pages('quizzes', '퀴즈 모음', ('부', '장마다 퀴즈'), rows, per)

    def generated(self, name, a):
        per = int(a['per']) if a.get('per', '').isdigit() else 12
        if name == 'FIELDS':
            return self.fields(per)
        if name == 'INDEX':
            return self.index(per)
        if name == 'QUIZZES':
            return self.quizzes(per)
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
        if name in GENERATORS:
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
        if name == 'SPEC':
            return self.spec(a)
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
                bad = CODELIKE.search('\n'.join(body))
                if bad:
                    self.err('그림(<pre class="fig">)에 코드·JSON·HTTP 처럼 보이는 줄: %s'
                             % bad.group(0).strip()[:40])
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
        holes = PRE.sub('', body).count(PLACEHOLDER)
        if holes:
            self.r.holes_per_part[part] = self.r.holes_per_part.get(part, 0) + holes
            self.r.placeholders += holes
            if not self.skel:
                self.err('"%s" 플레이스홀더가 %d곳 남았다' % (PLACEHOLDER, holes))
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
            self.count += 1
            self.pageno[sid] = self.count
            self.collect(part, sid, m.group(1), m.group(2))
            self.links += [(fname, h) for h in re.findall(r'href="#([^"]+)"', m.group(2))]
            self.nav_item(part, sid, m.group(1), m.group(2))
        if body.count('<article') != n or body.count('</article>') != n:
            self.err('<article> 열고 닫는 수가 맞지 않는다')
        self.r.per_part[part] = self.r.per_part.get(part, 0) + n
        return body

    def collect(self, part, sid, attrs, inner):
        """퀴즈 모음의 재료 — 부 표지의 제목, 장 표지의 "N장", 퀴즈 슬라이드."""
        if sid == 'p%02d' % part:
            h = re.search(r'<h2[^>]*>(.*?)</h2>', inner, re.S)
            if h:
                self.part_title[part] = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', h.group(1))).strip()
            return
        num = re.search(r'<p class="chnum">(.*?)</p>', inner)
        if num:
            self.chapter = re.sub(r'<[^>]+>', '', num.group(1)).strip()
        if re.search(r'class="[^"]*\bquiz\b', attrs):
            self.quiz_list.append((part, sid, self.chapter if self.chapter_part == part else '퀴즈'))
        if num:
            self.chapter_part = part

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
        self.count, self.pageno = 0, {}            # 슬라이드 id → 덱의 쪽 번호(1부터)
        self.quiz_list, self.part_title = [], {}
        self.chapter, self.chapter_part = '', None
        self.nav = ['    <option value="top">챕터 이동…</option>']
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
        self.want = {}
        for ln in read(os.path.join(self.root, 'deck', 'budget.txt')).split('\n'):
            f = ln.split()
            if len(f) == 2 and f[0].isdigit():
                self.want[int(f[0])] = int(f[1])
        for part in sorted(self.r.per_part):
            n, w = self.r.per_part[part], self.want.get(part)
            if w is None:
                self.err('%d부의 예산이 budget.txt 에 없다' % part)
            elif n > w * 1.1:
                self.err('%d부 %d장 — 예산 %d장을 10 %% 넘게 넘었다' % (part, n, w))
            elif n < w * 0.8 and not self.skel:
                self.r.warns.append('%d부 %d장 — 예산 %d장에 20 %% 넘게 모자란다' % (part, n, w))

    def coverage(self):
        for ex in a2arun.sources(self.root):
            if ex not in self.used:
                msg = '어느 슬라이드도 싣지 않는 예제: %s' % ex
                (self.r.warns if self.skel else self.r.errors).append(msg)


def build(root=ROOT, skel=False):
    b = Builder(root, skel)
    r = b.build()
    r.want = getattr(b, 'want', {})
    return r


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
    for p in sorted(r.per_part):
        print('  %2d부 %4d장 / 예산 %4s%s' % (p, r.per_part[p], r.want.get(p, '?'),
                                            ' · 플레이스홀더 %d곳' % r.holes_per_part[p]
                                            if r.holes_per_part.get(p) else ''))
    print('  %s — %d장, 플레이스홀더 %d곳, 오류 %d건, 알림 %d건'
          % (TARGET_NAME, r.slides, r.placeholders, len(r.errors), len(r.warns)))
    return 1 if r.errors else 0


if __name__ == '__main__':
    sys.exit(main())
