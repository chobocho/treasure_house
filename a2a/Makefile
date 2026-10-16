# A2A 프로토콜 완전 가이드 — 만드는 법 전부가 여기에 있다.
#
# 규칙 하나: 덱은 산출물이다. 덱 HTML 을 손으로 고치지 말 것.
# 고칠 곳은 deck/sections/*.html 조각이거나, 그 조각이 가리키는
# 예제(ex/)다. 예제를 고쳤으면 tools/a2arun.py 로 다시 돌린다.
#
# 이 기계는 메모리가 빠듯하다(갤럭시 폴드 / proot, 스왑이 늘 찼다).
# PLAN.md §0.9: 러너는 한 번에 하나(a2arun 이 scratch/run.lock 을 잡는다),
# go 는 -p 1, make -j 금지.

SHELL   := /bin/sh
PY      ?= python3
VENV    := .venv
VPY     := $(VENV)/bin/python
RUFF    := $(VENV)/bin/ruff
NODE    ?= node
GO      ?= go

DECK    := ../A2A_프로토콜_완전_가이드.html
TOOLS   := ../tools
SPEC_TAG := v1.0.1
SPEC_URL := https://codeload.github.com/a2aproject/A2A/tar.gz/refs/tags/$(SPEC_TAG)
DOCS    ?= docs

# 예제 소스 — 환경 확인 때 쓰고 버릴 gate/ 와 node_modules/ 는 뺀다.
TS := $(shell find ex/ts -name '*.ts' -not -path '*/node_modules/*' \
        -not -path 'ex/ts/gate/*' 2>/dev/null | sort)
export GOTOOLCHAIN := local
export GOFLAGS :=

.DEFAULT_GOAL := help
.PHONY: help deps docs sources data data-check test fmt lint ts-check golden run run-check \
        manifest-check deck deck-verify deck-check font font-check all clean

help:                   ## 이 목록
	@grep -hE '^[a-z][a-zA-Z0-9_-]*:.*?## ' $(MAKEFILE_LIST) \
	  | sed 's/:.*## /\t/' \
	  | awk -F'\t' '{printf "  %-15s %s\n", $$1, $$2}'

# ── 도구 · 자료 ────────────────────────────────────────────────────
# .venv · node_modules · docs/ 는 커밋하지 않는다. 지워도 이것으로 되살린다.
# tsc 7 은 네이티브 바이너리다 — android-arm64 패키지를 linux-arm64 로 별칭해
# 두었으므로 npm install 에 --force 가 필요하다(PLAN.md §1).
deps:                   ## venv·npm·go 모듈 (ex/py/requirements.txt 의 고정판)
	test -x $(VPY) || $(PY) -m venv $(VENV)
	$(VPY) -m pip install -r ex/py/requirements.txt
	cd ex/ts && npm install --force
	cd ex/go && $(GO) mod download

# 스펙은 태그 tarball 하나로 받는다. sha256 과 받은 날을 FETCHED.txt 에 남긴다.
docs:                   ## A2A 스펙 v1.0.1 → docs/spec/ (+ docs/FETCHED.txt)
	mkdir -p $(DOCS)/spec scratch
	curl -fsSL -o scratch/a2a-spec.tar.gz $(SPEC_URL)
	tar -xzf scratch/a2a-spec.tar.gz -C $(DOCS)/spec --strip-components=1
	{ printf 'a2aproject/A2A %s\t%s\n' '$(SPEC_TAG)' '$(SPEC_URL)'; \
	  printf 'sha256\t%s\n' "$$(sha256sum scratch/a2a-spec.tar.gz | cut -d' ' -f1)"; \
	  printf 'fetched\t%s\n' "$$(date -u +%Y-%m-%dT%H:%M:%SZ)"; } >> $(DOCS)/FETCHED.txt
	rm -f scratch/a2a-spec.tar.gz
	@cat $(DOCS)/FETCHED.txt

# 1부(역사)의 출처 글. 주장은 data/facts.tsv, 맞은 근거는 data/evidence.tsv.
sources:                ## data/sources.tsv 의 출처 → docs/<key>.txt (없는 것만)
	$(PY) tools/fetch_sources.py

data:                   ## facts.tsv 를 받아 둔 출처에 대 evidence.tsv 를 만든다
	$(PY) tools/make_data.py

data-check:             ## evidence.tsv 가 최신이고 모든 주장의 근거가 맞는지
	$(PY) tools/make_data.py --check

# ── 시험 ───────────────────────────────────────────────────────────
# PLAN.md §0.8: 파이썬 도구는 전부 시험을 먼저 쓴다(RED → GREEN).
# 단언을 느슨하게 해서 통과시키지 말 것.
test:                   ## 도구 시험 (tools/tests, unittest)
	$(PY) -W error -m unittest discover -s tools/tests

