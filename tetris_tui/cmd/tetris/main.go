// tetris — 터미널에서 도는 테트리스.
//
//	go run ./cmd/tetris                   1인용
//	go run ./cmd/tetris --seed 7          시드를 고정해서 같은 판을 다시
//
// 이 파일이 하는 일은 셋뿐이다: 깃발(flag)을 읽고, 모델을 하나 만들고,
// tea.NewProgram 에 넘겨 돌린다. 게임에 대해 아는 것이 하나도 없다 —
// 그게 Elm 아키텍처로 나눈 결과다.
package main

import (
	"flag"
	"fmt"
	"os"
	"time"

	tea "charm.land/bubbletea/v2"

	"treasure/tetris_tui/game"
)

func main() {
	mode := flag.String("mode", "1p", "모드: 1p")
	seed := flag.Uint("seed", 0, "판을 고정하는 시드 (0 이면 시계에서 뽑는다)")
	flag.Parse()

	opts := []game.Option{}
	if *seed != 0 {
		opts = append(opts, game.WithSeed(uint32(*seed)))
	} else {
		opts = append(opts, game.WithSeed(uint32(time.Now().UnixNano())))
	}

	var m tea.Model
	switch *mode {
	case "1p":
		m = game.New(opts...)
	default:
		fmt.Fprintf(os.Stderr, "모르는 모드 %q — 지금 쓸 수 있는 모드: 1p\n", *mode)
		os.Exit(2)
	}

	if _, err := tea.NewProgram(m).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "실행 실패:", err)
		os.Exit(1)
	}
}
