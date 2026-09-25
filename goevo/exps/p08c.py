# -*- coding: utf-8 -*-
"""8부 3장 — Go 1.27. 이 기계의 go 가 바로 1.27.1 이라, 거의 모든 항목을
돌려 볼 수 있다. 전과 후는 go 줄(1.26 ↔ 1.27), GODEBUG, GOEXPERIMENT 로."""

E = 'ex/08/'


def run(ctx):
    # --- 언어: go 줄이 막는 둘과 막지 않는 하나
    ctx.go(E + 'v127genmethod')
    ctx.go(E + 'v127genmethod', v='1.26', expect=1)
    ctx.go(E + 'v127geniface', cmd='go build .', tag='build', expect=1)
    ctx.go(E + 'v127randn')
    ctx.go(E + 'v127randn', v='1.26', cmd='go vet .', tag='vet', expect=1)
    ctx.go(E + 'v127promoted')
    ctx.go(E + 'v127promoted', v='1.26', expect=1)
    ctx.go(E + 'v127infer')
    ctx.go(E + 'v127infer', v='1.26')
    # --- 도구
    ctx.go(E + 'v127stdver', cmd='go test -count=1 .', tag='test', expect=1)
    ctx.go(E + 'v127stdver', v='1.27', cmd='go test -count=1 .', tag='test')
    ctx.go(E + 'v127godebugok')
    ctx.go(E + 'v127godebugold', expect=1)
    ctx.go(E + 'v127fix')
    ctx.go(E + 'v127fix', cmd='go fix -diff .', tag='fix', expect=1)
    ctx.go(E + 'v127tidy')
    ctx.go(E + 'v127tidy', cmd='go mod tidy -diff', tag='tidy', expect=1)
    ctx.go(E + 'v127tidy', v='1.26', cmd='go mod tidy -diff', tag='tidy')
    ctx.go(E + 'v127small', cmd='go doc -ex strings.Cut', tag='docex')
    ctx.go(E + 'v127small', cmd='go doc strings.ExampleCut', tag='docexample')
    # --- 런타임
    ctx.go(E + 'v127timer')
    ctx.go(E + 'v127timer', cmd='GOTRACEBACK=none go run .',
           godebug='asynctimerchan=1', expect=2)
    ctx.go(E + 'v127labels')
    ctx.go(E + 'v127labels', v='1.26')
    ctx.go(E + 'v127labels', godebug='tracebacklabels=0')
    ctx.go(E + 'v127leak')
    # --- 표준 라이브러리
    ctx.go(E + 'v127json')
    ctx.go(E + 'v127jsonv1')
    ctx.go(E + 'v127jsonv1', exp='nojsonv2')
    ctx.go(E + 'v127mldsa')
    ctx.go(E + 'v127uuid')
    ctx.go(E + 'v127simd', exp='simd')
    ctx.go(E + 'v127simd', expect=1)
    ctx.go(E + 'v127small')
    ctx.go(E + 'v127small2')
    ctx.go(E + 'v127testserver', cmd='go test -count=1 -v .', tag='test')
