# DOS-RTS — 세 언어 구현을 한꺼번에 검사하고, 덱에 실을 출력을 out/ 에 남긴다.
#
#   make all       전부 (권장)
#   make py        파이썬 검사만
#   make lua       루아 검사만 (luajit)
#   make love      같은 테스트를 LÖVE 런타임에서 (헤드리스)
#   make ts        타입스크립트 빌드 + 검사만
#   make parity    prim/trace/해시/렌더 결과가 세 언어에서 바이트 단위로 같은지
#   make lockstep  두 시뮬 락스텝 검증 + 부동소수점 버그 주입 실험
#   make bench     성능 비교
#   make frames    덱에 실을 프레임 PPM/PNG
#   make shots     pygame 헤드리스 스크린샷 (out/shots/*.png)
#   make golden    골든 파일 재생성 (바뀌면 세 언어를 전부 다시 맞춰야 한다)
#   make deck      덱 조립 + 역검증  ← "오류 N건" 줄을 반드시 읽을 것

SHELL   := /bin/bash
ROOT    := $(CURDIR)
GOLDEN  := $(ROOT)/golden
OUT     := $(ROOT)/out
PY      := python3
LUA     := luajit
LOVE    := love
NODE    := node
TSC     := $(ROOT)/ts/node_modules/.bin/tsc

# 모듈 순서는 SPEC.md 의 절 순서와 같다 — 의존 방향이기도 하다.
PYTESTS := test_fixed test_rng test_tmap test_mapgen test_circle test_spatial \
           test_select test_path test_hpa test_jps test_flow test_move \
           test_fog test_combat test_econ test_ai test_sim test_net \
           test_replay test_speaker test_raster test_render test_prim test_trace

.PHONY: all py lua love ts web demos parity lockstep bench frames shots \
        golden deck verify-log clean

all: py lua ts web demos parity lockstep
	@echo '── 전부 통과 ──'

py:
	@mkdir -p $(OUT)
	@set -o pipefail; { for t in $(PYTESTS); do \
	    cd $(ROOT)/py/tests && $(PY) $$t.py || { echo "★ $$t 실패"; exit 1; }; \
	  done; } | tee $(OUT)/py_tests.txt
	cd $(ROOT)/py && $(PY) -m rts.main prim   > $(OUT)/py_prim.txt
	cd $(ROOT)/py && $(PY) -m rts.main trace  > $(OUT)/py_trace.jsonl
	cd $(ROOT)/py && $(PY) -m rts.main hashes > $(OUT)/py_hashes.txt
	@cmp $(OUT)/py_prim.txt   $(GOLDEN)/prim.txt   && echo '  py prim   == golden OK'
	@cmp $(OUT)/py_trace.jsonl $(GOLDEN)/trace.jsonl && echo '  py trace  == golden OK'
	@cmp $(OUT)/py_hashes.txt $(GOLDEN)/hashes.txt && echo '  py hashes == golden OK'

lua:
	@mkdir -p $(OUT)
	@set -o pipefail; cd $(ROOT)/lua && $(LUA) tests/run.lua | tee $(OUT)/lua_tests.txt
	cd $(ROOT)/lua && $(LUA) rts/main.lua prim   > $(OUT)/lua_prim.txt
	cd $(ROOT)/lua && $(LUA) rts/main.lua trace  > $(OUT)/lua_trace.jsonl
	cd $(ROOT)/lua && $(LUA) rts/main.lua hashes > $(OUT)/lua_hashes.txt

love:
	@mkdir -p $(OUT)
	@set -o pipefail; cd $(ROOT)/lua && SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
	  $(LOVE) tools/love_headless | tee $(OUT)/love_tests.txt

ts:
	@mkdir -p $(OUT)
	cd $(ROOT)/ts && $(TSC) -p tsconfig.json
	@set -o pipefail; cd $(ROOT)/ts && $(NODE) dist/tests/run.js | tee $(OUT)/ts_tests.txt
	cd $(ROOT)/ts && $(NODE) dist/src/main.js prim   > $(OUT)/ts_prim.txt
	cd $(ROOT)/ts && $(NODE) dist/src/main.js trace  > $(OUT)/ts_trace.jsonl
	cd $(ROOT)/ts && $(NODE) dist/src/main.js hashes > $(OUT)/ts_hashes.txt

web:
	@mkdir -p $(OUT)
	cd $(ROOT)/ts && $(TSC) -p tsconfig.web.json
	cd $(ROOT) && $(PY) tools/gen_webdata.py
	cd $(ROOT) && $(PY) tools/bundle_web.py
	@set -o pipefail; cd $(ROOT) && $(NODE) tools/check_web.js | tee $(OUT)/check_web.txt

demos:
	@set -o pipefail; cd $(ROOT) && $(NODE) tools/check_demos.js deck/demos.js \
	  | tee $(OUT)/check_demos.txt

