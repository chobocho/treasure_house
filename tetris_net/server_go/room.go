package main

// room.go — 방 하나의 게임 규칙. **순수 상태 기계**다.
//
// 소켓도 타이머도 time.Now() 도 없다. (pid, 메시지, now) 를 넣으면
// (누구에게, 무엇을) 목록이 나온다. 그래야 JS·파이썬 구현과 같은 골든 벡터로
// 검증할 수 있다. 규격 전문은 ../protocol.md, 검증표는 ../protocol_vectors.json.
//
// room.mjs / room.py 와 줄 단위로 나란히 놓고 읽어도 될 만큼 구조를 맞춰 뒀다.
// 세 구현이 다르게 생겼으면 어디서 갈렸는지 찾는 데만 하루가 든다.

import (
	"encoding/json"
	"sort"
)

// Cfg — 방 설정. JSON 키는 프로토콜과 같다.
type Cfg struct {
	Max     int    `json:"max"`     // 좌석 수 (1~8)
	PerPeer int    `json:"perPeer"` // PC 1대가 쥘 수 있는 좌석 수 — "한 PC 에서 최대 2명"
	Target  string `json:"target"`  // random / even / attackers / ko
	Delay   int    `json:"delay"`   // 가비지 유예(ms). 지키는 건 클라이언트다
	Cap     int    `json:"cap"`     // 한 락에서 솟을 수 있는 최대 줄
	HitTTL  int64  `json:"hitTTL"`  // "최근에 나를 때렸다"로 치는 시간(ms)
}

func DefaultCfg() Cfg {
	return Cfg{Max: 8, PerPeer: 2, Target: "random", Delay: 900, Cap: 8, HitTTL: 8000}
}

// ── 나가는 메시지 ────────────────────────────────────────────────────
type SeatInfo struct {
	I     int    `json:"i"`
	Pid   int    `json:"pid"`
	Name  string `json:"name"`
	Kind  string `json:"kind"`
	Lv    string `json:"lv"`
	Ready bool   `json:"ready"`
	Alive bool   `json:"alive"`
}
type MsgRoom struct {
	T     string     `json:"t"`
	Host  int        `json:"host"`
	Seats []SeatInfo `json:"seats"`
}
type MsgErr struct {
	T    string `json:"t"`
	Code string `json:"code"`
}
type MsgStart struct {
	T     string     `json:"t"`
	Seed  uint32     `json:"seed"`
	Seats []SeatInfo `json:"seats"`
}
type MsgGrb struct {
	T    string `json:"t"`
	I    int    `json:"i"`
	N    int    `json:"n"`
	From int    `json:"from"`
	Hole uint32 `json:"hole"`
}
type MsgSt struct {
	T string `json:"t"`
	I int    `json:"i"`
	B string `json:"b"`
	S []int  `json:"s"`
}
type MsgKo struct {
	T     string `json:"t"`
	I     int    `json:"i"`
	Place int    `json:"place"`
	By    int    `json:"by"`
}
type MsgEnd struct {
	T     string `json:"t"`
	Order []int  `json:"order"`
}

// Out — "누구에게(0이면 방 전체), 무엇을".
type Out struct {
	To int
	M  any
}

// ── 들어오는 메시지 ──────────────────────────────────────────────────
// 한 구조체로 전부 받는다. 종류별 구조체를 두면 두 번 파싱해야 한다.
type In struct {
	T    string `json:"t"`
	I    *int   `json:"i"`
	N    int    `json:"n"`
	V    bool   `json:"v"`
	Kind string `json:"kind"`
	Name string `json:"name"`
	Lv   string `json:"lv"`
	B    string `json:"b"`
	S    []int  `json:"s"`
}

type hit struct {
	from int
	at   int64
}
type seat struct {
	pid    int
	name   string
	kind   string
	lv     string
	ready  bool
	alive  bool
	recv   int
	height int
	place  int
	hits   []hit
}