# ── 예제 ───────────────────────────────────────────────────────────
# 72칸 — 접힌 폴드(374px)에서 코드 블록이 가로로 밀리지 않는 폭(PLAN.md §0.10).
fmt:                    ## 예제를 다듬는다 (ruff·prettier·gofmt, 72칸)
	$(RUFF) format --line-length 72 ex/py
	test -z "$(TS)" || (cd ex/ts && npx prettier --print-width 72 --write \
	  $(patsubst ex/ts/%,%,$(TS)))
	gofmt -w $$(find ex/go -name '*.go' -not -path 'ex/go/gate/*')

# ex/py 가 PYTHONPATH 뿌리다 — ruff 가 workshop·agents 를 first-party 로 보도록 src 를 준다
# (안 주면 import 정렬(I001)이 그 둘을 서드파티로 보고 틀렸다고 한다).
lint:                   ## 다듬어졌는지 · 정적 검사 (ruff · prettier · gofmt · go vet)
	$(RUFF) format --line-length 72 --check ex/py
	$(RUFF) check --config 'src = ["ex/py"]' ex/py
	test -z "$(TS)" || (cd ex/ts && npx prettier --print-width 72 --check \
	  $(patsubst ex/ts/%,%,$(TS)))
	@bad=$$(gofmt -l $$(find ex/go -name '*.go' -not -path 'ex/go/gate/*')); \
	  if test -n "$$bad"; then echo "  ✗ gofmt 를 안 거친 파일: $$bad"; exit 1; fi
	cd ex/go && $(GO) vet -p 1 $$($(GO) list ./... | grep -v '/gate/')

ts-check:               ## TypeScript 타입 검사 (tsc --noEmit, tsconfig)
	cd ex/ts && npx tsc -p .

# 세 언어의 workshop 이 골든 벡터(ex/fixtures/golden)에 동의하는지. 아직 자리만.
golden:                 ## 골든 벡터 시험 (py unittest · node --test · go test)
	@if test -d ex/py/workshop; then \
	  PYTHONPATH=ex/py $(VPY) -m unittest discover -s ex/py/workshop -t ex/py; \
	else echo '  ex/py/workshop 아직 없다'; fi
	@set -- $$(find ex/ts/workshop -name '*.test.ts' 2>/dev/null | sort); \
	  if test $$# -gt 0; then $(NODE) --test "$$@"; else echo '  ex/ts/workshop 시험 아직 없다'; fi
	@if test -d ex/go/workshop; then \
	  cd ex/go && $(GO) test -p 1 -count=1 ./workshop/...; \
	else echo '  ex/go/workshop 아직 없다'; fi

run:                    ## 예제를 전부 돌려 캡처를 쓴다 (norun 빼고)
	$(PY) tools/a2arun.py --all -q

run-check:              ## 전부 다시 돌려 캡처와 글자까지 같은지 본다 (오래 걸린다)
	$(PY) tools/a2arun.py --all --check

manifest-check:         ## 돌리지 않고 입력·캡처 해시만 장부와 대조
	$(PY) tools/a2arun.py --manifest-check

# ── 덱 ─────────────────────────────────────────────────────────────
# SKEL=1 이면 '준비 중입니다' 플레이스홀더와 아직 안 실은 예제를
# 오류로 세지 않는다. 본문을 다 채우면 이 변수를 뗀다.
deck:                   ## 조각 + 예제 + 캡처 → 덱 HTML 한 장
	$(PY) deck/build_deck.py $(if $(SKEL),--skeleton,)

deck-verify:            ## 덱의 코드·출력이 원본과 같은지 역검증
	$(PY) deck/verify_deck.py

deck-check:             ## 완성된 덱 점검 (node DOM 스텁 + 엔진 계약)
	$(NODE) deck/check_deck.js $(DECK) $(if $(SKEL),--skeleton,)

# 폰·태블릿에는 한글 고정폭 글꼴이 없다. 안 실으면 표와 코드가 어긋난다.
font:                   ## 고정폭 글꼴(DeckMono) 서브셋 내장
	$(PY) $(TOOLS)/embed_mono_font.py $(DECK)

font-check:             ## 내장 글꼴이 덱의 글자를 다 덮는지
	$(PY) $(TOOLS)/embed_mono_font.py --check $(DECK)

all:                    ## 전부 — 시험부터 글꼴까지, 하나라도 걸리면 여기서 멈춘다
all: test data-check lint ts-check golden manifest-check deck deck-verify deck-check \
     font font-check

# out/ 은 절대 지우지 않는다(증거다). docs/ 는 make docs 로 되살린다.
clean:                  ## 덱·작업 찌꺼기 지우기 (캡처는 남긴다)
	rm -rf $(DECK) scratch/run scratch/tmp scratch/bin
