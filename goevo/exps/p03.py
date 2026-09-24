# -*- coding: utf-8 -*-
"""3부 — Go 1.1 ~ 1.4. 이 시기의 언어 변화(메서드 값, 끝나는 문장,
세 인덱스 슬라이스, 변수 없는 for range, **T 금지)는 go.mod 의 go 줄로
갈리지 않는다(scratch/brief/langgates.txt). 그래서 go 줄은 그 릴리스로
적고 '1.27.1 에서의 동작' 을 보인다. 금지된 것은 지금 컴파일러의 오류가
증거다(EXPECT_FAIL 이 붙은 예제)."""


def run(ctx):
    # ── Go 1.1
    ctx.go('ex/03/methodvalue')
    ctx.go('ex/03/terminating')
    ctx.go('ex/03/missingreturn', expect=1)
    ctx.go('ex/03/divzero', expect=1)
    ctx.go('ex/03/surrogate')
    ctx.go('ex/03/surrogatelit', expect=1)
    ctx.go('ex/03/intsize')
    ctx.go('ex/03/buildtag')
    ctx.go('ex/03/buildtag', cmd="go list -f '{{.GoFiles}} {{.IgnoredGoFiles}}' .",
           tag='list')
    ctx.go('ex/03/scanner')
    ctx.go('ex/03/reflectfn')
    ctx.go('ex/03/small11')
    # ── Go 1.2
    ctx.go('ex/03/slice3')
    ctx.go('ex/03/slice3bad', expect=1)
    ctx.go('ex/03/nilptr')
    ctx.go('ex/03/rtlimits')
    # 캐시된 결과('(cached)')는 첫 실행과 글자가 달라 -count=1 로 막는다
    ctx.go('ex/03/cover', cmd='go test -count=1 -cover .', tag='cover')
    ctx.go('ex/03/fmtindex')
    ctx.go('ex/03/tmpl')
    ctx.go('ex/03/textmarshal')
    ctx.go('ex/03/small12')
    # ── Go 1.3
    ctx.go('ex/03/mapiter')
    ctx.go('ex/03/semaphore')
    # 반복 횟수를 못 박아 둔다 — ns/op 는 정규화가 지운다
    ctx.go('ex/03/pool', cmd='go test -count=1 -bench . -benchtime=100x .',
           tag='bench')
    # ── Go 1.4
    ctx.go('ex/03/forrange')
    # gofmt -s 는 'for _ = range' 를 'for range' 로 줄인다(차이가 있으면 종료 1)
    ctx.go('ex/03/forrange', cmd='gofmt -s -d main.go', tag='gofmt', expect=1)
    ctx.go('ex/03/ptrptr', expect=1)
    ctx.go('ex/03/ifacealloc')
    ctx.go('ex/03/intpkg')
    ctx.go('ex/03/intpkg', cmd='go build ./outsider', tag='outsider', expect=1)
    ctx.go('ex/03/generate', cmd='go generate -x .', tag='generate')
    ctx.go('ex/03/generate')
    ctx.go('ex/03/filename')
    ctx.go('ex/03/filename', cmd="go list -f '{{.GoFiles}} {{.IgnoredGoFiles}}' .",
           tag='list')
    ctx.go('ex/03/testmain', cmd='go test -count=1 -v .', tag='test')
    ctx.go('ex/03/atomicvalue')
    ctx.go('ex/03/small14')
