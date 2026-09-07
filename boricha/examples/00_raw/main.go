// 00_raw — 프레임워크 없이 손으로 짠 터미널 프로그램.
//
// 이 예제의 목적은 잘 도는 것이 아니라 **무엇이 힘든지 눈으로 보는 것**이다.
// 여기에는 Model 도 Update 도 View 도 없다. 읽고, 해석하고, 그리는 일을
// 한 함수 안에서 손으로 한다. 그 결과 다음 네 가지가 그대로 드러난다.
//
//  1. 방향키 한 번이 바이트 세 개로 온다 — 키가 아니라 바이트다
//  2. 화면 전체를 지우고 다시 그리므로 깜빡인다
//  3. 창 크기가 바뀌어도 모른다 — 크기는 시작할 때 한 번만 물었다
//  4. 어디서든 죽으면 터미널이 원시 모드인 채로 남는다 (셸에서 stty sane 이 필요해진다)
//
// 이 네 가지를 하나씩 없애는 과정이 곧 이 덱의 나머지 전부다.
package main

import (
	"fmt"
	"os"
	"strings"

	"treasure/boricha/term"
)

func main() {
	// 원시 모드로 바꾸는 일과 되돌리는 일만 term 패키지를 빌린다.
	// (그 안이 어떻게 생겼는지는 4부에서 한 비트씩 뜯어본다.)
	tm := term.New(os.Stdin, os.Stdout)
	if err := tm.MakeRaw(); err != nil {
		fmt.Fprintln(os.Stderr, "터미널이 아니다:", err)
		os.Exit(1)
	}
	// defer 를 걸어 두지만, 이 프로그램이 패닉으로 죽으면 defer 는 돌긴 해도
	// 패닉 메시지가 원시 모드 화면 위에 계단처럼 찍힌다. 그 장면은 4부에서 본다.
	defer tm.Restore()

	_ = tm.EnterAltScreen()
	_ = tm.HideCursor()
	defer tm.Cleanup()

	// 크기를 딱 한 번 묻는다. 이 프로그램은 창이 바뀌는 것을 끝내 모른다.
	cols, rows, err := tm.Size()
	if err != nil {
		cols, rows = 80, 24
	}

	var last []byte // 방금 받은 바이트들 — 화면에 그대로 보여 준다
	count := 0

	buf := make([]byte, 64)
	for {
		draw(tm, cols, rows, last, count)

		// 읽기는 여기서 막힌다. 키를 누르기 전까지 이 프로그램은 아무것도 못 한다 —
		// 시계도 못 보고, 배경 작업도 못 돌린다. 채널도 고루틴도 없기 때문이다.
		n, err := os.Stdin.Read(buf)
		if err != nil || n == 0 {
			return
		}
		last = append(last[:0], buf[:n]...)
		count++

		// "키"를 알아보는 유일한 방법이 바이트 비교다.
		// q 로 끝내고, Ctrl+C(0x03)도 직접 처리한다 — ISIG 를 껐으므로
		// 커널이 대신 죽여 주지 않는다. 이 줄을 빼먹으면 빠져나갈 길이 없다.
		if last[0] == 'q' || last[0] == 0x03 {
			return
		}
	}
}

// draw 는 화면 전체를 지우고 처음부터 다시 그린다.
//
// 이것이 가장 단순한 방법이고, 동시에 깜빡임의 원인이다. 지운 순간과 다시 그린 순간
// 사이에 터미널이 화면을 한 번 보여 주면, 사람 눈에는 검은 화면이 스친다.
// 6부의 렌더러는 "달라진 줄만" 다시 써서 이 틈을 없앤다.
func draw(tm *term.Term, cols, rows int, last []byte, count int) {
	var b strings.Builder
	b.WriteString(term.ClearScreen)
	b.WriteString(term.CursorTo(1, 1))

	line := func(s string) {
		// 줄을 넘기려면 "\r\n" 을 직접 써야 한다. OPOST 를 껐으므로 "\n" 은
		// 커서를 한 줄 내리기만 하고 1열로 되돌려 주지 않는다 — 그래서 계단이 생긴다.
		b.WriteString(s)
		b.WriteString("\r\n")
	}

	line("보리차 0단계 — 날것의 터미널  (q 로 끝내기)")
	line(strings.Repeat("─", min(cols, 60)))
	line(fmt.Sprintf("화면 크기: %d칸 × %d줄  (시작할 때 한 번만 물었다)", cols, rows))
	line(fmt.Sprintf("입력 횟수: %d", count))
	line("")

	if last == nil {
		line("아무 키나 눌러 보세요. 방향키도 눌러 보세요.")
	} else {
		line(fmt.Sprintf("받은 바이트 %d개: %s", len(last), hexes(last)))
		line(fmt.Sprintf("글자로 보면  : %q", string(last)))
		line("")
		if len(last) >= 3 && last[0] == 0x1b {
			line("→ ESC 로 시작하는 여러 바이트. 방향키 한 번이 바이트 세 개다.")
			line("  이걸 KeyLeft 하나로 바꾸는 것이 5부의 파서가 할 일이다.")
		}
	}
	_ = tm.WriteString(b.String())
}

func hexes(p []byte) string {
	parts := make([]string, len(p))
	for i, c := range p {
		parts[i] = fmt.Sprintf("%02X", c)
	}
	return strings.Join(parts, " ")
}
