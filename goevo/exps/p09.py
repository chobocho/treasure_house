# -*- coding: utf-8 -*-
"""9부 — 1.28 초안과 Go 2 이야기. 1.28 은 아직 없다(2026-09 기준). 그래서
(가) 1.28 을 요구하거나 1.28 의 새 API 를 쓰면 1.27.1 이 거절하는 것,
(나) 초안이 바꾸겠다는 동작의 **지금 모습**만 캡처한다."""


def run(ctx):
    ctx.go('ex/09/gomod128', expect=1)
    ctx.go('ex/09/futureapi', expect=1)
    ctx.go('ex/09/encodedlen')
    ctx.go('ex/09/proxyenv',
           cmd='HTTP_PROXY=http://upper.example:3128 '
               'http_proxy=http://lower.example:3128 go run .',
           tag='both')
    ctx.go('ex/09/scannererr', cmd='go vet .', tag='vet')
    ctx.go('ex/09/scannererr')
