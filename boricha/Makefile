# 보리차 — 빌드·검증·기록·덱 조립
#
# 규칙 하나: 덱에 실리는 것은 전부 이 Makefile 이 만들어 낸 것이어야 한다.
# 코드는 덱 빌더가 소스에서 잘라 오고, 화면은 record 와 tmux-smoke 가 찍어 온다.
# 손으로 타이핑해 슬라이드에 넣은 것은 이 덱에 하나도 없다.

GO      ?= go
# 이 모듈에는 의존성이 없다. 그래도 GOPROXY 를 꺼 두는 이유는,
# 네트워크가 끊긴 상태에서 go 가 프록시를 기다리며 멈추는 일을 원천 차단하기 위해서다.
export GOPROXY = off
export GOTOOLCHAIN = local

# 램이 빠듯한 기계(갤럭시 폴드)에서 돌린다. 병렬도를 1로 낮추면 시간은 늘지만
# OOM 킬러에게 세션째로 잡혀 죽는 일이 없어진다.
P       ?= 1
PY      ?= python3
OUT     ?= out
DECK    ?= ../나만의_Bubble_Tea_만들기.html

.PHONY: all build vet test fmt cross gen-width record html logs tmux-smoke deck deck-check clean

all: vet test

build:
	$(GO) build -p $(P) ./...

vet:
	$(GO) vet ./...

fmt:
	gofmt -l -w .

test:
	$(GO) test -p $(P) ./...

# 리눅스 말고 다른 곳에서도 컴파일은 되는지 본다.
# macOS 는 여기서 **돌려 볼 수 없다** — 컴파일이 되는 것까지가 우리가 말할 수 있는 전부다.
# 윈도우는 ErrUnsupported 를 돌려주는 스텁이라 컴파일만 확인하면 된다.
cross:
	GOOS=darwin  GOARCH=arm64 $(GO) build -p $(P) ./...
	GOOS=windows GOARCH=amd64 $(GO) build -p $(P) ./...

# 글자 폭 표를 유니코드 자료에서 굽는다.
# 결정론이 계약이다 — 다시 돌린 뒤 width/table.go 가 그대로여야 한다.
gen-width:
	$(GO) run ./tools/gen_width

# ── 화면 기록 ────────────────────────────────────────────────────────
# 모델을 진짜 터미널 없이 돌려 프레임을 JSON 으로 남긴다(8단계에서 채운다).
# 결정론이 계약이다: 다시 돌린 뒤 git diff 가 비어 있어야 한다.
MODES =
FRAMES = $(addprefix $(OUT)/frames_,$(addsuffix .json,$(MODES)))

record: $(FRAMES)

html:

# ── 진짜 PTY 증거 ────────────────────────────────────────────────────
# 에이전트 세션에는 터미널이 없다. tmux 로 창을 하나 띄워 그 화면을 긁어 오는 것이
# "정말 도는가" 를 증명하는 유일한 방법이다. -e 는 ANSI 색을 남긴다 —
# 색이 빠지면 그 화면이 정말 그 프로그램의 것인지 증명할 수 없다.
#
# go run 대신 미리 빌드해 둔 실행 파일을 띄운다. go run 은 처음 한 번 컴파일하느라
# 8초쯤 걸려서, 그 사이에 보낸 키가 통째로 사라진다.
EXAMPLES = 00_raw 01_hello 02_counter 03_keys 04_tick 05_window 06_style 07_cmds 08_mouse 09_paste

# 예제마다 눌러 볼 키. tmux 의 이름을 쓴다(Up, C-a, M-x, BTab …).
KEYS_00_raw     = Left
KEYS_01_hello   =
KEYS_02_counter = Up Up Up k + j
KEYS_03_keys    = Left C-a M-x BTab F5 Home
KEYS_04_tick    =
KEYS_05_window  =
KEYS_06_style   = Down Down Down Down
KEYS_07_cmds    = b
KEYS_08_mouse   =
KEYS_09_paste   =

# 키 이름으로는 못 보내는 것들은 바이트로 직접 밀어 넣는다(-H 는 16진수).
#   08_mouse : ESC[<0;20;14M  왼쪽 버튼 누름 → 화면 (19,13)에 표시가 찍힌다
#   09_paste : ESC[200~ "잘 되었다\n" ESC[201~  괄호 붙은 붙여넣기 한 덩어리
HEX_08_mouse = 1b 5b 3c 30 3b 32 30 3b 31 34 4d 1b 5b 3c 30 3b 32 30 3b 31 34 6d \
               1b 5b 3c 36 34 3b 33 30 3b 31 36 4d
HEX_09_paste = 1b 5b 32 30 30 7e ec 9e 98 20 eb 90 98 ec 97 88 eb 8b a4 0a 1b 5b 32 30 31 7e

TMUXTXT = $(addprefix $(OUT)/tmux_,$(addsuffix .txt,$(EXAMPLES)))

tmux-smoke: $(TMUXTXT)

$(OUT)/bin/%: examples/%/main.go $(shell find tea term input render width style -name '*.go' 2>/dev/null)
	@mkdir -p $(OUT)/bin
	@$(GO) build -p $(P) -o $@ ./examples/$*

$(OUT)/tmux_%.txt: $(OUT)/bin/%
	@tmux kill-session -t bo_$* 2>/dev/null || true
	@tmux new-session -d -s bo_$* -x 80 -y 24 "$(OUT)/bin/$*"
	@sleep 2
	@for k in $(KEYS_$*); do tmux send-keys -t bo_$* $$k; sleep 0.3; done
	@if [ -n "$(HEX_$*)" ]; then tmux send-keys -H -t bo_$* $(HEX_$*); sleep 0.5; fi
	@sleep 1
	@tmux capture-pane -e -p -t bo_$* > $@
	@tmux kill-session -t bo_$* 2>/dev/null || true
	@echo "  $@"

# ── 덱에 "실제 출력" 으로 실을 로그 ─────────────────────────────────
# 지어낸 숫자를 슬라이드에 적지 않기 위한 장치다.
logs:
	@mkdir -p $(OUT)
	@$(GO) version > $(OUT)/go_version.txt
	@$(GO) vet ./... > $(OUT)/go_vet.txt 2>&1 || true
	@$(GO) test -p $(P) -count=1 ./... > $(OUT)/go_test.txt 2>&1 || true
	@wc -l $$(find . -name '*.go' | sort) go.mod Makefile | tail -1 > $(OUT)/loc.txt
	@echo "  $(OUT)/go_test.txt · go_vet.txt · loc.txt"

deck:
	$(PY) deck/gen_appendix.py
	$(PY) deck/build_deck.py

deck-check:
	node deck/check_deck.js $(DECK)

clean:
	$(GO) clean -cache -testcache
	rm -rf $(OUT)/frames_*.json $(OUT)/*.html $(OUT)/*.html.json $(OUT)/bin
