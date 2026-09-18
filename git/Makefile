# Git 대백과사전 — 만드는 법 전부가 여기에 있다.
#
# 규칙 하나: 덱은 산출물이다. 덱 HTML 을 손으로 고치지 말 것.
# 고칠 곳은 deck/sections/*.html 조각이거나,
# 그 조각이 가리키는 소스·캡처·자료다.
#
# 이 기계는 메모리가 빠듯하다(갤럭시 폴드 / proot, 스왑이 늘 찼다).
# 규칙은 PLAN.md §0.7: 서브에이전트 둘까지, JVM 은 한 번에 하나
# (tools/flock_java.sh), -j 금지, 기록 실행은 직렬로.

SHELL       := /bin/sh
PY          ?= python3
NODE        ?= node
GO          ?= go
# g++ 로 못 박는다. PLAN §2 가 확인한 것은 g++ 15.2 다.
CXX         := g++
CXXFLAGS    := -std=c++20 -O2 -Wall -Wextra -Werror
GOFLAGS     := -p=1
export GOTOOLCHAIN := local
export GOFLAGS

DECK        := ../Git_대백과사전.html
TOOLS       := ../tools
JAVA_LOCK   := tools/flock_java.sh
TSC         := ts/node_modules/.bin/tsc

FIND        := find
# 덱에 실릴 소스. 시험 파일은 발췌만 인용하지만 폭 검사는 같이 받는다 —
# 덱에 실릴 줄은 예외 없이 72칸이다(PLAN.md §0.8).
SRC_PY      := $(shell $(FIND) py tools -name '*.py' 2>/dev/null | sort)
SRC_TS      := $(shell $(FIND) ts/src ts/tests -name '*.ts' \
                 2>/dev/null | sort)
SRC_GO      := $(shell $(FIND) go -name '*.go' 2>/dev/null | sort)
SRC_JAVA    := $(shell $(FIND) java -name '*.java' 2>/dev/null | sort)
SRC_CPP     := $(shell $(FIND) cpp \( -name '*.cpp' -o \
                 -name '*.hpp' \) 2>/dev/null | sort)
SRC_SH      := $(shell $(FIND) tools -name '*.sh' 2>/dev/null | sort)
SRC_TOP     := $(wildcard run_all.py)
SRC_ALL     := $(SRC_PY) $(SRC_TS) $(SRC_GO) $(SRC_JAVA) $(SRC_CPP) \
               $(SRC_SH) $(SRC_TOP)

.DEFAULT_GOAL := help
.PHONY: help deps mirror docs data data-check spec spec-check \
        golden golden-check \
        test test-py \
        test-go test-ts test-java test-cpp build build-go build-ts \
        build-java build-cpp parity run run-check record figs \
        figs-check figs-png tables claims-check width deck \
        deck-verify deck-slices deck-xref deck-check font font-check \
        all clean

help:                   ## 이 목록
	@grep -hE '^[a-z][a-zA-Z0-9_-]*:.*?## ' $(MAKEFILE_LIST) \
	  | sed 's/:.*## /\t/' \
	  | awk -F'\t' '{printf "  %-13s %s\n", $$1, $$2}'

# ── 받기 ───────────────────────────────────────────────────────────
# typescript@5 로 못 박는다. 6.x 는 플랫폼별 네이티브 실행 파일을 쓰는데
# 이 기계용(android-arm64) 꾸러미가 없어서 tsc 가 아예 안 뜬다.
# npm 캐시에는 가짜 tsc 가 들어 있으니 전역 tsc 를 믿지 말 것.
deps:                   ## TypeScript 컴파일러 내려받기 (ts/ 안에만)
	cd ts && npm install --no-save typescript@5 @types/node

# git/git 을 통째로 받으면 1 GB 가 넘는다(PLAN.md §0.7). 커밋과 트리만
# 받는 부분 복제로 태그 날짜·첫 커밋·git log -S 고고학에 충분하다.
# 이미 있으면 아무것도 안 한다 — 새 태그가 필요하면 fetch 를 손으로.
mirror:                 ## git/git 부분 복제 (blob 없이, 한 번만)
	@if test -d mirror/git.git; then \
	  echo '  mirror/git.git 이 이미 있다'; \
	else \
	  mkdir -p mirror && git clone --bare --filter=blob:none \
	    https://github.com/git/git mirror/git.git; \
	fi

# docs/ 는 커밋하지 않는 캐시다. 지워도 이것으로 다시 받는다.
docs:                   ## 공식 형식 문서·릴리스 노트 → docs/*.txt
	@if test -f tools/fetch_docs.py; then $(PY) tools/fetch_docs.py; \
	else echo '  tools/fetch_docs.py 아직 없다 (PLAN.md §5 4단계)'; fi

# releases·cves·timeline·contributors·commands·growth 표는 손으로
# 쓰지 않는다 — mirror 의 태그와 docs/ 의 릴리스 노트에서 만든다.
# 사람이 쓰는 원본은 data/events.tsv·cves_ko.tsv·commands_ko.tsv.
# mirror 가 있어야 돌므로 make all 에는 넣지 않는다(1분 반쯤).
data:                   ## mirror·docs → data/ 의 생성 표 여섯
	$(PY) tools/make_data.py

