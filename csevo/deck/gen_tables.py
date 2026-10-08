#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/*.tsv (+ out/manifest.json) → 덱이 싣는 HTML 표를 만든다.

    python3 deck/gen_tables.py           # out/tbl_*.html 을 다시 만든다
    python3 deck/gen_tables.py --check   # 지금 것과 같은지 대조만 한다

왜 표를 손으로 안 쓰는가: 이 덱의 표는 대부분 "버전·날짜·기능 게이트·런타임 짝"
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


KIND_NAMES = [('lang', '언어'), ('runtime', '런타임'), ('compiler', '컴파일러'),
              ('library', '라이브러리'), ('platform', '플랫폼'),
              ('ecosystem', '생태계')]


def release_tables(releases, features, gates):
    """버전마다 개관 표 하나 — tbl_rel_<버전>.html (goevo 에서 옮김).

    나온 달·VS·.NET 은 releases.tsv, 갈래마다의 기능은 features 의 그 버전
    행 전부(전용 장이 있으면 그리로 가는 링크), 게이트 수는 langgates.tsv.
    표가 기능 목록에서 곧장 만들어지므로 개관 장과 목록이 어긋날 수 없다.
    버전 비교는 끝의 .0 을 뗀 꼴로 한다(cites.vnorm). O(행 수)."""
    e = lambda s: html.escape(s, quote=False)
    out = {}
    for r in releases:
        ver = cites.vnorm(r['version'])
        pair = ' · '.join(x for x in (r.get('framework', ''), r.get('vs', ''))
                          if x)
        rows = ['<table class="kv">',
                '<tr><th>나온 달</th><td>%s</td></tr>' % e(r['date']),
                '<tr><th>함께 나온 것</th><td>%s</td></tr>' % e(pair or '—')]
        mine = [f for f in features if cites.vnorm(f.get('version', '')) == ver]
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
        n = sum(1 for g in gates if cites.vnorm(g['required-version']) == ver)
        rows.append('<tr><th>컴파일러 게이트</th><td>%d개</td></tr>' % n)
        rows.append('</table>')
        out['tbl_rel_%s.html' % ver] = '\n'.join(rows) + '\n'
    return out


def gate_counts(releases, gates):
    """버전마다 컴파일러가 그 버전을 요구하는 기능(게이트)의 수 —
    tbl_gate_counts.html. 0부와 16부가 "왜 C# 1–5 는 -langversion 짝이
    드문가" 를 이 표로 보인다. 게이트가 없는 버전도 0 으로 적는다. O(행 수)."""
    n = {}
    for g in gates:
        k = cites.vnorm(g['required-version'])
        n[k] = n.get(k, 0) + 1
    rows = [('C# ' + r['version'], r['date'],
             str(n.get(cites.vnorm(r['version']), 0))) for r in releases]
    return _table(['버전', '나온 달', '게이트 수'], rows, numcols=(2,))


# ---------------------------------------------------------------- 16부
# 16부(흐름으로 다시 읽기)는 앞의 부를 버전 축으로 다시 묶는다. 표는 전부
# releases.tsv · dotnet.tsv · langgates.tsv · 기능 목록에서 계산한다 —
# 간격·짝·개수를 눈으로 세면 틀리기 때문이다.

def _month(d):
    """'2019-09' 또는 '2019-09-23' → 해×12 + 달 (달 차이 계산용)."""
    y, m = d.split('-')[:2]
    return int(y) * 12 + int(m)


def _vs_short(s):
    """'Visual Studio 2017 version 15.7' → 'VS 2017 15.7' — 접힌 화면 폭."""
    return re.sub(r'\bversion ', '', s.replace('Visual Studio', 'VS'))


def _part_link(p):
    return '<a href="#p%d">%d부</a>' % (p, p) if p else '—'


def _html_table(head, rows, numcols=()):
    """_table 과 같되 칸 내용이 이미 HTML 이다(링크를 담는다)."""
    e = lambda s: html.escape(str(s), quote=False)
    out = ['<table>', '<tr>' + ''.join(
        '<th%s>%s</th>' % (' class="num"' if i in numcols else '', e(h))
        for i, h in enumerate(head)) + '</tr>']
    for r in rows:
        out.append('<tr>' + ''.join(
            '<td%s>%s</td>' % (' class="num"' if i in numcols else '', c)
            for i, c in enumerate(r)) + '</tr>')
    out.append('</table>')
    return '\n'.join(out) + '\n'


