# -*- coding: utf-8 -*-
"""excerpt.py — 받아 둔 펌웨어·규약 소스에서 40줄 이하를 잘라 싣는다.

    python3 tools/excerpt.py FILE START END KEY --why '왜 이 창인가'
    python3 tools/excerpt.py --all          # INDEX.tsv 대로 다시 자른다
    python3 tools/excerpt.py --pin OWNER/REPO PATH [REF]

PLAN.md §0.14 의 규칙을 기계로 지킨다. 남의 코드(PX4 BSD-3,
ArduPilot·Betaflight GPL-3, MAVLink)는 덱에 한 조각 40줄까지만
싣고, 조각마다 머리 한 줄에 '저장소 경로 @커밋 L시작-끝 · 라이선스 ·
받은 날' 을 그 언어의 주석으로 적는다. 덱의 <!--CODE file=
data/excerpts/…--> 는 이 파일만 가리킨다.

재현성: 커밋 sha 는 주소에 박혀 있어야 한다. data/cite_keys.tsv 의
url 이 raw.githubusercontent.com/<owner>/<repo>/<40자 sha>/<path>
꼴이 아니면(main·master 같은 가지 이름이면) 거절한다 — 가지는 날마다
움직여 같은 줄 번호가 다른 코드를 가리키게 된다. sha 는 --pin 이
GitHub API(repos/…/commits?path=…&per_page=1)에서 받아 준다.

FILE 은 docs/raw/ 아래 원문(make docs 가 받은 것), 받은 날은
docs/FETCHED.txt 에서 읽는다. 잘라 낸 기록은 data/excerpts/INDEX.tsv
(key | repo | path | sha | start | end | licence | why). O(파일 길이).
"""
import io
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DOCS = os.path.join(BASE, 'docs')
OUT = os.path.join(BASE, 'data', 'excerpts')
INDEX = os.path.join(OUT, 'INDEX.tsv')
sys.path.insert(0, HERE)
import fetch_docs                                      # noqa: E402

MAX_LINES = 40
ICOLS = ('key', 'repo', 'path', 'sha', 'start', 'end', 'licence', 'why')
# 언어별 한 줄 주석 (앞, 뒤)
COMMENT = {'c': ('// ', ''), 'cpp': ('// ', ''), 'h': ('// ', ''),
           'hpp': ('// ', ''), 'js': ('// ', ''), 'py': ('# ', ''),
           'sh': ('# ', ''), 'xml': ('<!-- ', ' -->'),
           'html': ('<!-- ', ' -->')}
RAW = re.compile(r'^https://raw\.githubusercontent\.com/([^/]+/[^/]+)/'
                 r'([^/]+)/(.+)$')


def parse_raw_url(url):
    """sha 로 박힌 raw 주소 → {'repo', 'sha', 'path'}.

    raw.githubusercontent.com 이 아니거나 sha 가 아니면 ValueError.
    """
    m = RAW.match(url)
    if not m:
        raise ValueError('GitHub raw 주소가 아니다: ' + url)
    if not re.match(r'^[0-9a-f]{40}$', m.group(2)):
        raise ValueError('커밋 sha 로 박힌 주소가 아니다(가지 %s) — '
                         '--pin 으로 sha 를 받아 url 을 고칠 것'
                         % m.group(2))
    return dict(repo=m.group(1), sha=m.group(2), path=m.group(3))


def header(ext, repo, path, sha, start, end, licence, date):
    """머리 한 줄 — 그 언어의 주석으로."""
    if ext not in COMMENT:
        raise ValueError('주석 문법을 모르는 확장자: ' + ext)
    a, b = COMMENT[ext]
    return '%s%s %s @%s L%d-%d · %s · fetched %s%s' % (
        a, repo, path, sha, start, end, licence, date, b)


def cut(text, start, end):
    """1부터 세는 줄 start..end(끝 포함). 40줄 넘으면 거절."""
    ls = text.split('\n')
    if text.endswith('\n'):
        ls.pop()
    if start < 1 or end < start or end > len(ls):
        raise ValueError('줄 범위 %d-%d 가 1-%d 밖이다'
                         % (start, end, len(ls)))
    if end - start + 1 > MAX_LINES:
        raise ValueError('%d줄 — 발췌는 %d줄까지다(PLAN.md §0.14)'
                         % (end - start + 1, MAX_LINES))
    return ls[start - 1:end]


def render(ext, repo, path, sha, start, end, licence, date, text):
    """발췌 파일의 글: 머리 한 줄 + 잘라 낸 줄들."""
    body = cut(text, start, end)
    return '\n'.join([header(ext, repo, path, sha, start, end, licence,
                             date)] + body) + '\n'


def read_index(path):
    if not os.path.exists(path):
        return []
    rows, head = [], None
    with io.open(path, encoding='utf-8') as f:
        for line in f.read().split('\n'):
            if not line.strip() or line.startswith('#'):
                continue
            cols = line.split('\t')
            if head is None:
                head = cols
                continue
            rows.append(dict(zip(head, cols)))
    return rows


