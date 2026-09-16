# 무선통신 대백과사전 — 만드는 법 전부가 여기에 있다.
#
# 규칙 하나: 덱은 산출물이다. 덱 HTML 을 손으로 고치지 말 것.
# 고칠 곳은 deck/sections/*.html 조각이거나,
# 그 조각이 가리키는 소스·자료다.
#
# 이 기계는 메모리가 빠듯하다(갤럭시 폴드 / proot, 여유 200 MB 남짓).
# 규칙은 PLAN.md §0.7: 서브에이전트 둘까지, JVM 금지, numpy 없음,
# 몬테카를로는 한 번에 하나씩 직렬로 60초 안에 끝나게.

SHELL       := /bin/sh
PY          ?= python3
NODE        ?= node

DECK        := ../무선통신_대백과사전.html
TOOLS       := ../tools

FIND        := find
# 덱에 전문이 실리는 소스. 시험 파일은 발췌만 인용한다(PLAN.md §6 15부).
# 그래도 폭 검사는 같이 받는다 — 덱에 실릴 줄은 예외 없이 72칸이다.
SRC_PY      := $(shell $(FIND) py tools -name '*.py' 2>/dev/null | sort)
SRC_ALL     := $(SRC_PY) $(wildcard run_all.py)

.DEFAULT_GOAL := help
.PHONY: help test run record figs figs-png photos tables specs \
        bands bands-check claims-check width deck deck-verify \
        deck-slices deck-xref deck-check font font-check all clean

help:                   ## 이 목록
	@grep -hE '^[a-z][a-zA-Z0-9_-]*:.*?## ' $(MAKEFILE_LIST) \
	  | sed 's/:.*## /\t/' \
	  | awk -F'\t' '{printf "  %-12s %s\n", $$1, $$2}'

# ── 시험 ───────────────────────────────────────────────────────────
# PLAN.md §0.3: 숫자를 내는 식에는 반드시 그 식을 확인하는 시험이 있다.
# 시험이 없는 식은 덱에 못 들어간다. 허용 오차를 낮춰 통과시키지 말 것.
test:                   ## wirelesslib 시험 (RED → GREEN)
	@test -d py/wirelesslib/tests \
	  && $(PY) -m unittest discover -s py -v \
	  || echo '  시험 아직 없다 (PLAN.md §5 4단계)'

# ── 증거 ───────────────────────────────────────────────────────────
run:                    ## demo_*.py 를 전부 돌려 out/ 를 채운다
	@test -f run_all.py \
	  && $(PY) run_all.py \
	  || echo '  run_all.py 아직 없다 (PLAN.md §5 5단계)'

# 세 번 떠서 md5 가 같아야 한다. 캡처가 그 실행의 우연(난수 씨앗·
# 해시 순서·딕셔너리 차례)에 기대면 여기서 걸린다. 걸린 것을 그대로
# 실으면 독자가 같은 코드를 돌렸을 때 다른 숫자가 나온다 —
# 그러면 그것은 증거가 아니라 그림이다.
record:                 ## 캡처를 세 번 떠서 같은지 본다
	@test -f tools/record.sh \
	  && sh tools/record.sh --check \
	  || echo '  tools/record.sh 아직 없다'

figs:                   ## 도해 SVG 다시 만들기 (viewBox 폭 340)
	@test -f deck/gen_figs.py \
	  && $(PY) deck/gen_figs.py \
	  || echo '  deck/gen_figs.py 아직 없다 (PLAN.md §5 6단계)'

