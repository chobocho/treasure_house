# Go의 진화 — 만드는 법 전부가 여기에 있다.
#
# 규칙 하나: 덱은 산출물이다. 덱 HTML 을 손으로 고치지 말 것.
# 고칠 곳은 deck/sections/*.html 조각이거나,
# 그 조각이 가리키는 예제·캡처·자료다(PLAN.md §0.1).
#
# 이 기계는 메모리가 빠듯하다(갤럭시 폴드 / proot, 스왑이 늘 찼다).
# 규칙은 PLAN.md §0.8: 서브에이전트 둘까지, go 프로세스는 한 번에
# 하나(GOFLAGS=-p=1), -j 금지, 기록 실행은 직렬로, 실험 하나 60초.
#
# git/Makefile 에서 물려받아 줄였다 — java·ts·cpp·golden·mirror 는
# 이 덱에 없다(PLAN.md §5 1단계).

SHELL       := /bin/sh
PY          ?= python3
NODE        ?= node
GO          ?= go
GOFMT       ?= gofmt

# 옛 Go 를 받으려 들지 않게 못 박는다. 이 기계(android/arm64)에는 받을
# 툴체인이 없고(PLAN.md §0.6), 예제 go.mod 에 toolchain 줄이 끼어도
# 내려받기가 일어나면 안 된다. 캐시·모듈·HOME 은 전부 scratch/ 아래다.
SCRATCH     := $(CURDIR)/scratch
export GOTOOLCHAIN := local
export GOFLAGS     := -p=1
export GOPROXY     := off
export GOCACHE     := $(SCRATCH)/gocache
export GOPATH      := $(SCRATCH)/gopath
export GOMODCACHE  := $(SCRATCH)/gopath/pkg/mod

DECK        := ../Go의_진화.html
TOOLS       := ../tools

FIND        := find
# 덱에 실릴 소스. 폭 검사를 받는다 — 덱에 실릴 줄은 예외 없이
# 72칸이다(PLAN.md §0.9). ex/ 의 _test.go 도 발췌해 실릴 수 있어
# 같이 본다. 이 덱은 빌드 도구를 가르치지 않으므로(PLAN.md §0.13)
# 도구 가운데 0부가 증거 방식을 설명하며 인용할 gover.py 만 본다.
# 다른 도구를 인용하게 되면 조립기의 <pre> 폭 검사가 그 자리에서 잡는다.
SRC_GO      := $(shell $(FIND) ex -name '*.go' 2>/dev/null | sort)
SRC_PY      := $(wildcard tools/gover.py)
SRC_ALL     := $(SRC_GO) $(SRC_PY)
# ex/ 아래 go.mod 를 가진 디렉터리 하나가 예제 하나다.
EX_DIRS     := $(patsubst %/go.mod,%,$(shell $(FIND) ex -name go.mod \
                 2>/dev/null | sort))

.DEFAULT_GOAL := help
.PHONY: help test docs data data-check examples-check run run-check \
        record figs figs-check figs-png tables width budget-hint deck \
        deck-verify deck-slices deck-xref deck-check claims-check font \
        font-check all clean

help:                   ## 이 목록
	@grep -hE '^[a-z][a-zA-Z0-9_-]*:.*?## ' $(MAKEFILE_LIST) \
	  | sed 's/:.*## /\t/' \
	  | awk -F'\t' '{printf "  %-15s %s\n", $$1, $$2}'

# ── 시험 ───────────────────────────────────────────────────────────
# PLAN.md §0.7: 여기서 쓰는 파이썬 도구는 전부 시험을 먼저 쓴다(RED →
# GREEN). 픽스처는 받아 둔 진짜 문서의 작은 발췌다. 단언을 느슨하게
# 해서 통과시키지 말 것.
test:                   ## 도구 시험 (tools/tests, unittest)
	$(PY) -m unittest discover -s tools/tests