def version_parts(features):
    """버전 → 그 버전의 기능 행이 사는 부 번호(파일 이름 pNN 의 NN).
    한 버전이 여러 부에 걸치면 가장 앞의 부. O(행 수)."""
    out = {}
    for f in features:
        m = re.search(r'/p(\d+)[a-z]*\.tsv$', f.get('_file', ''))
        if not m:
            continue
        v, p = cites.vnorm(f.get('version', '')), int(m.group(1))
        if v and (v not in out or p < out[v]):
            out[v] = p
    return out


def p16_timeline(releases, parts):
    """연표 두 장 — .NET 짝이 없는 버전들(tbl_p16_rel_1)과 있는 버전들
    (tbl_p16_rel_2). 간격은 앞 버전에서 몇 달 뒤인가. O(행 수)."""
    e = lambda s: html.escape(s, quote=False)
    one, two, prev = [], [], None
    for r in releases:
        gap = '—' if prev is None else str(_month(r['date']) - prev)
        prev = _month(r['date'])
        link = _part_link(parts.get(cites.vnorm(r['version'])))
        cells = ['C# ' + e(r['version']), e(r['date']), gap]
        if r.get('framework'):
            two.append(cells + [e(r['framework']), e(_vs_short(r['vs'])),
                                link])
        else:
            one.append(cells + [e(_vs_short(r['vs'])), link])
    return {
        'tbl_p16_rel_1.html': _html_table(
            ['버전', '나온 달', '간격(달)', 'Visual Studio', '부'], one,
            numcols=(2,)),
        'tbl_p16_rel_2.html': _html_table(
            ['버전', '나온 달', '간격(달)', '.NET', 'Visual Studio', '부'],
            two, numcols=(2,)),
    }


def p16_cadence(releases):
    """간격 통계 — .NET 짝이 없는 시대, 있는 시대, 전체. 시대를 넘는
    간격은 전체에만 센다. O(행 수)."""
    def stats(label, rs, gaps):
        if not gaps:
            return [label, str(len(rs)), '—', '—', '—']
        return [label, str(len(rs)), str(min(gaps)), str(max(gaps)),
                '%.1f' % (sum(gaps) / float(len(gaps)))]

    def gaps_of(rs):
        return [_month(b['date']) - _month(a['date'])
                for a, b in zip(rs, rs[1:])]

    vs = [r for r in releases if not r.get('framework')]
    net = [r for r in releases if r.get('framework')]
    rows = []
    for rs, tail in ((vs, ' (Visual Studio 와 함께)'), (net, ' (.NET 과 함께)')):
        if rs:
            label = 'C# %s–%s%s' % (rs[0]['version'], rs[-1]['version'], tail)
            rows.append(stats(label, rs, gaps_of(rs)))
    rows.append(stats('전체', releases, gaps_of(releases)))
    return _table(['묶음', '버전 수', '최소 간격', '최대 간격', '평균(달)'],
                  rows, numcols=(1, 2, 3, 4))


def p16_pairs(releases, dotnet):
    """.NET Core·.NET 릴리스마다 짝이 된 C# 버전(releases.tsv 의 framework
    칸)과 두 날짜의 달 차이. 짝이 없는 릴리스도 한 줄. O(행 수)."""
    e = lambda s: html.escape(s, quote=False)
    by = dict((r.get('framework'), r) for r in releases if r.get('framework'))
    rows = []
    for d in dotnet:
        name = '%s %s' % (d['product'], d['version'])
        r = by.get(name)
        if r:
            rows.append([e(name), e(d['date']), 'C# ' + e(r['version']),
                         e(r['date']),
                         str(_month(d['date']) - _month(r['date']))])
        else:
            rows.append([e(name), e(d['date']), '—', '—', '—'])
    return _html_table(['.NET', 'GA 날짜', 'C#', 'C# 나온 달', '달 차이'],
                       rows, numcols=(4,))


def p16_featgates(releases, features, gates):
    """버전마다 — 덱의 기능 행, 그중 게이트(msgid)가 적힌 행, 그 행들이
    가리키는 서로 다른 게이트, 컴파일러의 게이트 전부. 마지막 줄은 합.
    O(행 수)."""
    rows, tot = [], [0, 0, 0, 0]
    for r in releases:
        v = cites.vnorm(r['version'])
        mine = [f for f in features if cites.vnorm(f.get('version', '')) == v]
        gated = [f for f in mine if f.get('msgid')]
        nums = [len(mine), len(gated), len(set(f['msgid'] for f in gated)),
                sum(1 for g in gates
                    if cites.vnorm(g['required-version']) == v)]
        tot = [a + b for a, b in zip(tot, nums)]
        rows.append(['C# ' + r['version']] + [str(n) for n in nums])
    rows.append(['합'] + [str(n) for n in tot])
    return _table(['버전', '기능 행', '게이트 행', '다룬 게이트',
                   '컴파일러 게이트'], rows, numcols=(1, 2, 3, 4))


