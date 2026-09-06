package ui

import (
	"strings"

	"treasure/tetris_tui/core"
)

// 키 배치를 **데이터로** 둔다. 도움말 화면도, 덱의 조작표도, 실제 입력 처리도
// 전부 이 한 곳을 읽는다. 세 군데에 따로 적어 두면 반드시 어긋난다 —
// 그리고 어긋난 쪽은 늘 도움말이라, 사용자만 거짓말을 읽게 된다.

// Binding 하나 = 키 이름 여러 개 → 뜻 하나.
//
// 키 "이름"은 우리가 지어낸 게 아니라 Bubble Tea 의 msg.String() 이 만드는 값이다
// ("left", "ctrl+c", "a" …). 예제 03_keys 가 그걸 눈으로 확인하는 도구였다.
type Binding struct {
	Keys []string
	Act  core.Action
	Desc string
}

// KeyMap 은 한 자리(seat)의 키 배치.
type KeyMap struct {
	Name     string
	Bindings []Binding
}

// Lookup 은 키 이름으로 뜻을 찾는다.
//
// 바인딩이 열 개 남짓이라 선형 탐색으로 충분하다. map 을 만들면 초기화 순서와
// 전역 상태가 늘어나는데, 키 입력은 초당 수십 번뿐이라 얻는 게 없다.
func (k KeyMap) Lookup(key string) (core.Action, bool) {
	for _, b := range k.Bindings {
		for _, s := range b.Keys {
			if s == key {
				return b.Act, true
			}
		}
	}
	return 0, false
}

// keyLabel 은 키 이름을 화면에 보기 좋게 바꾼다.
var keyLabel = map[string]string{
	"left": "←", "right": "→", "up": "↑", "down": "↓",
	"space": "스페이스", "esc": "Esc", "f1": "F1",
}

func label(key string) string {
	if s, ok := keyLabel[key]; ok {
		return s
	}
	return key
}

// HelpLine 은 "←→ 이동 · ↓ 소프트드롭 · …" 같은 한 줄짜리 도움말을 만든다.
// 바인딩에서 자동으로 뽑으므로 배치를 바꾸면 도움말도 따라 바뀐다.
func (k KeyMap) HelpLine() string {
	parts := make([]string, 0, len(k.Bindings))
	for _, b := range k.Bindings {
		keys := make([]string, 0, len(b.Keys))
		for _, s := range b.Keys {
			keys = append(keys, label(s))
		}
		parts = append(parts, strings.Join(keys, "/")+" "+b.Desc)
	}
	return strings.Join(parts, " · ")
}

// Arrows 는 1인용과 2인용의 오른쪽 자리가 쓰는 화살표 배치.
//
// 회전에 ↑ 와 x 를 둘 다 두는 건 관례다. ↑ 는 직관적이고, x/z 짝은
// 시계·반시계를 한 손으로 누를 수 있어서 익숙해지면 더 빠르다.
var Arrows = KeyMap{
	Name: "화살표",
	Bindings: []Binding{
		{Keys: []string{"left"}, Act: core.ActLeft, Desc: "왼쪽"},
		{Keys: []string{"right"}, Act: core.ActRight, Desc: "오른쪽"},
		{Keys: []string{"down"}, Act: core.ActSoft, Desc: "소프트드롭"},
		{Keys: []string{"up", "x"}, Act: core.ActCW, Desc: "시계 회전"},
		{Keys: []string{"z"}, Act: core.ActCCW, Desc: "반시계 회전"},
		{Keys: []string{"space"}, Act: core.ActHard, Desc: "하드드롭"},
		{Keys: []string{"c"}, Act: core.ActHold, Desc: "홀드"},
	},
}

// Wasd 는 2인용의 왼쪽 자리가 쓰는 배치.
//
// 하드드롭이 f 인 이유: 스페이스는 한 손으로 누르기 애매한 데다 오른쪽 자리가 쓴다.
// 두 자리가 키를 하나라도 공유하면 한 번의 입력이 양쪽 판을 동시에 움직인다.
var Wasd = KeyMap{
	Name: "WASD",
	Bindings: []Binding{
		{Keys: []string{"a"}, Act: core.ActLeft, Desc: "왼쪽"},
		{Keys: []string{"d"}, Act: core.ActRight, Desc: "오른쪽"},
		{Keys: []string{"s"}, Act: core.ActSoft, Desc: "소프트드롭"},
		{Keys: []string{"w"}, Act: core.ActCW, Desc: "시계 회전"},
		{Keys: []string{"q"}, Act: core.ActCCW, Desc: "반시계 회전"},
		{Keys: []string{"f"}, Act: core.ActHard, Desc: "하드드롭"},
		{Keys: []string{"e"}, Act: core.ActHold, Desc: "홀드"},
	},
}

// Global 은 판과 무관한 조작. 어느 자리의 키맵에도 속하지 않는다.
type Global int

const (
	GlobalNone Global = iota
	GlobalPause
	GlobalQuit
	GlobalRestart
	GlobalHelp
)

// 전역 키. 두 자리의 배치와 겹치면 안 된다 —
// 겹치면 "왼쪽으로 옮기려 했는데 게임이 끝나는" 일이 벌어진다.
var globalBindings = []struct {
	Keys []string
	G    Global
	Desc string
}{
	{[]string{"p"}, GlobalPause, "일시정지"},
	{[]string{"r"}, GlobalRestart, "다시 시작"},
	{[]string{"f1"}, GlobalHelp, "도움말"},
	{[]string{"esc", "ctrl+c"}, GlobalQuit, "나가기"},
}

// LookupGlobal 은 전역 키를 찾는다.
func LookupGlobal(key string) Global {
	for _, b := range globalBindings {
		for _, s := range b.Keys {
			if s == key {
				return b.G
			}
		}
	}
	return GlobalNone
}

// GlobalHelpLine 은 전역 키의 한 줄 도움말.
func GlobalHelpLine() string {
	parts := make([]string, 0, len(globalBindings))
	for _, b := range globalBindings {
		keys := make([]string, 0, len(b.Keys))
		for _, s := range b.Keys {
			keys = append(keys, label(s))
		}
		parts = append(parts, strings.Join(keys, "/")+" "+b.Desc)
	}
	return strings.Join(parts, " · ")
}
