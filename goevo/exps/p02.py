# -*- coding: utf-8 -*-
"""2부 — 공개에서 Go 1 까지. Go 1 이 더한 것은 지금 돌려 보이고, Go 1 이
없앤 문법·경로는 지금 컴파일러가 거절하는 것으로 보인다(PLAN.md §0.6 d).
Go 1 이전 스냅숏·릴리스의 수는 받아 둔 문서에서 센다."""
import io
import json
import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(HERE, 'docs')


def read(rel):
    with io.open(os.path.join(DOCS, rel), encoding='utf-8') as f:
        return f.read()


def run(ctx):
    for ex in ('appendstr', 'complit', 'initgo', 'rune', 'errortype',
               'delete', 'maporder', 'multiassign', 'equality',
               'newimport', 'copystruct'):
        ctx.go('ex/02/' + ex)
    # Go 1 이 없앤 것 — 지금 컴파일러의 거절이 증거다
    for ex in ('closerecv', 'oserror', 'olddelete', 'shadow', 'funceq',
               'oldimport'):
        ctx.go('ex/02/' + ex, expect=1)

    # Go 1 이전의 이름 붙은 릴리스(r56–r60)와 주간 스냅숏의 해마다 수.
    # 출처는 go.dev/doc/devel/pre_go1 과 weekly 의 절 제목이다.
    rel = re.findall(r'^§\t(r\d+) \(released (\d{4})/(\d\d)/(\d\d)\)',
                     read('pre_go1.txt'), re.M)
    ctx.table('pre_go1_releases', ['릴리스', '날짜'],
              [(r, '%s-%s-%s' % (y, m, d)) for r, y, m, d in rel],
              caption='출처: go.dev/doc/devel/pre_go1 의 절 제목')
    weeks = re.findall(r'^§\t(\d{4})-\d\d-\d\d', read('weekly.txt'), re.M)
    years = sorted(set(weeks))
    ctx.table('weekly_by_year', ['해', '주간 스냅숏 수'],
              [(y, weeks.count(y)) for y in years] + [('합계', len(weeks))],
              caption='출처: go.dev/doc/devel/weekly 의 절 제목(날짜)')
    tags = [t['name'] for t in json.loads(read('tags.json'))]
    kinds = [('weekly.*', 'weekly.'), ('release.r*', 'release.r'),
             ('go1*', 'go1')]
    ctx.table('tags_by_kind', ['태그 이름꼴', '개수'],
              [(k, sum(1 for t in tags if t.startswith(p)))
               for k, p in kinds],
              caption='출처: GitHub API 의 golang/go 태그 목록(2026-09-24)')

    # Go 1 의 패키지 재배치 — 노트의 'Old path | New path' 표를 그대로.
    # 한 장에 다 넣으면 접힌 화면에서 길어 둘로 나눈다.
    notes = read('relnotes/go1.txt')
    part = notes.split('Old path | New path\n', 1)[1].split('\nNote that', 1)[0]
    pairs = [tuple(c.strip() for c in l.split('|')) for l in part.split('\n')
             if '|' in l]
    half = (len(pairs) + 1) // 2
    for i, chunk in enumerate((pairs[:half], pairs[half:]), 1):
        ctx.table('go1_hierarchy_%d' % i, ['옛 경로(r60)', '새 경로(Go 1)'],
                  chunk, caption='출처: Go 1 릴리스 노트 §The package '
                                 'hierarchy (%d/2)' % i)
