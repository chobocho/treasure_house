# -*- coding: utf-8 -*-
"""0부 — 이 덱을 만든 기계. 이 덱이 왜 이런 방식으로 '전과 후' 를
보이는지(PLAN.md §0.6, §0.8)의 근거 캡처들."""

M = 'ex/00/machine'


def run(ctx):
    ctx.go(M)
    ctx.go(M, cmd='go version', tag='version')
    ctx.go(M, cmd='go tool', tag='tool')
    ctx.go(M, cmd='go env GOOS GOARCH GOVERSION GOTOOLCHAIN', tag='env')
    # 옛 툴체인은 이 기계에 받을 수 없다 — 모듈 프록시에 android/arm64
    # 판이 없다. 받으려면 네트워크를 거쳐야 하므로 GOPROXY 를 명령 줄에 적는다.
    ctx.go(M, cmd='GOPROXY=https://proxy.golang.org GOTOOLCHAIN=go1.26.0 '
           'go version', tag='oldtoolchain', expect=1)
    # 경쟁 검출기(-race)는 이 플랫폼에서 돌지 않는다
    ctx.go(M, cmd='go run -race .', tag='race', expect=2)
    # 증거 방식 (가) — 언어 버전 지시자. 같은 파일을 go 1.21 로 내리면
    # 컴파일러가 거절한다. 그 오류 메시지가 곧 '1.22 에서 생겼다' 의 증거다.
    ctx.go('ex/00/langdir')
    ctx.go('ex/00/langdir', v='1.21', expect=1)
    # 증거 방식 (나) — GODEBUG. 기본값은 go 줄을 따르고(1.20 이면 옛 동작),
    # 환경 변수로도 옛 동작을 고를 수 있다.
    ctx.go('ex/00/panicnil')
    ctx.go('ex/00/panicnil', v='1.20')
    ctx.go('ex/00/panicnil', godebug='panicnil=1')
