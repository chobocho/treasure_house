package ui

import (
	"strings"
	"testing"

	"treasure/tetris_tui/core"
)

// 두 키맵 모두 여덟 가지 뜻을 전부 갖고 있어야 한다.
// 하나라도 빠지면 그 자리의 플레이어만 홀드를 못 쓰는 식의 불공정이 생긴다.
func TestBothKeyMapsCoverEveryAction(t *testing.T) {
	want := []core.Action{
		core.ActLeft, core.ActRight, core.ActSoft,
		core.ActCW, core.ActCCW, core.ActHard, core.ActHold,
	}
	for _, km := range []KeyMap{Arrows, Wasd} {
		have := map[core.Action]bool{}
		for _, b := range km.Bindings {
			have[b.Act] = true
		}
		for _, a := range want {
			if !have[a] {
				t.Errorf("%s 배치에 액션 %d 가 없다", km.Name, a)
			}
		}
	}
}

// 한 키맵 안에서 같은 키가 두 번 나오면 안 된다.
func TestNoDuplicateKeysWithinAKeyMap(t *testing.T) {
	for _, km := range []KeyMap{Arrows, Wasd} {
		seen := map[string]bool{}
		for _, b := range km.Bindings {
			for _, k := range b.Keys {
				if seen[k] {
					t.Errorf("%s 배치에서 키 %q 가 두 번 쓰였다", km.Name, k)
				}
				seen[k] = true
			}
		}
	}
}

// 두 자리가 같은 키를 쓰면 2인용에서 한 키가 양쪽을 동시에 움직인다.
// 이게 2인용의 가장 흔한 버그다.
func TestTheTwoSeatsShareNoKeys(t *testing.T) {
	left := map[string]bool{}
	for _, b := range Wasd.Bindings {
		for _, k := range b.Keys {
			left[k] = true
		}
	}
	for _, b := range Arrows.Bindings {
		for _, k := range b.Keys {
			if left[k] {
				t.Errorf("키 %q 를 두 자리가 함께 쓴다", k)
			}
		}
	}
}

// 전역 키는 어느 자리의 키맵과도 겹치면 안 된다.
// 겹치면 "왼쪽으로 옮기려 했는데 게임이 끝나는" 일이 벌어진다.
func TestGlobalKeysDoNotCollideWithSeats(t *testing.T) {
	for _, km := range []KeyMap{Arrows, Wasd} {
		for _, b := range km.Bindings {
			for _, k := range b.Keys {
				if g := LookupGlobal(k); g != GlobalNone {
					t.Errorf("%s 배치의 키 %q 가 전역 키(%d)와 겹친다", km.Name, k, g)
				}
			}
		}
	}
}

func TestArrowLookup(t *testing.T) {
	cases := map[string]core.Action{
		"left":  core.ActLeft,
		"right": core.ActRight,
		"down":  core.ActSoft,
		"up":    core.ActCW,
		"x":     core.ActCW,
		"z":     core.ActCCW,
		"space": core.ActHard,
		"c":     core.ActHold,
	}
	for k, want := range cases {
		got, ok := Arrows.Lookup(k)
		if !ok {
			t.Errorf("화살표 배치에 키 %q 가 없다", k)
			continue
		}
		if got != want {
			t.Errorf("키 %q 가 액션 %d — %d 를 기대했다", k, got, want)
		}
	}
	if _, ok := Arrows.Lookup("없는키"); ok {
		t.Error("없는 키가 찾아졌다")
	}
}

func TestWasdLookup(t *testing.T) {
	cases := map[string]core.Action{
		"a": core.ActLeft,
		"d": core.ActRight,
		"s": core.ActSoft,
		"w": core.ActCW,
		"q": core.ActCCW,
		"f": core.ActHard,
		"e": core.ActHold,
	}
	for k, want := range cases {
		got, ok := Wasd.Lookup(k)
		if !ok {
			t.Errorf("WASD 배치에 키 %q 가 없다", k)
			continue
		}
		if got != want {
			t.Errorf("키 %q 가 액션 %d — %d 를 기대했다", k, got, want)
		}
	}
}

func TestGlobalKeys(t *testing.T) {
	cases := map[string]Global{
		"p":      GlobalPause,
		"esc":    GlobalQuit,
		"ctrl+c": GlobalQuit,
		"r":      GlobalRestart,
		"f1":     GlobalHelp,
		"g":      GlobalNone,
	}
	for k, want := range cases {
		if got := LookupGlobal(k); got != want {
			t.Errorf("전역 키 %q 가 %d — %d 를 기대했다", k, got, want)
		}
	}
}

// 도움말은 키맵에서 자동으로 만들어진다. 손으로 적으면 배치를 바꿨을 때 어긋난다.
func TestHelpLineIsGeneratedFromTheBindings(t *testing.T) {
	line := Arrows.HelpLine()
	for _, want := range []string{"←", "→", "왼쪽", "오른쪽", "하드드롭"} {
		if !strings.Contains(line, want) {
			t.Errorf("도움말에 %q 가 없다: %s", want, line)
		}
	}
	if !strings.Contains(Wasd.HelpLine(), "a") {
		t.Errorf("WASD 도움말에 a 가 없다: %s", Wasd.HelpLine())
	}
	if !strings.Contains(GlobalHelpLine(), "p") {
		t.Errorf("전역 도움말에 p 가 없다: %s", GlobalHelpLine())
	}
}

// 설명이 비어 있는 바인딩이 있으면 도움말에 빈칸이 생긴다.
func TestEveryBindingHasKeysAndDescription(t *testing.T) {
	for _, km := range []KeyMap{Arrows, Wasd} {
		for i, b := range km.Bindings {
			if len(b.Keys) == 0 {
				t.Errorf("%s 배치의 %d번 바인딩에 키가 없다", km.Name, i)
			}
			if b.Desc == "" {
				t.Errorf("%s 배치의 %d번 바인딩에 설명이 없다", km.Name, i)
			}
		}
	}
}