KIND_COLS = [('lang',), ('runtime',), ('compiler',), ('library',),
             ('ecosystem', 'platform')]


def p16_kinds(features):
    """부마다 갈래별 기능 행 수 — 언어·런타임·컴파일러·라이브러리·그 밖
    (생태계·플랫폼). 버전 칸은 그 부의 버전들. 마지막 줄은 합. O(행 수)."""
    parts = {}
    for f in features:
        m = re.search(r'/p(\d+)[a-z]*\.tsv$', f.get('_file', ''))
        if not m:
            continue
        p = parts.setdefault(int(m.group(1)), {'v': [], 'n': [0] * 5})
        v = f.get('version', '')
        if v not in p['v']:
            p['v'].append(v)
        for i, kinds in enumerate(KIND_COLS):
            if f.get('kind') in kinds:
                p['n'][i] += 1
    rows, tot = [], [0] * 6
    for num in sorted(parts):
        p = parts[num]
        ns = p['n'] + [sum(p['n'])]
        tot = [a + b for a, b in zip(tot, ns)]
        rows.append([_part_link(num),
                     html.escape(' · '.join(p['v']), quote=False)]
                    + [str(n) for n in ns])
    rows.append(['합', ''] + [str(n) for n in tot])
    return _html_table(['부', '버전', '언어', '런타임', '컴파일러',
                        '라이브러리', '그 밖', '합'], rows,
                       numcols=(2, 3, 4, 5, 6, 7))


def p16_standard(releases, ecma_text):
    """ECMA 표준 페이지의 'Visual C# 버전 ↔ ECMA-334 ↔ ISO/IEC' 표에 그
    버전이 나온 달과 '몇 해 뒤의 표준인가' 를 붙인다. 표의 V1 은
    releases.tsv 의 1.0, V7 은 7.0 과 맞춘다. O(줄 수)."""
    e = lambda s: html.escape(s, quote=False)
    date = dict((cites.vnorm(r['version']), r['date']) for r in releases)
    rows = []
    for line in ecma_text.split('\n'):
        m = re.match(r'^V(\d+) \| ([^|]+) \| (.+)$', line.strip())
        if not m:
            continue
        v, ecma, iso = m.group(1), m.group(2).strip(), m.group(3).strip()
        iso = re.sub(r'\s*\(.*\)$', '', iso)
        d = date.get(v, '—')
        y = re.search(r':(\d{4})$', ecma)
        lag = (str(int(y.group(1)) - int(d[:4]))
               if y and d != '—' else '—')
        rows.append(['V' + v, e(d), e(ecma), e(iso), lag])
    return _html_table(['Visual C#', 'C# 나온 달', 'ECMA-334', 'ISO/IEC',
                        '늦음(해)'], rows, numcols=(4,))


def p16_tables(releases, dotnet, features, gates, ecma_text):
    """16부의 표 전부 — {파일 이름: 내용}."""
    made = p16_timeline(releases, version_parts(features))
    made['tbl_p16_cadence.html'] = p16_cadence(releases)
    made['tbl_p16_pair.html'] = p16_pairs(releases, dotnet)
    made['tbl_p16_featgates.html'] = p16_featgates(releases, features, gates)
    made['tbl_p16_kinds.html'] = p16_kinds(features)
    if ecma_text:
        made['tbl_p16_std.html'] = p16_standard(releases, ecma_text)
    return made


# ---------------------------------------------------------------- 부록(17부)
# 부록의 표는 전부 여기서 만든다 — 버전 찾아가기, 게이트 표, 용어집 색인,
# 출처 목록과 그 인용 수, 예제·캡처의 수. 인용 수는 조각 파일(부록 제외)을
# 세고, 예제 수는 ex/ 와 out/manifest.json 을 센다. 손으로 센 수는 없다.

