# Rust 테트리스 — 빌드·시험·녹화·덱 조립.
#
# 이 기계(Termux + proot Ubuntu)에서는 툴체인이 둘이다:
#   CARGO   proot Ubuntu cargo 1.93 — core·render·tui·gui (minifb 가 리눅스 타깃 필요)
#   TCARGO  Termux cargo 1.99 — wasm32 타깃, fmt, clippy
# 보통의 PC 라면 둘 다 그냥 `cargo` 로 두면 된다.
CARGO  ?= /usr/bin/cargo
TPFX   ?= /data/data/com.termux/files/usr
TCARGO ?= $(TPFX)/bin/cargo
# 두 컴파일러가 target/ 을 같이 쓰면 "incompatible version of rustc" 로 깨진다 → 따로
# 또 Termux cargo 는 PATH 의 rustc 를 부르므로 Ubuntu rustc 가 끼어들지 않게 못 박는다.
TDIR = target-termux
TENV = CARGO_TARGET_DIR=$(TDIR) RUSTC=$(TPFX)/bin/rustc PATH="$(TPFX)/bin:$$PATH"
WASM_OUT = $(TDIR)/wasm32-unknown-unknown/wasm/tetris_wasm.wasm
# wasm32 표준 라이브러리가 툴체인에 없으면 풀어 둔 sysroot 를 준다(make WASM_SYSROOT=…).
# RUSTFLAGS 를 통째로 넘기면 Ubuntu cargo 까지 그 sysroot 를 써서 깨지므로 wasm 에만.
WASM_SYSROOT ?=
WENV = $(if $(WASM_SYSROOT),RUSTFLAGS=--sysroot=$(WASM_SYSROOT))
export CARGO_BUILD_JOBS = 1

.PHONY: all test lint fmt build wasm wasm-test record logs deck check clean

all: test lint build wasm wasm-test logs deck check

test:
	$(CARGO) test --workspace

lint:
	$(TCARGO) fmt --check
	$(TENV) $(TCARGO) clippy --workspace --all-targets --exclude tetris-gui -- -D warnings

fmt:
	$(TCARGO) fmt

build:
	$(CARGO) build --release -p tetris-tui -p tetris-gui

# 덱은 out/tetris_wasm.wasm 을 싣는다(커밋한다). wasm 타깃이 없는 기계에서도
# 덱만은 다시 조립할 수 있게.
wasm:
	$(TENV) $(WENV) $(TCARGO) build -p tetris-wasm \
	  --target wasm32-unknown-unknown --profile wasm
	cp $(WASM_OUT) out/tetris_wasm.wasm
	cp $(WASM_OUT) wasm/web/tetris_wasm.wasm

wasm-test:
	node wasm/test/node_test.mjs out/tetris_wasm.wasm

# 실제로 띄워서 찍는다. 중력이 실시간이라 녹화는 실행마다 조금씩 다르다.
record: build
	PATH="$$PATH:$(TPFX)/bin" sh tools/record_tui.sh
	sh tools/record_gui.sh

# 덱에 싣는 명령 출력. 덱의 "실행 결과" 상자는 전부 여기서 나온다.
logs:
	WASM_SYSROOT=$(WASM_SYSROOT) python3 tools/logs.py

# 조립한 뒤 DeckMono 글꼴을 싣는다 — 폰에는 한글 고정폭 글꼴이 없어 표가 어긋난다
deck:
	python3 deck/build.py
	python3 ../tools/embed_mono_font.py ../Rust_테트리스_만들기.html

check:
	python3 ../tools/embed_mono_font.py --check ../Rust_테트리스_만들기.html
	node deck/check_deck.js

clean:
	$(CARGO) clean
	rm -rf $(TDIR)
