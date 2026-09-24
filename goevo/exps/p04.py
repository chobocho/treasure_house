# -*- coding: utf-8 -*-
"""4부 — Go 1.5 ~ 1.10. 옛 툴체인이 없으므로 대부분 '1.27.1 에서의 동작' 이고,
전과 후를 보일 수 있는 것은 셋뿐이다: 타입 별칭(go 줄 1.8 ↔ 1.9),
GODEBUG http2client(1.6), GODEBUG netdns(1.5). HTTP 예제는 127.0.0.1
안에서만 오간다 — 바깥 네트워크는 쓰지 않는다."""


def run(ctx):
    # --- 1.5
    X = 'ex/04/ldflagsx'
    ctx.go(X)
    ctx.go(X, cmd='go run -ldflags=-X=main.version=release .', tag='x')
    # 1.5 이전의 두 인자 꼴 — 1.7 에서 없어졌다
    ctx.go(X, cmd="go run -ldflags='-X main.version release' .",
           tag='xold', expect=1)
    ctx.go(X, cmd='go tool compile -V', tag='compilev')
    ctx.go('ex/04/gogc')
    ctx.go('ex/04/gogc', cmd='GOGC=200 go run .', tag='gogc200')
    ctx.go('ex/04/gogc', cmd='GOGC=off go run .', tag='gogcoff')
    ctx.go('ex/04/gomaxprocs')
    ctx.go('ex/04/gomaxprocs', cmd='GOMAXPROCS=1 go run .', tag='one')
    ctx.go('ex/04/maplit')
    ctx.go('ex/04/maplit', cmd='gofmt -s -d old.go', tag='simplify',
           expect=1)
    ctx.go('ex/04/internalpkg')
    ctx.go('ex/04/internalpkg', cmd='go build -tags demo .', tag='demo',
           expect=1)
    ctx.go('ex/04/godoc')
    ctx.go('ex/04/godoc', cmd='go doc strings.Compare', tag='doc')
    ctx.go('ex/04/godoc', cmd='go doc io.Writer.Write', tag='method')
    ctx.go('ex/04/bigfloat')
    ctx.go('ex/04/flagusage')
    ctx.go('ex/04/netdns')
    ctx.go('ex/04/netdns', godebug='netdns=go+2')
    ctx.go('ex/04/small15')
    # --- 1.6
    ctx.go('ex/04/http2')
    ctx.go('ex/04/http2', godebug='http2client=0')
    ctx.go('ex/04/mapmisuse', cmd='GOTRACEBACK=none go run .', tag='none',
           expect=1)
    ctx.go('ex/04/traceback', expect=1)
    ctx.go('ex/04/traceback', cmd='GOTRACEBACK=all go run .', tag='all',
           expect=1)
    ctx.go('ex/04/sortsort')
    ctx.go('ex/04/template')
    ctx.go('ex/04/vetprintf', cmd='go vet .', tag='vet', expect=1)
    ctx.go('ex/04/small16')
    # --- 1.7
    ctx.go('ex/04/cancel')
    ctx.go('ex/04/deadline')
    ctx.go('ex/04/lostcancel', cmd='go vet .', tag='vet', expect=1)
    ctx.go('ex/04/bce')
    ctx.go('ex/04/bce', cmd="go build -gcflags='-d=ssa/check_bce/debug=1' .",
           tag='bce')
    S = 'ex/04/subtests'
    ctx.go(S, cmd='go test -v .', tag='v')
    ctx.go(S, cmd='go test -v -run TestSplit/trailing .', tag='run')
    ctx.go(S, cmd='go test -run XXX -bench . -benchmem -benchtime=10000x .',
           tag='bench')
    ctx.go('ex/04/small17')
    # --- 1.8
    ctx.go('ex/04/structconv')
    ctx.go('ex/04/sortslice')
    ctx.go('ex/04/gopath', cmd='GOPATH= go run .', tag='unset')
    ctx.go('ex/04/gopath', cmd='GOPATH= go env GOPATH', tag='env')
    ctx.go('ex/04/shutdown')
    ctx.go('ex/04/small18')
    # --- 1.9
    ctx.go('ex/04/alias')
    ctx.go('ex/04/alias', v='1.8', expect=1)
    ctx.go('ex/04/aliasrepair')
    ctx.go('ex/04/monotonic')
    ctx.go('ex/04/mathbits')
    ctx.go('ex/04/helper', cmd='go test .', tag='test', expect=1)
    ctx.go('ex/04/helper', cmd='go test -list .', tag='list')
    ctx.go('ex/04/helper', cmd='go env -json GOOS GOARCH', tag='envjson')
    ctx.go('ex/04/syncmap')
    ctx.go('ex/04/frames')
    # --- 1.10
    T = 'ex/04/testcache'
    # 첫 실행은 캐시를 채울 뿐이다(캐시가 이미 차 있으면 이것도 cached).
    # 덱에 싣지 않는다.
    ctx.go(T, cmd='go test .', tag='warm')
    ctx.go(T, cmd='go test .', tag='cached')
    ctx.go(T, cmd='go test -count=1 .', tag='count1')
    ctx.go(T, cmd='go env GOCACHE', tag='gocache')
    ctx.go('ex/04/testvet', cmd='go test .', tag='test', expect=1)
    ctx.go('ex/04/testvet', cmd='go test -vet=off .', tag='vetoff')
    ctx.go('ex/04/failfast', cmd='go test .', tag='test', expect=1)
    ctx.go('ex/04/failfast', cmd='go test -failfast .', tag='failfast',
           expect=1)
    ctx.go('ex/04/builder')
    ctx.go('ex/04/builder',
           cmd='go test -run XXX -bench . -benchmem -benchtime=10000x .',
           tag='bench')
    ctx.go('ex/04/gofmt110')
    ctx.go('ex/04/urlresolve')
    ctx.go('ex/04/fields')
    ctx.go('ex/04/small110')
