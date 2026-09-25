# -*- coding: utf-8 -*-
"""6부 — Go 1.18 ~ 1.20. go 줄로 전과 후를 보일 수 있는 것: 타입 매개변수·any·
제네릭 타입(1.17 ↔ 1.18), 슬라이스→배열 변환·unsafe.String·인터페이스의
comparable 만족(1.19 ↔ 1.20), go fix 의 // +build 지우기(1.17 ↔ 1.18),
vet 의 루프 변수 검사(1.20 ↔ 1.22). GODEBUG 짝: execerrdot(1.19),
installgoroot·randautoseed·zipinsecurepath(1.20). 퍼징은 이 기계에서
-fuzz 가 지원되지 않아 씨앗 말뭉치 실행만 보인다. HTTP 는 127.0.0.1 안에서만."""


def run(ctx):
    # --- 1.18 제네릭
    ctx.go('ex/06/reverse')
    ctx.go('ex/06/reverse', v='1.17', expect=1)
    ctx.go('ex/06/sortiface')
    ctx.go('ex/06/contract', cmd='go build .', tag='build', expect=1)
    ctx.go('ex/06/typeparam')
    ctx.go('ex/06/brackets')
    ctx.go('ex/06/constraint')
    ctx.go('ex/06/constraint', v='1.17', expect=1)
    ctx.go('ex/06/notilde', expect=1)
    ctx.go('ex/06/anycomp')
    ctx.go('ex/06/anyonly')
    ctx.go('ex/06/anyonly', v='1.17', expect=1)
    ctx.go('ex/06/constraintvar', expect=1)
    ctx.go('ex/06/scalebad', expect=1)
    ctx.go('ex/06/scale')
    ctx.go('ex/06/stack')
    ctx.go('ex/06/stack', v='1.17', expect=1)
    ctx.go('ex/06/shape', cmd='go build -gcflags=-m=2 .', tag='m2')
    ctx.go('ex/06/genmethod', expect=1)
    ctx.go('ex/06/fieldaccess', expect=1)
    ctx.go('ex/06/vetgen', cmd='go vet .', tag='vet', expect=1)
    ctx.go('ex/06/vetgen')
    # --- 1.18 도구
    F = 'ex/06/fuzz'
    ctx.go(F, cmd='go test -run FuzzAbbrev -v .', tag='seed', expect=1)
    ctx.go(F, cmd='go test -fuzz FuzzAbbrev -fuzztime 20x .', tag='fuzz',
           expect=1)
    ctx.go(F, cmd='go doc testing', tag='doc')
    W = 'ex/06/work'
    ctx.go(W)
    ctx.go(W, cmd='GOWORK=off go run .', tag='off', expect=1)
    ctx.go(W, cmd='go env GOWORK', tag='env')
    ctx.go(W, cmd='go work edit -json', tag='json')
    ctx.go(W, cmd='go list -m', tag='list')
    ctx.go('ex/06/buildinfo')
    ctx.go('ex/06/plusbuild')
    ctx.go('ex/06/plusbuild', cmd='go fix -diff .', tag='fix', expect=1)
    ctx.go('ex/06/plusbuild', cmd='go fix -diff .', v='1.17', tag='fix')
    ctx.go('ex/06/unusedclosure', cmd='go build .', tag='build', expect=1)
    ctx.go('ex/06/appendgrow')
    # --- 1.18 표준 라이브러리
    ctx.go('ex/06/netip')
    ctx.go('ex/06/cut')
    ctx.go('ex/06/small118')
    ctx.go('ex/06/tmplbreak')
    # --- 1.19
    ctx.go('ex/06/atomictypes')
    M = 'ex/06/memlimit'
    ctx.go(M)
    ctx.go(M, cmd='GOMEMLIMIT=256MiB GOGC=off go run .', tag='env')
    G = 'ex/06/gclimit'
    ctx.go(G)
    ctx.go(G, cmd='GOGC=off go run .', tag='off')
    ctx.go(G, cmd='GOGC=off GOMEMLIMIT=32MiB go run .', tag='limit')
    ctx.go('ex/06/docfmt', cmd='gofmt -d tally.go', tag='gofmt', expect=1)
    ctx.go('ex/06/docfmt', cmd='go doc -all .', tag='doc')
    ctx.go('ex/06/doccomment')
    U = 'ex/06/unixtag'
    ctx.go(U)
    ctx.go(U, cmd='go list -f {{.GoFiles}} .', tag='files')
    ctx.go(U, cmd='GOOS=windows go list -f {{.GoFiles}} .', tag='windows')
    ctx.go(U, cmd='go list -json=ImportPath,GoFiles .', tag='json')
    ctx.go('ex/06/execdot')
    ctx.go('ex/06/execdot', godebug='execerrdot=0')
    ctx.go('ex/06/netctx')
    ctx.go('ex/06/appendf')
    ctx.go('ex/06/appendf',
           cmd='go test -run XXX -bench . -benchmem -benchtime=10000x .',
           tag='bench')
    ctx.go('ex/06/sortfind')
    ctx.go('ex/06/small119')
    ctx.go('ex/06/vetas', cmd='go vet .', tag='vet', expect=1)
    # --- 1.20
    ctx.go('ex/06/slice2array')
    ctx.go('ex/06/slice2array', v='1.19', expect=1)
    ctx.go('ex/06/unsafestr')
    ctx.go('ex/06/unsafestr', v='1.19', expect=1)
    ctx.go('ex/06/compiface')
    ctx.go('ex/06/compiface', v='1.19', expect=1)
    ctx.go('ex/06/structcmp')
    ctx.go('ex/06/localtype')
    C = 'ex/06/cover'
    ctx.go(C, cmd='go run -cover .', tag='nodir')
    ctx.go(C, cmd='GOCOVERDIR=. go run -cover .', tag='dir')
    # 앞 실행이 작업 사본에 남긴 커버리지 파일을 읽는다(차례에 기댐).
    ctx.go(C, cmd='go tool covdata percent -i=../06-cover__go1.20-dir',
           tag='pct')
    ctx.go(C, cmd='go tool covdata func -i=../06-cover__go1.20-dir',
           tag='func')
    P = 'ex/06/pgo'
    ctx.go(P, cmd='go build -pgo=off -gcflags=-m .', tag='off')
    ctx.go(P, cmd='go build -pgo=default.pgo -gcflags=-m .', tag='pgo')
    S = 'ex/06/skip'
    ctx.go(S, cmd='go test -v -skip Slow .', tag='skip')
    ctx.go(S, cmd='go test -v -run Table -skip TestTable/huge .',
           tag='sub')
    ctx.go(S, cmd='go list -f {{.Target}} fmt', tag='target')
    ctx.go(S, cmd='go list -f {{.Target}} fmt', godebug='installgoroot=all',
           tag='target')
    # vet 의 두 경고는 한 패키지에 두면 찍히는 차례가 매번 달라 둘로 나눴다
    ctx.go('ex/06/vetloop', cmd='go vet .', tag='vet', expect=1)
    ctx.go('ex/06/vetloop', cmd='go vet .', v='1.22', tag='vet')
    ctx.go('ex/06/vettime', cmd='go vet .', tag='vet', expect=1)
    ctx.go('ex/06/errjoin')
    ctx.go('ex/06/cause')
    ctx.go('ex/06/ecdh')
    ctx.go('ex/06/respctl')
    ctx.go('ex/06/rewrite')
    R = 'ex/06/randseed'
    ctx.go(R)
    ctx.go(R, godebug='randautoseed=0')
    ctx.go(R, v='1.19')
    ctx.go('ex/06/zipslip')
    ctx.go('ex/06/zipslip', godebug='zipinsecurepath=0')
    ctx.go('ex/06/small120')
