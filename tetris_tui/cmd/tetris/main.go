// tetris — 터미널에서 도는 테트리스.
//
//	go run ./cmd/tetris                              메뉴
//	go run ./cmd/tetris -mode 1p                     1인용
//	go run ./cmd/tetris -mode 2p                     같은 키보드로 둘이
//	go run ./cmd/tetris -mode ai -level hard         사람 대 AI
//	go run ./cmd/tetris -mode aivai -seed 7          AI 대 AI (구경용)
//
// 이 파일이 하는 일은 셋뿐이다: 깃발을 읽고, 모델을 하나 고르고,
// tea.NewProgram 에 넘겨 돌린다. 게임에 대해 아는 것이 하나도 없다 —
// 그게 Elm 아키텍처로 나눈 결과다.
package main

import (
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	tea "charm.land/bubbletea/v2"

	"treasure/tetris_tui/menu"
)

func main() {
	mode := flag.String("mode", "", "모드: 1p · 2p · ai · aivai (비우면 메뉴)")
	level := flag.String("level", "hard", "AI 난이도: easy · normal · hard · max")
	seed := flag.Uint("seed", 0, "판을 고정하는 시드 (0 이면 시계에서 뽑는다)")
	bestOf := flag.Int("bestof", 3, "대전 판수 (홀수)")
	flag.Parse()

	s := uint32(*seed)
	if s == 0 {
		s = uint32(time.Now().UnixNano())
	}

	m, err := pick(*mode, *level, s, *bestOf)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	if _, err := tea.NewProgram(m).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "실행 실패:", err)
		os.Exit(1)
	}
}

// pick 은 이름 하나로 화면을 고른다.
//
// 메뉴도 같은 이름을 쓴다 — 깃발로 들어가든 메뉴로 들어가든 같은 화면이 나와야 한다.
func pick(mode, level string, seed uint32, bestOf int) (tea.Model, error) {
	if mode == "" {
		return menu.New(seed, level, bestOf), nil
	}
	m, ok := menu.Build(mode, seed, level, bestOf)
	if !ok {
		return nil, fmt.Errorf("모르는 모드 %q — 쓸 수 있는 모드: %s",
			mode, strings.Join(menu.ModeNames(), " · "))
	}
	return m, nil
}
