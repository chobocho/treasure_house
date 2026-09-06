# Bubble Tea 테트리스 — 빌드·검증·기록·덱 조립
#
# 규칙 하나: 덱에 실리는 것은 전부 이 Makefile 이 만들어 낸 것이어야 한다.
# 화면도(record), 실행 증거도(tmux-smoke), 코드도(deck 이 소스에서 잘라 온다).

GO      ?= go
# 모듈 캐시가 이미 채워져 있고 이 기계의 네트워크는 자주 끊긴다.
# 캐시만 보게 해서 "빌드 중 갑자기 멈춤"을 원천 차단한다.
GOFLAGS ?= -mod=mod
export GOPROXY = off
export GOTOOLCHAIN = local

# 램이 빠듯한 기계(갤럭시 폴드)에서 돌린다. 병렬 빌드를 1로 낮추면
# 시간은 늘지만 OOM 킬러에게 세션째로 잡혀 죽는 일이 없어진다.
P       ?= 1
PY      ?= python3
OUT     ?= out
DECK    ?= ../Go_Bubble_Tea_테트리스_만들기.html

.PHONY: all deps build vet test record html logs tmux-smoke deck deck-check fmt clean

all: vet test

deps:
	$(GO) mod download

build:
	$(GO) build -p $(P) ./...

vet:
	$(GO) vet ./...

fmt:
	gofmt -l -w .

test:
	$(GO) test -p $(P) ./...

# 화면 기록 — 모델을 터미널 없이 돌려 프레임을 JSON 으로 남긴다.
# 결정론이 계약이다: 다시 돌린 뒤 git diff 가 비어 있어야 한다.
# 모드는 4~6단계에서 tools/record 의 등록부에 채워진다.
MODES = 1p 2p ai aivai
FRAMES = $(addprefix $(OUT)/frames_,$(addsuffix .json,$(MODES)))
SRCGO = $(shell find core ai ui game battle menu tools -name '*.go' 2>/dev/null)

record: $(FRAMES)

# 1인용 — 조작 → 낙하 → 줄 지우기 → 일시정지까지 한 판에 다 나오게 짰다.
SCRIPT_1p = 80x24 left left space wait wait right right space wait wait \
            c up space wait down down down wait wait space wait wait wait \
            left left left left space wait wait p wait wait p wait

# 2인용 — 두 자리가 서로 다른 키로 동시에 움직인다는 것을 보인다.
SCRIPT_2p = 80x24 a a f wait left left space wait w a a f wait \
            up right space wait s wait wait d d f wait \
            left space wait wait e wait c wait wait

# 사람 대 AI — 사람이 몇 수 두는 동안 AI 가 생각하고 스스로 둔다.
SCRIPT_ai = 80x24 wait10 left left space wait10 right space wait10 \
            wait10 wait10 wait10 c space wait10 wait10 wait10

# AI 대 AI — 최종 가중치 대 보통. 길게 돌려서 가비지가 오가는 것까지 본다.
SCRIPT_aivai = 80x24 wait20 wait20 wait20 wait20 wait20 wait20 wait20 wait20 \
               wait20 wait20 wait20 wait20 wait20 wait20 wait20 wait20 \
               wait20 wait20 wait20 wait20 wait20 wait20 wait20 wait20

$(OUT)/frames_%.json: $(SRCGO)
	@mkdir -p $(OUT)
	$(GO) run ./tools/record -mode $* -script "$(SCRIPT_$*)" -out $@

# 기록과 캡처를 덱이 읽는 HTML 로 바꾼다.
# 프레임은 재생기가 넘겨 보는 묶음으로, tmux 캡처는 한 장짜리 조각으로.
HTMLFRAMES = $(addprefix $(OUT)/frames_,$(addsuffix .html.json,$(MODES)))
TMUXNAMES = menu 1p 2p ai aivai 01_hello 02_counter 03_keys 04_tick 05_window 06_lipgloss 07_cmds
HTMLTMUX = $(addprefix $(OUT)/tmux_,$(addsuffix .html,$(TMUXNAMES)))

html: $(HTMLFRAMES) $(HTMLTMUX)

$(OUT)/frames_%.html.json: $(OUT)/frames_%.json tools/ansi2html/main.go
	$(GO) run ./tools/ansi2html -in $< -out $@

$(OUT)/tmux_%.html: $(OUT)/tmux_%.txt tools/ansi2html/main.go
	@$(GO) run ./tools/ansi2html -in $< -out $@

