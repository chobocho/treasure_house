# -*- coding: utf-8 -*-
"""8부 2장 — Go 1.26. 언어 관문은 new(expr) 하나다(scratch/brief/langgates.txt):
go 1.25 ↔ 1.26 의 컴파일 오류 짝. 자기 참조 제약은 관문이 없어 go 1.25 로
내려도 컴파일된다 — 그것도 캡처한다. go fix 의 현대화 도구는 go 줄을 보고
고칠지 정한다(1.20 ↔ 1.26, 1.25 ↔ 1.26). GODEBUG 짝: cryptocustomrand(go 줄
1.25 로도), tlssecpmlkem, urlstrictcolons·urlmaxqueryparams.
GOEXPERIMENT 짝: nogreenteagc, norandomizedheapbase64, runtimesecret. 1.26 의
goroutineleakprofile 실험은 1.27 에서 지워졌다 — 그 거절도 캡처한다.
컴파일러의 슬라이스 스택 할당은 -d=variablemakehash=n 으로 끈 짝.
네트워크 없음: TLS 는 net.Pipe, HTTP 는 httptest. 벤치마크는 -benchtime=Nx."""


def run(ctx):
    # --- 언어
    ctx.go('ex/08/v126newexpr')
    ctx.go('ex/08/v126newexpr', v='1.25', expect=1)
    ctx.go('ex/08/v126newjson')
    ctx.go('ex/08/v126newtrap')
    ctx.go('ex/08/v126newnil', expect=1)
    ctx.go('ex/08/v126selfref')
    ctx.go('ex/08/v126selfref', v='1.25')
    # --- go fix
    ctx.go('ex/08/v126gofix')
    ctx.go('ex/08/v126gofix', cmd='go fix -diff .', tag='diff', expect=1)
    ctx.go('ex/08/v126gofix', v='1.20', cmd='go fix -diff .', tag='diff',
           expect=1)
    ctx.go('ex/08/v126gofix', cmd='go tool fix help', tag='help')
    ctx.go('ex/08/v126fixnew')
    ctx.go('ex/08/v126fixnew', cmd='go fix -newexpr -diff .', tag='diff',
           expect=1)
    ctx.go('ex/08/v126fixnew', v='1.25', cmd='go fix -newexpr -diff .',
           tag='diff')
    ctx.go('ex/08/v126fixinline')
    ctx.go('ex/08/v126fixinline', cmd='go fix -diff ./...', tag='diff',
           expect=1)
    # --- go 명령
    ctx.go('ex/08/v126modinit')
    ctx.go('ex/08/v126modinit', cmd='go tool doc fmt.Println', tag='tooldoc',
           expect=2)
    ctx.go('ex/08/v126modinit', cmd='go doc fmt.Println', tag='doc')
    # --- 런타임
    ctx.go('ex/08/v126greentea')
    ctx.go('ex/08/v126greentea', exp='nogreenteagc')
    ctx.go('ex/08/v126heapbase')
    ctx.go('ex/08/v126heapbase', exp='norandomizedheapbase64')
    ctx.go('ex/08/v126leak')
    ctx.go('ex/08/v126leak', exp='goroutineleakprofile', expect=2)
    # --- 컴파일러·링커·포트
    ctx.go('ex/08/v126stackslice')
    ctx.go('ex/08/v126stackslice',
           cmd='go run -gcflags=-d=variablemakehash=n .', tag='off')
    ctx.go('ex/08/v126elf')
    ctx.go('ex/08/v126ports',
           cmd='GOOS=windows GOARCH=arm go build -o x.exe .', tag='winarm',
           expect=2)
    ctx.go('ex/08/v126ports',
           cmd='GOOS=windows GOARCH=arm64 go build -o x.exe .',
           tag='winarm64')
    # --- 암호
    ctx.go('ex/08/v126cryptorand')
    ctx.go('ex/08/v126cryptorand', godebug='cryptocustomrand=1')
    ctx.go('ex/08/v126cryptorand', v='1.25')
    ctx.go('ex/08/v126cryptotest', cmd='go test -count=1 -v .', tag='test')
    ctx.go('ex/08/v126hpke')
    ctx.go('ex/08/v126tlspq')
    ctx.go('ex/08/v126tlspq', godebug='tlssecpmlkem=0')
    # --- 표준 라이브러리
    ctx.go('ex/08/v126astype')
    ctx.go('ex/08/v126reflectiter')
    ctx.go('ex/08/v126multihandler')
    ctx.go('ex/08/v126allocs')
    ctx.go('ex/08/v126url')
    ctx.go('ex/08/v126url', godebug='urlstrictcolons=0,urlmaxqueryparams=0')
    ctx.go('ex/08/v126url', v='1.25')
    ctx.go('ex/08/v126http')
    ctx.go('ex/08/v126signal')
    ctx.go('ex/08/v126metrics')
    ctx.go('ex/08/v126small')
    ctx.go('ex/08/v126small2')
    # --- testing
    ctx.go('ex/08/v126artifact', cmd='go test -count=1', tag='test')
    ctx.go('ex/08/v126artifact', cmd='go test -count=1 -artifacts', tag='artifacts')
    ctx.go('ex/08/v126bloop',
           cmd='go test -count=1 -run=NONE -bench=. -benchmem -benchtime=1000x .',
           tag='bench')
    ctx.go('ex/08/v126bloop',
           cmd='go test -count=1 -gcflags=-m -run=NONE -bench=. -benchtime=1x .',
           tag='m')
    # --- 실험 패키지
    ctx.go('ex/08/v126secret')
    ctx.go('ex/08/v126secret', exp='runtimesecret')