def _cover_of(v, ids, suffix=''):
    """버전 → 그 버전 장 표지의 id(pN-v<cls>, suffix 가 있으면 그것을 붙인
    id — 예: '-overview'). 여럿이면 가장 앞의 부."""
    cls = cites.vnorm(v).replace('.', '_')
    best = None
    for i in ids:
        m = re.match(r'^p(\d+)-v%s%s$' % (re.escape(cls), re.escape(suffix)),
                     i)
        if m and (best is None or int(m.group(1)) < best[0]):
            best = (int(m.group(1)), i)
    return best


def app_where(releases, features, gates, ids):
    """버전 찾아가기 — 버전마다 표지·부·개관 장으로 가는 링크와, 그 버전
    배지를 단 장의 수(기능 행의 서로 다른 slide-id), 컴파일러 게이트 수.
    O(행 수 × id 수)."""
    e = lambda s: html.escape(s, quote=False)
    rows = []
    for r in releases:
        v = cites.vnorm(r['version'])
        cov = _cover_of(v, ids)
        name = 'C# ' + e(r['version'])
        if cov:
            ov = cov[1] + '-overview'
            cells = ['<a href="#%s">%s</a>' % (cov[1], name), e(r['date']),
                     _part_link(cov[0]),
                     '<a href="#%s">개관</a>' % ov if ov in ids else '—']
        else:
            cells = [name, e(r['date']), '—', '—']
        sids = set(f['slide-id'] for f in features
                   if f.get('slide-id')
                   and cites.vnorm(f.get('version', '')) == v)
        n = sum(1 for g in gates if cites.vnorm(g['required-version']) == v)
        rows.append(cells + [str(len(sids)), str(n)])
    return _html_table(['버전', '나온 달', '부', '개관', '배지 단 장',
                        '게이트'], rows, numcols=(4, 5))


def app_releases(releases, dotnet):
    """버전 일정표의 긴 꼴 — Visual Studio 이름을 줄이지 않고, 짝이 된 .NET 의
    GA 날짜(dotnet.tsv)를 붙인다. O(행 수)."""
    ga = dict(('%s %s' % (d['product'], d['version']), d['date'])
              for d in dotnet)
    rows = []
    for r in releases:
        fw = r.get('framework', '')
        rows.append(['C# ' + r['version'], r['date'], r.get('vs', '') or '—',
                     fw or '—', ga.get(fw, '—') if fw else '—'])
    return _table(['버전', '나온 달', 'Visual Studio', '.NET', 'GA 날짜'],
                  rows)


def _short_msgid(m):
    return re.sub(r'^IDS_(Feature)?', '', m)


def gate_links(gates, features, msgid_cites, ids):
    """게이트마다 그것을 보이는 장 — (어떻게, [(id, 글자)]).

    차례대로 본다. (row) 그 MessageID 를 적은 기능 행의 장. (shared) 행에
    장이 없으면, 같은 파일에서 바로 앞의 장 있는 행이 같은 인용(키·절)일
    때 그 장 — '작은 변화들' 처럼 한 장을 여러 행이 나눠 쓰는 꼴이다.
    (cite) MessageID.cs 의 그 case 줄을 인용한 장. (overview) 행은 있으나
    장이 없으면 그 버전의 개관 장. (none) 덱에 없음. O(게이트 × 행)."""
    out = {}
    for g in gates:
        mid = g['msgid']
        mine = [(i, f) for i, f in enumerate(features)
                if f.get('msgid') == mid]
        got, seen = [], set()
        for _i, f in mine:
            sid = f.get('slide-id', '')
            if sid and sid not in seen:
                seen.add(sid)
                got.append((sid, f.get('title', '')))
        if got:
            out[mid] = ('row', got)
            continue
        for i, f in mine:
            for j in range(i - 1, -1, -1):
                p = features[j]
                if p.get('_file') != f.get('_file'):
                    break
                if not p.get('slide-id'):
                    continue
                if (p.get('cite-key'), p.get('cite-sec')) == \
                        (f.get('cite-key'), f.get('cite-sec')):
                    got.append((p['slide-id'], f.get('title', '')))
                break
            if got:
                break
        if got:
            out[mid] = ('shared', got)
            continue
        title = mine[0][1].get('title', '') if mine else ''
        cited = msgid_cites.get(mid, [])
        if cited:
            out[mid] = ('cite', [(cited[0], title or _short_msgid(mid))])
            continue
        if mine:
            ov = _cover_of(g['required-version'], ids, '-overview')
            if ov:
                out[mid] = ('overview', [(ov[1], title + ' (개관)')])
                continue
        out[mid] = ('none', [])
    return out


