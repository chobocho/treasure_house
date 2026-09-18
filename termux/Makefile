# Termux 대백과사전 — 만드는 법 전부가 여기에 있다.
#
# 규칙 하나: 덱은 산출물이다. 덱 HTML 을 손으로 고치지 말 것.
# 고칠 곳은 deck/sections/*.html 조각이거나,
# 그 조각이 가리키는 소스·캡처·자료다.
#
# 이 덱은 자기가 다루는 기계 위에서 만들어진다 — Termux 안의
# proot 우분투다. 메모리가 빠듯하고(스왑이 늘 찼다) 이 세션은
# 팬텀 프로세스 킬러에 언제든 죽을 수 있다. 규칙은 PLAN.md §0.6:
# 서브에이전트 둘까지, JVM·Docker 금지, 무거운 빌드 금지, 직렬 실행.
# 호스트 Termux 는 사용자의 일상 환경이다. 그쪽으로 가는 문은
# tools/tmx.sh 하나뿐이고, clean 은 $PREFIX·$HOME 을 건드리지 않는다.

SHELL       := /bin/sh
PY          ?= python3
NODE        ?= node

DECK        := ../Termux_대백과사전.html
TOOLS       := ../tools

FIND        := find
# 덱에 전문이 실리는 우리 코드(PLAN.md §1). 커버리지 100 % 는 여기에만
# 건다. 시험 파일은 발췌만 인용하지만 폭 검사는 같이 받는다 —
# 덱에 실릴 줄은 예외 없이 72칸이다.
SRC_PY      := $(shell $(FIND) tools py exp -name '*.py' \
                 2>/dev/null | sort)
SRC_SH      := $(shell $(FIND) tools exp -name '*.sh' \
                 2>/dev/null | sort)
SRC_C       := $(shell $(FIND) exp -name '*.[ch]' \
                 2>/dev/null | sort)
SRC_TOP     := $(wildcard run_all.py)
SRC_ALL     := $(SRC_PY) $(SRC_SH) $(SRC_C) $(SRC_TOP)

.DEFAULT_GOAL := help
.PHONY: help test sources sources-check run run-check record scrub \
        figs figs-check figs-png tables claims-check width deck \
        deck-verify deck-slices deck-xref deck-check font font-check \
        all clean distclean

help:                   ## 이 목록
	@grep -hE '^[a-z][a-zA-Z0-9_-]*:.*?## ' $(MAKEFILE_LIST) \
	  | sed 's/:.*## /\t/' \
	  | awk -F'\t' '{printf "  %-13s %s\n", $$1, $$2}'

# ── 시험 ───────────────────────────────────────────────────────────
# PLAN.md §0.5: tools/·py/·exp/ 의 모든 것은 시험이 먼저다(RED → GREEN).
# 단언을 느슨하게 풀어 통과시키지 말 것. Termux 가 말한 성질이 이
# 기기에서 거짓이면, 캡처를 고치지 말고 장이 참인 것을 말하게 한다.
test:                   ## 시험 전부 (deck/ tools/ py/ exp/ 의 tests)
	@for d in deck/tests tools/tests py/tests exp/tests; do \
	  if test -d $$d; then \
	    echo "  == $$d"; \
	    $(PY) -m unittest discover -s $$d || exit 1; \
	  fi; \
	done
	@test -d tools/tests || echo '  tools/ 시험 아직 없다 (§5 2단계)'
	@test -d py/tests || echo '  py/ 시험 아직 없다 (§5 4단계)'
	@test -d exp/tests || echo '  exp/ 시험 아직 없다 (§5 5단계)'

# ── upstream 소스 ─────────────────────────────────────────────────
# sources/ 는 커밋하지 않는 캐시다. 지워도 이것으로 다시 받는다.
# 받는 커밋은 data/repos.tsv 의 핀이다. 인용되는 것은 작업 트리가
# 아니라 그 커밋이다.
sources:                ## upstream 저장소·문서를 핀 고정 커밋으로 받기
	@if test -f tools/fetch_src.sh; then \
	  sh tools/fetch_src.sh && $(PY) tools/doc_text.py --all; \
	else echo '  tools/fetch_src.sh 아직 없다 (PLAN.md §5 3단계)'; fi

sources-check:          ## 핀 커밋이 전부 sources/ 에 있는가
	$(PY) deck/srcpin.py --check

# ── 증거 ───────────────────────────────────────────────────────────
run:                    ## 캡처·실험을 전부 직렬로 돌려 out/ 를 채운다
	$(PY) run_all.py

run-check:              ## 캡처의 폭과 manifest 가 맞는지만 본다
	@if test -f run_all.py; then $(PY) run_all.py --check; \
	else echo '  run_all.py 아직 없다 (PLAN.md §5 6단계)'; fi

