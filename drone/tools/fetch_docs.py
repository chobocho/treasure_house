# -*- coding: utf-8 -*-
"""fetch_docs.py — data/cite_keys.tsv 의 1차 문서를 docs/ 로 받는다.

    python3 tools/fetch_docs.py              # 전부 다시 받는다
    python3 tools/fetch_docs.py --missing    # 없는 것만
    python3 tools/fetch_docs.py --only KEY   # 키 하나만

이 덱의 세 심판 가운데 둘째다(PLAN.md §0.3). 펌웨어·통신 규약·법령·
논문에 관한 문장은 모두 여기서 받은 글의 '§' 절 하나로 되짚을 수
있어야 한다(<!--CITE key=… sec=…-->, deck/cites.py).

표 한 줄 = 문서 하나. 칸은 key | name | url | kind | licence | file.
받은 원문은 docs/raw/…, 바꾼 글은 docs/<file>. 어떻게 바꿀지는
주소와 내용의 모양으로 정한다(detect):

  html  → html_text.convert        pdf  → tools/pdf_text.sh
  ecfr  → html_text.convert_ecfr   law  → html_text.convert_law
  md    → html_text.convert_md
  c     → 글 그대로 + 첫 줄 '§ 파일 이름' + 함수마다 '§ 함수 이름'
  xml·json·text → 글 그대로 + 첫 줄 '§ 파일 이름'

파일마다 docs/FETCHED.txt 에 '경로 | 주소 | 날짜 | sha256(원문) |
첫 제목' 한 줄. docs/ 는 커밋하지 않는 캐시이고 FETCHED.txt 만
커밋해 "그날 무엇을 봤는가" 를 남긴다.

남의 서버에 예의를: 요청 사이 0.3초, 20초 제한, 세 번까지 다시.
eCFR API 는 압축을 요구한다(Accept-Encoding 이 없으면 406) — gzip 을
청하고 푼다. O(문서 수) 요청.
"""
import datetime
import gzip
import hashlib
import io
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DOCS = os.path.join(BASE, 'docs')
KEYS = os.path.join(BASE, 'data', 'cite_keys.tsv')
sys.path.insert(0, HERE)
import html_text                                       # noqa: E402

UA = 'Mozilla/5.0 (treasure_house drone deck; research)'
KINDS = ('doc', 'code', 'paper', 'law', 'spec', 'history', 'press',
         'web')
COLS = ('key', 'name', 'url', 'kind', 'licence', 'file')
C_EXT = ('.c', '.cc', '.cpp', '.h', '.hpp')
# 원문 파일의 확장자 — file 칸에 이미 있으면 그대로 쓴다
EXT = {'html': '.html', 'pdf': '.pdf', 'ecfr': '.xml', 'law': '.xml',
       'xml': '.xml', 'json': '.json', 'md': '.md', 'c': '',
       'text': '.txt'}
KNOWN = set(C_EXT) | {'.xml', '.json', '.md', '.py', '.txt', '.pdf',
                      '.html', '.js', '.csv'}


# ------------------------------------------------------------ 표
def read_keys(path):
    """cite_keys.tsv → (행 목록, 잘못 목록). 행은 {칸: 값}."""
    with io.open(path, encoding='utf-8') as f:
        text = f.read()
    rows, bad, head = [], [], None
    seen_k, seen_f = set(), set()
    for n, line in enumerate(text.split('\n'), 1):
        if not line.strip() or line.startswith('#'):
            continue
        cols = [c.strip() for c in line.split('\t')]
        if head is None:
            head = cols
            if tuple(head) != COLS:
                bad.append('%d: 칸 이름이 %s 가 아니다' % (n, COLS))
            continue
        r = dict(zip(head, cols))
        why = []
        if not r.get('url', '').startswith('https://'):
            why.append('url 이 https:// 가 아니다')
        if r.get('kind') not in KINDS:
            why.append('kind %r 는 %s 가 아니다'
                       % (r.get('kind'), KINDS))
        if not r.get('file', '').endswith('.txt'):
            why.append('file 은 docs/ 아래 .txt 여야 한다')
        if r.get('key') in seen_k:
            why.append('키가 겹친다')
        if r.get('file') in seen_f:
            why.append('file 이 겹친다')
        seen_k.add(r.get('key'))
        seen_f.add(r.get('file'))
        if why:
            bad.append('%d: %s — %s'
                       % (n, r.get('key'), ', '.join(why)))
        else:
            rows.append(r)
    return rows, bad