def _pack(groups, per, ncols, unit=''):
    """[(머리 글자, [행 html])] → 장마다의 행 목록. 한 장에 per 줄(머리 줄
    포함)까지. 무리가 장을 넘으면 다음 장 첫 줄에 '(이어서)' 머리를 다시
    단다. 머리 줄이 장의 마지막 줄로 남지 않게 한다. O(행 수)."""
    def head(label, n, cont):
        return '<tr><th colspan="%d">%s · %s%d개%s</th></tr>' % (
            ncols, label, unit, n, ' (이어서)' if cont else '')
    slides = [[]]
    for label, rows in groups:
        for i, r in enumerate(rows):
            cur = slides[-1]
            if i == 0:
                if cur and len(cur) + 2 > per:
                    slides.append([])
                    cur = slides[-1]
                cur.append(head(label, len(rows), False))
            elif len(cur) + 1 > per:
                slides.append([])
                cur = slides[-1]
                cur.append(head(label, len(rows), True))
            cur.append(r)
    return [s for s in slides if s]


def _paged(prefix, head_html, slides):
    return dict(('tbl_%s_%d.html' % (prefix, k + 1),
                 '<table>\n%s\n%s\n</table>\n' % (head_html, '\n'.join(s)))
                for k, s in enumerate(slides))


def app_gates(releases, gates, links, per=16):
    """게이트 표 — 버전마다 머리 줄, 게이트마다 (Roslyn 의 기능 이름, 이
    덱에서 보이는 장). 접힌 화면에 들게 per 줄씩 여러 장. O(게이트 수)."""
    e = lambda s: html.escape(s, quote=False)
    groups = []
    for r in releases:
        v = cites.vnorm(r['version'])
        rows = []
        for g in gates:
            if cites.vnorm(g['required-version']) != v:
                continue
            name = (e(g['feature']) if g.get('feature') else
                    '<code>%s</code> (이름 없음)' % e(_short_msgid(g['msgid'])))
            _how, got = links.get(g['msgid'], ('none', []))
            where = ' · '.join('<a href="#%s">%s</a>' % (sid, e(t))
                               for sid, t in got) or '—'
            rows.append('<tr><td>%s</td><td>%s</td></tr>' % (name, where))
        if rows:
            groups.append(('C# ' + e(r['version']), rows))
    return _paged('app_gates', '<tr><th>Roslyn 의 기능 이름</th>'
                  '<th>이 덱에서</th></tr>', _pack(groups, per, 2, '게이트 '))


GATE_HOW = [('row', '기능 행의 장'), ('shared', '앞 행과 같은 장(같은 인용)'),
            ('cite', 'MessageID 줄을 인용한 장'), ('overview', '버전 개관만'),
            ('none', '덱에 없음')]


def app_gates_how(links):
    """게이트가 어떤 길로 장에 이어졌나 — 길마다의 수와 합. O(게이트 수)."""
    rows = [[name, str(sum(1 for h, _g in links.values() if h == how))]
            for how, name in GATE_HOW]
    rows.append(['합', str(len(links))])
    return _table(['이어진 길', '게이트'], rows, numcols=(1,))


CHO = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'
CHO_BASE = {'ㄲ': 'ㄱ', 'ㄸ': 'ㄷ', 'ㅃ': 'ㅂ', 'ㅆ': 'ㅅ', 'ㅉ': 'ㅈ'}
CHO_ROWS = 'ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ'