# ── 받기 ───────────────────────────────────────────────────────────
# docs/ 는 커밋하지 않는 캐시다. 지워도 이것으로 다시 받는다.
# 8·9부(1.25–1.28)를 만지는 세션은 시작할 때 반드시 다시 받는다
# (PLAN.md §0.5) — docs/FETCHED.txt 에 날짜와 첫 제목이 남는다.
docs:                   ## 공식 문서 → docs/ (노트·API 목록·명세)
	@if test -f tools/fetch_docs.py; then $(PY) tools/fetch_docs.py; \
	else echo '  tools/fetch_docs.py 아직 없다 (PLAN.md §5 2단계)'; fi

# releases·api_added·godebug 표는 손으로 쓰지 않는다 — docs/ 에서
# 만든다.
data:                   ## docs/ → data/ 의 생성 표 셋
	@if test -f tools/make_data.py; then $(PY) tools/make_data.py; \
	else echo '  tools/make_data.py 아직 없다 (PLAN.md §5 3단계)'; fi

# "1.N 에 들어왔다" 를 api/go1.N.txt 와 노트 제목에 대 본다 — 기억으로
# 적은 버전이 여기서 걸린다(PLAN.md §3.2).
data-check:             ## features.tsv 의 버전·인용이 docs/ 와 맞는지
	@if test -f tools/make_data.py; then \
	  $(PY) tools/make_data.py --check; \
	else echo '  tools/make_data.py 아직 없다 (PLAN.md §5 3단계)'; fi

# 모든 예제는 go vet 과 gofmt 를 통과해야 한다(PLAN.md §3.3). 예외는
# EXPECT_FAIL 파일을 둔 예제 — 사라진 문법을 지금 컴파일러가 거절하는
# 것을 보이려고 일부러 깨 둔 것이다(§0.6 d). 거절은 실험이 expect 로 본다. go 는 한
# 번에 하나만 돈다 — 디렉터리를 차례로 들어가고, 실험(tools/gover.py)과
# 같은 잠금(scratch/go.lock)을 잡는다. 서브에이전트가 동시에 돌려도 줄을 선다.
examples-check:         ## ex/ 의 예제 전부 go vet + gofmt -l
	@bad=0; n=0; k=0; \
	for d in $(EX_DIRS); do \
	  n=$$((n + 1)); \
	  if test -f $$d/EXPECT_FAIL; then k=$$((k + 1)); continue; fi; \
	  (cd $$d && flock $(SCRATCH)/go.lock $(GO) vet ./...) \
	    || { echo "  ✗ vet: $$d"; bad=1; }; \
	  out=$$($(GOFMT) -l $$d); \
	  if test -n "$$out"; then echo "  ✗ gofmt: $$out"; bad=1; fi; \
	done; echo "  예제 $$n개 — vet·gofmt 검사 (일부러 깨진 것 $$k개 제외)"; \
	exit $$bad

budget-hint:            ## 릴리스 노트 길이에 비례한 기능 장 수 제안
	@if test -f tools/budget_hint.py; then $(PY) tools/budget_hint.py; \
	else echo '  tools/budget_hint.py 아직 없다 (PLAN.md §4)'; fi

# ── 증거 ───────────────────────────────────────────────────────────
run:                    ## 실험을 전부 직렬로 돌려 out/ 를 채운다
	@if test -f run_all.py; then $(PY) run_all.py; \
	else echo '  run_all.py 아직 없다 (PLAN.md §5 4단계)'; fi

run-check:              ## 캡처의 폭과 manifest 가 맞는지만 본다
	@if test -f run_all.py; then $(PY) run_all.py --check; \
	else echo '  run_all.py 아직 없다 (PLAN.md §5 4단계)'; fi

# 세 번 떠서 sha256 이 같아야 한다. 캡처가 그 실행의 우연(경로·고루틴
# 번호·주소·시각)에 기대면 여기서 걸린다. 길게 걸리니 뒤에서 돌리고
# Monitor 로 기다린다(Bash 안의 & 금지 — git/PLAN.md 진행 기록).
record:                 ## 캡처를 세 번 돌려 같은지 본다
	@if test -f run_all.py; then sh tools/record.sh --check; \
	else echo '  run_all.py 아직 없다 (PLAN.md §5 4단계)'; fi