data-check:             ## data/ 의 생성 표가 mirror 와 그대로인지
	$(PY) tools/make_data.py --check

# ── 규격서 ─────────────────────────────────────────────────────────
# SPEC.md 의 바이트 예시(<!--EX-->)는 손으로 쓰지 않는다. 진짜 git
# 이 뜬 것을 채워 넣고, 다시 떠서 같은지 본다. git 이 바뀌면 여기가
# 먼저 운다.
spec:                   ## SPEC.md 의 예시 블록을 진짜 git 으로 채우기
	$(PY) tools/spec_examples.py --fill

spec-check:             ## SPEC.md 의 예시가 진짜 git 과 같은지
	$(PY) tools/spec_examples.py --check

# ── 기준 바이트 ────────────────────────────────────────────────────
# golden/ 은 진짜 git 이 만든다. 다시 만드는 것은 "지금까지의 기준이
# 틀렸다" 는 선언이다. 이유를 커밋 메시지에 적지 않고 돌리지 말 것.
golden:                 ## 진짜 git 으로 golden/ 다시 만들기
	@if test -f tools/make_golden.py; then $(PY) tools/make_golden.py; \
	else echo '  tools/make_golden.py 아직 없다 (PLAN.md §5 3단계)'; fi

golden-check:           ## golden/ 이 진짜 git 과 그대로인지 대조만
	@if test -f tools/make_golden.py; then \
	  $(PY) tools/make_golden.py --check; \
	else echo '  tools/make_golden.py 아직 없다 (PLAN.md §5 3단계)'; fi

# ── 짓기 ───────────────────────────────────────────────────────────
# 다섯 언어의 결과물이 모두 build/ 로 간다. parity 가 여기를 본다.
build-go:               ## Go mygit 짓기 (build/mygit-go)
	@if test -f go/go.mod; then \
	  mkdir -p build && cd go && \
	  $(GO) build -o ../build/mygit-go ./cmd/mygit; \
	else echo '  go/ 아직 없다 (PLAN.md §5 6단계)'; fi

build-ts:               ## TypeScript 컴파일 (build/ts)
	@if test -f ts/tsconfig.json; then \
	  test -x $(TSC) || { echo '  tsc 가 없다 — make deps 먼저'; \
	                      exit 1; }; \
	  $(TSC) -p ts/tsconfig.json; \
	else echo '  ts/ 아직 없다 (PLAN.md §5 6단계)'; fi

# JVM 은 한 번에 하나다. javac 도 JVM 이므로 여기도 flock 을 통한다.
build-java:             ## Java 컴파일 (build/java)
	@if test -d java/mygit; then \
	  mkdir -p build/java; \
	  sh $(JAVA_LOCK) javac -Xlint:all -Werror -d build/java \
	    $$(find java -name '*.java'); \
	else echo '  java/ 아직 없다 (PLAN.md §5 6단계)'; fi

# zlib 이 없는 기계라 -lz 를 걸지 않는다 — inflate 를 손으로
# 짠다(PLAN.md §9 결정 3).
build-cpp:              ## C++ mygit 짓기 (build/mygit-cpp)
	@if test -f cpp/main.cpp; then \
	  mkdir -p build; \
	  $(CXX) $(CXXFLAGS) -Icpp -o build/mygit-cpp \
	    $$(find cpp -maxdepth 1 -name '*.cpp'); \
	else echo '  cpp/ 아직 없다 (PLAN.md §5 6단계)'; fi

build: build-go build-ts build-java build-cpp  ## 파이썬 말고 넷 다 짓기

# ── 시험 ───────────────────────────────────────────────────────────
# PLAN.md §0.6: 기준 바이트는 진짜 git 이 먼저 만든다. 시험은 구현보다
# 먼저 쓰고, 올바른 까닭으로 실패(RED)하는 것을 본 뒤에 구현한다.
# 통과시키려고 단언을 느슨하게 하지 말 것.
test-py:                ## 파이썬 시험 (unittest)
	@if test -d py/mygit/tests; then \
	  $(PY) -m unittest discover -s py -t py; \
	else echo '  파이썬 시험 아직 없다 (PLAN.md §5 5단계)'; fi

test-go:                ## Go 시험
	@if test -f go/go.mod; then cd go && $(GO) test ./...; \
	else echo '  Go 시험 아직 없다 (PLAN.md §5 6단계)'; fi

test-ts: build-ts       ## TypeScript 시험 (node --test)
	@if test -d build/ts/tests; then \
	  $(NODE) --test build/ts/tests/; \
	else echo '  TypeScript 시험 아직 없다 (PLAN.md §5 6단계)'; fi

# 둘이 겹치면 이 기계는 OOM 으로 세션째 죽는다. 스위트 하나 = JVM 하나.
test-java: build-java   ## Java 시험 (JVM 하나만 — flock)
	@if test -d build/java/mygit; then \
	  sh $(JAVA_LOCK) java -cp build/java mygit.tests.RunTests; \
	else echo '  Java 시험 아직 없다 (PLAN.md §5 6단계)'; fi