type Room struct {
	Cfg       Cfg
	seats     []*seat
	phase     string // lobby / play / over
	peers     map[int]bool
	rngState  uint32
	RoundSeed uint32
}

func NewRoom(cfg Cfg, seed uint32) *Room {
	if seed == 0 {
		seed = 1
	}
	if cfg.Max < 1 {
		cfg.Max = 1
	}
	return &Room{Cfg: cfg, seats: make([]*seat, cfg.Max), phase: "lobby",
		peers: map[int]bool{}, rngState: seed}
}

// 규격의 xorshift32. 세 구현이 여기서부터 갈리면 그 뒤는 볼 것도 없다.
func (r *Room) Rng() uint32 {
	x := r.rngState
	x ^= x << 13
	x ^= x >> 17
	x ^= x << 5
	r.rngState = x
	return x
}

// ── 조회 헬퍼 ────────────────────────────────────────────────────────
func (r *Room) Host() int {
	h := 0
	for p := range r.peers {
		if h == 0 || p < h {
			h = p
		}
	}
	return h
}
func (r *Room) occupied() []int {
	o := []int{}
	for i, s := range r.seats {
		if s != nil {
			o = append(o, i)
		}
	}
	return o
}
func (r *Room) aliveSeats() []int {
	o := []int{}
	for _, i := range r.occupied() {
		if r.seats[i].alive {
			o = append(o, i)
		}
	}
	return o
}
func (r *Room) mine(pid int) []int {
	o := []int{}
	for _, i := range r.occupied() {
		if r.seats[i].pid == pid {
			o = append(o, i)
		}
	}
	return o
}
func (r *Room) seatList() []SeatInfo {
	out := []SeatInfo{}
	for _, i := range r.occupied() {
		s := r.seats[i]
		out = append(out, SeatInfo{I: i, Pid: s.pid, Name: s.name, Kind: s.kind,
			Lv: s.lv, Ready: s.ready, Alive: s.alive})
	}
	return out
}
func (r *Room) roomMsg() []Out {
	return []Out{{To: 0, M: MsgRoom{T: "room", Host: r.Host(), Seats: r.seatList()}}}
}
func errOut(pid int, code string) []Out { return []Out{{To: pid, M: MsgErr{T: "err", Code: code}}} }

// Phase 는 hub 가 로비 표시에 쓴다.
func (r *Room) Phase() string { return r.phase }
func (r *Room) Empty() bool   { return len(r.peers) == 0 }

// ── 진입점 ──────────────────────────────────────────────────────────
func (r *Room) Handle(pid int, raw json.RawMessage, now int64) []Out {
	var m In
	if len(raw) > 0 {
		if err := json.Unmarshal(raw, &m); err != nil {
			return errOut(pid, "bad")
		}
	}
	if m.T == "bye" {
		return r.onBye(pid, now)
	}
	r.peers[pid] = true
	switch m.T {
	case "seat":
		return r.onSeat(pid, m)
	case "unseat":
		return r.onUnseat(pid, m)
	case "ready":
		return r.onReady(pid, m)
	case "start":
		return r.onStart(pid)
	case "atk":
		return r.onAtk(pid, m, now)
	case "st":
		return r.onSt(pid, m)
	case "ko":
		return r.onKo(pid, m, now)
	}
	return nil
}

func (r *Room) onSeat(pid int, m In) []Out {
	if r.phase != "lobby" {
		return errOut(pid, "phase")
	}
	i := -1
	if m.I != nil {
		i = *m.I
	}
	if i < 0 { // 자동 배정 = 가장 앞의 빈 자리
		i = -1
		for k, s := range r.seats {
			if s == nil {
				i = k
				break
			}
		}
		if i < 0 {
			return errOut(pid, "seat")
		}
	} else if i >= len(r.seats) || r.seats[i] != nil {
		return errOut(pid, "seat")
	}
	// 자리를 먼저 확정하고 그다음에 PC 당 좌석 수를 본다. 순서를 바꾸면
	// "빈 자리도 없고 내 몫도 찼을 때" 어느 오류가 나가는지가 구현마다 달라진다.
	if len(r.mine(pid)) >= r.Cfg.PerPeer {
		return errOut(pid, "full")
	}
	kind := "human"
	if m.Kind == "ai" {
		kind = "ai"
	}
	r.seats[i] = &seat{pid: pid, name: m.Name, kind: kind, lv: m.Lv, alive: true, hits: []hit{}}
	return r.roomMsg()
}