# 그린 것을 **눈으로 본다.** 압축 덱은 이 단계에서 28장 중 8장을 고쳤다.
figs-png: figs          ## SVG 를 PNG 로 렌더해 본다 (.svgrender/)
	@mkdir -p .svgrender
	@for f in deck/figs/*.svg; do \
	  test -e "$$f" || continue; \
	  n=".svgrender/$$(basename $$f .svg).png"; \
	  rsvg-convert -w 680 "$$f" -o "$$n"; \
	done; echo '  .svgrender/ 에 PNG 를 냈다 — 열어서 볼 것'

# 자유 라이선스가 아닌 사진은 여기서 멈춘다 (PLAN.md §0.9).
photos:                 ## Commons 에서 사진 받기 (manifest.tsv 기준)
	@test -f tools/fetch_photos.py \
	  && $(PY) tools/fetch_photos.py \
	  || echo '  tools/fetch_photos.py 아직 없다 (PLAN.md §5 7단계)'

tables:                 ## data/*.tsv → out/tbl_*.html
	$(PY) deck/gen_tables.py

# 대역 표는 규격 원문에서 뽑는다.
# 손으로 적으면 한 자리 틀려도 티가 안 난다.
bands:                  ## 규격 zip → data/bands.tsv
	$(PY) tools/extract_bands.py

bands-check:            ## data/bands.tsv 가 규격 원문과 같은지
	@test -d specs/zips \
	  && $(PY) tools/extract_bands.py --check \
	  || echo '  규격 zip 이 없다 — make specs 먼저 (검사 건너뜀)'

# 규격 zip 을 3gpp.org 에서 받는다. 이 서버는 중간 인증서를 안 보내므로
# 반드시 tools/fetch.sh 를 통한다 (PLAN.md §2).
specs:                  ## specs_fetch.txt 의 TS 를 specs/ 로 받는다
	@test -f tools/spec_text.py \
	  && $(PY) tools/spec_text.py --fetch-list data/specs_fetch.txt \
	  || echo '  tools/spec_text.py 아직 없다 (PLAN.md §5 3단계)'

# 이 덱에서 가장 틀리기 쉬운 것은 코드가 아니라 문장이다.
claims-check:           ## 인용한 조항과 연도에 근거가 있는가
	$(PY) deck/check_claims.py

width:                  ## 덱에 실릴 줄이 폴더블 폭(72칸)을 넘는지
	$(PY) tools/width.py $(SRC_ALL) Makefile

# ── 덱 ─────────────────────────────────────────────────────────────
deck:                   ## 조각 + 소스 + 출력 + 자료 → 덱 HTML 한 장
	$(PY) deck/build_deck.py

deck-verify:            ## 덱의 코드·출력·표가 원본과 같은지 역검증
	$(PY) deck/verify_deck.py

# lines=A-B 가 함수·주석 경계에 맞는가. 소스를 고쳐 줄이 밀리면 번호는
# 그대로인데 내용이 밀린다 — Keycloak 덱 2차 리뷰에서 84곳이 나왔다.
deck-slices:            ## 인용 범위가 소스 경계에 맞는지
	$(PY) deck/check_slices.py

deck-xref:              ## "N부 M장" 이 진짜 그 자리를 가리키는지
	$(PY) deck/check_xref.py

# SKEL=1 이면 '아직 없습니다' 플레이스홀더를 오류로 세지 않는다.
# 본문을 다 채우면(PLAN.md §5 8단계) 이 변수를 뗀다.
deck-check:             ## 완성된 덱 점검 (node DOM 스텁 + 데모 기댓값)
	$(NODE) deck/check_deck.js $(DECK) $(if $(SKEL),--skeleton,)

# 폰·태블릿에는 한글 고정폭 글꼴이 없다. 안 실으면 표와 코드가 어긋난다.
font:                   ## 고정폭 글꼴(DeckMono) 서브셋 내장
	$(PY) $(TOOLS)/embed_mono_font.py $(DECK)

font-check:             ## 내장 글꼴이 덱의 글자를 다 덮는지
	$(PY) $(TOOLS)/embed_mono_font.py --check $(DECK)

## 조립부터 검증까지 — 하나라도 걸리면 여기서 멈춘다
all: tables deck deck-verify deck-slices deck-xref deck-check \
     claims-check width font font-check  ## 전부

clean:                  ## 덱 지우기 (캡처·자료·규격 캐시는 남긴다)
	rm -f $(DECK)