figs:                   ## 도해 SVG 다시 만들기 (viewBox 폭 340)
	@if test -f deck/gen_figs.py; then $(PY) deck/gen_figs.py; \
	else echo '  deck/gen_figs.py 아직 없다 (PLAN.md §5 6단계)'; fi

figs-check:             ## 그림이 자료와 어긋나지 않았는지
	@if test -f deck/gen_figs.py; then $(PY) deck/gen_figs.py --check; \
	else echo '  deck/gen_figs.py 아직 없다 (PLAN.md §5 6단계)'; fi

# 그린 것을 **눈으로 본다.** 압축 덱은 28장 중 8장, 무선 덱은
# 30장 중 4장을 이 단계에서 고쳤다.
figs-png: figs          ## SVG 를 PNG 로 렌더해 본다 (.svgrender/)
	@mkdir -p .svgrender
	@for f in deck/figs/*.svg; do \
	  test -e "$$f" || continue; \
	  n=".svgrender/$$(basename $$f .svg).png"; \
	  rsvg-convert -w 680 "$$f" -o "$$n"; \
	done; echo '  .svgrender/ 에 PNG 를 냈다 — 열어서 볼 것'

tables:                 ## data/*.tsv → out/tbl_*.html
	$(PY) deck/gen_tables.py

# 이 덱에서 가장 틀리기 쉬운 것은 코드가 아니라 "몇 버전" 이다.
claims-check:           ## 인용한 문서 절·연도·버전에 근거가 있는가
	$(PY) deck/check_claims.py

width:                  ## 덱에 실릴 줄이 폴더블 폭(72칸)을 넘는지
	$(PY) tools/width.py $(SRC_ALL) Makefile

# ── 덱 ─────────────────────────────────────────────────────────────
deck:                   ## 조각 + 예제 + 캡처 + 자료 → 덱 HTML 한 장
	$(PY) deck/build_deck.py

deck-verify:            ## 덱의 코드·출력·표가 원본과 같은지 역검증
	$(PY) deck/verify_deck.py

# lines=A-B 가 함수·주석 경계에 맞는가. 소스를 고쳐 줄이 밀리면
# 번호는 그대로인데 내용이 밀린다 — Keycloak 덱에서 84곳이 나왔다.
deck-slices:            ## 인용 범위가 소스 경계에 맞는지
	$(PY) deck/check_slices.py

deck-xref:              ## "N부 M장"·버전 배지가 진짜 그 자리·그 표인지
	$(PY) deck/check_xref.py

# SKEL=1 이면 '준비 중입니다' 플레이스홀더를 오류로 세지 않는다.
# 본문을 다 채우면(PLAN.md §5 9단계) 이 변수를 뗀다.
deck-check:             ## 완성된 덱 점검 (node DOM 스텁 + 엔진 계약)
	$(NODE) deck/check_deck.js $(DECK) $(if $(SKEL),--skeleton,)

# 폰·태블릿에는 한글 고정폭 글꼴이 없다. 안 실으면 표와 코드가 어긋난다.
font:                   ## 고정폭 글꼴(DeckMono) 서브셋 내장
	$(PY) $(TOOLS)/embed_mono_font.py $(DECK)

font-check:             ## 내장 글꼴이 덱의 글자를 다 덮는지
	$(PY) $(TOOLS)/embed_mono_font.py --check $(DECK)

## 조립부터 검증까지 — 하나라도 걸리면 여기서 멈춘다
all: test data-check examples-check tables run-check figs-check deck \
     deck-verify deck-slices deck-xref deck-check claims-check width \
     font font-check  ## 전부

# out/ · data/ 는 절대 지우지 않는다. docs/ 는 캐시라 make docs 로
# 되살린다.
clean:                  ## 덱·빌드 찌꺼기 지우기 (캡처·자료는 남긴다)
	rm -rf $(DECK) .svgrender scratch/work
