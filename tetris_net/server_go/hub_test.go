package main

// hub_test.go — 진짜 HTTP 서버를 띄우고, 진짜 웹소켓으로 붙어서, 진짜 한 판을 돌린다.
// room_test.go 가 규칙을 보고 ws_test.go 가 바이트를 봤다면, 여기서는 둘을 붙여 본다.
import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

type client struct {
	t  *testing.T
	c  *Conn
	in chan map[string]any
}

func dialTest(t *testing.T, srv *httptest.Server) *client {
	t.Helper()
	url := "ws://" + strings.TrimPrefix(srv.URL, "http://") + "/ws"
	c, err := Dial(url)
	if err != nil {
		t.Fatalf("접속 실패: %v", err)
	}
	cl := &client{t: t, c: c, in: make(chan map[string]any, 64)}
	go func() {
		defer close(cl.in)
		for {
			op, data, err := c.ReadMessage()
			if err != nil {
				return
			}
			if op != OpText {
				continue
			}
			var m map[string]any
			if json.Unmarshal(data, &m) == nil {
				cl.in <- m
			}
		}
	}()
	t.Cleanup(func() { c.Close() })
	return cl
}

func (cl *client) send(s string) {
	cl.t.Helper()
	if err := cl.c.WriteText([]byte(s)); err != nil {
		cl.t.Fatalf("보내기 실패: %v", err)
	}
}

// 원하는 t 의 메시지가 올 때까지 기다린다. 중간에 오는 다른 메시지는 흘려보낸다.
func (cl *client) want(kind string) map[string]any {
	cl.t.Helper()
	deadline := time.After(4 * time.Second)
	for {
		select {
		case m, ok := <-cl.in:
			if !ok {
				cl.t.Fatalf("%q 를 기다리다 연결이 끊겼다", kind)
			}
			if m["t"] == kind {
				return m
			}
		case <-deadline:
			cl.t.Fatalf("%q 가 4초 안에 오지 않았다", kind)
		}
	}
}

func newTestServer(t *testing.T) *httptest.Server {
	t.Helper()
	h := NewHub()
	mux := http.NewServeMux()
	mux.HandleFunc("/ws", h.ServeWS)
	s := httptest.NewServer(mux)
	t.Cleanup(s.Close)
	return s
}

func TestHelloVersion(t *testing.T) {
	s := newTestServer(t)
	cl := dialTest(t, s)
	cl.send(`{"t":"hello","v":2,"name":"옛날"}`)
	if m := cl.want("err"); m["code"] != "ver" {
		t.Fatalf("버전 불일치는 err ver 여야 한다: %v", m)
	}
}