# 시험 파일마다 따로 짓고 돌린다. 하나가 실패해도 나머지를 본다.
test-cpp:               ## C++ 시험 (cpp/tests/test_*.cpp)
	@if test -d cpp/tests; then \
	  mkdir -p build/cpp; bad=0; \
	  lib=$$(find cpp -maxdepth 1 -name '*.cpp' ! -name main.cpp); \
	  for t in cpp/tests/test_*.cpp; do \
	    b="build/cpp/$$(basename $$t .cpp)"; \
	    $(CXX) $(CXXFLAGS) -Icpp $$t $$lib -o $$b && ./$$b || bad=1; \
	  done; exit $$bad; \
	else echo '  C++ 시험 아직 없다 (PLAN.md §5 6단계)'; fi

test: test-py test-go test-ts test-java test-cpp  ## 다섯 언어 (직렬)

# ── 증거 ───────────────────────────────────────────────────────────
# 다섯 구현에 같은 대본을 돌려 .git 트리와 객체 목록을 맞대어 본다.
parity:                 ## 다섯 구현 대조 (out/tbl_parity.html)
	@if test -f run_all.py; then $(PY) run_all.py --only mygit_parity; \
	else echo '  run_all.py 아직 없다 (PLAN.md §5 7단계)'; fi

run:                    ## 실험을 전부 직렬로 돌려 out/ 를 채운다
	$(PY) run_all.py

run-check:              ## 캡처의 폭과 manifest 가 맞는지만 본다
	@if test -f run_all.py; then $(PY) run_all.py --check; \
	else echo '  run_all.py 아직 없다 (PLAN.md §5 7단계)'; fi

# 세 번 떠서 md5 가 같아야 한다. 캡처가 그 실행의 우연(시각·경로·
# 딕셔너리 차례)에 기대면 여기서 걸린다. 25분쯤 걸리니 뒤에서 돌린다.
record:                 ## 캡처를 세 번 돌려 같은지 본다
	sh tools/record.sh --check

figs:                   ## 도해 SVG 다시 만들기 (viewBox 폭 340)
	@if test -f deck/gen_figs.py; then $(PY) deck/gen_figs.py; \
	else echo '  deck/gen_figs.py 아직 없다 (PLAN.md §5 8단계)'; fi

figs-check:             ## 그림이 소스와 어긋나지 않았는지
	@if test -f deck/gen_figs.py; then $(PY) deck/gen_figs.py --check; \
	else echo '  deck/gen_figs.py 아직 없다 (PLAN.md §5 8단계)'; fi

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

# 이 덱에서 가장 틀리기 쉬운 것은 코드가 아니라 문장이다.
claims-check:           ## 인용한 문서 절과 연도에 근거가 있는가
	$(PY) deck/check_claims.py

width:                  ## 덱에 실릴 줄이 폴더블 폭(72칸)을 넘는지
	$(PY) tools/width.py $(SRC_ALL) Makefile

# ── 덱 ─────────────────────────────────────────────────────────────
deck:                   ## 조각 + 소스 + 캡처 + 자료 → 덱 HTML 한 장
	$(PY) deck/build_deck.py

deck-verify:            ## 덱의 코드·출력·표가 원본과 같은지 역검증
	$(PY) deck/verify_deck.py

# lines=A-B 가 함수·주석 경계에 맞는가. 소스를 고쳐 줄이 밀리면
# 번호는 그대로인데 내용이 밀린다 — Keycloak 덱에서 84곳이 나왔다.
deck-slices:            ## 인용 범위가 소스 경계에 맞는지
	$(PY) deck/check_slices.py

deck-xref:              ## "N부 M장" 이 진짜 그 자리를 가리키는지
	$(PY) deck/check_xref.py

# SKEL=1 이면 '아직 없습니다' 플레이스홀더를 오류로 세지 않는다.
# 본문을 다 채우면(PLAN.md §5 9단계) 이 변수를 뗀다.
deck-check:             ## 완성된 덱 점검 (node DOM 스텁 + 데모 기댓값)
	$(NODE) deck/check_deck.js $(DECK) $(if $(SKEL),--skeleton,)

# 폰·태블릿에는 한글 고정폭 글꼴이 없다. 안 실으면 표와 코드가 어긋난다.
font:                   ## 고정폭 글꼴(DeckMono) 서브셋 내장
	$(PY) $(TOOLS)/embed_mono_font.py $(DECK)

font-check:             ## 내장 글꼴이 덱의 글자를 다 덮는지
	$(PY) $(TOOLS)/embed_mono_font.py --check $(DECK)

## 조립부터 검증까지 — 하나라도 걸리면 여기서 멈춘다
all: spec-check tables run-check figs-check deck deck-verify \
     deck-slices deck-xref deck-check claims-check width font \
     font-check  ## 전부

# golden/ · out/ · mirror/ 는 절대 지우지 않는다(PLAN.md §7).
clean:                  ## 덱·빌드 찌꺼기 지우기 (캡처·기준은 남긴다)
	rm -rf $(DECK) build .build .svgrender