func (r *Room) onUnseat(pid int, m In) []Out {
	if r.phase != "lobby" {
		return errOut(pid, "phase")
	}
	i := -1
	if m.I != nil {
		i = *m.I
	}
	if i < 0 || i >= len(r.seats) || r.seats[i] == nil || r.seats[i].pid != pid {
		return errOut(pid, "own")
	}
	r.seats[i] = nil
	return r.roomMsg()
}

func (r *Room) onReady(pid int, m In) []Out {
	if r.phase != "lobby" {
		return errOut(pid, "phase")
	}
	for _, i := range r.mine(pid) {
		r.seats[i].ready = m.V
	}
	return r.roomMsg()
}

func (r *Room) onStart(pid int) []Out {
	if r.phase != "lobby" {
		return errOut(pid, "phase")
	}
	if pid != r.Host() {
		return errOut(pid, "host")
	}
	occ := r.occupied()
	if len(occ) == 0 {
		return errOut(pid, "seat")
	}
	// AI 좌석은 준비를 기다리지 않는다 — 누를 사람이 없다.
	for _, i := range occ {
		if r.seats[i].kind == "human" && !r.seats[i].ready {
			return errOut(pid, "ready")
		}
	}
	r.RoundSeed = r.Rng()
	r.phase = "play"
	for _, i := range occ {
		s := r.seats[i]
		s.alive, s.recv, s.height, s.place, s.hits = true, 0, 0, 0, []hit{}
	}
	return []Out{{To: 0, M: MsgStart{T: "start", Seed: r.RoundSeed, Seats: r.seatList()}}}
}

// ── 공격 라우팅 — 이 게임에서 서버가 하는 유일한 판단 ───────────────────
func (r *Room) pickTarget(from int, now int64) int {
	cand := []int{}
	for _, j := range r.aliveSeats() {
		if j != from {
			cand = append(cand, j)
		}
	}
	if len(cand) == 0 {
		return -1
	}
	switch r.Cfg.Target {
	case "even": // 가장 덜 맞은 쪽 — 난수를 쓰지 않는다
		best := cand[0]
		for _, j := range cand {
			if r.seats[j].recv < r.seats[best].recv {
				best = j
			}
		}
		return best
	case "ko": // 가장 높이 쌓인 쪽 = 죽기 직전
		best := cand[0]
		for _, j := range cand {
			if r.seats[j].height > r.seats[best].height {
				best = j
			}
		}
		return best
	case "attackers": // 최근에 나를 때린 쪽에 반격
		hits := r.seats[from].hits
		for k := len(hits) - 1; k >= 0; k-- {
			h := hits[k]
			if now-h.at > r.Cfg.HitTTL {
				break // hits 는 시간순이라 여기서 끊으면 된다
			}
			if h.from != from && r.seats[h.from] != nil && r.seats[h.from].alive {
				return h.from
			}
		}
		// 기억이 없으면 random 으로 떨어진다 — 이때만 난수를 쓴다
	}
	return cand[int(r.Rng()%uint32(len(cand)))]
}

