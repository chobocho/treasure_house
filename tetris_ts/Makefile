# Makefile — TypeScript 테트리스 (코어 · GA AI · 8인 온라인)
#
# 이 저장소의 다른 프로젝트와 달리 emcc/clang 이 필요 없다. 필요한 건 node 와
# typescript 뿐이고, typescript 는 devDependency 라 `make deps` 한 번이면 끝난다.
#
# 순서가 있는 타깃이 둘 있다:
#   golden : build 가 먼저다 (도구가 dist/src/trace.js 를 import 하므로)
#   test   : golden 이 먼저다 (없으면 파리티 테스트가 실패한다)

NODE    ?= node
NPX     ?= npx
PORT    ?= 8787
POP     ?= 32
GEN     ?= 50
DECK    ?= ../TypeScript_테트리스_AI_8인_대전.html

.PHONY: all deps build golden test train run match web deck clean distclean

all: build

## deps — typescript 설치 (npm 캐시의 가짜 tsc 를 피하려고 --no-save 로 명시 설치)
deps:
	$(NPX) --no-install tsc --version >/dev/null 2>&1 || npm install --no-save typescript @types/node

## build — strict 타입체크 + dist/ 로 컴파일
build: deps
	$(NPX) tsc

## golden — C++ wasm 에서 정답지를 뽑는다 (tetris_ai/tetris_ai.wasm 필요)
golden: build
	$(NODE) tools/trace_wasm.mjs
	$(NODE) tools/trace_ai_wasm.mjs
	$(NODE) tools/trace_ga_js.mjs

## test — 전체 테스트. 골든 파일이 없으면 먼저 만든다.
test: build
	@test -f test/golden/core_traces.json -a -f test/golden/ai_traces.json \
	     -a -f test/golden/ga_traces.json || $(MAKE) golden
	$(NODE) --test 'dist/test/*.test.js'

## train — GA 실학습. weights.json 과 ga_log.json 을 갱신한다.
train: build
	$(NODE) dist/train.js --pop $(POP) --gen $(GEN)

## run — 8인 서버 (web/ 정적 파일 + /ws 엔드포인트)
run: web
	$(NODE) dist/src/net/server.js --port $(PORT)

## match — 서버 + 봇 8석 실측 대전
match: web
	$(NODE) dist/bot_client.js --match --port $(PORT)

## web — 브라우저 번들 조립 (dist/ 의 컴파일 결과를 web/ 로 복사)
web: build
	$(NODE) tools/bundle_web.mjs

## deck — 슬라이드 덱 생성
deck: build
	python3 deck/build_deck.py

clean:
	rm -rf dist

distclean: clean
	rm -rf node_modules scratch
