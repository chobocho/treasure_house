# 밑바닥부터 만드는 트랜스포머 — 만드는 법 전부가 여기에 있다.
#
# 규칙 하나: 덱은 산출물이다. 덱 HTML 을 손으로 고치지 말 것.
# 고칠 곳은 deck/sections/*.html 조각이거나,
# 그 조각이 가리키는 소스·자료다.
#
# 이 기계는 메모리가 빠듯하다(갤럭시 폴드 / proot, 스왑이 늘 찼다).
# 규칙은 PLAN.md §0.7: 서브에이전트 둘까지, JVM 금지,
# numpy·torch 금지, C 학습은 한 번에 하나씩 직렬로 3분 안에.

SHELL       := /bin/sh
PY          ?= python3
NODE        ?= node
CC          ?= gcc

DECK        := ../밑바닥부터_만드는_트랜스포머.html
TOOLS       := ../tools

# 두 구현이 같은 답을 내려면 컴파일러가 식을 몰래 바꾸면 안 된다.
# -ffp-contract=off 는 a*b+c 를 FMA 한 방으로 합치지 말라는 뜻이다 —
# 합치면 반올림이 달라져 파이썬과 소수 끝자리가 어긋난다(§0.9).
CFLAGS      := -O2 -std=c99 -Wall -Wextra -Werror \
               -ffp-contract=off -fno-fast-math
LDLIBS      := -lm -lpthread

FIND        := find
# 덱에 전문이 실리는 소스. 시험 파일은 발췌만 인용한다(PLAN.md §6).
# 그래도 폭 검사는 같이 받는다 — 덱에 실릴 줄은 예외 없이 72칸이다.
SRC_PY      := $(shell $(FIND) py corpus tools -name '*.py' \
                 2>/dev/null | sort)
SRC_C       := $(shell $(FIND) c -name '*.[ch]' 2>/dev/null | sort)
SRC_TOP     := $(wildcard run_all.py)
SRC_ALL     := $(SRC_PY) $(SRC_C) $(SRC_TOP)
C_LIB       := $(filter-out c/main.c c/tests/%,$(SRC_C))

.DEFAULT_GOAL := help
.PHONY: help test test-py test-c cc corpus papers run run-check \
        record parity figs figs-check figs-png tables claims-check \
        width deck deck-verify deck-slices deck-xref deck-check \
        demo-model demo-infer font font-check all clean

help:                   ## 이 목록
	@grep -hE '^[a-z][a-zA-Z0-9_-]*:.*?## ' $(MAKEFILE_LIST) \
	  | sed 's/:.*## /\t/' \
	  | awk -F'\t' '{printf "  %-12s %s\n", $$1, $$2}'

# ── 시험 ───────────────────────────────────────────────────────────
# PLAN.md §0.3: 숫자나 기울기를 내는 식에는 반드시 그 식을 확인하는
# 시험이 있다. 허용 오차를 낮춰 통과시키지 말 것.
test: test-py test-c    ## 파이썬 unittest + C 시험 (RED → GREEN)

test-py:                ## 파이썬 시험만
	@if test -d py/transformerlib/tests; then \
	  $(PY) -m unittest discover -s py -t py; \
	else echo '  파이썬 시험 아직 없다 (PLAN.md §5 5단계)'; fi

# C 시험은 파일마다 따로 만들어 돌린다. 하나가 실패해도 나머지를 본다.
test-c: cc              ## C 시험만 (c/tests/test_*.c)
	@if test -d c/tests; then \
	  mkdir -p .build; bad=0; \
	  for t in c/tests/test_*.c; do \
	    b=".build/$$(basename $$t .c)"; \
	    $(CC) $(CFLAGS) -Ic $$t $(C_LIB) -o $$b $(LDLIBS) \
	      && ./$$b || bad=1; \
	  done; exit $$bad; \
	else echo '  C 시험 아직 없다 (PLAN.md §5 6단계)'; fi

