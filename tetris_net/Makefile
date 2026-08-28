# tetris_net — wasm 빌드 + 3중 검증 + 실측 + 덱 생성
#
#   make            tetris_net.wasm 빌드
#   make test       전 계층 테스트 (wasm · room 3구현 · 브라우저 코드)
#   make server     Go 서버 바이너리
#   make run-go     Go 서버 실행 (:8787, web/ 을 같이 내준다)
#   make run-py     파이썬 서버 실행 (:8787)
#   make match      헤드리스 8인 대전을 Go·파이썬 서버 양쪽에 붙여 실측
#   make web        브라우저에서 바로 열리는 클라이언트 묶음 만들기
#   make deck       슬라이드 덱 재생성 (소스 커버리지 검사 포함)
#   make clean

CXX     ?= clang++
WFLAGS   = --target=wasm32 -nostdlib -O2 -fno-exceptions -fno-rtti -Wall -Wextra \
           -Wl,--no-entry -Wl,--export-dynamic -Wl,-z,stack-size=65536
PORT    ?= 8787

.PHONY: all test test-wasm test-room test-go test-py test-browser server run-go run-py match web b64 deck clean

all: tetris_net.wasm

# 2편의 ai.cpp/tetris.cpp 를 include 로 얹는다 — 그 두 파일은 한 줄도 고치지 않는다.
tetris_net.wasm: net.cpp ../tetris_ai/ai.cpp ../tetris_ai/tetris.cpp
	$(CXX) $(WFLAGS) -o $@ net.cpp
	@printf '%s: %s bytes\n' $@ $$(stat -c%s $@)

test: test-wasm test-room test-go test-py test-browser
	@printf '\n전 계층 통과.\n'

test-wasm: tetris_net.wasm
	node test_net.mjs

# room 엔진 3구현이 같은 골든 벡터를 재현하는지 — 이 셋이 이 프로젝트의 등뼈다
test-room:
	node test_room.mjs
test-go:
	cd server_go && go vet ./... && go test -count=1 ./...
test-py:
	cd server_py && python3 -m unittest test_server

test-browser: tetris_net.wasm
	node test_browser.mjs

server:
	cd server_go && go build -o tetris-server .

run-go: server web
	cd server_go && ./tetris-server -addr :$(PORT) -dir ../web
run-py: web
	cd server_py && python3 server.py --port $(PORT) --dir ../web

# 진짜 웹소켓으로 PC 4대 × 2석 = 8인 대전을 두 서버에 각각 붙여 본다.
match: server tetris_net.wasm
	@echo '── Go 서버'
	@cd server_go && (./tetris-server -addr :18787 & echo $$! > /tmp/tn_go.pid) && sleep 1
	-node bot_client.mjs --url ws://127.0.0.1:18787/ws --pcs 4 --seats 2 --max 8 --level mix
	@kill $$(cat /tmp/tn_go.pid) 2>/dev/null || true
	@echo '\n── 파이썬 서버'
	@cd server_py && (python3 server.py --port 18788 & echo $$! > /tmp/tn_py.pid) && sleep 1
	-node bot_client.mjs --url ws://127.0.0.1:18788/ws --pcs 4 --seats 2 --max 8 --level mix
	@kill $$(cat /tmp/tn_py.pid) 2>/dev/null || true

# 브라우저용 묶음. room.mjs 는 원본 그대로 두고 `export ` 만 떼어 낸다 —
# 서버가 검증한 파일과 브라우저가 도는 파일이 갈리면 안 된다.
web: tetris_net.wasm
	@mkdir -p web
	sed 's/^export //' room.mjs > web/room.js
	cp netcore_browser.js net_client.js seats.js arena.js match.js app.js web/
	cp tetris_net.wasm web/
	cp ../tetris_ai/weights.json web/
	@echo 'web/ 준비 완료 — make run-go 또는 make run-py'

b64: tetris_net.wasm
	base64 -w0 tetris_net.wasm > tetris_net.wasm.b64
	@printf 'base64: %s bytes\n' $$(stat -c%s tetris_net.wasm.b64)

deck: b64
	python3 deck/build_deck.py

clean:
	rm -f tetris_net.wasm tetris_net.wasm.b64 server_go/tetris-server
	rm -rf web/room.js web/*.wasm web/weights.json

# ── 웹소켓 라이브러리판 — gorilla/websocket(Go) · websockets(파이썬) ─────────────
# 직접 구현(ws.go·ws.py)과 같은 프로토콜·같은 hub·room 을 라이브러리 전송층 위에서 돌린다.
# Go 쪽 room.go·hub.go·main.go·테스트 2종은 매번 server_go 에서 새로 복사한다 —
# 복사본이 원본과 갈라지는 일 자체를 불가능하게 만든다 (web/room.js 와 같은 규칙).
.PHONY: lib-copy test-lib test-go-lib test-py-lib server-lib run-go-lib run-py-lib match-lib clean-lib

lib-copy:
	cp server_go/room.go server_go/hub.go server_go/main.go \
	   server_go/room_test.go server_go/hub_test.go server_go_lib/

test-lib: test-go-lib test-py-lib
	@printf '\n라이브러리판 통과.\n'
test-go-lib: lib-copy
	cd server_go_lib && go vet ./... && go test -count=1 ./...
test-py-lib:
	cd server_py && python3 -m unittest test_server_lib

server-lib: lib-copy
	cd server_go_lib && go build -o tetris-server-lib .

run-go-lib: server-lib web
	cd server_go_lib && ./tetris-server-lib -addr :$(PORT) -dir ../web
run-py-lib: web
	cd server_py && python3 server_lib.py --port $(PORT) --dir ../web

# 진짜 웹소켓 8인 대전을 라이브러리판 두 서버에도 똑같이 붙여 본다 (match 와 같은 구성)
match-lib: server-lib tetris_net.wasm
	@echo '── Go 서버 (gorilla/websocket)'
	@cd server_go_lib && (./tetris-server-lib -addr :18789 & echo $$! > /tmp/tn_go_lib.pid) && sleep 1
	-node bot_client.mjs --url ws://127.0.0.1:18789/ws --pcs 4 --seats 2 --max 8 --level mix
	@kill $$(cat /tmp/tn_go_lib.pid) 2>/dev/null || true
	@echo '\n── 파이썬 서버 (websockets)'
	@cd server_py && (python3 server_lib.py --port 18790 & echo $$! > /tmp/tn_py_lib.pid) && sleep 1
	-node bot_client.mjs --url ws://127.0.0.1:18790/ws --pcs 4 --seats 2 --max 8 --level mix
	@kill $$(cat /tmp/tn_py_lib.pid) 2>/dev/null || true

clean-lib:
	rm -f server_go_lib/tetris-server-lib server_go_lib/room.go server_go_lib/hub.go \
	      server_go_lib/main.go server_go_lib/room_test.go server_go_lib/hub_test.go
