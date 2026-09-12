# 압축 대백과사전 — 만드는 법 전부가 여기에 있다.
#
# 규칙 하나: 덱은 산출물이다. 덱 HTML 을 손으로 고치지 말 것.
# 고칠 곳은 deck/sections/*.html 조각이거나, 그 조각이 가리키는 소스다.
#
# 이 기계는 메모리가 빠듯하다(갤럭시 폴드 / proot). 규칙은 PLAN.md §0-6:
# Go 는 -p=1, JVM 은 한 번에 하나(tools/flock_java.sh), 벤치마크는 직렬.

SHELL       := /bin/sh
PY          ?= python3
GO          ?= go
NODE        ?= node
# g++ 로 못 박는다. 이 환경에는 CXX 가 clang++ 로 잡혀 있는데,
# PLAN §2 가 확인한 것은 g++ 15.2 이고 골든도 그 위에서 만들었다.
CXX         := g++
CXXFLAGS    := -std=c++20 -O2 -Wall -Wextra -Werror
GOFLAGS     := -p=1
export GOTOOLCHAIN := local
export GOFLAGS

DECK        := ../압축_대백과사전.html
TOOLS       := ../tools
JAVA_LOCK   := tools/flock_java.sh

# 덱에 전문이 실리는 소스.
# 시험 파일은 발췌만 인용한다(PLAN.md §5 12단계).
FIND        := find
SRC_PY      := $(shell $(FIND) src/py cli corpus bench interop \
                 -name '*.py' ! -path '*/tests/*' 2>/dev/null | sort)
SRC_GO      := $(shell $(FIND) src/go cli \
                 -name '*.go' ! -name '*_test.go' 2>/dev/null | sort)
SRC_CPP     := $(shell $(FIND) src/cpp cli \
                 \( -name '*.cpp' -o -name '*.h' \) 2>/dev/null | sort)
SRC_JAVA    := $(shell $(FIND) src/java cli \
                 -name '*.java' ! -name '*Test.java' 2>/dev/null | sort)
SRC_TS      := $(shell $(FIND) src/ts cli -name node_modules -prune \
                 -o -name '*.ts' ! -name '*.test.ts' -print \
                 2>/dev/null | sort)
SRC_ALL     := $(SRC_PY) $(SRC_GO) $(SRC_CPP) $(SRC_JAVA) $(SRC_TS)

.DEFAULT_GOAL := help
.PHONY: help deps corpus build build-cpp build-go build-ts \
        build-java \
        test test-py test-go test-cpp test-java test-ts \
        golden golden-check corpus-check parity decoders \
        interop bench \
        record width \
        figs deck deck-verify deck-slices deck-xref deck-check \
        tables-check font font-check all clean

help:                   ## 이 목록
	@grep -hE '^[a-z][a-zA-Z0-9_-]*:.*?## ' $(MAKEFILE_LIST) \
	  | sed 's/:.*## /\t/' \
	  | awk -F'\t' '{printf "  %-12s %s\n", $$1, $$2}'

# ── 준비 ───────────────────────────────────────────────────────────
# tsc 는 이 기계에 없다. npm 캐시 속 tsc 는 가짜라 속는다
# (tetris_ts 기록).
# 여기서 받은 것이 없으면 TS 층은 막힌 것이다 —
# 없는 채로 지어내지 말 것.
# typescript@5 로 못 박는다. 6.x 는 플랫폼별 네이티브 실행 파일을 쓰는데
# 이 기계용(android-arm64) 꾸러미가 없어서 tsc 가 아예 안 뜬다.
# 5.x 는 순수 자바스크립트라 어디서든 돈다.
deps:                   ## TypeScript 컴파일러 내려받기 (src/ts 안에만)
	cd src/ts && npm install --no-save typescript@5 @types/node

corpus:                 ## 시험 자료 만들기 (씨앗 고정 — 늘 같은 파일)
	$(PY) corpus/gen_corpus.py

corpus-check:           ## 코퍼스와 그 원본이 그대로인지 대조만
	$(PY) corpus/gen_corpus.py --check

# ── 짓기 ───────────────────────────────────────────────────────────
# 다섯 언어의 결과물이 모두 build/ 로 간다. 파서티 검사가 여기를 본다.
build-cpp:              ## C++ 명령줄 도구 짓기
	@mkdir -p build
	$(CXX) $(CXXFLAGS) -o build/cppcli cli/cpp/main.cpp

build-go:               ## Go 명령줄 도구 짓기
	@mkdir -p build
	$(GO) build -o build/gocli ./cli/go

# tsc 가 없으면 여기서 멈춘다. 없는 채로 지어내지 말 것 (make deps).
TSC := src/ts/node_modules/.bin/tsc

build-ts:               ## TypeScript 옮기기 (tsc → build/ts)
	@test -x $(TSC) || (echo '  tsc 가 없다 — make deps 먼저'; exit 1)
	$(TSC) -p tsconfig.json

# JVM 은 한 번에 하나다. javac 도 JVM 이므로 여기도 flock 을 통한다.
build-java:             ## 자바 컴파일 (build/java)
	@mkdir -p build/java
	sh $(JAVA_LOCK) javac -Xlint:all -d build/java \
	  $$(find src/java cli/java -name '*.java')

## 있는 언어 전부 짓기
build: build-cpp build-go build-ts build-java

# ── 시험 ───────────────────────────────────────────────────────────
test-py:                ## 파이썬 시험
	@test -d src/py/compresslib/tests \
	  && $(PY) -m unittest discover -s src/py \
	  || echo '  파이썬 시험 아직 없다'

