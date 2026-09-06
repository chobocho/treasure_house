# IsoRPG — 세 언어 구현을 한꺼번에 검사하고, 덱에 실을 출력을 out/ 에 남긴다.
#
#   make all      전부 (권장)
#   make py       파이썬 검사만
#   make lua      루아 검사만 (luajit)
#   make love     같은 테스트를 LÖVE 런타임에서 (헤드리스)
#   make ts       타입스크립트 빌드 + 검사만
#   make parity   prim/trace/렌더 결과가 세 언어에서 바이트 단위로 같은지
#   make bench    성능 비교
#   make frames   덱에 실을 프레임 PPM/PNG
#   make shots    pygame 헤드리스 스크린샷 (out/shots/*.png) + PPM 대조 검사
#   make golden   골든 파일 재생성 (바뀌면 세 언어를 전부 다시 맞춰야 한다)

SHELL   := /bin/bash
ROOT    := $(CURDIR)
GOLDEN  := $(ROOT)/golden
OUT     := $(ROOT)/out
PY      := python3
LUA     := luajit
LOVE    := love
NODE    := node
TSC     := $(ROOT)/ts/node_modules/.bin/tsc

PYTESTS := test_fixed test_proj test_sort test_map test_path test_raster \
           test_los test_dice test_save test_prim test_trace test_engine

.PHONY: all py lua love ts parity bench frames shots golden clean verify-log

all: py lua ts web parity
	@echo '── 전부 통과 ──'

py:
	@mkdir -p $(OUT)
	@set -o pipefail; { for t in $(PYTESTS); do \
	    cd $(ROOT)/py/tests && $(PY) $$t.py || { echo "★ $$t 실패"; exit 1; }; \
	  done; } | tee $(OUT)/py_tests.txt
	cd $(ROOT)/py && $(PY) -m isorpg.main prim  > $(OUT)/py_prim.txt
	cd $(ROOT)/py && $(PY) -m isorpg.main trace > $(OUT)/py_trace.jsonl
	@cmp $(OUT)/py_prim.txt $(GOLDEN)/prim.txt && echo '  py prim  == golden OK'
	@cmp $(OUT)/py_trace.jsonl $(GOLDEN)/trace.jsonl && echo '  py trace == golden OK'

lua:
	@mkdir -p $(OUT)
	cd $(ROOT)/lua && $(LUA) tests/run.lua | tee $(OUT)/lua_tests.txt
	cd $(ROOT)/lua && $(LUA) isorpg/main.lua prim  > $(OUT)/lua_prim.txt
	cd $(ROOT)/lua && $(LUA) isorpg/main.lua trace > $(OUT)/lua_trace.jsonl

love:
	@mkdir -p $(OUT)
	@set -o pipefail; cd $(ROOT)/lua && SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
	  $(LOVE) tools/love_headless | tee $(OUT)/love_tests.txt

ts:
	@mkdir -p $(OUT)
	cd $(ROOT)/ts && $(TSC) -p tsconfig.json
	cd $(ROOT)/ts && $(NODE) dist/tests/run.js | tee $(OUT)/ts_tests.txt
	cd $(ROOT)/ts && $(NODE) dist/src/main.js prim  > $(OUT)/ts_prim.txt
	cd $(ROOT)/ts && $(NODE) dist/src/main.js trace > $(OUT)/ts_trace.jsonl

web:
	@mkdir -p $(OUT)
	cd $(ROOT)/ts && $(TSC) -p tsconfig.web.json
	cd $(ROOT) && $(PY) tools/gen_webdata.py
	cd $(ROOT) && $(PY) tools/bundle_web.py
	cd $(ROOT) && $(NODE) tools/check_web.js | tee $(OUT)/check_web.txt