parity:
	@mkdir -p $(OUT)
	cd $(ROOT)/py  && $(PY) -m rts.main render $(OUT)/frame_final.ppm
	cd $(ROOT)/lua && $(LUA) rts/main.lua render $(OUT)/frame_final_lua.ppm
	cd $(ROOT)/ts  && $(NODE) dist/src/main.js render $(OUT)/frame_final_ts.ppm
	@{ \
	  echo '== 1. 프리미티브 보고서 =='; \
	  cmp $(GOLDEN)/prim.txt $(OUT)/py_prim.txt  && echo '  python == golden OK'; \
	  cmp $(GOLDEN)/prim.txt $(OUT)/lua_prim.txt && echo '  lua    == golden OK'; \
	  cmp $(GOLDEN)/prim.txt $(OUT)/ts_prim.txt  && echo '  ts     == golden OK'; \
	  echo '== 2. 시나리오 트레이스 =='; \
	  cmp $(GOLDEN)/trace.jsonl $(OUT)/py_trace.jsonl  && echo '  python == golden OK'; \
	  cmp $(GOLDEN)/trace.jsonl $(OUT)/lua_trace.jsonl && echo '  lua    == golden OK'; \
	  cmp $(GOLDEN)/trace.jsonl $(OUT)/ts_trace.jsonl  && echo '  ts     == golden OK'; \
	  echo '== 3. 틱별 상태 해시 =='; \
	  cmp $(GOLDEN)/hashes.txt $(OUT)/py_hashes.txt  && echo '  python == golden OK'; \
	  cmp $(GOLDEN)/hashes.txt $(OUT)/lua_hashes.txt && echo '  lua    == golden OK'; \
	  cmp $(GOLDEN)/hashes.txt $(OUT)/ts_hashes.txt  && echo '  ts     == golden OK'; \
	  echo '== 4. 브라우저 번들 =='; \
	  cd $(ROOT) && $(NODE) tools/check_web.js; \
	  echo '== 5. 렌더 결과 바이트 비교 (320x200 8비트 인덱스 · PPM 192,015바이트) =='; \
	  cmp $(OUT)/frame_final.ppm $(OUT)/frame_final_lua.ppm && echo '  python == lua  OK'; \
	  cmp $(OUT)/frame_final.ppm $(OUT)/frame_final_ts.ppm  && echo '  python == ts   OK'; \
	} | tee $(OUT)/parity.txt

lockstep:
	@mkdir -p $(OUT)
	@{ \
	  echo '== 1. python =='; cd $(ROOT)/py  && $(PY) -m rts.main lockstep; \
	  echo '== 2. lua =='   ; cd $(ROOT)/lua && $(LUA) rts/main.lua lockstep; \
	  echo '== 3. ts =='    ; cd $(ROOT)/ts  && $(NODE) dist/src/main.js lockstep; \
	} | tee $(OUT)/lockstep.txt

bench:
	@mkdir -p $(OUT)
	@{ \
	  echo '== 1. python3 =='; cd $(ROOT)/py  && $(PY) -m rts.main bench; \
	  echo '== 2. luajit ==' ; cd $(ROOT)/lua && $(LUA) rts/main.lua bench; \
	  echo '== 3. node =='   ; cd $(ROOT)/ts  && $(NODE) dist/src/main.js bench; \
	} | tee $(OUT)/bench.txt

frames:
	@mkdir -p $(OUT)
	cd $(ROOT)/py && for s in 1 60 150 300 450 600; do \
	  $(PY) -m rts.main render $(OUT)/frame_$$s.ppm $$s; done
	cd $(ROOT) && for s in 1 60 150 300 450 600; do \
	  $(PY) tools/ppm2png.py $(OUT)/frame_$$s.ppm $(OUT)/frame_$$s.png 2; done

shots:
	@mkdir -p $(OUT)/shots
	@set -o pipefail; cd $(ROOT)/py && $(PY) -m rts_pygame.shots | tee $(OUT)/shots.txt

golden:
	cd $(ROOT) && $(PY) tools/gen_prim.py
	cd $(ROOT) && $(PY) tools/gen_autotile.py
	cd $(ROOT) && $(PY) tools/gen_circle.py
	cd $(ROOT) && $(PY) tools/gen_palette.py
	cd $(ROOT) && $(PY) tools/gen_sprites.py
	cd $(ROOT) && $(PY) tools/gen_maps.py
	cd $(ROOT) && $(PY) tools/gen_script.py
	cd $(ROOT)/py && $(PY) -m rts.main trace  > $(GOLDEN)/trace.jsonl
	cd $(ROOT)/py && $(PY) -m rts.main hashes > $(GOLDEN)/hashes.txt
	@echo '골든 갱신 완료 — make all 로 세 언어를 다시 맞춰 볼 것'

deck:
	cd $(ROOT) && $(PY) deck/build_deck.py
	cd $(ROOT) && $(PY) deck/verify_deck.py

verify-log:
	@$(MAKE) --no-print-directory all 2>&1 \
	  | grep -v '^cd \|^{\|^ *\\$$\|^@\|^make\|^  *for ' | sed '/^$$/d' > $(OUT)/verify_all.txt
	@cat $(OUT)/verify_all.txt

clean:
	rm -rf $(OUT)/*.ppm $(OUT)/*.jsonl $(ROOT)/ts/dist $(ROOT)/ts/distweb