func (r *Room) onAtk(pid int, m In, now int64) []Out {
	if r.phase != "play" {
		return errOut(pid, "phase")
	}
	i := -1
	if m.I != nil {
		i = *m.I
	}
	if i < 0 || i >= len(r.seats) || r.seats[i] == nil || r.seats[i].pid != pid {
		return errOut(pid, "own")
	}
	if m.N <= 0 || !r.seats[i].alive {
		return nil
	}
	j := r.pickTarget(i, now)
	if j < 0 {
		return nil // 혼자 남았거나 1인용 — 공격은 허공으로
	}
	hole := r.Rng() % 10
	r.seats[j].recv += m.N
	r.seats[j].hits = append(r.seats[j].hits, hit{from: i, at: now})
	// 관전 화면이 "누가 누구를" 화살표로 그려야 하므로 피해자에게만 보내지 않는다.
	return []Out{{To: 0, M: MsgGrb{T: "grb", I: j, N: m.N, From: i, Hole: hole}}}
}

func (r *Room) onSt(pid int, m In) []Out {
	if r.phase != "play" {
		return errOut(pid, "phase")
	}
	i := -1
	if m.I != nil {
		i = *m.I
	}
	if i < 0 || i >= len(r.seats) || r.seats[i] == nil || r.seats[i].pid != pid {
		return errOut(pid, "own")
	}
	if len(m.S) > 4 {
		r.seats[i].height = m.S[4] // 서버가 읽는 칸은 s[0], s[4] 뿐
	}
	ps := []int{}
	for p := range r.peers {
		if p != pid {
			ps = append(ps, p)
		}
	}
	sort.Ints(ps)
	out := []Out{}
	for _, p := range ps {
		out = append(out, Out{To: p, M: MsgSt{T: "st", I: i, B: m.B, S: m.S}})
	}
	return out
}

// 좌석 하나를 탈락시킨다. end 까지 낼 수 있으므로 out 을 받아 이어 붙인다.
func (r *Room) kill(i int, now int64, out *[]Out) {
	if r.phase != "play" {
		return
	}
	s := r.seats[i]
	if s == nil || !s.alive {
		return
	}
	place := len(r.aliveSeats()) // 지금 살아 있는 수 = 그대로 등수
	s.alive = false
	s.place = place
	by := -1
	for k := len(s.hits) - 1; k >= 0; k-- {
		if now-s.hits[k].at > r.Cfg.HitTTL {
			break
		}
		if s.hits[k].from != i {
			by = s.hits[k].from
			break
		}
	}
	*out = append(*out, Out{To: 0, M: MsgKo{T: "ko", I: i, Place: place, By: by}})

	left := r.aliveSeats()
	if len(left) <= 1 {
		if len(left) == 1 {
			r.seats[left[0]].place = 1
		}
		r.phase = "over"
		occ := r.occupied()
		sort.Slice(occ, func(a, b int) bool { return r.seats[occ[a]].place < r.seats[occ[b]].place })
		*out = append(*out, Out{To: 0, M: MsgEnd{T: "end", Order: occ}})
	}
}

func (r *Room) onKo(pid int, m In, now int64) []Out {
	if r.phase != "play" {
		return errOut(pid, "phase")
	}
	i := -1
	if m.I != nil {
		i = *m.I
	}
	if i < 0 || i >= len(r.seats) || r.seats[i] == nil || r.seats[i].pid != pid {
		return errOut(pid, "own")
	}
	out := []Out{}
	r.kill(i, now, &out)
	return out
}

// PC 가 끊겼다. 로비면 자리를 비우고, 대전 중이면 그 PC 의 좌석이 번호 순으로 전멸한다.
func (r *Room) onBye(pid int, now int64) []Out {
	if !r.peers[pid] {
		return nil
	}
	delete(r.peers, pid)
	held := r.mine(pid)
	if r.phase == "play" {
		out := []Out{}
		for _, i := range held {
			r.kill(i, now, &out) // kill() 이 phase 를 over 로 바꾸면 뒤는 무시된다
		}
		return out
	}
	for _, i := range held {
		r.seats[i] = nil
	}
	return r.roomMsg() // 방장이 바뀔 수 있으므로 항상 알린다
}
