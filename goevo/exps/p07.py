# -*- coding: utf-8 -*-
"""7부 — Go 1.21 ~ 1.24. go 줄로 전과 후를 보일 수 있는 것
(scratch/brief/langgates.txt): min·max·clear 와 제네릭 함수 인자 추론
(1.20 ↔ 1.21), 루프 변수의 반복별 의미(1.21 ↔ 1.22, 컴파일은 되고 출력이
달라진다; GOEXPERIMENT=loopvar 는 1.27.1 에도 남아 있다), 함수 range
(1.22 ↔ 1.23), 제네릭 타입 별칭(1.22 ↔ 1.23 — 1.27.1 의 관문은 go1.23).
GODEBUG 짝: panicnil 을 go.mod·//go:debug 로, httpmuxgo121, randseednop,
rsa1024min, fips140. 1.27 에서 없어진 설정(asynctimerchan·gotypesalias)은
옛 값을 주면 치명적 오류로 멈춘다 — 그것도 캡처한다.
HTTP 는 httptest 로만(네트워크 없음). 벤치마크는 -benchtime=Nx 고정."""


def run(ctx):
    # --- 1.21 언어
    ctx.go('ex/07/minmax')
    ctx.go('ex/07/minmax', v='1.20', expect=1)
    ctx.go('ex/07/clear')
    ctx.go('ex/07/clear', v='1.20', expect=1)
    ctx.go('ex/07/infer')
    ctx.go('ex/07/infer', v='1.20', expect=1)
    ctx.go('ex/07/untyped')
    # 무형 상수 추론은 go 줄로 갈리지 않는다
    ctx.go('ex/07/untyped', v='1.20')
    ctx.go('ex/07/initorder')
    # 1.21 의 미리보기: go 1.21 인데 GOEXPERIMENT=loopvar
    ctx.go('ex/07/loopvar', v='1.21', exp='loopvar')
    # --- 1.21 호환성·툴체인
    ctx.go('ex/07/defaults')
    ctx.go('ex/07/defaults', v='1.20')
    ctx.go('ex/07/defaults', v='1.26')
    ctx.go('ex/07/godebugline')
    ctx.go('ex/07/godebugbad', expect=1)
    ctx.go('ex/07/goline', v='1.27.9', expect=1)
    ctx.go('ex/07/goline', v='1.21.0')
    ctx.go('ex/07/goline', v='1.28.0', cmd='GOTOOLCHAIN=auto go run .',
           tag='auto', expect=1)
    ctx.go('ex/07/goline', cmd='go get go@1.22.0', tag='getgo')
    ctx.go('ex/07/goline', cmd='go get toolchain@go1.27.1', tag='gettc')
    ctx.go('ex/07/goline', cmd='go mod edit -go=1.22.3 -toolchain=go1.27.1 -print',
           tag='edit')
    ctx.go('ex/07/goline', cmd='go build -v -C . .', tag='c', expect=2)
    # --- 1.21 표준 라이브러리
    ctx.go('ex/07/slog')
    ctx.go('ex/07/slogvaluer')
    ctx.go('ex/07/slices')
    ctx.go('ex/07/sortfunc')
    ctx.go('ex/07/maps')
    ctx.go('ex/07/context')
    ctx.go('ex/07/once')
    ctx.go('ex/07/small121')
    ctx.go('ex/07/small121b')
    ctx.go('ex/07/creator')
    # --- 1.21 PGO·WASI
    ctx.go('ex/07/pgo')
    ctx.go('ex/07/pgo', cmd='go run -pgo=off .', tag='off')
    ctx.go('ex/07/pgo', cmd='go build -gcflags=ex/07/pgo=-m .', tag='m')
    ctx.go('ex/07/pgo', cmd='go build -pgo=off -gcflags=ex/07/pgo=-m .',
           tag='moff')
    ctx.go('ex/07/wasip1')
    ctx.go('ex/07/wasip1', cmd="go list -f '{{.GoFiles}}' .", tag='files')
    ctx.go('ex/07/wasip1',
           cmd="GOOS=wasip1 GOARCH=wasm go list -f '{{.GoFiles}}' .",
           tag='wfiles')
    ctx.go('ex/07/wasip1', cmd='GOOS=wasip1 GOARCH=wasm go build -o main.wasm .',
           tag='build')
    # --- 1.22 루프 변수
    ctx.go('ex/07/loopvar')
    ctx.go('ex/07/loopvar', v='1.21')
    ctx.go('ex/07/loopvar3')
    ctx.go('ex/07/loopvar3', v='1.21')
    ctx.go('ex/07/loopvartest', cmd='go test .', tag='test', expect=1)
    ctx.go('ex/07/loopvartest', v='1.21', cmd='go test .', tag='test')
    ctx.go('ex/07/loopvarfile')
    ctx.go('ex/07/rangeint')
    # --- 1.22 라이브러리
    ctx.go('ex/07/randv2')
    ctx.go('ex/07/routing')
    ctx.go('ex/07/precedence')
    ctx.go('ex/07/muxold')
    ctx.go('ex/07/muxold', v='1.21')
    ctx.go('ex/07/muxold', godebug='httpmuxgo121=1')
    ctx.go('ex/07/goversion')
    for a in ('appends', 'defers', 'slog'):     # 분석기 하나씩 — 순서가 고정된다
        ctx.go('ex/07/vet122', cmd='go vet -%s .' % a, tag=a, expect=1)
    ctx.go('ex/07/cover122', cmd='go test -cover ./...', tag='cover')
    ctx.go('ex/07/small122')
    ctx.go('ex/07/small122b')
    ctx.go('ex/07/small122c')
    # --- 1.23 반복자
    ctx.go('ex/07/rangefunc')
    ctx.go('ex/07/rangefunc', v='1.22', expect=1)
    ctx.go('ex/07/badyield', expect=1)
    ctx.go('ex/07/pull')
    ctx.go('ex/07/slicesiter')
    ctx.go('ex/07/adapters')
    ctx.go('ex/07/deferrange')
    # --- 1.23 타이머·GODEBUG 의 수명
    ctx.go('ex/07/timer')
    ctx.go('ex/07/timer', v='1.22')
    ctx.go('ex/07/timer', godebug='asynctimerchan=1',
           cmd='GOTRACEBACK=none go run .', expect=2)
    ctx.go('ex/07/godebugmod')
    ctx.go('ex/07/unique')
    ctx.go('ex/07/aliastypes')
    ctx.go('ex/07/aliastypes', godebug='gotypesalias=0',
           cmd='GOTRACEBACK=none go run .', expect=2)
    # --- 1.23 도구
    ctx.go('ex/07/small123', cmd='go telemetry', tag='telemetry')
    ctx.go('ex/07/small123', cmd='go env -changed', tag='changed')
    ctx.go('ex/07/small123', cmd='go env GOARM64', tag='goarm64')
    ctx.go('ex/07/stdversion', cmd='go vet .', tag='vet', expect=1)
    ctx.go('ex/07/stdversion')
    ctx.go('ex/07/linkname', cmd='go build .', tag='build', expect=1)
    ctx.go('ex/07/linkname', cmd='go run -ldflags=-checklinkname=0 .',
           tag='nocheck')
    ctx.go('ex/07/traceback', expect=1)
    ctx.go('ex/07/small123')
    ctx.go('ex/07/small123b')
    # --- 1.24 언어·런타임
    ctx.go('ex/07/genalias')
    ctx.go('ex/07/genalias', v='1.23')
    ctx.go('ex/07/genalias', v='1.22', expect=1)
    ctx.go('ex/07/genalias', cmd='GOEXPERIMENT=noaliastypeparams go build .',
           tag='noexp', expect=2)
    ctx.go('ex/07/weak')
    ctx.go('ex/07/cleanup')
    ctx.go('ex/07/strseq', cmd='GOEXPERIMENT=noswissmap go build .',
           tag='noswiss', expect=2)
    # --- 1.24 표준 라이브러리
    ctx.go('ex/07/osroot')
    ctx.go('ex/07/bloop',
           cmd='go test -run=NONE -bench=. -benchmem -benchtime=1000x .',
           tag='bench')
    ctx.go('ex/07/omitzero')
    ctx.go('ex/07/mlkem')
    ctx.go('ex/07/kdf')
    ctx.go('ex/07/fips')
    ctx.go('ex/07/fips', godebug='fips140=on')
    ctx.go('ex/07/fips', cmd='GOFIPS140=v1.0.0 go run .', tag='gofips')
    ctx.go('ex/07/seednop')
    ctx.go('ex/07/seednop', v='1.23')
    ctx.go('ex/07/seednop', godebug='randseednop=0')
    ctx.go('ex/07/rsamin')
    ctx.go('ex/07/rsamin', godebug='rsa1024min=0')
    ctx.go('ex/07/strseq')
    ctx.go('ex/07/strseq', cmd='go doc -short testing/synctest', tag='synctest')
    ctx.go('ex/07/testctx', cmd='go test -v .', tag='test')
    ctx.go('ex/07/small124')
    ctx.go('ex/07/small124b')
    # --- 1.24 도구
    ctx.go('ex/07/tool', cmd='go tool stamp a b', tag='tool')
    ctx.go('ex/07/tool', cmd='go generate -x .', tag='generate')
    ctx.go('ex/07/tool', cmd='go list tool', tag='list')
    ctx.go('ex/07/vettests', cmd='go vet .', tag='vet', expect=1)
    ctx.go('ex/07/vetprintf', cmd='go vet .', tag='vet', expect=1)
    ctx.go('ex/07/vetprintf', v='1.23', cmd='go vet .', tag='vet')
    ctx.go('ex/07/vetprintf')
    ctx.go('ex/07/buildjson', cmd='go build -json .', tag='json', expect=1)
    ctx.go('ex/07/strseq', cmd='GODEBUG=toolchaintrace=1 go version',
           tag='trace')
    ctx.go('ex/07/wasmexport',
           cmd='GOOS=wasip1 GOARCH=wasm go build -buildmode=c-shared -o add.wasm .',
           tag='build')
