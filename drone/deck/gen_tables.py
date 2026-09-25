#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/*.tsv → 덱이 싣는 HTML 표 (out/tbl_*.html).

    python3 deck/gen_tables.py           # 다시 만든다
    python3 deck/gen_tables.py --check   # 지금 파일과 같은지만 본다

왜 표를 손으로 안 쓰는가: 기준 쿼드로터의 값, 기호, 정리 목록, 규제
조문 — 전부 한 칸만 틀려도 티가 안 나는 나열이다. 사실은 data/*.tsv
한 곳에만 적고 표는 거기서 만든다. 측정 표(run_all 이 쓰는 tbl_*)와
이름이 겹치지 않도록 이 도구의 표는 tbl_d_ 로 시작한다.

한 표가 접힌 폴드 한 화면(행 14개)을 넘으면 _1, _2 … 로 쪼갠다.
시간·공간 O(행 수).
"""
import html
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cites  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
OUT = os.path.join(BASE, 'out')
SECTIONS = os.path.join(HERE, 'sections')
PER = 14
LEVEL = {'1학년': '<span class="lv l1">1학년</span>',
         '심화': '<span class="lv adv">심화</span>'}
KIND = {'full': '증명', 'sketch': '스케치', 'cited': '인용'}
# 연표의 갈래 — gen_figs.KINDS 와 같은 이름(그림과 표가 같은 말을 쓴다)
TL_KIND = {'military': '군용', 'hobby': 'RC 취미', 'multirotor': '멀티로터·FC',
           'consumer': '소비자', 'racing': '레이싱', 'delivery': '배송·산업',
           'show': '드론쇼', 'law': '규제'}
RECORD = {'Guinness': '기네스', 'claimed': '주최측 주장', 'none': '—'}


def esc(s):
    return html.escape(str(s), quote=False)


def render(head, rows, num=(), raw=()):
    """head·rows → <table>. raw 는 HTML 을 그대로 둘 열 번호(정리 문장)."""
    out = ['<table class="data">', '<tr>' + ''.join(
        '<th%s>%s</th>' % (' class="num"' if i in num else '', esc(h))
        for i, h in enumerate(head)) + '</tr>']
    for r in rows:
        out.append('<tr>' + ''.join(
            '<td%s>%s</td>' % (' class="num"' if i in num else '',
                               c if i in raw else esc(c))
            for i, c in enumerate(r)) + '</tr>')
    out.append('</table>')
    return '\n'.join(out) + '\n'


def chunks(rows, per=PER):
    return [rows[k:k + per] for k in range(0, len(rows), per)] or [[]]


def thm_places():
    """정리 id → 그 THM 상자가 처음 나온 슬라이드 id (조각 파일을 훑는다)."""
    where = {}
    if not os.path.isdir(SECTIONS):
        return where
    art = re.compile(r'<article[^>]*id="([^"]+)"[^>]*>(.*?)</article>',
                     re.S)
    for name in sorted(os.listdir(SECTIONS)):
        if not name.endswith('.html'):
            continue
        text = io.open(os.path.join(SECTIONS, name), encoding='utf-8').read()
        for m in art.finditer(text):
            for tid in re.findall(r'<!--THM id=(\S+?)-->', m.group(2)):
                where.setdefault(tid, m.group(1))
    return where


def tables():
    """{파일 이름: HTML}. 표를 더하려면 여기에 한 덩어리 더한다."""
    out = {}
    prm = cites.rows(BASE, 'params.tsv')
    phys = [r for r in prm if not r['parameter'].startswith(
        ('k', 'i_max', 'tau_d', 'yaw_w', 'rate', 'tilt', 'vmax_ctrl',
         'dt', 'att', 'pos', 'sigma'))
        or r['parameter'] in ('kT', 'kQ')]
    ctrl = [r for r in prm if r not in phys]
    for tag, part in (('params_phys', phys), ('params_ctrl', ctrl)):
        for k, ch in enumerate(chunks(part), 1):
            out['tbl_d_%s_%d.html' % (tag, k)] = render(
                ['이름', '값', '단위', '까닭'],
                [[r['parameter'], r['value'], r['unit'], r['why']]
                 for r in ch], num=(1,))
    sym = cites.rows(BASE, 'symbols.tsv')
    for k, ch in enumerate(chunks(sym), 1):
        out['tbl_d_symbols_%d.html' % k] = render(
            ['기호', '뜻', '단위'],
            [[r['symbol'], r['meaning'], r['unit']] for r in ch])
    where = thm_places()
    thm = cites.rows(BASE, 'theorems.tsv')
    for k, ch in enumerate(chunks(thm, 10), 1):
        rows = []
        for r in ch:
            w = where.get(r['id'])
            link = '<a href="#%s">보기</a>' % w if w else '—'
            rows.append([r['id'], LEVEL.get(r['level'], esc(r['level'])),
                         KIND.get(r['proof-kind'], r['proof-kind']),
                         r['statement'], link])
        out['tbl_d_theorems_%d.html' % k] = render(
            ['id', '등급', '꼴', '문장', '어디'], rows, raw=(1, 3, 4))
    out.update(appendix())
    return out


def appendix():
    """부록의 자료 표 — 연표·쇼 기록·법령·도구·펌웨어·출처."""
    out = {}

    def put(tag, head, rows, num=(), raw=()):
        for k, ch in enumerate(chunks(rows), 1):
            out['tbl_d_%s_%d.html' % (tag, k)] = render(head, ch, num, raw)

    put('timeline', ['날짜', '일', '갈래', '출처'],
        [[r['date'], r['event(ko)'], TL_KIND.get(r['kind'], r['kind']),
          r['source']] for r in cites.rows(BASE, 'timeline.tsv')])
    put('shows', ['날짜', '곳', '주최', '대수', '기록', '출처'],
        [[r['date'], r['place'], r['organiser'], r['drone-count'],
          RECORD.get(r['record'], r['record']), r['source']]
         for r in cites.rows(BASE, 'shows.tsv')], num=(3,))
    put('law', ['관할', '법령', '조문', '요지', '출처'],
        [[r['jurisdiction'], r['rule'], r['article'], r['requirement(ko)'],
          r['source']] for r in cites.rows(BASE, 'law.tsv')])
    put('tools', ['도구', '만든 곳', '종류', '공개', '파일 형식', '출처'],
        [[r['tool'], r['vendor'], r['kind'], r['open-source'],
          r['file-formats'], r['source']]
         for r in cites.rows(BASE, 'tools_show.tsv')])
    put('firmware', ['펌웨어', '첫 공개', '허가', '언어', '자세 표현', '출처'],
        [[r['project'], r['first-release'], r['licence'], r['language'],
          r['attitude-representation'], r['source']]
         for r in cites.rows(BASE, 'firmware.tsv')])
    # 주소는 글로 늘어놓으면 폴드 폭을 넘는다 — 링크 하나로 줄인다
    put('sources', ['열쇠', '이름', '종류', '주소'],
        [[r['key'], r['name'], r['kind'],
          '<a href="%s">열기</a>' % html.escape(r['url'], quote=True)]
         for r in cites.rows(BASE, 'cite_keys.tsv')], raw=(3,))
    return out


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    bad = 0
    made = tables()
    for name, text in sorted(made.items()):
        p = os.path.join(OUT, name)
        if '--check' in argv:
            old = io.open(p, encoding='utf-8').read() if os.path.exists(
                p) else None
            if old != text:
                print('  ✗ out/%s 가 자료와 다르다 (make tables)' % name)
                bad = 1
            continue
        with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
    print('  자료 표 %d개%s' % (len(made), '' if bad else ' — 이상 없음'))
    return bad


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