parity:
	@mkdir -p $(OUT)
	cd $(ROOT)/py  && $(PY) -m isorpg.main render $(OUT)/frame_final.ppm
	cd $(ROOT)/lua && $(LUA) isorpg/main.lua render $(OUT)/frame_final_lua.ppm
	cd $(ROOT)/ts  && $(NODE) dist/src/main.js render $(OUT)/frame_final_ts.ppm
	@{ \
	  echo '== 1. 프리미티브 보고서 (208줄) =='; \
	  cmp $(GOLDEN)/prim.txt $(OUT)/py_prim.txt  && echo '  python == golden OK'; \
	  cmp $(GOLDEN)/prim.txt $(OUT)/lua_prim.txt && echo '  lua    == golden OK'; \
	  cmp $(GOLDEN)/prim.txt $(OUT)/ts_prim.txt  && echo '  ts     == golden OK'; \
	  echo '== 2. 시나리오 트레이스 (233줄) =='; \
	  cmp $(GOLDEN)/trace.jsonl $(OUT)/py_trace.jsonl  && echo '  python == golden OK'; \
	  cmp $(GOLDEN)/trace.jsonl $(OUT)/lua_trace.jsonl && echo '  lua    == golden OK'; \
	  cmp $(GOLDEN)/trace.jsonl $(OUT)/ts_trace.jsonl  && echo '  ts     == golden OK'; \
	  echo '== 3. 브라우저 번들 =='; \
	  cd $(ROOT) && $(NODE) tools/check_web.js; \
	  echo '== 4. 렌더 결과 바이트 비교 (320x200 8비트 인덱스 · PPM 192,015바이트) =='; \
	  cmp $(OUT)/frame_final.ppm $(OUT)/frame_final_lua.ppm && echo '  python == lua  OK'; \
	  cmp $(OUT)/frame_final.ppm $(OUT)/frame_final_ts.ppm  && echo '  python == ts   OK'; \
	} | tee $(OUT)/parity.txt

bench:
	@mkdir -p $(OUT)
	@{ \
	  echo '== 1. python3 =='; cd $(ROOT)/py  && $(PY) -m isorpg.main bench; \
	  echo '== 2. luajit ==' ; cd $(ROOT)/lua && $(LUA) isorpg/main.lua bench; \
	  echo '== 3. node =='   ; cd $(ROOT)/ts  && $(NODE) dist/src/main.js bench; \
	} | tee $(OUT)/bench.txt

frames:
	@mkdir -p $(OUT)
	cd $(ROOT)/py && for s in 1 25 45 83 97 146 194; do \
	  $(PY) -m isorpg.main render $(OUT)/frame_$$s.ppm $$s; done
	cd $(ROOT) && for s in 1 25 45 83 97 146 194; do \
	  $(PY) tools/ppm2png.py $(OUT)/frame_$$s.ppm $(OUT)/frame_$$s.png 2; done

shots:
	@mkdir -p $(OUT)/shots
	@set -o pipefail; cd $(ROOT)/py && $(PY) -m isorpg_pygame.shots | tee $(OUT)/shots.txt

golden:
	cd $(ROOT) && $(PY) tools/gen_prim.py
	cd $(ROOT) && $(PY) tools/gen_palette.py
	cd $(ROOT) && $(PY) tools/gen_tiles.py
	cd $(ROOT)/py && $(PY) -c "from isorpg import gamemap as M; \
	  open('$(GOLDEN)/map.txt','w',encoding='utf-8').write(M.save_rle(M.gen_map()))"
	cd $(ROOT)/py && $(PY) -m isorpg.main trace > $(GOLDEN)/trace.jsonl
	@echo '골든 갱신 완료 — make all 로 세 언어를 다시 맞춰 볼 것'

verify-log:
	@$(MAKE) --no-print-directory all 2>&1 \
	  | grep -v '^cd \|^{\|^ *\\$$\|^@\|^make\|^  *for ' | sed '/^$$/d' > $(OUT)/verify_all.txt
	@cat $(OUT)/verify_all.txt

clean:
	rm -rf $(OUT)/*.ppm $(OUT)/*.jsonl $(ROOT)/ts/dist