# 세 번 떠서 stable 캡처의 md5 가 같아야 한다. 배터리·시간처럼
# 다시 뜨면 달라지는 것은 manifest 에 snapshot 으로 적고 대조에서 뺀다.
# 15분쯤 걸리니 뒤에서 돌린다. 서브에이전트가 컴파일하는 동안엔 금지.
record:                 ## stable 캡처를 세 번 돌려 같은지 본다
	sh tools/record.sh --check

# 캡처는 사용자의 폰에서 뜬다. 전화번호·MAC·SSID·위치·주소가 한 번
# 새면 되돌릴 수 없다. 그래서 사람 눈이 아니라 빌드가 막는다(§0.8).
scrub:                  ## out/·data/ 에 개인정보가 없는가
	@if test -f tools/scrub.py; then \
	  $(PY) tools/scrub.py --check out data; \
	else echo '  tools/scrub.py 아직 없다 (PLAN.md §5 2단계)'; fi

figs:                   ## 도해 SVG 다시 만들기 (viewBox 폭 340)
	$(PY) deck/gen_figs.py

figs-check:             ## 그림이 자료와 어긋나지 않았는지
	@if test -f deck/gen_figs.py; then $(PY) deck/gen_figs.py --check; \
	else echo '  deck/gen_figs.py 아직 없다 (PLAN.md §5 7단계)'; fi

# 그린 것을 **눈으로 본다.** 압축 덱은 28장 중 8장, 무선 덱은
# 30장 중 4장을 이 단계에서 고쳤다. 이 덱은 바탕이 검정이라
# 투명 배경 그대로 렌더하면 글자가 안 보인다 — 검정을 깔고 그린다.
figs-png: figs          ## SVG 를 PNG 로 렌더해 본다 (.svgrender/)
	@mkdir -p .svgrender
	@for f in deck/figs/*.svg; do \
	  test -e "$$f" || continue; \
	  n=".svgrender/$$(basename $$f .svg).png"; \
	  rsvg-convert -b '#000000' -w 680 "$$f" -o "$$n"; \
	done; echo '  .svgrender/ 에 PNG 를 냈다 — 열어서 볼 것'

tables:                 ## data/*.tsv → out/tbl_*.html
	$(PY) deck/gen_tables.py

# 이 덱에서 가장 틀리기 쉬운 것은 코드가 아니라 문장이다.
claims-check:           ## 소스 배지의 줄과 본문의 연도에 근거가 있는가
	$(PY) deck/check_claims.py

width:                  ## 덱에 실릴 줄이 폴더블 폭(72칸)을 넘는지
	$(PY) tools/width.py $(SRC_ALL) Makefile

# ── 덱 ─────────────────────────────────────────────────────────────
deck:                   ## 조각 + 소스 + 캡처 + 자료 → 덱 HTML 한 장
	$(PY) deck/build_deck.py

deck-verify:            ## 덱의 코드·캡처·표가 원본과 같은지 역검증
	$(PY) deck/verify_deck.py

# lines=A-B 가 함수·주석 경계에 맞는가. 소스를 고쳐 줄이 밀리면
# 번호는 그대로인데 내용이 밀린다 — Keycloak 덱에서 84곳이 나왔다.
deck-slices:            ## 인용 범위가 소스 경계에 맞는지
	$(PY) deck/check_slices.py

deck-xref:              ## "N부 M장" 이 진짜 그 자리를 가리키는지
	$(PY) deck/check_xref.py

# SKEL=1 이면 '준비 중입니다' 플레이스홀더를 오류로 세지 않는다.
# 본문을 다 채우면(PLAN.md §5 8단계) 이 변수를 뗀다.
deck-check:             ## 완성된 덱 점검 (node DOM 스텁 + 데모 기댓값)
	$(NODE) deck/check_deck.js $(DECK) $(if $(SKEL),--skeleton,)

# 폰·태블릿에는 한글 고정폭 글꼴이 없다. 안 실으면 표와 코드가 어긋난다.
font:                   ## 고정폭 글꼴(DeckMono) 서브셋 내장
	$(PY) $(TOOLS)/embed_mono_font.py $(DECK)

font-check:             ## 내장 글꼴이 덱의 글자를 다 덮는지
	$(PY) $(TOOLS)/embed_mono_font.py --check $(DECK)

## 조립부터 검증까지 — 하나라도 걸리면 여기서 멈춘다
all: sources-check tables run-check scrub figs-check deck deck-verify \
     deck-slices deck-xref deck-check claims-check width font \
     font-check  ## 전부

# clean 은 이 디렉터리 안의 산출물만 지운다. 호스트 Termux 의
# $PREFIX·$HOME 은 어떤 target 도 건드리지 않는다(PLAN.md §0.7).
clean:                  ## 덱·빌드 찌꺼기 지우기 (캡처·자료는 남긴다)
	rm -rf $(DECK) .build .svgrender scratch

distclean: clean        ## + upstream 캐시(sources/)까지 지우기
	rm -rf sources
