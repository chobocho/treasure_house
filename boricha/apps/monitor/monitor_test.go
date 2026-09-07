package monitor

import (
	"strings"
	"testing"
	"time"

	"treasure/boricha/tea"
	"treasure/boricha/testkit"
)

// 시험은 빨라야 돌아간다. 0.7초 간격이면 이 파일 하나가 20초를 먹는다.
func fast() Model { return New().SetInterval(2 * time.Millisecond) }

// CPU 사용률은 두 표본의 차이로만 구할 수 있다. 이 계산이 이 앱의 핵심이고,
// 처음 쓰는 사람이 가장 자주 틀리는 곳이다.
func TestCPUPercent(t *testing.T) {
	cases := []struct {
		name      string
		prev, cur Sample
		want      float64
	}{
		// 100틱 중 60틱을 놀았다면 사용률은 40%.
		{"보통", Sample{CPUTotal: 1000, CPUIdle: 800}, Sample{CPUTotal: 1100, CPUIdle: 860}, 0.4},
		{"완전히 놀았다", Sample{CPUTotal: 1000, CPUIdle: 800}, Sample{CPUTotal: 1100, CPUIdle: 900}, 0},
		{"쉬지 않았다", Sample{CPUTotal: 1000, CPUIdle: 800}, Sample{CPUTotal: 1100, CPUIdle: 800}, 1},
		// 첫 표본에는 견줄 것이 없다. 0으로 두는 편이 정직하다 —
		// 누적값을 그대로 비율로 쓰면 켠 지 오래된 기계에서 늘 같은 숫자가 나온다.
		{"첫 표본", Sample{}, Sample{CPUTotal: 1000, CPUIdle: 900}, 0.1},
		{"변화 없음", Sample{CPUTotal: 1000, CPUIdle: 900}, Sample{CPUTotal: 1000, CPUIdle: 900}, 0},
		// 되감긴 값(기계가 잠들었다 깨어나면 실제로 일어난다)에 음수를 내면 안 된다.
		{"되감김", Sample{CPUTotal: 2000, CPUIdle: 1000}, Sample{CPUTotal: 1000, CPUIdle: 900}, 0},
	}
	for _, c := range cases {
		if got := c.cur.CPUPercent(c.prev); got != c.want {
			t.Errorf("%s: = %v, 원하는 값 %v", c.name, got, c.want)
		}
	}
}

// 메모리는 MemFree 가 아니라 MemAvailable 로 잰다.
// 리눅스는 남는 메모리를 캐시로 다 쓰므로 MemFree 로 재면 늘 "부족" 으로 보인다.
func TestMemPercent(t *testing.T) {
	cases := []struct {
		s    Sample
		want float64
	}{
		{Sample{MemTotal: 1000, MemAvail: 250}, 0.75},
		{Sample{MemTotal: 1000, MemAvail: 1000}, 0},
		{Sample{MemTotal: 0}, 0}, // 0으로 나누지 않는다
	}
	for _, c := range cases {
		if got := c.s.MemPercent(); got != c.want {
			t.Errorf("%+v = %v, 원하는 값 %v", c.s, got, c.want)
		}
	}
}

// 이 기계는 리눅스(안드로이드)라 /proc 가 있다. 실제로 읽히는지 본다.
// 없는 곳에서는 Err 가 채워져야 하고, 그 경우에도 죽지 않아야 한다.
func TestReadOnThisMachine(t *testing.T) {
	s := Read()
	if s.Err != nil {
		t.Skipf("이 기계에는 /proc 가 없다: %v", s.Err)
	}
	if s.CPUTotal == 0 {
		t.Error("CPU 누적값이 0")
	}
	if s.MemTotal == 0 {
		t.Error("MemTotal 이 0")
	}
	if s.MemAvail > s.MemTotal {
		t.Errorf("남은 메모리(%d)가 전체(%d)보다 많다", s.MemAvail, s.MemTotal)
	}
	if s.Uptime <= 0 {
		t.Errorf("가동 시간이 %v", s.Uptime)
	}
}

func TestSparkline(t *testing.T) {
	cases := []struct {
		vals []float64
		w    int
		want string
	}{
		{nil, 4, "    "},
		{[]float64{0, 1}, 2, "▁█"},
		{[]float64{0.5}, 3, "  ▄"},
		{[]float64{-1, 2}, 2, "▁█"},     // 범위를 벗어난 값도 잘라 맞춘다
		{[]float64{0, 0.5, 1}, 2, "▄█"}, // 폭보다 많으면 최근 것만
		{[]float64{0.5}, 0, ""},
	}
	for _, c := range cases {
		if got := sparkline(c.vals, c.w); got != c.want {
			t.Errorf("sparkline(%v, %d) = %q, 원하는 값 %q", c.vals, c.w, got, c.want)
		}
	}
	// 폭은 언제나 요청한 만큼이다. 블록 문자는 모두 한 칸이므로 룬 수가 곧 칸 수다.
	for w := 1; w <= 20; w++ {
		if n := len([]rune(sparkline([]float64{0.1, 0.9}, w))); n != w {
			t.Errorf("폭 %d 인데 %d글자", w, n)
		}
	}
}

// space 로 멈추면 다음 읽기를 예약하지 않는다 — 그것이 곧 멈춤이다.
func TestPauseStopsSampling(t *testing.T) {
	r, err := testkit.RunScript(fast(), `70x24 .3 <space> .6`)
	if err != nil {
		t.Fatal(err)
	}
	m := r.Final.(Model)
	if !m.paused {
		t.Fatal("멈추지 않았다")
	}
	// 멈춘 뒤 여섯 번 기다렸는데도 읽은 횟수가 크게 늘지 않아야 한다.
	if m.reads > 5 {
		t.Errorf("멈췄는데 %d번 읽었다", m.reads)
	}
}

func TestResumeSampling(t *testing.T) {
	r, _ := testkit.RunScript(fast(), `70x24 .2 <space> .2 <space> .4`)
	m := r.Final.(Model)
	if m.paused {
		t.Fatal("다시 시작하지 않았다")
	}
	if m.reads < 3 {
		t.Errorf("다시 시작했는데 %d번만 읽었다", m.reads)
	}
}

// 화면은 주어진 크기를 넘지 않는다.
func TestViewFits(t *testing.T) {
	for _, size := range []string{"60x18", "100x30", "40x14"} {
		r, err := testkit.RunScript(fast(), size+" .3")
		if err != nil {
			t.Fatal(err)
		}
		for i, f := range r.Frames {
			if n := strings.Count(f, "\n") + 1; n != r.Rows {
				t.Errorf("%s 프레임 %d 이 %d줄", size, i, n)
			}
		}
	}
}

var _ tea.Model = Model{}
