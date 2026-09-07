package style

import "testing"

// 색은 SGR 매개변수로 나간다. 프로필마다 쓸 수 있는 문법이 다르므로,
// 같은 색이라도 터미널에 따라 다른 바이트가 된다.
func TestForegroundSequences(t *testing.T) {
	cases := []struct {
		p    Profile
		c    Color
		want string
	}{
		// 색을 못 내는 터미널에는 아무것도 안 보낸다. 빈 문자열이 곧 "안 함" 이다.
		{NoColor, "5", ""},
		{NoColor, "#ff0000", ""},

		// 16색: 0–7 은 30–37, 8–15 는 90–97(밝은 색).
		{ANSI, "0", "\x1b[30m"},
		{ANSI, "7", "\x1b[37m"},
		{ANSI, "8", "\x1b[90m"},
		{ANSI, "15", "\x1b[97m"},

		// 256색: 38;5;N
		{ANSI256, "205", "\x1b[38;5;205m"},
		{ANSI256, "0", "\x1b[38;5;0m"},

		// 24비트: 38;2;R;G;B
		{TrueColor, "#ff00ff", "\x1b[38;2;255;0;255m"},
		{TrueColor, "#000000", "\x1b[38;2;0;0;0m"},
		{TrueColor, "#abc", "\x1b[38;2;170;187;204m"}, // 세 자리 축약형

		// 프로필이 낮으면 내려 맞춘다. 24비트 색을 256색 터미널에 보내면
		// 대부분 무시되거나 엉뚱하게 나오므로, 가장 가까운 팔레트 번호로 바꾼다.
		{ANSI256, "#ff0000", "\x1b[38;5;196m"},
		{ANSI256, "#000000", "\x1b[38;5;16m"},
		{ANSI256, "#ffffff", "\x1b[38;5;231m"},
		{ANSI, "#ff0000", "\x1b[91m"},
		{ANSI, "#000000", "\x1b[30m"},
		{ANSI, "205", "\x1b[95m"},

		// 빈 색은 "지정 안 함".
		{TrueColor, "", ""},
		// 알아볼 수 없는 값도 조용히 무시한다 — 화면이 깨지는 것보다 색이 없는 편이 낫다.
		{TrueColor, "노랑", ""},
		{ANSI256, "999", ""},
	}
	for _, c := range cases {
		if got := c.p.Foreground(c.c); got != c.want {
			t.Errorf("%v.Foreground(%q) = %q, 원하는 값 %q", c.p, c.c, got, c.want)
		}
	}
}

func TestBackgroundSequences(t *testing.T) {
	cases := []struct {
		p    Profile
		c    Color
		want string
	}{
		{ANSI, "1", "\x1b[41m"},
		{ANSI, "9", "\x1b[101m"},
		{ANSI256, "205", "\x1b[48;5;205m"},
		{TrueColor, "#ff00ff", "\x1b[48;2;255;0;255m"},
		{NoColor, "1", ""},
	}
	for _, c := range cases {
		if got := c.p.Background(c.c); got != c.want {
			t.Errorf("%v.Background(%q) = %q, 원하는 값 %q", c.p, c.c, got, c.want)
		}
	}
}

// 프로필 판별은 환경 변수와 "출력이 터미널인가" 로 한다.
// 순수 함수로 만들어 두면 진짜 환경 없이도 전부 시험할 수 있다.
func TestDetectProfile(t *testing.T) {
	env := func(m map[string]string) func(string) string {
		return func(k string) string { return m[k] }
	}
	cases := []struct {
		name string
		vars map[string]string
		tty  bool
		want Profile
	}{
		{"터미널이 아니면 색 없음", map[string]string{"TERM": "xterm-256color"}, false, NoColor},
		{"NO_COLOR 는 무조건 이긴다", map[string]string{"TERM": "xterm-256color", "NO_COLOR": "1"}, true, NoColor},
		{"NO_COLOR 는 빈 값이면 안 켠 것", map[string]string{"TERM": "xterm-256color", "NO_COLOR": ""}, true, ANSI256},
		{"TERM 없음", map[string]string{}, true, NoColor},
		{"dumb", map[string]string{"TERM": "dumb"}, true, NoColor},
		{"기본 xterm 은 16색", map[string]string{"TERM": "xterm"}, true, ANSI},
		{"256color", map[string]string{"TERM": "xterm-256color"}, true, ANSI256},
		{"screen-256color", map[string]string{"TERM": "screen-256color"}, true, ANSI256},
		{"COLORTERM=truecolor", map[string]string{"TERM": "xterm-256color", "COLORTERM": "truecolor"}, true, TrueColor},
		{"COLORTERM=24bit", map[string]string{"TERM": "xterm", "COLORTERM": "24bit"}, true, TrueColor},
		// 파이프로 내보낼 때도 색을 켜고 싶은 경우(로그 도구 등)를 위한 관례.
		{"CLICOLOR_FORCE", map[string]string{"TERM": "xterm-256color", "CLICOLOR_FORCE": "1"}, false, ANSI256},
		{"CLICOLOR_FORCE=0 은 안 켠 것", map[string]string{"TERM": "xterm-256color", "CLICOLOR_FORCE": "0"}, false, NoColor},
	}
	for _, c := range cases {
		if got := DetectProfile(env(c.vars), c.tty); got != c.want {
			t.Errorf("%s: = %v, 원하는 값 %v", c.name, got, c.want)
		}
	}
}

func TestProfileString(t *testing.T) {
	want := map[Profile]string{NoColor: "색 없음", ANSI: "16색", ANSI256: "256색", TrueColor: "24비트"}
	for p, w := range want {
		if got := p.String(); got != w {
			t.Errorf("%d.String() = %q, 원하는 값 %q", int(p), got, w)
		}
	}
}
