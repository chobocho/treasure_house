package style

import (
	"strconv"
	"strings"
)

// Profile 은 터미널이 낼 수 있는 색의 수준이다.
//
// 왜 이런 것이 필요한가. 24비트 색 시퀀스를 16색 터미널에 보내면 무시되거나
// 엉뚱한 색이 나온다. 그렇다고 늘 16색만 쓰면 요즘 터미널이 아깝다.
// 그래서 한 번 판별해 두고, 낼 수 없는 색은 가장 가까운 색으로 내려 맞춘다.
type Profile int

const (
	NoColor   Profile = iota // 색을 쓰지 않는다 (파이프로 내보낼 때, NO_COLOR, dumb 터미널)
	ANSI                     // 16색
	ANSI256                  // 256색
	TrueColor                // 24비트 (1,600만 색)
)

func (p Profile) String() string {
	switch p {
	case ANSI:
		return "16색"
	case ANSI256:
		return "256색"
	case TrueColor:
		return "24비트"
	}
	return "색 없음"
}

// Color 는 색 하나를 문자열로 적은 것이다. Lip Gloss 와 같은 방식이다.
//
//	"5"        팔레트 번호 (0–255)
//	"#ff00ff"  24비트 색
//	"#f0f"     세 자리 축약형
//	""         지정하지 않음
//
// 왜 문자열인가. 색을 구조체로 만들면 style.New().Foreground(...) 한 줄을 쓸 때마다
// 생성자를 불러야 한다. 문자열 상수면 그냥 적으면 된다 — 스타일을 선언하듯 쓰게 하는 것이
// 이 패키지의 목적이다.
type Color string

// rgb 는 색을 24비트 값으로 푼다. ok 가 거짓이면 알아볼 수 없는 색이다.
func (c Color) rgb() (r, g, b uint8, ok bool) {
	s := string(c)
	if !strings.HasPrefix(s, "#") {
		if i, ok2 := c.index(); ok2 {
			v := palette256[i]
			return uint8(v >> 16), uint8(v >> 8), uint8(v), true
		}
		return 0, 0, 0, false
	}
	h := s[1:]
	switch len(h) {
	case 3:
		// #abc 는 #aabbcc 와 같다.
		v, err := strconv.ParseUint(h, 16, 32)
		if err != nil {
			return 0, 0, 0, false
		}
		r = uint8((v>>8)&0xf) * 0x11
		g = uint8((v>>4)&0xf) * 0x11
		b = uint8(v&0xf) * 0x11
		return r, g, b, true
	case 6:
		v, err := strconv.ParseUint(h, 16, 32)
		if err != nil {
			return 0, 0, 0, false
		}
		return uint8(v >> 16), uint8(v >> 8), uint8(v), true
	}
	return 0, 0, 0, false
}

// index 는 팔레트 번호로 적힌 색을 숫자로 푼다.
func (c Color) index() (int, bool) {
	if c == "" || strings.HasPrefix(string(c), "#") {
		return 0, false
	}
	n, err := strconv.Atoi(string(c))
	if err != nil || n < 0 || n > 255 {
		return 0, false
	}
	return n, true
}

// Foreground 는 글자색 SGR 시퀀스를 만든다. 낼 수 없는 색이면 빈 문자열이다.
func (p Profile) Foreground(c Color) string { return wrapSGR(p.fgParams(c)) }

// Background 는 배경색 SGR 시퀀스를 만든다.
func (p Profile) Background(c Color) string { return wrapSGR(p.bgParams(c)) }

// fgParams/bgParams 는 시퀀스가 아니라 **매개변수만** 돌려준다.
//
// 왜 나눠 두는가. Style 은 굵게·밑줄·글자색·배경색을 한 시퀀스에 모아 보낸다
// ("\e[1;4;32;44m"). 완성된 시퀀스만 만들 줄 알면 그걸 다시 뜯어야 한다.
func (p Profile) fgParams(c Color) string { return p.params(c, false) }
func (p Profile) bgParams(c Color) string { return p.params(c, true) }

func wrapSGR(params string) string {
	if params == "" {
		return ""
	}
	return "\x1b[" + params + "m"
}

func (p Profile) params(c Color, bg bool) string {
	if p == NoColor || c == "" {
		return ""
	}
	// 팔레트 번호로 적혔고 터미널이 256색 이상이면 그대로 보낸다.
	if i, ok := c.index(); ok {
		switch {
		case p >= ANSI256:
			return base(bg, "38", "48") + ";5;" + strconv.Itoa(i)
		case i < 16:
			return ansi16(i, bg)
		default:
			return ansi16(nearest16(palette256[i]), bg)
		}
	}
	r, g, b, ok := c.rgb()
	if !ok {
		// 알아볼 수 없는 색. 화면이 깨지는 것보다 색이 없는 편이 낫다.
		return ""
	}
	v := uint32(r)<<16 | uint32(g)<<8 | uint32(b)
	switch p {
	case TrueColor:
		return base(bg, "38", "48") + ";2;" +
			strconv.Itoa(int(r)) + ";" + strconv.Itoa(int(g)) + ";" + strconv.Itoa(int(b))
	case ANSI256:
		return base(bg, "38", "48") + ";5;" + strconv.Itoa(nearest256(v))
	default:
		return ansi16(nearest16(v), bg)
	}
}

func base(bg bool, fg, bgs string) string {
	if bg {
		return bgs
	}
	return fg
}