func TestCreateJoinAndPlay(t *testing.T) {
	s := newTestServer(t)
	a, b := dialTest(t, s), dialTest(t, s)

	a.send(`{"t":"hello","v":3,"name":"보라"}`)
	a.want("hi")
	a.send(`{"t":"create","cfg":{"max":4,"target":"random"}}`)
	j := a.want("joined")
	code, _ := j["code"].(string)
	if len(code) != 6 {
		t.Fatalf("방 코드는 6자여야 한다: %q", code)
	}

	b.send(`{"t":"hello","v":3,"name":"다온"}`)
	b.want("hi")
	b.send(`{"t":"join","room":"` + code + `"}`)
	b.want("joined")

	// PC 1대가 2석씩 — "PC 2대로 4인"
	a.send(`{"t":"seat","i":0,"kind":"human","name":"보라"}`)
	a.send(`{"t":"seat","i":1,"kind":"ai","name":"봇A","lv":"hard"}`)
	b.send(`{"t":"seat","i":2,"kind":"human","name":"다온"}`)
	b.send(`{"t":"seat","i":3,"kind":"ai","name":"봇B","lv":"hard"}`)
	a.send(`{"t":"ready","v":true}`)
	b.send(`{"t":"ready","v":true}`)

	// 좌석 4석이 다 차고 사람 좌석이 전부 준비될 때까지 기다린다.
	// 좌석만 세면 ready 가 아직 안 들어온 순간에 start 를 눌러 err ready 를 받는다.
	deadline := time.After(4 * time.Second)
	for {
		done := false
		select {
		case m := <-a.in:
			if m["t"] == "room" {
				if ss, ok := m["seats"].([]any); ok && len(ss) == 4 {
					done = true
					for _, x := range ss {
						sm := x.(map[string]any)
						if sm["kind"] == "human" && sm["ready"] != true {
							done = false
						}
					}
				}
			}
		case <-deadline:
			t.Fatal("좌석 4석이 준비 상태로 채워지지 않았다")
		}
		if done {
			break
		}
	}

	a.send(`{"t":"start"}`)
	st := a.want("start")
	if _, ok := st["seed"].(float64); !ok {
		t.Fatalf("start 에 seed 가 없다: %v", st)
	}
	bst := b.want("start")
	if bst["seed"] != st["seed"] {
		t.Fatalf("두 PC 가 받은 시드가 다르다: %v vs %v", st["seed"], bst["seed"])
	}

	// 좌석 0(보라)이 4줄 공격 → 서버가 타겟을 골라 grb 를 방 전체에 뿌린다
	a.send(`{"t":"atk","i":0,"n":4}`)
	g := a.want("grb")
	if g["from"] != float64(0) || g["n"] != float64(4) {
		t.Fatalf("grb 내용이 이상하다: %v", g)
	}
	if h, ok := g["hole"].(float64); !ok || h < 0 || h > 9 {
		t.Fatalf("구멍 위치가 0~9 밖이다: %v", g)
	}
	g2 := b.want("grb") // 관전용으로 상대 PC 에도 간다
	if g2["i"] != g["i"] || g2["hole"] != g["hole"] {
		t.Fatalf("두 PC 가 받은 grb 가 다르다: %v vs %v", g, g2)
	}
}

func TestJoinUnknownRoom(t *testing.T) {
	s := newTestServer(t)
	cl := dialTest(t, s)
	cl.send(`{"t":"hello","v":3,"name":"x"}`)
	cl.want("hi")
	cl.send(`{"t":"join","room":"ZZZZZZ"}`)
	if m := cl.want("err"); m["code"] != "nosuch" {
		t.Fatalf("없는 방은 err nosuch: %v", m)
	}
}

func TestPingPong(t *testing.T) {
	s := newTestServer(t)
	cl := dialTest(t, s)
	cl.send(`{"t":"hello","v":3,"name":"x"}`)
	cl.want("hi")
	cl.send(`{"t":"ping","c":42}`)
	if m := cl.want("pong"); m["c"] != float64(42) {
		t.Fatalf("pong 의 c 가 다르다: %v", m)
	}
}

// PC 가 끊기면 그 PC 의 좌석이 대전에서 빠져야 한다.
func TestPeerDropKillsSeats(t *testing.T) {
	s := newTestServer(t)
	a, b := dialTest(t, s), dialTest(t, s)
	a.send(`{"t":"hello","v":3,"name":"A"}`)
	a.want("hi")
	a.send(`{"t":"create","cfg":{"max":4}}`)
	code := a.want("joined")["code"].(string)
	b.send(`{"t":"hello","v":3,"name":"B"}`)
	b.want("hi")
	b.send(`{"t":"join","room":"` + code + `"}`)
	b.want("joined")
	a.send(`{"t":"seat","i":0,"kind":"ai","name":"A"}`)
	b.send(`{"t":"seat","i":1,"kind":"ai","name":"B"}`)
	time.Sleep(150 * time.Millisecond)
	a.send(`{"t":"start"}`)
	a.want("start")
	b.want("start")

	b.c.Close() // PC 한 대가 사라진다
	ko := a.want("ko")
	if ko["i"] != float64(1) {
		t.Fatalf("끊긴 PC 의 좌석이 죽어야 한다: %v", ko)
	}
	if e := a.want("end"); e["order"] == nil {
		t.Fatalf("혼자 남았으면 end 가 와야 한다: %v", e)
	}
}
