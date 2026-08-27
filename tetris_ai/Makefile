# tetris_ai — 프리스탠딩 wasm 빌드 + 테스트 + GA 학습
#
#   make          tetris_ai.wasm 빌드
#   make test     Node 테스트 하니스 + 브라우저 글루 스모크
#   make native   ASan/UBSan 네이티브 빌드 후 실행
#   make train    GA 학습 (weights.json, ga_log.json 갱신)
#   make b64      덱에 인라인할 base64 생성
#   make deck     슬라이드 덱 재생성 (소스 커버리지 검사 포함)
#   make clean

CXX       ?= clang++
WFLAGS     = --target=wasm32 -nostdlib -O2 -fno-exceptions -fno-rtti -Wall -Wextra \
             -Wl,--no-entry -Wl,--export-dynamic -Wl,-z,stack-size=65536
# 네이티브 빌드에서는 wasm 전용 속성(export_name)이 무시된다 — 경고만 끈다.
NFLAGS     = -O1 -g -std=c++17 -Wall -Wextra -Wno-unknown-attributes \
             -fsanitize=address,undefined -fno-omit-frame-pointer

.PHONY: all test native train b64 deck matchup clean
all: tetris_ai.wasm

tetris_ai.wasm: ai.cpp tetris.cpp
	$(CXX) $(WFLAGS) -o $@ ai.cpp
	@printf '%s: %s bytes\n' $@ $$(stat -c%s $@)

# 부 1 의 코어만 따로 — 배틀 패치가 원본을 깨지 않았는지 보는 용도
tetris.wasm: tetris.cpp
	$(CXX) --target=wasm32 -nostdlib -O2 -fno-exceptions -fno-rtti -Wall -Wextra \
	       -Wl,--no-entry -Wl,--export-dynamic -o $@ $<

test: tetris_ai.wasm
	node test_ai.mjs
	node test_browser.mjs

native: native_main.cpp ai.cpp tetris.cpp
	g++ $(NFLAGS) -o tetris_ai_native native_main.cpp
	./tetris_ai_native 1 2 3

train: tetris_ai.wasm
	node ga.mjs --pop 32 --gen 50

b64: tetris_ai.wasm
	base64 -w0 tetris_ai.wasm > tetris_ai.wasm.b64
	@printf 'base64: %s bytes\n' $$(stat -c%s tetris_ai.wasm.b64)

# 난이도 프리셋끼리 24판씩 붙여 승률을 잰다 (실수 확률이 무작위라 실행마다 조금 다르다)
matchup: tetris_ai.wasm
	node matchup.mjs

# 덱을 다시 만든다. 슬라이드에 실린 코드가 실제 파일과 일치하는지,
# 그리고 모든 소스 줄이 빠짐없이 실렸는지 커버리지로 확인한다.
deck: b64
	python3 deck/build_deck.py

clean:
	rm -f tetris_ai.wasm tetris.wasm tetris_ai_native tetris_ai.wasm.b64
