// bugs — 덱에 실을 "고치기 전 / 고친 뒤" 화면을 만들어 내는 프로그램.
//
//	go run ./cmd/bugs -kind width          고장 난 판
//	go run ./cmd/bugs -kind width -fixed   고친 판
//
// 종류: width(표 정렬), tick(시계 재예약), wrap(줄 넘침)
package main

import (
	"flag"
	"fmt"
	"os"

	"treasure/boricha/apps/bugs"
	"treasure/boricha/tea"
)

func main() {
	kind := flag.String("kind", "width", "함정 종류: width · tick · wrap")
	fixed := flag.Bool("fixed", false, "고친 판으로 돌린다")
	flag.Parse()

	var m tea.Model
	switch *kind {
	case "width":
		m = bugs.NewWidth(*fixed)
	case "tick":
		m = bugs.NewTick(*fixed)
	case "wrap":
		// 줄 넘침은 tea 로 재현할 수 없다 — 우리 렌더러가 이미 잘라 주기 때문이다.
		// 그래서 이 판만 프레임워크 없이 직접 그린다.
		if err := bugs.RunRawWrap(*fixed); err != nil {
			fmt.Fprintln(os.Stderr, "오류:", err)
			os.Exit(1)
		}
		return
	default:
		fmt.Fprintln(os.Stderr, "모르는 종류:", *kind)
		os.Exit(2)
	}

	// 줄 넘침 함정은 대체 화면에서 보아야 한다. 보통 화면에서는 셸의 스크롤백이
	// 밀린 줄을 흡수해 버려서, 무엇이 잘못됐는지 보이지 않는다.
	if _, err := tea.NewProgram(m, tea.WithAltScreen()).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}