// ansi16 은 0–15 번 색의 SGR 번호를 만든다.
// 앞 8개는 30–37(글자)/40–47(배경), 뒤 8개(밝은 색)는 90–97/100–107 이다.
// 90번대는 원래 표준에 없던 확장인데, 지금은 사실상 어디서나 통한다.
func ansi16(i int, bg bool) string {
	n := i
	if n >= 8 {
		n = n - 8 + 60 + 30
		if bg {
			n += 10
		}
		return strconv.Itoa(n)
	}
	n += 30
	if bg {
		n += 10
	}
	return strconv.Itoa(n)
}

// nearest256 은 24비트 색을 256색 팔레트에서 가장 가까운 번호로 바꾼다.
//
// 0–15 번은 터미널마다 사용자가 바꿔 쓰는 자리라 후보에서 뺀다 —
// "빨강" 을 눌렀는데 사용자 테마의 이상한 색이 나오면 그게 더 나쁘다.
// 16–231 은 6×6×6 정육면체, 232–255 는 회색 24단계다.
// O(1): 정육면체는 각 축을 따로 가장 가까운 눈금에 붙이고, 회색과 한 번만 견준다.
func nearest256(v uint32) int {
	r, g, b := int(v>>16&0xff), int(v>>8&0xff), int(v&0xff)
	ci := 16 + 36*cubeStep(r) + 6*cubeStep(g) + cubeStep(b)
	cd := dist(r, g, b, palette256[ci])

	// 회색 계단. 8, 18, 28 … 238 의 24단계.
	gi := (r + g + b) / 3
	step := (gi - 8 + 5) / 10
	if step < 0 {
		step = 0
	}
	if step > 23 {
		step = 23
	}
	gray := 232 + step
	if dist(r, g, b, palette256[gray]) < cd {
		return gray
	}
	return ci
}

// 정육면체의 눈금은 0, 95, 135, 175, 215, 255 다. 0 다음이 95로 확 뛰는 것은
// 어두운 쪽에서 사람 눈이 차이를 더 잘 느끼기 때문에 생긴 배치다.
var cubeLevels = [6]int{0, 95, 135, 175, 215, 255}

func cubeStep(v int) int {
	best, bd := 0, 1<<30
	for i, l := range cubeLevels {
		d := l - v
		if d < 0 {
			d = -d
		}
		if d < bd {
			best, bd = i, d
		}
	}
	return best
}

// nearest16 은 24비트 색을 16색 중 가장 가까운 번호로 바꾼다.
// 후보가 16개뿐이라 그냥 다 재 본다.
func nearest16(v uint32) int {
	r, g, b := int(v>>16&0xff), int(v>>8&0xff), int(v&0xff)
	best, bd := 0, 1<<30
	for i := 0; i < 16; i++ {
		if d := dist(r, g, b, palette256[i]); d < bd {
			best, bd = i, d
		}
	}
	return best
}

// dist 는 두 색이 사람 눈에 얼마나 달라 보이는지를 잰다(작을수록 비슷하다).
//
// 그냥 RGB 거리(ΔR²+ΔG²+ΔB²)를 쓰면 안 된다. 실제로 겪은 예: 256색의 205번
// (#FF5FAF, 분홍)을 16색으로 내려 맞출 때 RGB 거리는 "은색(#C0C0C0)" 을 고른다.
// 사람 눈에는 자홍(#FF00FF)이 훨씬 가깝다. 초록의 차이를 눈이 가장 민감하게 느끼는데
// RGB 거리는 세 축을 똑같이 취급하기 때문이다.
//
// 그래서 "redmean" 이라는 널리 쓰이는 근사식을 쓴다. 두 색의 빨강 평균에 따라
// 빨강·파랑 축의 무게를 옮기고, 초록에는 항상 큰 무게를 준다. CIE Lab 같은 제대로 된
// 색 공간을 쓰면 더 정확하지만 변환에 부동소수와 표가 필요하다 — 정수 곱셈 몇 번으로
// 실용적인 답이 나오는 이 식이 우리 목적에는 충분하다.
func dist(r, g, b int, v uint32) int {
	r2, g2, b2 := int(v>>16&0xff), int(v>>8&0xff), int(v&0xff)
	rmean := (r + r2) / 2
	dr, dg, db := r-r2, g-g2, b-b2
	return ((512+rmean)*dr*dr)>>8 + 4*dg*dg + ((767-rmean)*db*db)>>8
}

// DetectProfile 은 환경 변수와 "출력이 터미널인가" 로 색 수준을 정한다.
//
// env 를 인자로 받는 이유는 시험 때문이다. os.Getenv 를 직접 부르면 이 함수의 모든 갈래를
// 확인하려고 진짜 환경 변수를 건드려야 하고, 그러면 시험끼리 서로 간섭한다.
//
// 우선순위:
//  1. NO_COLOR 가 비어 있지 않으면 무조건 색 없음 (no-color.org 의 관례)
//  2. CLICOLOR_FORCE 가 "0" 이 아니면 터미널이 아니어도 색을 쓴다
//  3. 터미널이 아니면 색 없음 (파이프·파일로 나가는 글에 시퀀스를 섞지 않는다)
//  4. TERM 이 비었거나 "dumb" 이면 색 없음
//  5. COLORTERM 이 truecolor/24bit 면 24비트
//  6. TERM 에 "256color" 가 들어 있으면 256색
//  7. 그 밖에는 16색
func DetectProfile(env func(string) string, tty bool) Profile {
	if env("NO_COLOR") != "" {
		return NoColor
	}
	force := env("CLICOLOR_FORCE")
	if !tty && (force == "" || force == "0") {
		return NoColor
	}
	term := env("TERM")
	if term == "" || term == "dumb" {
		return NoColor
	}
	switch env("COLORTERM") {
	case "truecolor", "24bit":
		return TrueColor
	}
	if strings.Contains(term, "256color") {
		return ANSI256
	}
	return ANSI
}
