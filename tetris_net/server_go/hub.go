package main

// hub.go — 방 코드·연결·중계. 게임 규칙은 한 줄도 여기 없다 (전부 room.go 에 있다).
//
// 동시성 설계가 이 파일의 전부다. 규칙은 이렇다:
//   * 방 하나 = 고루틴 하나. Room 상태는 그 고루틴만 만진다. 그래서 Room 에 뮤텍스가 없다.
//   * 연결 하나 = 읽기 고루틴 하나 + 쓰기 고루틴 하나.
//   * 고루틴 사이는 오직 채널로만 이야기한다.
// 방 상태에 락을 걸지 않으니 "골든 벡터로 검증한 그 순수 함수"가 그대로 서버에서 돈다.

import (
	"crypto/rand"
	"encoding/json"
	"log"
	"math/big"
	"net/http"
	"sync"
	"time"
)

const ProtoVersion = 3

// 사람이 불러 주기 쉬운 글자만 남긴다 — 0/O, 1/I/L 처럼 헷갈리는 건 뺐다.
const codeAlphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

type event struct {
	pid int
	raw json.RawMessage
	at  int64
}

// Peer — PC 1대. 좌석은 최대 2석까지 이 안에 들어간다.
type Peer struct {
	pid     int
	name    string
	conn    *Conn
	send    chan []byte
	rh      *RoomHost
	greeted bool

	// send 채널을 닫는 곳이 두 군데(방 고루틴·읽기 고루틴)라서 잠금이 필요하다.
	// 닫힌 채널에 쓰면 패닉이고, 두 번 닫아도 패닉이다. dead 플래그가 그 둘을 막는다.
	mu   sync.Mutex
	dead bool
}

func (p *Peer) push(v any) {
	b, err := json.Marshal(v)
	if err != nil {
		return
	}
	p.mu.Lock()
	defer p.mu.Unlock()
	if p.dead {
		return
	}
	select {
	case p.send <- b:
	default:
		// 큐가 찼다 = 이 PC 가 우리가 보내는 속도를 못 따라온다.
		// 기다려 주면 방 고루틴 전체가 그 PC 하나 때문에 멈춘다. 끊는 게 맞다.
		p.dead = true
		close(p.send)
		go p.conn.Close()
	}
}

// finish — 우아한 종료. 채널만 닫고 소켓은 쓰기 고루틴이 큐를 다 비운 뒤에 닫는다.
// 버전 불일치 같은 "마지막 한 마디"가 이 순서 덕분에 상대에게 도착한다.
func (p *Peer) finish() {
	p.mu.Lock()
	defer p.mu.Unlock()
	if !p.dead {
		p.dead = true
		close(p.send)
	}
}

// RoomHost — 방 하나 + 그 방에 붙은 PC 들. 아래 필드는 전부 room 고루틴만 만진다.
type RoomHost struct {
	code  string
	room  *Room
	peers map[int]*Peer
	in    chan event
	join  chan *Peer
	t0    time.Time
	hub   *Hub
}

type Hub struct {
	mu      sync.Mutex
	rooms   map[string]*RoomHost
	nextPid int
}

func NewHub() *Hub { return &Hub{rooms: map[string]*RoomHost{}, nextPid: 0} }

func randInt(n int64) int64 {
	v, err := rand.Int(rand.Reader, big.NewInt(n))
	if err != nil {
		return 0
	}
	return v.Int64()
}
func newCode() string {
	b := make([]byte, 6)
	for i := range b {
		b[i] = codeAlphabet[randInt(int64(len(codeAlphabet)))]
	}
	return string(b)
}

func (h *Hub) createRoom(cfg Cfg) *RoomHost {
	h.mu.Lock()
	defer h.mu.Unlock()
	code := newCode()
	for h.rooms[code] != nil {
		code = newCode()
	}
	rh := &RoomHost{
		code:  code,
		room:  NewRoom(cfg, uint32(randInt(1<<31))|1),
		peers: map[int]*Peer{},
		in:    make(chan event, 256),
		join:  make(chan *Peer, 8),
		t0:    time.Now(),
		hub:   h,
	}
	h.rooms[code] = rh
	go rh.loop()
	return rh
}

func (h *Hub) find(code string) *RoomHost {
	h.mu.Lock()
	defer h.mu.Unlock()
	return h.rooms[code]
}
func (h *Hub) drop(code string) {
	h.mu.Lock()
	defer h.mu.Unlock()
	delete(h.rooms, code)
}

// Stats — /rooms 가 내보내는 운영용 요약.
func (h *Hub) Stats() []map[string]any {
	h.mu.Lock()
	defer h.mu.Unlock()
	out := []map[string]any{}
	for code, rh := range h.rooms {
		out = append(out, map[string]any{"code": code, "age": int(time.Since(rh.t0).Seconds())})
	}
	return out
}

// ── 방 고루틴 ──
func (rh *RoomHost) loop() {
	for {
		select {
		case p := <-rh.join:
			rh.peers[p.pid] = p
		case ev := <-rh.in:
			outs := rh.room.Handle(ev.pid, ev.raw, ev.at)
			rh.dispatch(outs)
			var probe struct {
				T string `json:"t"`
			}
			json.Unmarshal(ev.raw, &probe)
			if probe.T == "bye" {
				delete(rh.peers, ev.pid)
				if len(rh.peers) == 0 {
					rh.hub.drop(rh.code)
					return // 아무도 없는 방은 고루틴째로 사라진다
				}
			}
		}
	}
}