def write_index(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\t'.join(ICOLS) + '\n')
        for r in rows:
            f.write('\t'.join(str(r[c]) for c in ICOLS) + '\n')


def upsert(rows, row):
    """같은 key 가 있으면 바꾸고, 없으면 뒤에 붙인다."""
    out = [row if r['key'] == row['key'] else r for r in rows]
    if not any(r['key'] == row['key'] for r in rows):
        out.append(row)
    return out


# ------------------------------------------------------------ 실행
def _cite_row_for_raw(rel):
    """docs/ 기준 'raw/…' 경로 → 그 원문을 낸 cite_keys 행."""
    rows, _ = fetch_docs.read_keys(fetch_docs.KEYS)
    for r in rows:
        if any(fetch_docs.raw_path(r['file'], f) == rel
               for f in fetch_docs.EXT):
            return r
    raise SystemExit('cite_keys.tsv 에 %s 를 낸 행이 없다' % rel)


def _fetch_date(file):
    line = fetch_docs.read_fetched(
        os.path.join(DOCS, 'FETCHED.txt')).get(file)
    if not line:
        raise SystemExit('docs/FETCHED.txt 에 %s 가 없다 (make docs)'
                         % file)
    return line.split('\t')[2]


def make(rel, start, end, key, why):
    """발췌 하나를 쓰고 INDEX 행을 돌려준다."""
    row = _cite_row_for_raw(rel)
    pin = parse_raw_url(row['url'])
    with io.open(os.path.join(DOCS, rel), encoding='utf-8') as f:
        text = f.read()
    ext = pin['path'].rsplit('.', 1)[-1]
    out = render(ext, pin['repo'], pin['path'], pin['sha'], start, end,
                 row['licence'], _fetch_date(row['file']), text)
    os.makedirs(OUT, exist_ok=True)
    with io.open(os.path.join(OUT, '%s.%s' % (key, ext)), 'w',
                 encoding='utf-8', newline='\n') as f:
        f.write(out)
    return dict(key=key, repo=pin['repo'], path=pin['path'],
                sha=pin['sha'], start=str(start), end=str(end),
                licence=row['licence'], why=why)


def raw_for(repo, path, sha):
    """INDEX 행 → docs/ 기준 원문 경로. cite_keys 의 sha 와 대조."""
    rows, _ = fetch_docs.read_keys(fetch_docs.KEYS)
    for r in rows:
        try:
            pin = parse_raw_url(r['url'])
        except ValueError:
            continue
        if (pin['repo'], pin['path']) == (repo, path):
            if pin['sha'] != sha:
                raise SystemExit('%s: cite_keys 의 sha %s ≠ INDEX 의 %s'
                                 % (path, pin['sha'][:12], sha[:12]))
            return fetch_docs.raw_path(r['file'], 'c')
    raise SystemExit('cite_keys.tsv 에 %s/%s 행이 없다' % (repo, path))


def pin(repo, path, ref=None):
    """GitHub API → (sha, 커밋 날짜) — path 를 마지막으로 바꾼 커밋."""
    url = ('https://api.github.com/repos/%s/commits?path=%s&per_page=1'
           % (repo, path)) + ('&sha=' + ref if ref else '')
    req = urllib.request.Request(url, headers={'User-Agent':
                                               fetch_docs.UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        c = json.loads(r.read().decode('utf-8'))[0]
    return c['sha'], c['commit']['committer']['date']


def main(argv):
    if argv[:1] == ['--pin']:
        sha, date = pin(*argv[1:4])
        print('%s\t%s' % (sha, date))
        return 0
    rows = read_index(INDEX)
    if argv[:1] == ['--all']:
        for r in rows:
            rel = raw_for(r['repo'], r['path'], r['sha'])
            make(rel, int(r['start']), int(r['end']), r['key'],
                 r['why'])
        print('data/excerpts/ — 발췌 %d개를 다시 잘랐다' % len(rows))
        return 0
    why = ''
    if '--why' in argv:
        k = argv.index('--why')
        why = argv[k + 1]
        del argv[k:k + 2]
    if len(argv) != 4:
        sys.stderr.write(__doc__)
        return 2
    rel = os.path.relpath(os.path.abspath(argv[0]), DOCS)
    old = [r for r in rows if r['key'] == argv[3]]
    why = why or (old[0]['why'] if old else '')
    if not why:
        raise SystemExit('새 발췌에는 --why 가 있어야 한다(INDEX.tsv)')
    row = make(rel, int(argv[1]), int(argv[2]), argv[3], why)
    write_index(INDEX, upsert(rows, row))
    print('data/excerpts/%s.%s — %s L%s-%s' % (
        row['key'], row['path'].rsplit('.', 1)[-1], row['path'],
        row['start'], row['end']))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