cc:                     ## c/tfs 만들기
	@if test -f c/main.c; then \
	  mkdir -p .build; \
	  $(CC) $(CFLAGS) -Ic $(C_LIB) c/main.c -o c/tfs $(LDLIBS); \
	else echo '  c/main.c 아직 없다 (PLAN.md §3.2)'; fi

# ── 말뭉치·논문 ─────────────────────────────────────────────────────
corpus:                 ## 합성 과제 + 위키문헌 받기 (두 번 해도 같다)
	@if test -f corpus/gen_tasks.py; then \
	  $(PY) corpus/gen_tasks.py && $(PY) corpus/fetch_ko.py; \
	else echo '  corpus/*.py 아직 없다 (PLAN.md §5 4단계)'; fi

# papers/ 는 커밋하지 않는 캐시다. 지워도 이것으로 다시 받는다.
papers:                 ## data/papers.tsv 의 논문 본문을 papers/ 로
	@if test -f tools/paper_text.py; then \
	  $(PY) tools/paper_text.py --fetch-all data/papers.tsv; \
	else echo '  tools/paper_text.py 아직 없다 (PLAN.md §5 3단계)'; fi

# ── 증거 ───────────────────────────────────────────────────────────
run:                    ## 기록 실행을 전부 직렬로 돌려 out/ 를 채운다
	$(PY) run_all.py

run-check:              ## 캡처의 폭과 manifest 가 맞는지만 본다
	@if test -f run_all.py; then $(PY) run_all.py --check; \
	else echo '  run_all.py 아직 없다 (PLAN.md §5 7단계)'; fi

# 세 번 떠서 md5 가 같아야 한다. 캡처가 그 실행의 우연(난수 씨앗·
# 스레드 차례·딕셔너리 차례)에 기대면 여기서 걸린다. 걸린 것을
# 그대로 실으면 독자가 같은 코드를 돌렸을 때 다른 숫자가 나온다 —
# 그러면 그것은 증거가 아니라 그림이다. 75분쯤 걸리니 뒤에서 돌린다.
record:                 ## 캡처를 세 번 돌려 같은지 본다
	sh tools/record.sh --check

parity:                 ## 파이썬↔C 대조표만 다시 뜬다
	$(PY) run_all.py --only c_vs_py

figs:                   ## 도해 SVG 다시 만들기 (viewBox 폭 340)
	$(PY) deck/gen_figs.py

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
claims-check:           ## 인용한 논문 절과 연도에 근거가 있는가
	$(PY) deck/check_claims.py

width:                  ## 덱에 실릴 줄이 폴더블 폭(72칸)을 넘는지
	$(PY) tools/width.py $(SRC_ALL) Makefile

# ── 덱 ─────────────────────────────────────────────────────────────
deck:                   ## 조각 + 소스 + 출력 + 자료 → 덱 HTML 한 장
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

# 문서 안 덧셈 모델은 float16 으로 줄여 실었다. 줄인 만큼 로짓이
# 달라지니 greedy 답이 C 와 같은지를 시험 줄 전부로 잰다.
demo-model:             ## ckpt/c_add.ckpt → deck/demos_model.js
	$(PY) tools/export_js.py

demo-infer:             ## 문서 안 추론 1000줄이 C 의 답과 같은지
	$(PY) tools/export_js.py --check

# 폰·태블릿에는 한글 고정폭 글꼴이 없다. 안 실으면 표와 코드가 어긋난다.
font:                   ## 고정폭 글꼴(DeckMono) 서브셋 내장
	$(PY) $(TOOLS)/embed_mono_font.py $(DECK)

font-check:             ## 내장 글꼴이 덱의 글자를 다 덮는지
	$(PY) $(TOOLS)/embed_mono_font.py --check $(DECK)

## 조립부터 검증까지 — 하나라도 걸리면 여기서 멈춘다
all: tables run-check figs-check deck deck-verify deck-slices \
     deck-xref deck-check demo-infer claims-check width font \
     font-check  ## 전부

clean:                  ## 덱·빌드 찌꺼기 지우기 (캡처·자료는 남긴다)
	rm -rf $(DECK) .build .svgrender c/tfs
