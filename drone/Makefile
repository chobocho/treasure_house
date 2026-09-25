# 드론의 모든 것 — 만드는 법 전부가 여기에 있다.
#
# 규칙 하나: 덱은 산출물이다. 덱 HTML 을 손으로 고치지 말 것.
# 고칠 곳은 deck/sections/*.html 조각이거나,
# 그 조각이 가리키는 소스·캡처·자료다(PLAN.md §0.1).
#
# 이 기계는 메모리가 빠듯하다(갤럭시 폴드 / proot, 스왑이 늘 찼다).
# 규칙은 PLAN.md §0.8: 서브에이전트 둘까지, 시뮬레이터 프로세스는
# 한 번에 하나, -j 금지, 기록 실행은 직렬로, 실험 하나 60초·200 MB.
#
# goevo/Makefile(그 앞은 git/Makefile)에서 물려받아 줄였다 —
# go·java·ts·cpp 는 이 덱에 없고, 파이썬·자바스크립트 시뮬레이터와
# 정리 검사가 있다.

SHELL       := /bin/sh
PY          ?= python3
NODE        ?= node

DECK        := ../드론의_모든_것.html
TOOLS       := ../tools

FIND        := find
# 덱에 실릴 소스. 폭 검사를 받는다 — 덱에 실릴 줄은 예외 없이
# 72칸이다(PLAN.md §0.9). 시험 파일도 RED·GREEN 장에 발췌되므로
# 같이 본다.
SRC_PY      := $(shell $(FIND) py ex exps -name '*.py' \
                 2>/dev/null | sort) \
               $(wildcard run_all.py)
SRC_JS      := $(shell $(FIND) js -name '*.js' 2>/dev/null | sort)
SRC_ALL     := $(SRC_PY) $(SRC_JS)

# SKEL=1 이면 뼈대 단계 — '준비 중입니다' 자리와 아직 안 쓰인 정리를
# 오류로 세지 않는다. 본문을 다 채우면(PLAN.md §5 12단계) 이 변수를
# 뗀다.
SKELFLAG    := $(if $(SKEL),--skeleton,)

.DEFAULT_GOAL := help
.PHONY: help test docs data data-check test-py test-js parity run \
        run-check record figs figs-check figs-png tables width deck \
        deck-verify deck-slices deck-xref deck-check claims-check \
        thm-check font font-check all clean

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

# 시뮬레이터의 공식 증인(PLAN.md §3.5)과 골든 벡터 작성기. 90초 안.
test-py:                ## 파이썬 시뮬레이터 시험 (py/tests)
	@if ls py/tests/test_*.py >/dev/null 2>&1; then \
	  cd py && $(PY) -m unittest discover -s tests -t .; \
	else echo '  py/tests 아직 없다 (PLAN.md §5 5단계)'; fi