test-go:                ## Go 시험 (직렬 — 메모리가 빠듯하다)
	$(GO) test -count=1 ./src/go/

test-cpp: build-cpp     ## C++ 시험 (gtest 없이 assert 로)
	sh src/cpp/run_tests.sh

# JVM 은 한 번에 하나다. 둘이 겹치면 이 기계는 OOM 으로 세션째 죽는다.
test-java:              ## 자바 시험 (JVM 하나만 — flock 으로 막는다)
	sh $(JAVA_LOCK) sh src/java/run_tests.sh

test-ts: build-ts       ## TypeScript 시험 (node --test)
	$(NODE) --test 'build/ts/src/ts/*.test.js'

test: test-py test-go test-cpp test-java test-ts  ## 다섯 언어 시험

# ── 증거 ───────────────────────────────────────────────────────────
# 골든을 다시 만드는 것은 "지금까지의 출력이 틀렸다" 는 선언이다.
# 이유를 커밋 메시지에 적지 않고 돌리지 말 것.
golden:                 ## 골든 벡터 다시 만들기 (이유를 커밋에 적을 것)
	@echo '  ⚠ 골든을 새로 만든다 — 왜 바뀌어야 하는지 커밋에 적을 것'
	$(PY) bench/make_golden.py

# 골든이 바뀌지 않았는지만 본다. 5×5 파서티(6단계)가 붙기 전까지는
# 파이썬 참조가 스스로 달라지지 않았다는 확인이 이것뿐이다.
golden-check:           ## 골든이 그대로인지 대조만
	$(PY) bench/make_golden.py --check

parity:                 ## 다섯 언어가 같은 바이트를 내는가 (5×5 교차)
	$(PY) bench/run_parity.py

# 복호기만 있는 모듈은 골든 벡터가 없다. 진짜 도구가 만든 파일을 다섯
# 언어가 같게 푸는지가 그 자리를 대신한다 (PLAN.md §0.4).
decoders:               ## 진짜 도구의 파일을 다섯 언어가 같게 푸는가
	$(PY) bench/run_decoders.py

interop:                ## 진짜 gzip·bzip2·xz·lz4 와 주고받아 보기
	$(PY) interop/run_interop.py

bench:                  ## 속도·비율 재기 (직렬 — 병렬로 돌리지 말 것)
	@test -f bench/run_bench.py \
	  && $(PY) bench/run_bench.py \
	  || echo '  bench/run_bench.py 아직 없다 (PLAN.md §5 8단계)'

record: parity interop bench  ## 캡처 다시 남기기 (×3 md5 대조)
	@test -f tools/record.sh \
	  && sh tools/record.sh \
	  || echo '  tools/record.sh 아직 없다'

width:                  ## 덱에 실릴 줄이 폴더블 폭(72칸)을 넘는지
	@test -n "$(SRC_ALL)" \
	  && $(PY) tools/width.py $(SRC_ALL) Makefile \
	  || $(PY) tools/width.py Makefile

# ── 덱 ─────────────────────────────────────────────────────────────
figs:                   ## 도해 SVG 다시 만들기
	@test -f deck/gen_figs.py \
	  && $(PY) deck/gen_figs.py \
	  || echo '  deck/gen_figs.py 아직 없다 (PLAN.md §5 9단계)'

deck:                   ## 조각 + 소스 + 출력 → 덱 HTML 한 장
	$(PY) deck/build_deck.py

deck-verify:            ## 덱의 코드·출력이 원본과 같은지 역검증
	$(PY) deck/verify_deck.py

# lines=A-B 가 함수·주석 경계에 맞는가. 소스를 고쳐 줄이 밀리면 번호는
# 그대로인데 내용이 밀린다 — Keycloak 덱 2차 리뷰에서 84곳이 나왔다.
deck-slices:            ## 인용 범위가 소스 경계에 맞는지
	$(PY) deck/check_slices.py

# 이 덱의 상수는 거의 전부 식에서 나온다. 딱 하나 예외인 squash 의
# 서른세 수가 다섯 언어에 같게 적혀 있는지 본다 (SPEC §18.6).
tables-check:           ## 손으로 적은 표가 다섯 언어에 같은지
	$(PY) tools/gen_tables.py --check

deck-xref:              ## "N부 M장" 이 진짜 그 자리를 가리키는지
	$(PY) deck/check_xref.py

# SKEL=1 이면 '준비 중입니다' 플레이스홀더를 오류로 세지 않는다.
# 본문을 다 채우면(PLAN.md §5 10단계) 이 변수를 뗀다.
deck-check:             ## 완성된 덱 점검 (node DOM 스텁)
	$(NODE) deck/check_deck.js $(DECK) $(if $(SKEL),--skeleton,)

font:                   ## 고정폭 글꼴(DeckMono) 서브셋 내장
	$(PY) $(TOOLS)/embed_mono_font.py $(DECK)

font-check:             ## 내장 글꼴이 덱의 글자를 다 덮는지
	$(PY) $(TOOLS)/embed_mono_font.py --check $(DECK)

## 조립부터 검증까지 — 하나라도 걸리면 여기서 멈춘다
all: deck deck-verify deck-slices deck-xref deck-check tables-check \
     font font-check  ## 전부

clean:                  ## 덱 지우기 (코퍼스·캡처·골든은 남긴다)
	rm -f $(DECK)
