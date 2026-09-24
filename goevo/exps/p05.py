# -*- coding: utf-8 -*-
"""5부 — Go 1.11 ~ 1.17. 모듈이 오고(1.11) 기본이 되기까지(1.16), 그리고
1.13·1.14·1.17 의 언어 변화. 언어 변화는 go.mod 의 go 줄로 갈린다
(scratch/brief/langgates.txt) — 1.13 숫자 리터럴·부호 있는 시프트,
1.14 겹치는 인터페이스, 1.17 슬라이스→배열 포인터·unsafe.Add/Slice.
모듈 예제는 전부 오프라인이다(GOPROXY=off). 네트워크가 필요한 것
(go get 원격, go install pkg@v)은 캡처하지 않고 노트를 인용한다."""


def run(ctx):
    # ── Go 1.11
    ctx.go('ex/05/gomod')
    ctx.go('ex/05/gomod', cmd='go list -m -json', tag='json')
    ctx.go('ex/05/gomod', cmd='go env GOMOD GOPATH', tag='env')
    ctx.go('ex/05/modinit', cmd='go -C hello mod init example.com/hello',
           tag='init')
    ctx.go('ex/05/modinit', cmd="GO111MODULE=off go list -f '{{.ImportPath}}' .",
           tag='gopath')
    ctx.go('ex/05/modinit', cmd="go list -f '{{.ImportPath}}' .", tag='mod')
    ctx.go('ex/05/modtools')
    ctx.go('ex/05/modtools', cmd='go list -m all', tag='all')
    ctx.go('ex/05/modtools', cmd='go mod graph', tag='graph')
    ctx.go('ex/05/modtools', cmd='go mod why -m example.com/lib', tag='why')
    ctx.go('ex/05/modtools', cmd='go mod verify', tag='verify')
    ctx.go('ex/05/wasm')
    ctx.go('ex/05/wasm', cmd="GOOS=js GOARCH=wasm go list -f '{{.GoFiles}}' .",
           tag='jsfiles')
    ctx.go('ex/05/wasm', cmd="go list -f '{{.GoFiles}}' .", tag='files')
    ctx.go('ex/05/wasm', cmd='GOOS=js GOARCH=wasm go build -o main.wasm .',
           tag='build')
    ctx.go('ex/05/goflags')
    ctx.go('ex/05/goflags', cmd='GOFLAGS=-tags=extra go run .', tag='goflags')
    ctx.go('ex/05/typeswitch', expect=1)
    # 이 거절은 go 줄로 갈리지 않는다 — 1.10 으로 내려도 같다
    ctx.go('ex/05/typeswitch', v='1.10', expect=1)
    ctx.go('ex/05/vetwrap', cmd='go vet .', tag='vet', expect=1)
    ctx.go('ex/05/bce', cmd='go build -gcflags=-d=ssa/check_bce/debug=1 .',
           tag='bce')
    ctx.go('ex/05/small11')
    # ── Go 1.12
    ctx.go('ex/05/langver')
    ctx.go('ex/05/langver', v='1.8', expect=1)
    ctx.go('ex/05/langver', cmd='go mod edit -go=1.11 -print', tag='edit')
    # replace 만 있고 require 가 없다 — 1.16 부터 빌드는 go.mod 를 고치지 않는다
    ctx.go('ex/05/replace', expect=1)
    ctx.go('ex/05/replace', cmd='go get example.com/greet', tag='get')
    ctx.go('ex/05/replace', cmd='GOFLAGS=-mod=mod go run .', tag='modmod')
    ctx.go('ex/05/fmtmap')
    ctx.go('ex/05/buildinfo')
    ctx.go('ex/05/mapiter')
    ctx.go('ex/05/bits')
    ctx.go('ex/05/benchx', cmd='go test -count=1 -run=NONE -bench=. -benchtime=100x .',
           tag='bench')
    ctx.go('ex/05/small12')
    ctx.go('ex/05/small12', cmd='go doc -src strings.ReplaceAll', tag='docsrc')
    # ── Go 1.13
    ctx.go('ex/05/numlit')
    ctx.go('ex/05/numlit', v='1.12', expect=1)
    ctx.go('ex/05/numfmt')
    # gofmt 는 접두사·지수의 대문자를 소문자로 고친다(차이가 있으면 종료 1)
    ctx.go('ex/05/numfmt', cmd='gofmt -d upper.go.txt', tag='gofmt', expect=1)
    ctx.go('ex/05/shift')
    ctx.go('ex/05/shift', v='1.12', expect=1)
    ctx.go('ex/05/wrap')
    ctx.go('ex/05/erras')
    ctx.go('ex/05/erris')
    ctx.go('ex/05/goenv')
    # gover 는 GOPROXY=off·GOSUMDB=off 로 돈다 — 비우면 기본값이 보인다
    ctx.go('ex/05/goenv', cmd='GOPROXY= GOSUMDB= go env GOPROXY GOSUMDB',
           tag='defaults')
    ctx.go('ex/05/panicmsg')
    ctx.go('ex/05/ed25519')
    ctx.go('ex/05/small13')
    ctx.go('ex/05/small13', cmd='go version -m /data/data/com.termux/files/usr/lib/go/bin/gofmt',
           tag='versionm')
    # ── Go 1.14
    ctx.go('ex/05/overlap')
    ctx.go('ex/05/overlap', v='1.13', expect=1)
    ctx.go('ex/05/modtools', cmd='go mod vendor -v', tag='vendor')
    ctx.go('ex/05/preempt')
    ctx.go('ex/05/maphash')
    ctx.go('ex/05/cleanup', cmd='go test -count=1 -v .', tag='test')
    ctx.go('ex/05/small14')
    # ── Go 1.15
    # 분석기 둘의 진단 차례는 실행마다 다를 수 있다 — 하나씩 따로 돌린다
    ctx.go('ex/05/vet115', cmd='go vet -stringintconv .', tag='stringintconv',
           expect=1)
    ctx.go('ex/05/vet115', cmd='go vet -ifaceassert .', tag='ifaceassert',
           expect=1)
    ctx.go('ex/05/tzdata')
    # 고루틴 덤프의 주소는 실행마다 다르다 — 패닉 값 줄만 남긴다
    ctx.go('ex/05/panicval', cmd='GOTRACEBACK=none go run .', tag='none',
           expect=1)
    ctx.go('ex/05/misplaced', expect=1)
    ctx.go('ex/05/testing115', cmd='go test -count=1 -v .', tag='test')
    ctx.go('ex/05/flaghelp', cmd='go run . -n 2', tag='n2')
    ctx.go('ex/05/flaghelp', cmd='go run . -h', tag='help')
    ctx.go('ex/05/goenv', cmd='go env GOMODCACHE', tag='modcache')
    ctx.go('ex/05/small15')
    # ── Go 1.16
    ctx.go('ex/05/embed')
    ctx.go('ex/05/embed', cmd="go list -f '{{.EmbedFiles}}' .", tag='list')
    ctx.go('ex/05/embedfs')
    ctx.go('ex/05/embedfs', cmd="go list -f '{{.EmbedPatterns}} {{.EmbedFiles}}' .",
           tag='list')
    ctx.go('ex/05/embedbad', expect=1)
    ctx.go('ex/05/iofs')
    ctx.go('ex/05/fstest', cmd='go test -count=1 -v .', tag='test', expect=1)
    ctx.go('ex/05/ioutil')
    ctx.go('ex/05/ioutil', cmd='go doc io/ioutil.ReadFile', tag='doc')
    ctx.go('ex/05/notifyctx')
    ctx.go('ex/05/metrics')
    ctx.go('ex/05/vet116', cmd='go vet .', tag='vet', expect=1)
    ctx.go('ex/05/constraint')
    ctx.go('ex/05/small16')
    # ── Go 1.17
    ctx.go('ex/05/slice2arr')
    ctx.go('ex/05/slice2arr', v='1.16', expect=1)
    ctx.go('ex/05/slice2arrpanic')
    ctx.go('ex/05/unsafeadd')
    ctx.go('ex/05/unsafeadd', v='1.16', expect=1)
    ctx.go('ex/05/prune')
    ctx.go('ex/05/prune', cmd='go mod graph', tag='graph')
    # 같은 go.mod 를 go 1.16 으로 정리하면 간접 의존 줄이 빠진다(차이가 있으면 종료 1)
    ctx.go('ex/05/prune', v='1.16', cmd='go mod tidy -diff', tag='tidy',
           expect=1)
    ctx.go('ex/05/prune', cmd='go mod tidy -diff', tag='tidy')
    ctx.go('ex/05/gobuild')
    ctx.go('ex/05/gobuild', cmd='go run -tags=purego .', tag='purego')
    ctx.go('ex/05/gobuild', cmd='gofmt -d old.go.txt', tag='gofmt', expect=1)
    ctx.go('ex/05/vet117', cmd='go vet -stdmethods .', tag='stdmethods',
           expect=1)
    ctx.go('ex/05/vet117', cmd='go vet -sigchanyzer .', tag='sigchanyzer',
           expect=1)
    ctx.go('ex/05/semicolon')
    ctx.go('ex/05/shuffle', cmd='go test -count=1 -v .', tag='test')
    ctx.go('ex/05/shuffle', cmd='go test -count=1 -v -shuffle=7 .', tag='shuffle',
           expect=1)
    ctx.go('ex/05/small17')
    ctx.go('ex/05/small17b')