test-js:                ## 자바스크립트 이식 시험 (node --test)
	@if ls js/test/*.test.js >/dev/null 2>&1; then \
	  $(NODE) --test js/test/; \
	else echo '  js/test 아직 없다 (PLAN.md §5 6단계)'; fi

# 골든 벡터(파이썬이 낸 값)와 JS 가 1e-9 안에서 같은가(PLAN.md §3.3).
parity:                 ## 파이썬 ↔ JS 골든 벡터 대조
	@if test -f js/test/parity.test.js; then \
	  $(NODE) --test js/test/parity.test.js; \
	else echo '  parity.test.js 아직 없다 (PLAN.md §5 6단계)'; fi

# ── 받기 ───────────────────────────────────────────────────────────
# docs/ 는 커밋하지 않는 캐시다. 지워도 이것으로 다시 받는다.
# 3·11·12·17부를 만지는 세션은 시작할 때 반드시 다시 받는다
# (PLAN.md §0.5) — docs/FETCHED.txt 에 날짜와 sha256 이 남는다.
docs:                   ## 1차 문서 → docs/ (펌웨어·문서·논문·법령)
	@if test -f tools/fetch_docs.py; then $(PY) tools/fetch_docs.py; \
	else echo '  tools/fetch_docs.py 아직 없다 (PLAN.md §5 2단계)'; fi

data:                   ## docs/ → data/excerpts/ (펌웨어 발췌)
	@if test -f tools/excerpt.py; then $(PY) tools/excerpt.py --all; \
	else echo '  tools/excerpt.py 아직 없다 (PLAN.md §5 2단계)'; fi

# 손으로 쓴 표의 모양과 출처 규칙 — 위키백과 주소만 적은 출처,
# 2025년 이후인데 '받은 날' 이 없는 행이 여기서 걸린다(PLAN.md §3.2).
data-check:             ## data/*.tsv 의 칸·출처 규칙
	@if test -f tools/data_check.py; then $(PY) tools/data_check.py; \
	else echo '  tools/data_check.py 아직 없다 (PLAN.md §5 4단계)'; fi

# 정리 표와 덱의 정리 상자·증명 장이 맞는가(PLAN.md §0.6).
thm-check:              ## 정리 표·THM 상자·증명 장 배지·증인 시험
	$(PY) deck/check_thm.py $(SKELFLAG)

# ── 증거 ───────────────────────────────────────────────────────────
run:                    ## 실험을 전부 직렬로 돌려 out/ 를 채운다
	@if test -f run_all.py; then $(PY) run_all.py; \
	else echo '  run_all.py 아직 없다 (PLAN.md §5 7단계)'; fi

run-check:              ## 캡처의 폭과 manifest 가 맞는지만 본다
	@if test -f run_all.py; then $(PY) run_all.py --check; \
	else echo '  run_all.py 아직 없다 (PLAN.md §5 7단계)'; fi

# 세 번 떠서 sha256 이 같아야 한다. 캡처가 그 실행의 우연(시각·난수·
# 딕셔너리 차례)에 기대면 여기서 걸린다. 길게 걸리니 뒤에서 돌리고
# Monitor 로 기다린다(Bash 안의 & 금지 — git/PLAN.md 진행 기록).
record:                 ## 캡처를 세 번 돌려 같은지 본다
	@if test -f run_all.py; then sh tools/record.sh --check; \
	else echo '  run_all.py 아직 없다 (PLAN.md §5 7단계)'; fi

figs:                   ## 도해 SVG 다시 만들기 (viewBox 폭 340)
	@if test -f deck/gen_figs.py; then $(PY) deck/gen_figs.py; \
	else echo '  deck/gen_figs.py 아직 없다 (PLAN.md §5 10단계)'; fi

figs-check:             ## 그림이 자료와 어긋나지 않았는지
	@if test -f deck/gen_figs.py; then $(PY) deck/gen_figs.py --check; \
	else echo '  deck/gen_figs.py 아직 없다 (PLAN.md §5 10단계)'; fi

# 그린 것을 **눈으로 본다.** 압축 덱은 28장 중 8장, 무선 덱은
# 30장 중 4장을 이 단계에서 고쳤다.
figs-png: figs          ## SVG 를 PNG 로 렌더해 본다
	@mkdir -p scratch/svgrender
	@for f in deck/figs/*.svg; do \
	  test -e "$$f" || continue; \
	  n="scratch/svgrender/$$(basename $$f .svg).png"; \
	  rsvg-convert -w 680 "$$f" -o "$$n"; \
	done; echo '  scratch/svgrender/ 에 PNG 를 냈다 — 열어서 볼 것'

tables:                 ## data/*.tsv · out/ → out/tbl_*.html
	@if test -f deck/gen_tables.py; then $(PY) deck/gen_tables.py; \
	else echo '  deck/gen_tables.py 아직 없다 (PLAN.md §5 7단계)'; fi

# 이 덱에서 가장 틀리기 쉬운 것은 코드가 아니라 날짜·대수·조문이다.
claims-check:           ## 인용한 문서 절·연도·대수·조문에 근거가 있는가
	$(PY) deck/check_claims.py

width:                  ## 덱에 실릴 줄이 폴더블 폭(72칸)을 넘는지
	@if test -n "$(strip $(SRC_ALL))"; then \
	  $(PY) tools/width.py $(SRC_ALL) Makefile; \
	else $(PY) tools/width.py Makefile; fi

# ── 덱 ─────────────────────────────────────────────────────────────
deck:                   ## 조각 + 소스 + 캡처 + 자료 → 덱 HTML 한 장
	$(PY) deck/build_deck.py

deck-verify:            ## 덱의 코드·출력·표·SHOW 역검증
	$(PY) deck/verify_deck.py

# lines=A-B 가 함수·주석 경계에 맞는가. 소스를 고쳐 줄이 밀리면
# 번호는 그대로인데 내용이 밀린다 — Keycloak 덱에서 84곳이 나왔다.
deck-slices:            ## 인용 범위가 소스 경계에 맞는지
	$(PY) deck/check_slices.py

deck-xref:              ## "N부 M장"·"정리 T14" 가 진짜인지
	$(PY) deck/check_xref.py

deck-check:             ## 완성된 덱 점검 (node DOM 스텁 + 엔진 계약)
	$(NODE) deck/check_deck.js $(DECK) $(SKELFLAG)

# 폰·태블릿에는 한글 고정폭 글꼴이 없다. 안 실으면 표와 코드가 어긋난다.
font:                   ## 고정폭 글꼴(DeckMono) 서브셋 내장
	$(PY) $(TOOLS)/embed_mono_font.py $(DECK)

font-check:             ## 내장 글꼴이 덱의 글자를 다 덮는지
	$(PY) $(TOOLS)/embed_mono_font.py --check $(DECK)

## 조립부터 검증까지 — 하나라도 걸리면 여기서 멈춘다
all: test test-py test-js parity data-check thm-check tables run-check \
     figs-check deck deck-verify deck-slices deck-xref deck-check \
     claims-check width font font-check  ## 전부

# out/ · data/ · golden/ 은 절대 지우지 않는다. docs/ 는 캐시라
# make docs 로 되살린다.
clean:                  ## 덱·빌드 찌꺼기 지우기 (캡처·자료는 남긴다)
	rm -rf $(DECK) scratch/svgrender scratch/work
