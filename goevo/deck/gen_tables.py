#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/*.tsv (+ out/manifest.json) → 덱이 싣는 HTML 표를 만든다.

    python3 deck/gen_tables.py           # out/tbl_*.html 을 다시 만든다
    python3 deck/gen_tables.py --check   # 지금 것과 같은지 대조만 한다

왜 표를 손으로 안 쓰는가: 이 덱의 표는 대부분 "릴리스 날짜·버전·API 수·GODEBUG 설정"
같은 사실의 나열이다. 그런 표는 한 칸만 틀려도 티가 안 나고, 본문과 표가
어긋나면 어느 쪽이 맞는지 아무도 모른다. 사실은 data/*.tsv 한 곳에만 적고
(행마다 출처 칸이 있다), 표는 거기서 만든다. 그러면 고칠 곳이 늘 한 곳이다.

새 표가 필요하면 VIEWS 에 한 줄 더한다. TSV 전체를 그대로 싣는 표는
따로 적지 않아도 tbl_<이름>.html 로 언제나 만들어진다.

시간·공간 모두 O(행 수).
"""
import hashlib
import html
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cites  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, 'data')
OUT = os.path.join(BASE, 'out')

# 잘라 보는 표. (내보낼 이름, 원본 tsv, 실을 칸 이름들, 거르개)
# 거르개는 (칸 이름, 값) — 그 칸이 그 값인 행만 싣는다. 없으면 전부.
VIEWS = [
    # PLAN.md §5 7단계(릴리스 개관 표 tbl_rel_1.N.html)와 부를 쓸 때마다 는다.
]

# 이 칸은 표에 글자로 싣지 않고 '출처' 링크로 바꾼다.
LINKCOLS = ('source', 'url')


def read(p):
    return io.open(p, encoding='utf-8').read()


def rows_of(name):
    """TSV 를 (칸 이름 목록, 행 목록) 으로. 첫 줄이 칸 이름, #은 주석."""
    text = read(os.path.join(DATA, name))
    head, body = None, []
    for line in text.split('\n'):
        if not line.strip() or line.startswith('#'):
            continue
        cols = [c.strip() for c in line.split('\t')]
        if head is None:
            head = cols
        else:
            # 칸이 모자라면 빈 칸으로 채운다 — 줄이 어긋나는 것보다 낫다
            cols += [''] * (len(head) - len(cols))
            body.append(cols[:len(head)])
    return head or [], body


def is_num(v):
    try:
        float(v.replace(',', ''))
        return True
    except ValueError:
        return False


def render(head, body, cols=None):
    """<table> 한 덩어리. 칸 이름은 그대로 머리글이 된다."""
    idx = [head.index(c) for c in cols] if cols else list(range(len(head)))
    numeric = [all(is_num(r[i]) for r in body) if body else False for i in idx]
    out = ['<table>']
    out.append('<tr>' + ''.join(
        '<th%s>%s</th>' % (' class="num"' if numeric[k] else '',
                           html.escape(head[i]))
        for k, i in enumerate(idx)) + '</tr>')
    for r in body:
        tds = []
        for k, i in enumerate(idx):
            v = r[i]
            if head[i] in LINKCOLS and v.startswith('http'):
                cell = '<a href="%s">출처</a>' % html.escape(v, quote=True)
            else:
                cell = html.escape(v)
            tds.append('<td%s>%s</td>'
                       % (' class="num"' if numeric[k] else '', cell))
        out.append('<tr>' + ''.join(tds) + '</tr>')
    out.append('</table>')
    return '\n'.join(out) + '\n'


KIND_NAMES = [('lang', '언어'), ('toolchain', '도구'), ('runtime', '런타임'),
              ('stdlib', '표준 라이브러리'), ('platform', '플랫폼'),
              ('ecosystem', '생태계')]


def release_tables(releases, features, api, drafts=()):
    """큰 릴리스마다 개관 표 하나 — tbl_rel_1.N.html (PLAN.md §3.4).

    날짜는 releases.tsv, 갈래마다의 기능은 features 의 그 버전 행 전부
    (전용 장이 있으면 그리로 가는 링크), API 줄은 api_added.tsv 에서.
    표가 기능 목록에서 곧장 만들어지므로 개관 장과 목록이 어긋날 수 없다
    (PLAN.md §5 7단계의 대조가 구조로 풀린다). O(행 수)."""
    e = lambda s: html.escape(s, quote=False)
    out = {}
    # 초안 노트만 있는 판(drafts)은 날짜 대신 '초안' 이라고 적는다
    items = [(r['version'], r['date']) for r in releases
             if r.get('kind') == 'major']
    items += [('go' + d, '아직 나오지 않음 — 초안') for d in drafts]
    for version, date in items:
        parts = version[2:].split('.')
        ver = '1.0' if parts == ['1'] else '.'.join(parts[:2])
        rows = ['<table class="kv">',
                '<tr><th>날짜</th><td>%s</td></tr>' % e(date)]
        mine = [f for f in features if f.get('version') == ver]
        for kind, name in KIND_NAMES:
            items = []
            for f in mine:
                if f.get('kind') != kind:
                    continue
                t = e(f.get('title', ''))
                sid = f.get('slide-id', '')
                items.append('<a href="#%s">%s</a>' % (sid, t) if sid else t)
            rows.append('<tr><th>%s</th><td>%s</td></tr>'
                        % (name, ' · '.join(items) or '—'))
        for a in api:
            if a.get('version') == ver:
                pk = a.get('sample-packages', '')
                rows.append('<tr><th>API</th><td>새 패키지 %s개%s · 새 기호 %s개'
                            '</td></tr>' % (a['new-packages'],
                                           '(%s)' % e(pk) if pk else '',
                                           a['new-symbols']))
        rows.append('</table>')
        out['tbl_rel_%s.html' % ver] = '\n'.join(rows) + '\n'
    return out


MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']


def _table(head, rows, numcols=()):
    """머리글과 행 → <table>. numcols 의 칸은 오른쪽 맞춤(num)."""
    e = lambda s: html.escape(str(s), quote=False)
    out = ['<table>', '<tr>' + ''.join(
        '<th%s>%s</th>' % (' class="num"' if i in numcols else '', e(h))
        for i, h in enumerate(head)) + '</tr>']
    for r in rows:
        out.append('<tr>' + ''.join(
            '<td%s>%s</td>' % (' class="num"' if i in numcols else '', e(c))
            for i, c in enumerate(r)) + '</tr>')
    out.append('</table>')
    return '\n'.join(out) + '\n'


def _chunks(prefix, head, rows, per, numcols=()):
    """긴 표를 per 행씩 여러 장으로 — 접힌 화면에서 한 장에 들게."""
    return dict(('tbl_%s_%d.html' % (prefix, k // per + 1),
                 _table(head, rows[k:k + per], numcols))
                for k in range(0, len(rows), per))


def appendix_tables(releases, api, godebug, blog_index, fetched, per=14,
                    min_posts=3):
    """부록(11부)의 표 — 전부 data/ 와 docs/ 에서 (PLAN.md §4 의 A 줄).

    일정표: 큰 릴리스마다 고침판(부 릴리스)의 수와 마지막 고침판.
    API 표: api_added.tsv 그대로(Go 1 의 126 패키지는 줄이 넘쳐 적지 않는다).
    GODEBUG 표: godebug.tsv 를 per 행씩.
    저자 색인(인물 색인): 블로그 색인의 저자 칸에서 사람마다 글 수와 첫·끝 날짜
    (글 min_posts 편 이상).
    출처 목록: docs/FETCHED.txt 의 경로를 종류별로 센다. O(행 수)."""
    out = {}
    majors, cur = [], None
    for r in releases:
        if r['kind'] == 'major':
            cur = [r['version'], r['date'], []]
            majors.append(cur)
        elif cur is not None:
            cur[2].append(r)
    rows = [(v, d, len(m), '%s (%s)' % (m[-1]['version'], m[-1]['date'])
             if m else '—') for v, d, m in majors]
    out.update(_chunks('app_majors', ['판', '날짜', '고침판', '마지막 고침판'],
                       rows, per, (2,)))
    rows = [(a['version'], a['new-packages'], a['new-symbols'],
             a['syscall-symbols'], '(Go 1 의 전부)' if a['version'] == '1.0'
             else a['sample-packages'] or '—') for a in api]
    out.update(_chunks('app_api', ['판', '새 패키지', '새 기호', '그중 syscall',
                                   '새 패키지 이름'], rows, per, (1, 2, 3)))
    rows = [(g['setting'], g['package'], g['introduced-in'],
             g['default-changed-in'], g['old-value']) for g in godebug]
    out.update(_chunks('app_godebug', ['설정', '패키지', '처음 적힌 판',
                                       '기본값 바뀐 판', '옛 값'], rows, per))
    people = {}
    for m in re.finditer(r'<span class="date">(\d+) (\w+) (\d{4})</span><br>'
                         r'\s*<span class="author">(.*?)<br>', blog_index, re.S):
        date = '%s-%02d-%02d' % (m.group(3), MONTHS.index(m.group(2)) + 1,
                                 int(m.group(1)))
        names = re.sub(r',?\s+(?:on behalf of|for) the Go team.*$', '',
                       m.group(4))
        for n in re.split(r',\s*(?:and\s+)?|\s+and\s+', names):
            n = html.unescape(n.strip())
            # 팀 전체 이름의 글은 사람이 아니다(p11-people-read 가 그렇게 밝힌다)
            if n and not re.match(r'(?i)^the go team$', n):
                people.setdefault(n, []).append(date)
    # 인물 색인은 글 min_posts 편 이상인 사람만 — 한 편씩 쓴 사람까지 실으면 여덟 장이 된다
    rows = sorted(((n, len(ds), min(ds), max(ds)) for n, ds in people.items()
                   if len(ds) >= min_posts),
                  key=lambda r: (-r[1], r[0]))
    out.update(_chunks('app_authors', ['사람', '블로그 글', '처음', '마지막'],
                       rows, per, (1,)))
    kinds = [('릴리스 노트', 'relnotes/'), ('API 목록', 'api/'),
             ('블로그 글', 'blog/'), ('그 밖의 문서', '')]
    count = dict((k, 0) for k, _ in kinds)
    for p in fetched:
        if p == 'blog/index.txt' or not p.endswith('.txt'):
            continue
        for k, pre in kinds:
            if p.startswith(pre):
                count[k] += 1
                break
    out['tbl_app_sources.html'] = _table(['종류', '파일 수'],
                                         [(k, count[k]) for k, _ in kinds],
                                         (1,))
    return out


def flow_tables(timeline, godebug, features, per=14):
    """10부(흐름으로 다시 읽기)의 표.

    연표: timeline.tsv 를 per 행씩. GODEBUG: 판마다 문서에 처음 적힌 설정의
    수와 기본값이 바뀐 설정의 수 — 호환성 약속의 '비용' 이 판마다 얼마나
    드는지. 갈래: 부(시대)마다 기능 목록의 kind 별 행 수. O(행 수)."""
    out = _chunks('flow_timeline', ['날짜', '사건'],
                  [(r['date'], r['event']) for r in timeline], per)
    intro, changed = {}, {}
    for g in godebug:
        if g['introduced-in'] != '-':
            intro[g['introduced-in']] = intro.get(g['introduced-in'], 0) + 1
        if g['default-changed-in'] != '-':
            v = g['default-changed-in']
            changed[v] = changed.get(v, 0) + 1
    vs = sorted(set(intro) | set(changed),
                key=lambda v: tuple(int(x) for x in v.split('.')))
    out['tbl_flow_godebug.html'] = _table(
        ['판', '처음 적힌 설정', '기본값이 바뀐 설정'],
        [(v, intro.get(v, 0), changed.get(v, 0)) for v in vs], (1, 2))
    kinds = [k for k, _ in KIND_NAMES]
    parts = {}
    for f in features:
        m = re.search(r'/p(\d\d)[a-z]?\.tsv$', f.get('_file', ''))
        if m and f.get('kind') in kinds:
            row = parts.setdefault(int(m.group(1)), dict((k, 0) for k in kinds))
            row[f['kind']] += 1
    out['tbl_flow_kinds.html'] = _table(
        ['부'] + [n for _, n in KIND_NAMES],
        [('%d부' % p,) + tuple(parts[p][k] for k in kinds)
         for p in sorted(parts)], tuple(range(1, len(kinds) + 1)))
    return out


# 갈래마다 한 장에 싣는 판의 수 — 도구·표준 라이브러리는 판마다 줄이
# 길어 적게 싣는다(접힌 화면에서 한 장이 넘치지 않게).
FLOW_PER = {'lang': 10, 'runtime': 9, 'toolchain': 6, 'stdlib': 5,
            'platform': 10, 'ecosystem': 10}


def flow_kind_tables(features, per=None):
    """10부 '네 갈래' — 갈래(kind)마다 판 순서의 표 tbl_flow_<kind>_N.html.

    한 판의 기능은 한 칸에 · 로 잇고, 전용 장이 있으면 그리로 링크한다.
    기능 목록에서 곧장 만들므로 8부처럼 나중에 쓴 부도 저절로 들어온다.
    O(행 수 · log 판 수)."""
    per = dict(FLOW_PER, **(per or {}))
    e = lambda s: html.escape(s, quote=False)
    out = {}
    for kind, _ in KIND_NAMES:
        byver = {}
        for f in features:
            if f.get('kind') != kind:
                continue
            t = e(f.get('title', ''))
            sid = f.get('slide-id', '')
            byver.setdefault(f['version'], []).append(
                '<a href="#%s">%s</a>' % (sid, t) if sid else t)
        vs = sorted(byver, key=lambda v: tuple(int(x) for x in v.split('.')))
        n = per[kind]
        for k in range(0, len(vs), n):
            rows = ['<table>', '<tr><th>판</th><th>바뀐 것</th></tr>']
            rows += ['<tr><td>%s</td><td>%s</td></tr>'
                     % (v, ' · '.join(byver[v])) for v in vs[k:k + n]]
            rows.append('</table>')
            out['tbl_flow_%s_%d.html' % (kind, k // n + 1)] = \
                '\n'.join(rows) + '\n'
    return out


def dict_rows(name):
    head, body = rows_of(name)
    return [dict(zip(head, r)) for r in body]


def build():
    """{내보낼 파일 이름: 내용}. 파일로 쓰기 전의 순수한 계산이다."""
    made = {}
    if not os.path.isdir(DATA):
        return made
    for name in sorted(os.listdir(DATA)):
        if not name.endswith('.tsv'):
            continue
        head, body = rows_of(name)
        if not head:
            continue
        made['tbl_%s.html' % name[:-4]] = render(head, body)
    if os.path.exists(os.path.join(DATA, 'releases.tsv')):
        drafts = [r['key'][len('relnotes-'):] for r in dict_rows('cite_keys.tsv')
                  if r.get('key', '').startswith('relnotes-')
                  and r.get('file', '').endswith('-draft.txt')]
        made.update(release_tables(dict_rows('releases.tsv'),
                                   cites.feature_rows(BASE),
                                   dict_rows('api_added.tsv'), drafts))
        fetched = [l.split('\t')[0] for l in
                   read(os.path.join(BASE, 'docs', 'FETCHED.txt')).split('\n')
                   if l and not l.startswith('#')]
        index = os.path.join(BASE, 'docs', 'raw', 'blog', 'index.txt')
        if os.path.exists(index):
            made.update(appendix_tables(dict_rows('releases.tsv'),
                                        dict_rows('api_added.tsv'),
                                        dict_rows('godebug.tsv'),
                                        read(index), fetched))
        made.update(flow_tables(dict_rows('timeline.tsv'),
                                dict_rows('godebug.tsv'),
                                cites.feature_rows(BASE), per=15))
        made.update(flow_kind_tables(cites.feature_rows(BASE)))
    for out_name, tsv, cols, filt in VIEWS:
        head, body = rows_of(tsv)
        if filt:
            col, want = filt
            body = [r for r in body if r[head.index(col)] == want]
        made[out_name] = render(head, body, cols)
    return made


def manifest_note():
    """out/manifest.json 이 있으면 몇 개의 캡처가 표에 쓰였는지 한 줄로."""
    p = os.path.join(OUT, 'manifest.json')
    if not os.path.exists(p):
        return '  (out/manifest.json 아직 없다 — make run 먼저)'
    return '  out/manifest.json 의 캡처 %d개' % len(json.loads(read(p)))


def main(argv):
    made = build()
    if '--check' in argv:
        bad = []
        for name, want in sorted(made.items()):
            p = os.path.join(OUT, name)
            if not os.path.exists(p):
                bad.append('%s 가 없다' % name)
            elif read(p) != want:
                bad.append('%s 가 data/ 와 어긋난다' % name)
        for line in bad:
            print('  ✗ ' + line)
        print('생성 표 %d개 — 어긋남 %d건' % (len(made), len(bad)))
        return 1 if bad else 0
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for name, text in sorted(made.items()):
        io.open(os.path.join(OUT, name), 'w',
                encoding='utf-8', newline='\n').write(text)
    sync_manifest(made)
    print('생성 표 %d개 → out/' % len(made))
    print(manifest_note())
    return 0


def sync_manifest(made):
    """다시 쓴 표의 SHA-256 을 out/manifest.json 에도 적는다.

    표는 data/ 에서 결정적으로 나오므로 여기서 적어도 재현성 약속이
    깨지지 않는다. 안 적으면 data/*.tsv 를 한 줄 고칠 때마다
    run_all.py --check 가 "manifest 와 어긋난다" 로 멈추고, 실험을
    하나 다시 돌려야 풀렸다(run_all.py 와 같은 JSON 꼴로 쓴다).
    """
    p = os.path.join(OUT, 'manifest.json')
    if not os.path.exists(p):
        return
    man = json.loads(read(p))
    for name, text in made.items():
        man[name] = hashlib.sha256(text.encode('utf-8')).hexdigest()
    io.open(p, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(man, indent=1, sort_keys=True) + '\n')


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
