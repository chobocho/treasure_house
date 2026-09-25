# -*- coding: utf-8 -*-
"""8부 1장 — Go 1.25. 언어 변화가 없는 릴리스라 go 줄 관문 짝은 없다
(scratch/brief/langgates.txt 에 1.25 가 없다). 전과 후는 GODEBUG 와
GOEXPERIMENT 로 보인다 — decoratemappings·x509sha256skid 는 GODEBUG 로도,
go 줄을 1.24 로 내려도(기본값이 go 줄을 따른다) 옛 동작이 나온다.
실험 셋: greenteagc(1.27.1 에서는 기본, nogreenteagc 로 끈다), jsonv2
(1.27.1 에서 기본 — nojsonv2 면 v2 패키지가 사라진다), nodwarf5.
1.24 의 GOEXPERIMENT=synctest 는 1.26 에서 지운다고 노트가 예고했고,
1.27.1 은 모르는 이름이라 거절한다. 시험은 -count=1 — 캐시 적중 여부로
마지막 줄이 흔들리지 않게."""

LDF = "go run '-ldflags=-s=false -w=false' ."
GOFMT = '/data/data/com.termux/files/usr/lib/go/bin/gofmt'


def run(ctx):
    # --- 언어: 명세의 core type 삭제 — 오류 메시지만 보인다
    ctx.go('ex/08/v125coretypes', cmd='go build .', tag='build', expect=1)
    # --- 도구
    ctx.go('ex/08/v125ignore', cmd='go list ./...', tag='list')
    ctx.go('ex/08/v125ignore', cmd='go list ./node_modules/pkg', tag='direct')
    ctx.go('ex/08/v125ignore', cmd='go mod edit -ignore=./dist -print',
           tag='edit')
    ctx.go('ex/08/v125ignore', cmd='go list work', tag='work')
    ctx.go('ex/08/v125ignore', cmd='go tool -n compile', tag='compile')
    ctx.go('ex/08/v125ignore', cmd='go tool -n nm', tag='nm')
    ctx.go('ex/08/v125ignore', cmd='go version -m -json ' + GOFMT,
           tag='versionjson')
    for a in ('waitgroup', 'hostport'):     # 분석기 하나씩 — 순서가 고정된다
        ctx.go('ex/08/v125vetwg', cmd='go vet -%s .' % a, tag=a, expect=1)
    # --- 런타임
    ctx.go('ex/08/v125maxprocs')
    ctx.go('ex/08/v125maxprocs', cmd='GOMAXPROCS=2 go run .', tag='env')
    ctx.go('ex/08/v125maxprocs', cmd='go list -f {{.DefaultGODEBUG}} .',
           tag='defaults')
    ctx.go('ex/08/v125maxprocs', v='1.24',
           cmd='go list -f {{.DefaultGODEBUG}} .', tag='defaults')
    ctx.go('ex/08/v125greentea')
    ctx.go('ex/08/v125greentea', exp='greenteagc')
    ctx.go('ex/08/v125greentea', exp='nogreenteagc')
    ctx.go('ex/08/v125flightrec')
    ctx.go('ex/08/v125repanic', cmd='GOTRACEBACK=none go run .', tag='run',
           expect=1)
    ctx.go('ex/08/v125vmaname')
    ctx.go('ex/08/v125vmaname', godebug='decoratemappings=0')
    ctx.go('ex/08/v125vmaname', v='1.24')
    # --- 컴파일러·링커
    ctx.go('ex/08/v125nilcheck', expect=1)
    ctx.go('ex/08/v125dwarf5', cmd=LDF, tag='dwarf')
    ctx.go('ex/08/v125dwarf5', exp='nodwarf5', cmd=LDF, tag='dwarf')
    ctx.go('ex/08/v125dwarf5')
    ctx.go('ex/08/v125stackmake')
    ctx.go('ex/08/v125stackmake',
           cmd='go run -gcflags=-d=variablemakehash=n .', tag='off')
    # --- 표준 라이브러리
    ctx.go('ex/08/v125synctest', cmd='go test -count=1 -v .', tag='test')
    ctx.go('ex/08/v125synctest', exp='synctest', cmd='go test -count=1 -v .',
           tag='test', expect=2)
    ctx.go('ex/08/v125jsonv2', exp='jsonv2')
    ctx.go('ex/08/v125jsonv2', exp='nojsonv2', cmd='go build .', tag='build',
           expect=1)
    ctx.go('ex/08/v125jsonv2', cmd='go vet .', tag='vet', expect=1)
    ctx.go('ex/08/v125wggo')
    ctx.go('ex/08/v125testattr', cmd='go test -count=1 -v .', tag='test')
    ctx.go('ex/08/v125typeassert')
    ctx.go('ex/08/v125csrf')
    ctx.go('ex/08/v125osroot')
    ctx.go('ex/08/v125skid')
    ctx.go('ex/08/v125skid', godebug='x509sha256skid=0')
    ctx.go('ex/08/v125skid', v='1.24')
    ctx.go('ex/08/v125small')
    ctx.go('ex/08/v125small2')
    ctx.go('ex/08/v125goast')
    # --- 플랫폼: 1.25 가 windows/arm 을 담은 마지막 릴리스였다
    ctx.go('ex/08/v125wggo', cmd='GOOS=windows GOARCH=arm go build .',
           tag='winarm', expect=2)
