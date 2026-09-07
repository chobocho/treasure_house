package testkit

import (
	"reflect"
	"testing"
)

// 각본은 사람이 읽고 쓸 수 있어야 한다. 시험에도 쓰고, 화면 기록에도 쓰고,
// 덱의 슬라이드에도 그대로 실을 것이기 때문이다.
//
//	80x24        화면 크기 (맨 앞에 한 번)
//	j k q        한 글자는 그 글자를 친 것
//	<up> <enter> 꺾쇠 안은 특수키
//	"보리차"      따옴표 안은 그대로 친 글
//	.            한 틱 기다리기
//	.5           다섯 틱 기다리기
func TestParse(t *testing.T) {
	cases := []struct {
		name string
		in   string
		want []Step
	}{
		{"크기", "80x24", []Step{{Kind: "size", W: 80, H: 24}}},
		{"글자", "j k", []Step{{Kind: "key", Text: "j"}, {Kind: "key", Text: "k"}}},
		{"특수키", "<up> <enter>", []Step{{Kind: "special", Text: "up"}, {Kind: "special", Text: "enter"}}},
		{"따옴표", `"보리차"`, []Step{{Kind: "text", Text: "보리차"}}},
		{"공백 든 따옴표", `"보리차 한 잔"`, []Step{{Kind: "text", Text: "보리차 한 잔"}}},
		{"기다리기", ". .3", []Step{{Kind: "wait", N: 1}, {Kind: "wait", N: 3}}},
		{"섞기", `40x10 j <enter> "차" .2`, []Step{
			{Kind: "size", W: 40, H: 10},
			{Kind: "key", Text: "j"},
			{Kind: "special", Text: "enter"},
			{Kind: "text", Text: "차"},
			{Kind: "wait", N: 2},
		}},
		{"빈 각본", "", nil},
		{"줄바꿈과 여분 공백", "  j \n  k  ", []Step{{Kind: "key", Text: "j"}, {Kind: "key", Text: "k"}}},
		{"한글 한 글자", "한", []Step{{Kind: "key", Text: "한"}}},
	}
	for _, c := range cases {
		got, err := Parse(c.in)
		if err != nil {
			t.Errorf("%s: %v", c.name, err)
			continue
		}
		if !reflect.DeepEqual(got, c.want) {
			t.Errorf("%s: Parse(%q) = %#v\n원하는 값 %#v", c.name, c.in, got, c.want)
		}
	}
}

func TestParseErrors(t *testing.T) {
	for _, in := range []string{`"안 닫힌 따옴표`, "<모르는키>", "0x24", "80x0", ".x"} {
		if _, err := Parse(in); err == nil {
			t.Errorf("Parse(%q) 가 오류를 안 냈다", in)
		}
	}
}

// 각본의 한 걸음은 실제로 터미널이 보낼 바이트가 된다.
// 그래야 이 시험이 진짜 입력 경로(파서까지)를 그대로 지난다.
func TestStepBytes(t *testing.T) {
	cases := []struct {
		step Step
		want string
	}{
		{Step{Kind: "key", Text: "j"}, "j"},
		{Step{Kind: "key", Text: "한"}, "한"},
		{Step{Kind: "text", Text: "보리차"}, "보리차"},
		{Step{Kind: "special", Text: "up"}, "\x1b[A"},
		{Step{Kind: "special", Text: "down"}, "\x1b[B"},
		{Step{Kind: "special", Text: "left"}, "\x1b[D"},
		{Step{Kind: "special", Text: "right"}, "\x1b[C"},
		{Step{Kind: "special", Text: "enter"}, "\r"},
		{Step{Kind: "special", Text: "tab"}, "\t"},
		{Step{Kind: "special", Text: "esc"}, "\x1b"},
		{Step{Kind: "special", Text: "space"}, " "},
		{Step{Kind: "special", Text: "backspace"}, "\x7f"},
		{Step{Kind: "special", Text: "ctrl+c"}, "\x03"},
		{Step{Kind: "special", Text: "pgdown"}, "\x1b[6~"},
		{Step{Kind: "wait", N: 3}, ""},
		{Step{Kind: "size", W: 80, H: 24}, ""},
	}
	for _, c := range cases {
		if got := string(c.step.Bytes()); got != c.want {
			t.Errorf("%+v.Bytes() = %q, 원하는 값 %q", c.step, got, c.want)
		}
	}
}