def select(rows, only, missing, exists):
    """받을 행. only 는 키 하나(없는 키면 KeyError).

    missing 이면 exists(행) 가 거짓인 행만.
    """
    if only is not None:
        pick = [r for r in rows if r['key'] == only]
        if not pick:
            raise KeyError(only)
        return pick
    return [r for r in rows if not (missing and exists(r))]


# ------------------------------------------------------------ 바꾸기
def detect(url, data):
    """주소와 원문 앞머리 → 바꾸는 방법 이름."""
    path = url.split('?')[0].split('#')[0].lower()
    head = data[:2048].lstrip()
    low = head.lower()
    if head.startswith(b'%PDF'):
        return 'pdf'
    if path.endswith(C_EXT):
        return 'c'
    if path.endswith('.md'):
        return 'md'
    if b'<DIV5' in head or b'<DIV8' in head:
        return 'ecfr'
    if '<법령'.encode('utf-8') in head:
        return 'law'
    if low.startswith((b'<!doctype html', b'<html')) or b'<html' in low:
        return 'html'
    if head.startswith(b'<?xml') or path.endswith('.xml'):
        return 'xml'
    if head[:1] in (b'{', b'['):
        return 'json'
    return 'text'


def raw_path(file, fmt):
    """docs/ 아래 원문 경로. 'a/b.cpp.txt' → 'raw/a/b.cpp'."""
    base = file[:-4] if file.endswith('.txt') else file
    if os.path.splitext(base)[1] in KNOWN:
        return 'raw/' + base
    return 'raw/' + base + EXT[fmt]


# 줄머리에서 시작하는 함수 정의: 이름 바로 뒤에 '(' 가 온다.
# 매크로 줄(#…), 주석, 들여쓴 줄, 제어문은 후보가 아니다.
# 이름 앞은 줄머리이거나 빈칸·*·& 다(생성자 'A::A(' 도 잡는다).
_C_CAND = re.compile(r'^(?:[A-Za-z_][^;=(]*?[\s*&])?'
                     r'([A-Za-z_~][\w:~]*)\s*\(')
_C_NOT = re.compile(r'^(return|if|else|for|while|switch|case|do|'
                    r'typedef|using|namespace|extern)\b')
_ATTR = re.compile(r'__attribute__\s*\(\(.*?\)\)')


def _c_function(ls, i):
    """ls[i] 가 최상위 함수 정의의 첫 줄이면 함수 이름, 아니면 None.

    뒤따르는 여덟 줄 안에서 '{' 가 ';' 보다 먼저 오면 정의다 —
    'PG_RESET_TEMPLATE(…);' 같은 매크로 호출과 선언을 거른다.
    """
    line = _ATTR.sub('', ls[i])
    if _C_NOT.match(line):
        return None
    m = _C_CAND.match(line)
    if not m:
        return None
    rest = '\n'.join([line[m.end():]] + ls[i + 1:i + 9])
    rest = re.sub(r'//[^\n]*', '', rest)
    b, s = rest.find('{'), rest.find(';')
    if b < 0 or (0 <= s < b):
        return None
    return m.group(1)


def c_headings(text):
    """C/C++ 소스의 최상위 함수 정의 앞에 '§<TAB>이름' 줄을 넣는다.

    원래 줄은 한 글자도 바꾸지 않는다(§ 줄을 빼면 원문과 같다).
    /* … */ 주석 안은 보지 않는다. O(줄 수 × 8).
    """
    ls = text.split('\n')
    out, in_comment = [], False
    for i, line in enumerate(ls):
        if in_comment:
            in_comment = '*/' not in line
        elif line.lstrip().startswith('/*') and '*/' not in line:
            in_comment = True
        else:
            name = _c_function(ls, i)
            if name:
                out.append('§\t' + name)
        out.append(line)
    return '\n'.join(out)


def code_text(name, text, fmt):
    """글 그대로 + 첫 줄 '§ 이름'. C/C++ 이면 함수 절 줄도.

    끝 줄바꿈이 없으면 하나 붙인다 — 그 밖의 글자는 그대로다.
    """
    body = c_headings(text) if fmt == 'c' else text
    if not body.endswith('\n'):
        body += '\n'                  # 끝 줄바꿈이 없는 원문도 있다
    return '§\t' + name + '\n' + body


