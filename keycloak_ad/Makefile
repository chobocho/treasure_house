# Keycloak × AD 덱 — 만드는 법 전부가 여기에 있다.
#
# 규칙 하나: 덱은 산출물이다. 덱 HTML 을 손으로 고치지 말 것.
# 고칠 곳은 deck/sections/*.html 조각이거나, 그 조각이 가리키는 소스다.
#
# 이 기계는 메모리가 빠듯하다(~2 GB). Go 는 -p 1 로 하나씩 돌리고,
# JVM(Keycloak)은 한 번에 하나만 띄운다. 자세한 것은 PLAN.md §3.

SHELL       := /bin/sh
GO          ?= go
# -p=1 이다. -p 1 로 쓰면 GOFLAGS 로 넘길 때 두 낱말로 갈려 거부당한다.
GOFLAGS     := -p=1
export GOTOOLCHAIN := local
export GOFLAGS

DECK        := ../Keycloak_AD_연동_쉽게_배우기.html
PY          := python3
TOOLS       := ../tools
# 덱에 전문이 실리는 파일들. 시험 파일은 발췌만 인용하므로 뺀다 —
# 발췌한 줄이 넓으면 조립기가 잡는다(deck/build_deck.py 의 폭 검사).
SRC         := $(shell find web ldap oidc -name '*.go' \
                 ! -name '*_test.go' 2>/dev/null)
SRCTEST     := $(shell find web ldap oidc -name '*_test.go' 2>/dev/null)
# 매니페스트도 전문이 실린다. 폭 규칙은 코드와 같다.
YAML        := $(shell find k8s -name '*.yaml' 2>/dev/null | sort)

.DEFAULT_GOAL := help
.PHONY: help test vet fmt width certs record validate-k8s k8s-tools \
        kc-fetch kc-run kc-stop kc-e2e \
        figs deck deck-check deck-verify font font-check all clean

help:                   ## 이 목록
	@grep -hE '^[a-z][a-zA-Z0-9_-]*:.*?## ' $(MAKEFILE_LIST) \
	  | sed 's/:.*## /\t/' \
	  | awk -F'\t' '{printf "  %-12s %s\n", $$1, $$2}'

# ── 소스 ───────────────────────────────────────────────────────────
test:                   ## Go 테스트 전부 (직렬 — 메모리가 빠듯하다)
	$(GO) test ./...

vet:                    ## go vet
	$(GO) vet ./...

fmt:                    ## gofmt 로 정렬
	gofmt -w $(SRC) $(SRCTEST)

width:                  ## 덱에 실릴 줄이 폴더블 폭(72칸)을 넘는지
	$(PY) tools/width.py $(SRC) certs/make_certs.sh data/campus.ldif \
	  $(YAML) k8s/validate.sh Makefile go.mod

certs:                  ## 시연용 CA·서버 인증서 만들고 검사
	sh certs/make_certs.sh
	sh certs/check_certs.sh

# ── 증거 ───────────────────────────────────────────────────────────
record:                 ## tier A 캡처를 out/ 에 다시 남긴다
	sh tools/record.sh

k8s-tools:              ## kubectl · kubeconform · JSON 스키마 내려받기
	sh tools/fetch_k8s_tools.sh

validate-k8s:           ## 매니페스트 tier B 검증
	sh k8s/validate.sh

# ── Keycloak (메모리 게이트가 걸려 있다) ───────────────────────────
kc-fetch:               ## Keycloak 배포판 내려받기
	sh keycloak/fetch.sh

kc-run:                 ## Keycloak 개발 모드로 띄우기
	sh keycloak/run_dev.sh

kc-stop:                ## Keycloak 끄기
	sh keycloak/stop.sh

kc-e2e:                 ## 로그인 전 과정을 curl 로 훑어 남기기
	sh keycloak/e2e_login.sh

# ── 덱 ─────────────────────────────────────────────────────────────
figs:                   ## 전체 그림 SVG 13장 다시 만들기
	$(PY) deck/gen_system.py

deck: figs              ## 조각 + 소스 + 출력 → 덱 HTML 한 장
	$(PY) deck/build_deck.py

# SKEL=1 이면 '준비 중' 표지를 오류로 안 센다. 부가 다 오면 뗀다.
deck-check:             ## 완성된 덱 점검 (node DOM 스텁)
	node deck/check_deck.js $(DECK) $(if $(SKEL),--skeleton,)

deck-verify:            ## 덱의 코드·출력이 원본과 같은지 역검증
	$(PY) deck/verify_deck.py

font:                   ## 고정폭 글꼴(DeckMono) 서브셋 내장
	$(PY) $(TOOLS)/embed_mono_font.py $(DECK)

font-check:             ## 내장 글꼴이 덱의 글자를 다 덮는지
	$(PY) $(TOOLS)/embed_mono_font.py --check $(DECK)

all: deck font deck-verify deck-check font-check  ## 조립부터 검증까지

clean:                  ## 덱 지우기 (인증서·캡처는 남긴다)
	rm -f $(DECK)
