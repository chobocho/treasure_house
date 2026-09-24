# -*- coding: utf-8 -*-
"""1부 — 탄생 이전. 설계 원칙(FAQ, 2012 발표문 Go at Google)이 지금의
컴파일러·도구에서 그대로 보이는지를 캡처한다. 옛 Go 가 아니라 1.27.1 의
동작이며, 원칙의 출처는 문서 배지가 맡는다."""


def run(ctx):
    for ex in ('keywords', 'compose', 'errvalue', 'csp', 'decl'):
        ctx.go('ex/01/' + ex)
    # 원칙이 곧 컴파일 오류인 것들
    for ex in ('unusedimport', 'export', 'numconv'):
        ctx.go('ex/01/' + ex, expect=1)
    # gofmt — 모양을 사람이 아니라 도구가 정한다
    ctx.go('ex/01/gofmt', cmd='gofmt -d main.go', tag='gofmt', expect=1)
    ctx.go('ex/01/gofmt')