def pdf_text(raw_file):
    """PDF → 절 줄을 넣은 글 (tools/pdf_text.sh)."""
    sh = os.path.join(HERE, 'pdf_text.sh')
    r = subprocess.run(['sh', sh, raw_file], capture_output=True,
                       timeout=120)
    if r.returncode != 0:
        raise RuntimeError('pdf_text.sh: ' +
                           r.stderr.decode('utf-8', 'replace'))
    return r.stdout.decode('utf-8', 'replace')


def convert(fmt, data, name, raw_file=None):
    """원문 바이트 → 인용용 글. pdf 는 원문 파일 경로가 필요하다."""
    if fmt == 'pdf':
        return pdf_text(raw_file)
    text = data.decode('utf-8', 'replace')
    if fmt == 'html':
        return html_text.convert(text)
    if fmt == 'md':
        return html_text.convert_md(text)
    if fmt == 'ecfr':
        return html_text.convert_ecfr(text)
    if fmt == 'law':
        return html_text.convert_law(text)
    return code_text(name, text, fmt)


def first_heading(text):
    """'§' 제목 줄의 글('#id' 절 줄은 건너뛴다), 없으면 첫 줄."""
    first = ''
    for line in text.split('\n'):
        if line.startswith('§\t') and not line.startswith('§\t#'):
            return line[2:]
        if not first and line.strip():
            first = line.strip()
    return first


def fetched_line(path, url, date, data, head):
    return '\t'.join((path, url, date, hashlib.sha256(data).hexdigest(),
                      head))


# ------------------------------------------------------------ 받기
def get(url):
    """주소 하나 → 바이트. 20초 제한, 세 번까지, 리다이렉트는 따른다.

    404·403·410 은 다시 해도 같으니 바로 멈춘다. 실패는
    RuntimeError('HTTP 403 …') — main 이 상태를 그대로 적는다.
    """
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': UA, 'Accept-Encoding': 'gzip'})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
                if r.headers.get('Content-Encoding') == 'gzip':
                    data = gzip.decompress(data)
                return data
        except urllib.error.HTTPError as e:
            last = 'HTTP %d' % e.code
            if e.code in (403, 404, 410):
                break
        except (urllib.error.URLError, OSError) as e:
            last = str(e)
        time.sleep(0.3 * (attempt + 1))
    raise RuntimeError('%s — %s' % (last, url))


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


def read_fetched(path):
    """FETCHED.txt → {경로: 줄}."""
    out = {}
    if os.path.exists(path):
        with io.open(path, encoding='utf-8') as f:
            for line in f.read().split('\n'):
                if line and not line.startswith('#'):
                    out[line.split('\t')[0]] = line
    return out


def fetch_one(r, today):
    """행 하나를 받아 원문·글을 쓰고 FETCHED 줄을 낸다."""
    data = get(r['url'])
    fmt = detect(r['url'], data)
    raw = os.path.join(DOCS, raw_path(r['file'], fmt))
    save(raw, data)
    name = os.path.basename(r['file'][:-4])
    text = convert(fmt, data, name, raw)
    save(os.path.join(DOCS, r['file']), text.encode('utf-8'))
    return fetched_line(r['file'], r['url'], today, data,
                        first_heading(text))


def main(argv):
    missing = '--missing' in argv
    only = argv[argv.index('--only') + 1] if '--only' in argv else None
    rows, bad = read_keys(KEYS)
    for b in bad:
        print('  ✗ cite_keys.tsv ' + b)
    if bad:
        return 1
    today = datetime.date.today().isoformat()
    fpath = os.path.join(DOCS, 'FETCHED.txt')
    log = read_fetched(fpath)

    def exists(r):
        return (os.path.exists(os.path.join(DOCS, r['file']))
                and r['file'] in log)
    fails = []
    todo = select(rows, only, missing, exists)
    for r in todo:
        try:
            log[r['file']] = fetch_one(r, today)
            print('  ✓ %-28s %s' % (r['key'], r['file']))
        except RuntimeError as e:
            fails.append('%s: %s' % (r['key'], e))
        time.sleep(0.3)
    order = [r['file'] for r in rows if r['file'] in log]
    os.makedirs(DOCS, exist_ok=True)
    with io.open(fpath, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# make docs 가 쓴다 — 경로\t주소\t받은 날\t'
                'sha256(원문)\t첫 제목\n')
        f.write('\n'.join(log[p] for p in order) + '\n')
    for b in fails:
        print('  ✗ ' + b)
    print('docs/ — 표 %d줄 · 이번에 받은 것 %d · 실패 %d'
          % (len(rows), len(todo) - len(fails), len(fails)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
