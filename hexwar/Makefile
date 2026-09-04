# HexWar — 세 언어 구현을 한꺼번에 검사하고, 덱에 실을 출력을 out/ 에 남긴다.
#
#   make all      전부 (권장)
#   make py       파이썬 검사만
#   make lua      루아 검사만
#   make ts       타입스크립트 빌드 + 검사만
#   make parity   렌더 결과가 세 언어에서 바이트 단위로 같은지
#   make bench    성능 비교
#   make golden   골든 파일 재생성 (트레이스가 바뀌면 전부 다시 검사해야 한다)

SHELL   := /bin/bash
ROOT    := $(CURDIR)
GOLDEN  := $(ROOT)/golden
OUT     := $(ROOT)/out
PY      := python3
LUA     := lua
NODE    := node
TSC     := $(ROOT)/ts/node_modules/.bin/tsc
export HEXWAR_GOLDEN := $(GOLDEN)

.PHONY: all py lua ts parity bench golden clean frames verify-log

all: py lua ts parity
	@echo '── 전부 통과 ──'

py:
	@mkdir -p $(OUT)
	cd $(ROOT) && $(PY) py/tests/test_prim.py   | tee $(OUT)/py_prim.txt
	cd $(ROOT) && $(PY) py/tests/test_engine.py | tee $(OUT)/py_engine.txt
	cd $(ROOT) && $(PY) py/tests/test_trace.py  | tee $(OUT)/py_trace.txt

lua:
	@mkdir -p $(OUT)
	cd $(ROOT)/lua && $(LUA) tests/test_prim.lua  | tee $(OUT)/lua_prim.txt
	cd $(ROOT)/lua && $(LUA) tests/test_trace.lua | tee $(OUT)/lua_trace.txt

ts:
	@mkdir -p $(OUT)
	cd $(ROOT)/ts && $(TSC) -p tsconfig.json
	cd $(ROOT)/ts && $(NODE) dist/tests/test_prim.js  | tee $(OUT)/ts_prim.txt
	cd $(ROOT)/ts && $(NODE) dist/tests/test_trace.js | tee $(OUT)/ts_trace.txt

parity:
	@mkdir -p $(OUT)
	cd $(ROOT)/py  && $(PY) -m hexwar.main render $(OUT)/frame_final.ppm 2>/dev/null
	cd $(ROOT)/lua && $(LUA) hexwar/main.lua render $(OUT)/frame_final_lua.ppm 2>/dev/null
	cd $(ROOT)/ts  && $(NODE) dist/src/main.js render $(OUT)/frame_final_ts.ppm 2>/dev/null
	@{ \
	  echo '렌더 결과 바이트 비교 (320x200 · 8비트 인덱스 · PPM 192,015바이트)'; \
	  cmp $(OUT)/frame_final.ppm $(OUT)/frame_final_lua.ppm && echo '  python == lua  OK'; \
	  cmp $(OUT)/frame_final.ppm $(OUT)/frame_final_ts.ppm  && echo '  python == ts   OK'; \
	  echo '트레이스 119스텝 비교'; \
	  cd $(ROOT)/py  && $(PY) -m hexwar.main trace > $(OUT)/t_py.jsonl; \
	  cd $(ROOT)/lua && $(LUA) hexwar/main.lua trace > $(OUT)/t_lua.jsonl; \
	  cd $(ROOT)/ts  && $(NODE) dist/src/main.js trace > $(OUT)/t_ts.jsonl; \
	  cmp $(OUT)/t_py.jsonl $(OUT)/t_lua.jsonl && echo '  python == lua  OK'; \
	  cmp $(OUT)/t_py.jsonl $(OUT)/t_ts.jsonl  && echo '  python == ts   OK'; \
	  cmp $(OUT)/t_py.jsonl $(GOLDEN)/trace.jsonl && echo '  python == golden OK'; \
	} | tee $(OUT)/parity.txt

# 덱에 싣는 '전체 검증' 출력 — make all 의 결과 줄만 남긴다
verify-log:
	@$(MAKE) --no-print-directory all 2>&1 \
	  | grep -v '^cd \|^{\|^ *\\$$\|^@\|^make' | sed '/^$$/d' > $(OUT)/verify_all.txt
	@cat $(OUT)/verify_all.txt

bench:
	@mkdir -p $(OUT)
	@{ \
	  echo '=== python3 ==='; cd $(ROOT)/py  && $(PY) -m hexwar.main bench; \
	  echo '=== lua ==='    ; cd $(ROOT)/lua && $(LUA) hexwar/main.lua bench; \
	  echo '=== node ==='   ; cd $(ROOT)/ts  && $(NODE) dist/src/main.js bench; \
	} | tee $(OUT)/bench.txt

frames:
	@mkdir -p $(OUT)
	cd $(ROOT)/py && for s in 1 12 40 72 76 119; do \
	  $(PY) -m hexwar.main render $(OUT)/frame_$$s.ppm $$s; done
	cd $(ROOT) && for s in 1 12 40 72 76 119; do \
	  $(PY) tools/ppm2png.py $(OUT)/frame_$$s.ppm $(OUT)/frame_$$s.png 2; done

golden:
	cd $(ROOT) && $(PY) tools/gen_prim.py
	cd $(ROOT) && $(PY) tools/gen_palette.py
	cd $(ROOT) && $(PY) tools/gen_tiles.py
	cd $(ROOT) && $(PY) tools/gen_scenario.py
	cd $(ROOT) && $(PY) tools/gen_script.py
	cd $(ROOT)/py && $(PY) -m hexwar.main trace > $(GOLDEN)/trace.jsonl
	@echo '골든 갱신 완료 — make all 로 세 언어를 다시 맞춰 볼 것'

clean:
	rm -rf $(OUT)/*.ppm $(OUT)/*.jsonl $(ROOT)/ts/dist
