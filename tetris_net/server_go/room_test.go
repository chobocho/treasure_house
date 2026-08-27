package main

// room_test.go — 골든 벡터로 Go room 엔진을 검증한다.
// JS(test_room.mjs)·파이썬(test_server.py)의 하니스와 같은 표를 읽고 같은 순서로 민다.
import (
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

type vecStep struct {
	Pid int             `json:"pid"`
	At  int64           `json:"at"`
	M   json.RawMessage `json:"m"`
	Out []struct {
		To int             `json:"to"`
		M  json.RawMessage `json:"m"`
	} `json:"out"`
}
type vecCase struct {
	Name  string          `json:"name"`
	Why   string          `json:"why"`
	Cfg   json.RawMessage `json:"cfg"`
	Seed  uint32          `json:"seed"`
	Setup []vecStep       `json:"setup"`
	Steps []vecStep       `json:"steps"`
}
type vecFile struct {
	V     int       `json:"v"`
	Cases []vecCase `json:"cases"`
}

// 세 언어의 JSON 키 순서까지 맞추는 건 규격이 아니라 우연이다.
// 그래서 양쪽 다 any 로 되돌린 뒤에 비교한다.
func norm(t *testing.T, b []byte) any {
	var v any
	if err := json.Unmarshal(b, &v); err != nil {
		t.Fatalf("JSON 파싱 실패: %v (%s)", err, b)
	}
	return v
}

func loadVectors(t *testing.T) vecFile {
	p := filepath.Join("..", "protocol_vectors.json")
	raw, err := os.ReadFile(p)
	if err != nil {
		t.Fatalf("골든 벡터를 읽지 못했다: %v", err)
	}
	var vf vecFile
	if err := json.Unmarshal(raw, &vf); err != nil {
		t.Fatalf("골든 벡터 파싱 실패: %v", err)
	}
	return vf
}

func TestGoldenVectors(t *testing.T) {
	vf := loadVectors(t)
	if vf.V != 3 {
		t.Fatalf("프로토콜 버전이 3이 아니다: %d", vf.V)
	}
	for _, c := range vf.Cases {
		t.Run(c.Name, func(t *testing.T) {
			var cfg Cfg
			cfg = DefaultCfg()
			if len(c.Cfg) > 0 {
				if err := json.Unmarshal(c.Cfg, &cfg); err != nil {
					t.Fatalf("cfg 파싱 실패: %v", err)
				}
			}
			r := NewRoom(cfg, c.Seed)
			for _, s := range c.Setup {
				r.Handle(s.Pid, s.M, s.At)
			}
			for k, s := range c.Steps {
				got := r.Handle(s.Pid, s.M, s.At)
				if len(got) != len(s.Out) {
					t.Fatalf("#%d(%s): 출력 개수 기대 %d, 실제 %d\n  실제: %s",
						k+1, c.Why, len(s.Out), len(got), dump(got))
				}
				for i := range got {
					if got[i].To != s.Out[i].To {
						t.Fatalf("#%d 출력%d: to 기대 %d, 실제 %d", k+1, i, s.Out[i].To, got[i].To)
					}
					gb, err := json.Marshal(got[i].M)
					if err != nil {
						t.Fatalf("직렬화 실패: %v", err)
					}
					if !reflect.DeepEqual(norm(t, s.Out[i].M), norm(t, gb)) {
						t.Fatalf("#%d 출력%d 불일치\n  기대: %s\n  실제: %s", k+1, i, s.Out[i].M, gb)
					}
				}
			}
		})
	}
}

func dump(o []Out) string { b, _ := json.Marshal(o); return string(b) }

// 규격의 난수 그대로인가 — 여기서 갈리면 그 뒤는 볼 것도 없다.
func TestXorshift32(t *testing.T) {
	r := NewRoom(DefaultCfg(), 1)
	want := []uint32{270369, 67634689, 2647435461, 307599695, 2398689233}
	for i, w := range want {
		if g := r.Rng(); g != w {
			t.Fatalf("난수 #%d: 기대 %d, 실제 %d", i+1, w, g)
		}
	}
}

// 요구사항 그대로의 최대 구성 — PC 4대 × 2석 = 8석
func TestEightSeatsFourPeers(t *testing.T) {
	r := NewRoom(Cfg{Max: 8, PerPeer: 2, Target: "random", Delay: 900, Cap: 8, HitTTL: 8000}, 1)
	for pid := 1; pid <= 4; pid++ {
		r.Handle(pid, []byte(`{"t":"seat","i":-1,"kind":"human","name":"a"}`), 0)
		r.Handle(pid, []byte(`{"t":"seat","i":-1,"kind":"ai","name":"b","lv":"hard"}`), 0)
		r.Handle(pid, []byte(`{"t":"ready","v":true}`), 0)
	}
	out := r.Handle(1, []byte(`{"t":"start"}`), 0)
	if len(out) != 1 {
		t.Fatalf("start 출력 1개를 기대했다: %s", dump(out))
	}
	ms, ok := out[0].M.(MsgStart)
	if !ok {
		t.Fatalf("start 메시지가 아니다: %T", out[0].M)
	}
	if len(ms.Seats) != 8 {
		t.Fatalf("좌석 8석을 기대했다: %d", len(ms.Seats))
	}
	for i, s := range ms.Seats {
		if want := i/2 + 1; s.Pid != want {
			t.Fatalf("좌석 %d 의 주인: 기대 pid %d, 실제 %d", i, want, s.Pid)
		}
	}
	if o := r.Handle(5, []byte(`{"t":"seat","i":-1,"kind":"human","name":"x"}`), 0); len(o) != 1 {
		t.Fatalf("9번째 좌석은 거절돼야 한다: %s", dump(o))
	}
}