# 진짜 PTY 에서 진짜로 도는지 확인하는 유일한 방법.
# 에이전트 세션에는 터미널이 없으므로 tmux 를 하나 띄워서 그 화면을 긁어 온다.
# -e 는 ANSI 색을 남긴다 — 색이 빠지면 "정말 그 화면인가"를 증명할 수 없다.
tmux-smoke:
	@mkdir -p $(OUT)
	@for ex in 01_hello 02_counter 03_keys 04_tick 05_window 06_lipgloss 07_cmds; do \
		tmux kill-session -t tui_$$ex 2>/dev/null || true; \
		tmux new-session -d -s tui_$$ex -x 80 -y 24 "$(GO) run ./examples/$$ex"; \
		sleep 3; \
		tmux capture-pane -e -p -t tui_$$ex > $(OUT)/tmux_$$ex.txt; \
		tmux send-keys -t tui_$$ex q 2>/dev/null || true; \
		sleep 1; \
		tmux kill-session -t tui_$$ex 2>/dev/null || true; \
		echo "  $(OUT)/tmux_$$ex.txt"; \
	done
	@tmux kill-session -t tui_menu 2>/dev/null || true
	@tmux new-session -d -s tui_menu -x 80 -y 24 "$(GO) run ./cmd/tetris -seed 1"
	@sleep 5
	@tmux capture-pane -e -p -t tui_menu > $(OUT)/tmux_menu.txt
	@tmux send-keys -t tui_menu q 2>/dev/null || true
	@sleep 1
	@tmux kill-session -t tui_menu 2>/dev/null || true
	@echo "  $(OUT)/tmux_menu.txt"
	@tmux kill-session -t tui_1p 2>/dev/null || true
	@tmux new-session -d -s tui_1p -x 80 -y 24 "$(GO) run ./cmd/tetris -mode 1p -seed 1"
	@sleep 5
	@tmux send-keys -t tui_1p Left Left Space
	@sleep 1
	@tmux send-keys -t tui_1p Right Space
	@sleep 1
	@tmux capture-pane -e -p -t tui_1p > $(OUT)/tmux_1p.txt
	@tmux send-keys -t tui_1p Escape 2>/dev/null || true
	@sleep 1
	@tmux kill-session -t tui_1p 2>/dev/null || true
	@echo "  $(OUT)/tmux_1p.txt"
	@tmux kill-session -t tui_2p 2>/dev/null || true
	@tmux new-session -d -s tui_2p -x 80 -y 24 "$(GO) run ./cmd/tetris -mode 2p -seed 2"
	@sleep 5
	@tmux send-keys -t tui_2p a a f
	@sleep 1
	@tmux send-keys -t tui_2p Left Left Space
	@sleep 1
	@tmux capture-pane -e -p -t tui_2p > $(OUT)/tmux_2p.txt
	@tmux send-keys -t tui_2p Escape 2>/dev/null || true
	@sleep 1
	@tmux kill-session -t tui_2p 2>/dev/null || true
	@echo "  $(OUT)/tmux_2p.txt"
	@tmux kill-session -t tui_ai 2>/dev/null || true
	@tmux new-session -d -s tui_ai -x 80 -y 24 "$(GO) run ./cmd/tetris -mode ai -level hard -seed 3"
	@sleep 5
	@tmux send-keys -t tui_ai Left Space
	@sleep 4
	@tmux capture-pane -e -p -t tui_ai > $(OUT)/tmux_ai.txt
	@tmux send-keys -t tui_ai Escape 2>/dev/null || true
	@sleep 1
	@tmux kill-session -t tui_ai 2>/dev/null || true
	@echo "  $(OUT)/tmux_ai.txt"
	@tmux kill-session -t tui_aivai 2>/dev/null || true
	@tmux new-session -d -s tui_aivai -x 80 -y 24 "$(GO) run ./cmd/tetris -mode aivai -level normal -seed 4"
	@sleep 12
	@tmux capture-pane -e -p -t tui_aivai > $(OUT)/tmux_aivai.txt
	@tmux send-keys -t tui_aivai Escape 2>/dev/null || true
	@sleep 1
	@tmux kill-session -t tui_aivai 2>/dev/null || true
	@echo "  $(OUT)/tmux_aivai.txt"
	@$(PY) deck/untab.py $(OUT)/tmux_*.txt

# 덱에 "실제 출력"으로 실을 로그들. 지어낸 숫자를 슬라이드에 적지 않기 위한 장치다.
logs:
	@mkdir -p $(OUT)
	@$(GO) version > $(OUT)/go_version.txt
	@$(GO) vet ./... > $(OUT)/go_vet.txt 2>&1 || true
	@$(GO) test -p 1 -count=1 ./... > $(OUT)/go_test.txt 2>&1 || true
	@$(GO) test -p 1 -count=1 -v ./core/ -run 'Parity|Exercise' > $(OUT)/core_parity.txt 2>&1 || true
	@$(GO) test -p 1 -count=1 -v ./ai/ -run 'Parity|Interesting' > $(OUT)/ai_parity.txt 2>&1 || true
	@wc -l $$(find . -name '*.go' | sort) go.mod Makefile ai/weights.json | tail -3 > $(OUT)/loc.txt
	@echo "  $(OUT)/go_test.txt · go_vet.txt · core_parity.txt · ai_parity.txt"

deck:
	$(PY) deck/gen_appendix.py
	$(PY) deck/build_deck.py

deck-check:
	node deck/check_deck.js $(DECK)

clean:
	$(GO) clean -cache -testcache
	rm -f $(OUT)/frames_*.json $(OUT)/*.html $(OUT)/*.html.json
