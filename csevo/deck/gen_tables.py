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