def _initial(term):
    """낱말 → ('sym'|'latin'|'hangul', 묶음 글자)."""
    c = term[:1]
    if '가' <= c <= '힣':
        j = CHO[(ord(c) - 0xAC00) // 588]
        return 'hangul', CHO_BASE.get(j, j)
    if c in CHO:
        return 'hangul', CHO_BASE.get(c, c)
    if c.isalpha() and c.upper() != c.lower() and ord(c.upper()) < 0x250:
        return 'latin', c.upper()
    return 'sym', ''


def app_glossary_index(rows, per):
    """용어집 찾아보기 — 첫 글자 묶음마다 그 낱말들이 있는 용어집 장.

    차례는 gen_glossary.render 와 같다(소문자로 견준 차례, 한 장에 per
    낱말, 장 id 는 p17-gl-N). 로마자는 글자마다 처음 나오는 장, 한글은
    초성(된소리는 예사소리에 묶는다)마다 그 낱말들이 걸친 장 전부.
    O(낱말 수 log 낱말 수)."""
    terms = sorted((r[0] for r in rows), key=lambda t: t.lower())
    sym, latin, han = [], {}, {}
    for k, t in enumerate(terms):
        n = k // per + 1
        kind, ch = _initial(t)
        if kind == 'sym':
            if n not in sym:
                sym.append(n)
        elif kind == 'latin':
            latin.setdefault(ch, n)
        else:
            han.setdefault(ch, set()).add(n)

    def links(ns):
        return ' · '.join('<a href="#p17-gl-%d">%d</a>' % (n, n)
                          for n in sorted(ns))
    out = []
    if sym:
        out.append(['기호·숫자', links(sym)])
    if latin:
        out.append(['로마자', ' · '.join(
            '<a href="#p17-gl-%d">%s</a>' % (latin[c], c)
            for c in sorted(latin))])
    for c in CHO_ROWS:
        if c in han:
            out.append([c, links(han[c])])
    return _html_table(['첫 글자', '용어집 장'], out)


CITE_KEY_RE = re.compile(r'<!--CITE key=(\S+?)(?=\s|-->)(.*?)-->')
ART_RE = re.compile(r'<article[^>]*\bid="([^"]+)"[^>]*>(.*?)</article>', re.S)


def cite_tally(files):
    """[(조각 이름, 글)] → ({키: [그 키를 인용한 장 id, 덱 차례]},
    {MessageID: [그 case 줄을 인용한 장 id]}). 한 장이 여러 번 인용해도
    한 번. O(글 길이)."""
    keys, msg = {}, {}
    for _name, text in files:
        for am in ART_RE.finditer(text):
            sid = am.group(1)
            for cm in CITE_KEY_RE.finditer(am.group(2)):
                k = cm.group(1)
                lst = keys.setdefault(k, [])
                if sid not in lst:
                    lst.append(sid)
                if k == 'msgid':
                    for mid in re.findall(r'MessageID\.(\w+)', cm.group(2)):
                        lst2 = msg.setdefault(mid, [])
                        if sid not in lst2:
                            lst2.append(sid)
    return keys, msg


SRC_KINDS = [
    ('버전 기록·새 기능', ('whatsnew/', 'csharplang/Language-Version-History')),
    ('기능 명세(csharplang 제안)', ('csharplang/proposals/',)),
    ('표준', ('standard/', 'csharpstandard/', 'ecma-334')),
    ('컴파일러(Roslyn)', ('roslyn/',)),
    ('.NET 릴리스', ('releases',)),
    ('블로그(devblogs)', ('blog/',)),
    ('역사 기록', ('history/',)),
]
SRC_OTHER = '그 밖'
# 갈래의 머리 줄이 이미 말하는 이름 앞머리 — 표에서는 뗀다
SRC_STRIP = re.compile(r'^(C# [\d.]+ 기능 명세 |C# 표준 초안 |Roslyn 문서 '
                       r'|devblogs )')


def src_kind(path):
    for label, prefixes in SRC_KINDS:
        if path.startswith(prefixes):
            return label
    return SRC_OTHER


def _natural(s):
    return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', s)]


def app_src_kinds(keys, tally):
    """출처 갈래마다 — 받아 둔 문서 수, 그중 인용된 문서, 그 갈래를 인용한
    장의 수(겹치지 않게). 마지막 줄은 합. O(키 수 + 인용 수)."""
    labels = [l for l, _p in SRC_KINDS] + [SRC_OTHER]
    rows, all_slides, tot = [], set(), [0, 0]
    for label in labels:
        mine = [k for k in keys if src_kind(k['file']) == label]
        if not mine:
            continue
        cited = [k for k in mine if tally.get(k['key'])]
        slides = set(s for k in mine for s in tally.get(k['key'], []))
        all_slides |= slides
        tot = [tot[0] + len(mine), tot[1] + len(cited)]
        rows.append([label, str(len(mine)), str(len(cited)),
                     str(len(slides))])
    rows.append(['합', str(tot[0]), str(tot[1]), str(len(all_slides))])
    return _table(['갈래', '문서', '인용된 문서', '인용한 장'], rows,
                  numcols=(1, 2, 3))


def app_src_lists(keys, tally, urls, per=24):
    """출처 목록 — 갈래마다(제안은 버전마다) 머리 줄, 문서마다 (이름 —
    받은 주소로 링크, 인용한 장 수, 처음 인용한 장). O(키 수 log 키 수)."""
    e = lambda s: html.escape(s, quote=False)
    groups = {}
    for k in keys:
        label = src_kind(k['file'])
        m = re.match(r'^csharplang/proposals/csharp-([\d.]+)/', k['file'])
        if m:
            label = '기능 명세 C# %s' % cites.vnorm(m.group(1))
        groups.setdefault(label, []).append(k)
    order = []
    for label, _p in SRC_KINDS + [(SRC_OTHER, ())]:
        if label.startswith('기능 명세('):
            order += sorted((g for g in groups if g.startswith('기능 명세 C#')),
                            key=_natural)
        elif label in groups:
            order.append(label)
    packed = []
    for label in order:
        rows = []
        for k in sorted(groups[label], key=lambda k: _natural(k['file'])):
            name = e(SRC_STRIP.sub('', k['name']))
            url = urls.get(k['file'])
            if url:
                name = '<a href="%s">%s</a>' % (html.escape(url, quote=True),
                                                name)
            sl = tally.get(k['key'], [])
            first = '—'
            if sl:
                pm = re.match(r'^p(\d+)-', sl[0])
                first = '<a href="#%s">%s</a>' % (
                    sl[0], '%s부' % pm.group(1) if pm else sl[0])
            rows.append('<tr><td>%s</td><td class="num">%d</td><td>%s</td>'
                        '</tr>' % (name, len(sl), first))
        packed.append((e(label), rows))
    return _paged('app_src', '<tr><th>문서</th><th class="num">장</th>'
                  '<th>처음</th></tr>', _pack(packed, per, 3))


def app_src_pins(fetched):
    """받아 둔 문서를 (저장소 또는 사이트, 고정 커밋) 으로 묶어 — 파일 수와
    받은 날. GitHub 의 raw·API 주소는 주소 속 커밋을 7자로 적는다.
    O(줄 수 log 줄 수)."""
    e = lambda s: html.escape(s, quote=False)
    groups = {}
    for r in fetched:
        u = re.sub(r'^https?://', '', r['url'])
        m = (re.match(r'^raw\.githubusercontent\.com/([^/]+/[^/]+)/'
                      r'([0-9a-f]{7,40})/', u)
             or re.match(r'^api\.github\.com/repos/([^/]+/[^/]+)/git/trees/'
                         r'([0-9a-f]{7,40})', u))
        key = (m.group(1), m.group(2)[:7]) if m else (u.split('/')[0], '')
        g = groups.setdefault(key, [0, set()])
        g[0] += 1
        g[1].add(r['date'])
    rows = []
    for (src, sha), (n, dates) in sorted(groups.items()):
        rows.append([e(src), '<code>%s</code>' % sha if sha else '—', str(n),
                     ' · '.join(sorted(dates))])
    return _html_table(['출처', '커밋', '파일', '받은 날'], rows, numcols=(2,))


def app_examples(parts):
    """부마다 예제 디렉터리·소스 파일·줄·일부러 깬 예제(EXPECT_FAIL)·캡처
    (out/manifest.json 의 NN-* 항목). 마지막 줄은 합. O(부 수)."""
    cols = ('ex', 'files', 'lines', 'fail', 'caps')
    rows, tot = [], [0] * len(cols)
    for p in sorted(parts):
        ns = [parts[p].get(c, 0) for c in cols]
        tot = [a + b for a, b in zip(tot, ns)]
        rows.append([_part_link(p) if p else '<a href="#p0">0부</a>']
                    + [str(n) for n in ns])
    rows.append(['합'] + [str(n) for n in tot])
    return _html_table(['부', '예제', '소스 파일', '줄', '일부러 깬 것',
                        '캡처'], rows, numcols=(1, 2, 3, 4, 5))


def section_files():
    """order.txt 차례의 조각 [(이름, 글)] — 부록(17_)은 뺀다(제 인용을
    세지 않게)."""
    order = [l.strip() for l in read(os.path.join(HERE, 'order.txt'))
             .split('\n') if l.strip() and not l.strip().startswith('#')]
    out = []
    for fn in order:
        p = os.path.join(HERE, 'sections', fn)
        if fn.startswith('17') or not os.path.exists(p):
            continue
        out.append((fn, read(p)))
    return out


def all_ids():
    ids = set()
    d = os.path.join(HERE, 'sections')
    for fn in sorted(os.listdir(d)):
        if fn.endswith('.html'):
            ids |= set(re.findall(r'\bid="([^"]+)"', read(os.path.join(d, fn))))
    return ids


def fetched_rows():
    p = os.path.join(BASE, 'docs', 'FETCHED.txt')
    out = []
    if not os.path.exists(p):
        return out
    for line in read(p).split('\n'):
        if not line.strip() or line.startswith('#'):
            continue
        c = line.split('\t')
        if len(c) >= 3:
            out.append({'path': c[0], 'url': c[1], 'date': c[2]})
    return out


SRC_EXT = ('.cs', '.java')


def example_stats():
    """ex/NN/<예제>/ 를 센다 — 예제(디렉터리), 소스 파일(.cs·.java, bin/
    밑은 뺀다), 줄, EXPECT_FAIL, 그리고 out/manifest.json 의 'NN-' 캡처."""
    parts = {}
    exdir = os.path.join(BASE, 'ex')
    for nn in sorted(os.listdir(exdir)) if os.path.isdir(exdir) else []:
        if not (nn.isdigit() and os.path.isdir(os.path.join(exdir, nn))):
            continue
        st = parts.setdefault(int(nn), {'ex': 0, 'files': 0, 'lines': 0,
                                        'fail': 0, 'caps': 0})
        for slug in sorted(os.listdir(os.path.join(exdir, nn))):
            d = os.path.join(exdir, nn, slug)
            if not os.path.isdir(d):
                continue
            st['ex'] += 1
            st['fail'] += os.path.exists(os.path.join(d, 'EXPECT_FAIL'))
            for root, dirs, names in os.walk(d):
                dirs[:] = sorted(x for x in dirs if x not in ('bin', 'obj'))
                for n in names:
                    if n.endswith(SRC_EXT):
                        st['files'] += 1
                        st['lines'] += len(read(os.path.join(root, n))
                                           .splitlines())
    mp = os.path.join(OUT, 'manifest.json')
    if os.path.exists(mp):
        for k in json.loads(read(mp)):
            m = re.match(r'^(\d\d)-', k)
            if m and int(m.group(1)) in parts:
                parts[int(m.group(1))]['caps'] += 1
    return parts


def appendix_tables(examples=True):
    """부록의 표 전부 — {파일 이름: 내용}. 파일을 읽는 것은 여기뿐이다.
    examples=False 면 예제 수 표를 뺀다 — ex/ 의 파일 이천여 개를 여는
    데 이 기계(proot)에서 10초 남짓 걸려, 시험에서는 건너뛴다."""
    import gen_glossary
    releases, gates = dict_rows('releases.tsv'), dict_rows('langgates.tsv')
    feats, ids = cites.feature_rows(BASE), all_ids()
    tally, msg = cite_tally(section_files())
    made = {'tbl_app_where.html': app_where(releases, feats, gates, ids),
            'tbl_app_rel.html': app_releases(releases,
                                             dict_rows('dotnet.tsv'))}
    links = gate_links(gates, feats, msg, ids)
    made.update(app_gates(releases, gates, links))
    made['tbl_app_gates_how.html'] = app_gates_how(links)
    made['tbl_app_glidx.html'] = app_glossary_index(
        gen_glossary.entries(), gen_glossary.PER_SLIDE)
    keys = dict_rows('cite_keys.tsv')
    fetched = fetched_rows()
    made['tbl_app_src_kinds.html'] = app_src_kinds(keys, tally)
    made.update(app_src_lists(keys, tally,
                              dict((r['path'], r['url']) for r in fetched)))
    made['tbl_app_src_pins.html'] = app_src_pins(fetched)
    if examples:
        made['tbl_app_ex.html'] = app_examples(example_stats())
    return made


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
    if os.path.exists(os.path.join(DATA, 'langgates.tsv')):
        made.update(release_tables(dict_rows('releases.tsv'),
                                   cites.feature_rows(BASE),
                                   dict_rows('langgates.tsv')))
        made['tbl_gate_counts.html'] = gate_counts(
            dict_rows('releases.tsv'), dict_rows('langgates.tsv'))
        # 16부 — ECMA 표는 docs/ 캐시에 있을 때만(없으면 make docs)
        ecma = os.path.join(BASE, 'docs', 'ecma-334.txt')
        made.update(p16_tables(
            dict_rows('releases.tsv'), dict_rows('dotnet.tsv'),
            cites.feature_rows(BASE), dict_rows('langgates.tsv'),
            read(ecma) if os.path.exists(ecma) else ''))
        # 부록(17부) — 조각 파일·용어집·ex/·manifest 도 센다
        made.update(appendix_tables())
    # 버전 개관·부록·흐름 표는 3단계 이후 goevo/deck/gen_tables.py 에서
    # C# 자료에 맞춰 옮겨 온다(PLAN.md §4).
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