func (rh *RoomHost) dispatch(outs []Out) {
	for _, o := range outs {
		if o.To == 0 {
			for _, p := range rh.peers {
				p.push(o.M)
			}
			continue
		}
		if p := rh.peers[o.To]; p != nil {
			p.push(o.M)
		}
	}
}

func (rh *RoomHost) now() int64 { return time.Since(rh.t0).Milliseconds() }

// ── 연결 하나의 일생 ──
func (h *Hub) ServeWS(w http.ResponseWriter, r *http.Request) {
	c, err := Upgrade(w, r)
	if err != nil {
		log.Printf("업그레이드 실패: %v", err)
		return
	}
	c.MaxPayload = 64 << 10 // 이 게임의 최대 메시지는 1KB 도 안 된다. 넉넉히 잡아도 이 정도
	h.mu.Lock()
	h.nextPid++
	pid := h.nextPid
	h.mu.Unlock()

	p := &Peer{pid: pid, conn: c, send: make(chan []byte, 64)}
	go func() { // 쓰기 고루틴 — 소켓에 쓰는 곳은 여기 한 곳뿐이다
		for b := range p.send {
			if err := c.WriteText(b); err != nil {
				break
			}
		}
		c.Close()
	}()
	defer func() {
		if p.rh != nil {
			p.rh.in <- event{pid: pid, raw: json.RawMessage(`{"t":"bye"}`), at: p.rh.now()}
		}
		p.finish()
	}()

	// 봉투는 hub 가 직접 읽어야 하는 칸만 담는다.
	// `v` 를 int 로 못 박으면 ready 의 `"v":true` 가 파싱에 걸려 통째로 버려진다 —
	// 같은 키 이름이 메시지마다 다른 타입인 건 흔한 일이고, 정적 타입 언어만 여기서 넘어진다.
	// 그래서 hub 가 해석할 필요가 없는 칸은 RawMessage 로 그냥 지나가게 둔다.
	type envelope struct {
		T    string          `json:"t"`
		V    json.RawMessage `json:"v"`
		Name string          `json:"name"`
		Room string          `json:"room"`
		Cfg  *Cfg            `json:"cfg"`
		C    json.RawMessage `json:"c"`
	}
	for {
		op, data, err := c.ReadMessage()
		if err != nil {
			return
		}
		if op != OpText {
			continue
		}
		var hello envelope
		if json.Unmarshal(data, &hello) != nil {
			p.push(MsgErr{T: "err", Code: "bad"})
			continue
		}
		switch {
		case hello.T == "hello":
			ver := 0
			json.Unmarshal(hello.V, &ver)
			if ver != ProtoVersion {
				p.push(MsgErr{T: "err", Code: "ver"})
				return
			}
			p.name, p.greeted = hello.Name, true
			p.push(map[string]any{"t": "hi", "pid": pid, "v": ProtoVersion})
		case !p.greeted:
			p.push(MsgErr{T: "err", Code: "hello"})
		case hello.T == "ping":
			p.push(map[string]any{"t": "pong", "c": hello.C})
		case hello.T == "create":
			if p.rh != nil {
				p.push(MsgErr{T: "err", Code: "inroom"})
				continue
			}
			cfg := DefaultCfg()
			if hello.Cfg != nil {
				cfg = mergeCfg(cfg, *hello.Cfg)
			}
			rh := h.createRoom(cfg)
			p.rh = rh
			p.push(map[string]any{"t": "joined", "code": rh.code, "cfg": cfg, "pid": pid})
			rh.join <- p
		case hello.T == "join":
			if p.rh != nil {
				p.push(MsgErr{T: "err", Code: "inroom"})
				continue
			}
			rh := h.find(hello.Room)
			if rh == nil {
				p.push(MsgErr{T: "err", Code: "nosuch"})
				continue
			}
			p.rh = rh
			p.push(map[string]any{"t": "joined", "code": rh.code, "cfg": rh.room.Cfg, "pid": pid})
			rh.join <- p
		case p.rh == nil:
			p.push(MsgErr{T: "err", Code: "nosuch"})
		default:
			p.rh.in <- event{pid: pid, raw: json.RawMessage(data), at: p.rh.now()}
		}
	}
}

// 클라이언트가 보낸 cfg 에서 0 인 칸은 기본값을 그대로 둔다.
// "안 적었다"와 "0 을 적었다"를 JSON 만으로는 못 가리므로, 0 은 안 적은 것으로 본다.
func mergeCfg(base, in Cfg) Cfg {
	if in.Max > 0 {
		base.Max = in.Max
		if base.Max > 8 {
			base.Max = 8
		}
	}
	if in.PerPeer > 0 {
		base.PerPeer = in.PerPeer
	}
	if in.Target != "" {
		base.Target = in.Target
	}
	if in.Delay > 0 {
		base.Delay = in.Delay
	}
	if in.Cap > 0 {
		base.Cap = in.Cap
	}
	if in.HitTTL > 0 {
		base.HitTTL = in.HitTTL
	}
	return base
}
