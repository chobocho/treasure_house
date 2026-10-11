# Rust 기초 문법집 — 만드는 법 전부가 여기에 있다.
#
# 규칙 하나: 덱은 산출물이다. 덱 HTML 을 손으로 고치지 말 것.
# 고칠 곳은 deck/sections/*.html 조각이거나, 그 조각이 가리키는
# 예제(ex/)다. 예제를 고쳤으면 tools/rsrun.py 로 다시 돌린다.
#
# 이 기계는 메모리가 빠듯하다(갤럭시 폴드 / proot, 스왑이 늘 찼다).
# PLAN.md §0.8: 집필 서브에이전트는 하나, rustc 는 한 번에 하나
# (rsrun 이 scratch/rustc.lock 을 잡는다), make -j 금지.

SHELL   := /bin/sh
PY      ?= python3
NODE    ?= node
TERMUX  ?= /data/data/com.termux/files/usr
RUSTFMT ?= $(TERMUX)/bin/rustfmt

DECK    := ../Rust_기초_문법집.html
TOOLS   := ../tools

.DEFAULT_GOAL := help
.PHONY: help test docs data data-check fmt fmt-check run run-check \
        record deck deck-verify deck-check font font-check all clean

help:                   ## 이 목록
	@grep -hE '^[a-z][a-zA-Z0-9_-]*:.*?## ' $(MAKEFILE_LIST) \
	  | sed 's/:.*## /\t/' \
	  | awk -F'\t' '{printf "  %-13s %s\n", $$1, $$2}'

# ── 시험 ───────────────────────────────────────────────────────────
# PLAN.md §0.7: 파이썬 도구는 전부 시험을 먼저 쓴다(RED → GREEN).
# 단언을 느슨하게 해서 통과시키지 말 것.
test:                   ## 도구 시험 (tools/tests, unittest)
	$(PY) -W error -m unittest discover -s tools/tests

# ── 자료 ───────────────────────────────────────────────────────────
# docs/ 는 커밋하지 않는 캐시다. 지워도 이것으로 다시 받는다.
docs:                   ## 공식 문서 → docs/ (릴리스 노트·역사 자료)
	@if test -f tools/fetch_docs.py; then $(PY) tools/fetch_docs.py; \
	else echo '  tools/fetch_docs.py 아직 없다 (PLAN.md §5 3단계)'; fi

# 릴리스 날짜는 손으로 쓰지 않는다 — RELEASES.md 에서 만든다.
data:                   ## docs/ → data/releases.tsv
	@if test -f tools/make_data.py; then $(PY) tools/make_data.py; \
	else echo '  tools/make_data.py 아직 없다 (PLAN.md §5 3단계)'; fi

# "1.N 부터" 와 역사 주장을 받아 둔 문서에 대 본다 — 기억으로 적은
# 버전이 여기서 걸린다.
data-check:             ## features·sources 의 근거가 docs/ 에 있는지
	@if test -f tools/make_data.py; then \
	  $(PY) tools/make_data.py --check; \
	else echo '  tools/make_data.py 아직 없다 (PLAN.md §5 3단계)'; fi

# ── 예제 ───────────────────────────────────────────────────────────
# 문법 오류를 보이려고 일부러 깨 둔 예제는 rustfmt 가 읽지 못한다.
# 그런 파일은 ex/nofmt.txt 에 경로를 적어 검사에서 뺀다.
RS := $(shell find ex -name '*.rs' 2>/dev/null | sort \
        | grep -v -x -F -f ex/nofmt.txt)

fmt:                    ## ex/ 의 예제를 rustfmt 로 다듬는다 (72칸)
	@test -z "$(RS)" || $(RUSTFMT) --config-path ex/rustfmt.toml $(RS)

fmt-check:              ## 예제가 rustfmt 를 거쳤는지
	@test -z "$(RS)" || $(RUSTFMT) --check --config-path ex/rustfmt.toml \
	  $(RS) >/dev/null || { echo '  ✗ rustfmt 를 안 거친 예제가 있다 — make fmt'; \
	  $(RUSTFMT) --check -l --config-path ex/rustfmt.toml $(RS); exit 1; }
	@echo "  예제 소스 $(words $(RS))개 — rustfmt 통과"

run:                    ## 캡처가 없거나 낡은 예제만 돌린다
	$(PY) tools/rsrun.py --all --stale -q

run-check:              ## 돌리지 않고 소스·캡처 해시만 장부와 대조
	$(PY) tools/rsrun.py --manifest-check

# 전부 다시 돌려 캡처와 글자까지 같은지 본다. 캡처가 그 실행의 우연
# (스레드 순서·주소·시각)에 기대면 여기서 걸린다. 오래 걸린다.
record:                 ## 예제를 전부 다시 돌려 캡처와 같은지 본다
	$(PY) tools/rsrun.py --all --check

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

## 조립부터 검증까지 — 하나라도 걸리면 여기서 멈춘다
all: test data-check fmt-check run-check deck deck-verify deck-check \
     font font-check  ## 전부

# out/ · data/ 는 절대 지우지 않는다(증거다). docs/ 는 make docs 로 되살린다.
clean:                  ## 덱·작업 찌꺼기 지우기 (캡처·자료는 남긴다)
	rm -rf $(DECK) scratch/run scratch/tmp
