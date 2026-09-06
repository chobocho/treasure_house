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

.PHONY: all deps build vet test record tmux-smoke deck deck-check fmt clean

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
record: $(OUT)/frames_1p.json

$(OUT)/frames_1p.json: $(shell find core ai ui game tools -name '*.go' 2>/dev/null)
	@mkdir -p $(OUT)
	$(GO) run ./tools/record -mode 1p -script "$(SCRIPT_1P)" -out $@

# 1인용 기록 스크립트. 조작 → 낙하 → 줄 지우기까지 한 판에 다 나오게 짰다.
SCRIPT_1P = 80x24 left left space wait wait right right space wait wait \
            c up space wait down down down wait wait space wait wait wait \
            left left left left space wait wait p wait wait p wait

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
	@tmux kill-session -t tui_1p 2>/dev/null || true
	@tmux new-session -d -s tui_1p -x 80 -y 24 "$(GO) run ./cmd/tetris --mode 1p --seed 1"
	@sleep 4
	@tmux send-keys -t tui_1p Left Left Space
	@sleep 1
	@tmux send-keys -t tui_1p Right Space
	@sleep 1
	@tmux capture-pane -e -p -t tui_1p > $(OUT)/tmux_1p.txt
	@tmux send-keys -t tui_1p Escape 2>/dev/null || true
	@sleep 1
	@tmux kill-session -t tui_1p 2>/dev/null || true
	@echo "  $(OUT)/tmux_1p.txt"
	@$(PY) deck/untab.py $(OUT)/tmux_*.txt

deck:
	$(PY) deck/build_deck.py

deck-check:
	@node deck/check_deck.js $(DECK)

clean:
	$(GO) clean -cache -testcache
	rm -f $(OUT)/frames_*.json
