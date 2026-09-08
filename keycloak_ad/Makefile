# Keycloak × AD 덱 — 만드는 법 전부가 여기에 있다.
#
# 규칙 하나: 덱은 산출물이다. 덱 HTML 을 손으로 고치지 말 것.
# 고칠 곳은 deck/sections/*.html 조각이거나, 그 조각이 가리키는 진짜 소스다.
#
# 이 기계는 메모리가 빠듯하다(~2 GB). 그래서 Go 는 -p 1 로 한 번에 하나씩 돌리고,
# JVM(Keycloak)은 한 번에 하나만 띄운다. 자세한 것은 PLAN.md §3.

SHELL       := /bin/sh
GO          ?= go
GOFLAGS     := -p 1
export GOTOOLCHAIN := local
export GOFLAGS

DECK        := ../Keycloak_AD_연동_쉽게_배우기.html
PY          := python3
TOOLS       := ../tools

.DEFAULT_GOAL := help
.PHONY: help test vet certs record validate-k8s kc-fetch kc-run kc-stop kc-e2e \
        figs deck deck-check deck-verify font font-check all clean

help:                     ## 이 목록
	@grep -hE '^[a-z][a-zA-Z0-9_-]*:.*?## ' $(MAKEFILE_LIST) \
	  | sed 's/:.*## /\t/' | awk -F'\t' '{printf "  %-16s %s\n", $$1, $$2}'

# ── 소스 ────────────────────────────────────────────────────────────────
test:                     ## 모든 Go 테스트 (직렬 — 메모리가 빠듯하다)
	$(GO) test ./...

vet:                      ## go vet
	$(GO) vet ./...

certs:                    ## 시연용 CA·서버 인증서 만들고 검사
	sh certs/make_certs.sh
	sh certs/check_certs.sh

# ── 증거 ────────────────────────────────────────────────────────────────
record:                   ## 모든 tier A 캡처를 out/ 에 다시 남긴다
	sh tools/record.sh

validate-k8s:             ## 매니페스트 tier B 검증 (kubectl · kubeconform)
	sh k8s/validate.sh

# ── Keycloak (메모리 게이트가 걸려 있다) ────────────────────────────────
kc-fetch:                 ## Keycloak 배포판 내려받기 (keycloak/VERSION 에 고정)
	sh keycloak/fetch.sh

kc-run:                   ## Keycloak 개발 모드로 띄우기 (여유 메모리 확인 후)
	sh keycloak/run_dev.sh

kc-stop:                  ## Keycloak 끄기
	sh keycloak/stop.sh

kc-e2e:                   ## 로그인 전 과정을 curl 로 훑어 out/ 에 남기기
	sh keycloak/e2e_login.sh

# ── 덱 ──────────────────────────────────────────────────────────────────
figs:                     ## 전체 그림 SVG 13장 다시 만들기
	$(PY) deck/gen_system.py

deck: figs                ## 조각 + 소스 + 출력 → 덱 HTML 한 장
	$(PY) deck/build_deck.py

# SKEL=1 을 붙이면 '준비 중' 표지를 오류로 세지 않는다 — 부가 다 들어오면 뗀다
deck-check:               ## 완성된 덱을 브라우저 없이 점검 (node DOM 스텁)
	node deck/check_deck.js $(DECK) $(if $(SKEL),--skeleton,)

deck-verify:              ## 덱에 실린 코드·출력이 원본과 같은지 역검증
	$(PY) deck/verify_deck.py

font:                     ## 고정폭 글꼴(DeckMono) 서브셋 내장
	$(PY) $(TOOLS)/embed_mono_font.py $(DECK)

font-check:               ## 내장 글꼴이 덱의 글자를 다 덮는지 검사
	$(PY) $(TOOLS)/embed_mono_font.py --check $(DECK)

all: deck font deck-verify deck-check font-check   ## 조립 → 글꼴 → 검증 전부

clean:                    ## 만들어진 것 지우기 (인증서·캡처는 남긴다)
	rm -f $(DECK)
