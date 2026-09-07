// Package monitor 는 두 번째 응용 프로그램 — 시스템 모니터다.
//
// 여기서 새로 배우는 것은 "밖에서 오는 값" 이다. 지금까지의 앱은 키에만 반응했지만,
// 이 앱은 시계에 맞춰 /proc 를 읽는다. 파일을 읽는 일은 순수하지 않으므로 Update 가
// 직접 하면 안 된다 — 명령(tea.Cmd)으로 밀어내고, 결과는 사건이 되어 돌아온다.
//
// /proc 는 리눅스(안드로이드 포함)에만 있다. 없는 곳에서는 읽기가 실패하고,
// 앱은 "못 읽었다" 를 화면에 정직하게 적는다. 있는 척하지 않는다.
package monitor

import (
	"os"
	"strconv"
	"strings"
)

// Sample 은 한 번 읽어 온 시스템 상태다.
type Sample struct {
	// CPU 누적 지표. 사용률은 두 번 읽은 값의 차이로만 구할 수 있다.
	CPUTotal, CPUIdle    uint64
	MemTotal, MemAvail   uint64 // kB
	Load1, Load5, Load15 float64
	Uptime               float64 // 초
	Err                  error
}

// CPUPercent 는 이전 표본과 견주어 사용률(0~1)을 구한다.
//
// /proc/stat 는 "부팅 이후 각 상태에 머문 시간" 의 누적값이다. 한 번 읽어서는
// 지금 얼마나 바쁜지 알 수 없다 — 두 시점의 차이라야 그 사이의 사용률이 된다.
// 이 사실을 모르고 한 번 읽은 값으로 비율을 내면, 켠 지 오래된 기계에서
// 언제나 비슷한 숫자가 나와 "왜 안 움직이지?" 하게 된다.
func (s Sample) CPUPercent(prev Sample) float64 {
	dt := s.CPUTotal - prev.CPUTotal
	di := s.CPUIdle - prev.CPUIdle
	if dt == 0 || s.CPUTotal < prev.CPUTotal {
		return 0
	}
	return float64(dt-di) / float64(dt)
}

// MemPercent 는 쓰고 있는 메모리의 비율이다.
//
// MemFree 가 아니라 MemAvailable 을 쓴다. 리눅스는 남는 메모리를 캐시로 다 쓰므로
// MemFree 는 늘 작게 나온다 — 그걸로 계산하면 언제나 "메모리 부족" 처럼 보인다.
func (s Sample) MemPercent() float64 {
	if s.MemTotal == 0 {
		return 0
	}
	used := s.MemTotal - s.MemAvail
	return float64(used) / float64(s.MemTotal)
}

// Read 는 /proc 에서 한 번 읽는다. 실패는 Err 에 담아 돌려준다 —
// 여기서 죽어 버리면 화면이 통째로 사라져 무엇이 잘못됐는지도 알 수 없다.
func Read() Sample {
	var s Sample
	if err := readStat(&s); err != nil {
		s.Err = err
		return s
	}
	_ = readMeminfo(&s)
	_ = readLoad(&s)
	_ = readUptime(&s)
	return s
}

func readStat(s *Sample) error {
	b, err := os.ReadFile("/proc/stat")
	if err != nil {
		return err
	}
	// 첫 줄이 "cpu  user nice system idle iowait irq softirq steal guest guest_nice"
	line, _, _ := strings.Cut(string(b), "\n")
	f := strings.Fields(line)
	if len(f) < 5 || f[0] != "cpu" {
		return errShape("/proc/stat")
	}
	for i, v := range f[1:] {
		n, err := strconv.ParseUint(v, 10, 64)
		if err != nil {
			continue
		}
		s.CPUTotal += n
		// 네 번째(idle)와 다섯 번째(iowait)는 "놀고 있던 시간" 이다.
		if i == 3 || i == 4 {
			s.CPUIdle += n
		}
	}
	return nil
}

func readMeminfo(s *Sample) error {
	b, err := os.ReadFile("/proc/meminfo")
	if err != nil {
		return err
	}
	for _, line := range strings.Split(string(b), "\n") {
		k, v, ok := strings.Cut(line, ":")
		if !ok {
			continue
		}
		n, err := strconv.ParseUint(strings.Fields(v)[0], 10, 64)
		if err != nil {
			continue
		}
		switch k {
		case "MemTotal":
			s.MemTotal = n
		case "MemAvailable":
			s.MemAvail = n
		}
	}
	return nil
}

func readLoad(s *Sample) error {
	b, err := os.ReadFile("/proc/loadavg")
	if err != nil {
		return err
	}
	f := strings.Fields(string(b))
	if len(f) < 3 {
		return errShape("/proc/loadavg")
	}
	s.Load1, _ = strconv.ParseFloat(f[0], 64)
	s.Load5, _ = strconv.ParseFloat(f[1], 64)
	s.Load15, _ = strconv.ParseFloat(f[2], 64)
	return nil
}

func readUptime(s *Sample) error {
	b, err := os.ReadFile("/proc/uptime")
	if err != nil {
		return err
	}
	f := strings.Fields(string(b))
	if len(f) < 1 {
		return errShape("/proc/uptime")
	}
	s.Uptime, _ = strconv.ParseFloat(f[0], 64)
	return nil
}

type errShape string

func (e errShape) Error() string { return string(e) + " 의 모양이 예상과 다르다" }
