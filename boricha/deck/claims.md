# claims.md — 이 덱이 하는 "사실 주장" 과 그 근거

규칙: 연도·표준 번호·남의 소프트웨어에 대한 주장은 전부 여기 적고 출처를 남긴다.
확인하지 못한 것은 슬라이드에 쓰지 않는다. 확인했지만 이 기계에서 돌려 보지 못한 것은
"돌려 보지 못했다" 고 함께 적는다.

| # | 주장 | 근거 | 실린 곳 |
|---|------|------|---------|
| 1 | VT100 은 1978년 8월 DEC 이 내놓은 영상 단말기이고, ANSI 이스케이프 코드를 지원한 첫 인기 단말기다 | <https://en.wikipedia.org/wiki/VT100> | 1부 "터미널은 왜 이렇게 생겼나" |
| 2 | ANSI X3.64 는 1981년 FIPS 86 으로 미국 정부 표준에 채택됐다 | <https://en.wikipedia.org/wiki/ANSI_escape_code> | 1부 "표준의 계보" |
| 3 | CSI 문법(매개변수 0x30–0x3F, 중간 0x20–0x2F, 마지막 0x40–0x7E)은 ECMA-48 이 정한 것이다 | <https://www.ecma-international.org/publications-and-standards/standards/ecma-48/> · <https://invisible-island.net/xterm/ctlseqs/ctlseqs.html> | 1부 "CSI 문법", 5부 파서 |
| 4 | DEC 사설 모드 1049 = 대체 화면 버퍼 | <https://invisible-island.net/xterm/ctlseqs/ctlseqs.html> | 1부, 4부 |
| 5 | DEC 사설 모드 2004 = 괄호 붙은 붙여넣기. 붙여넣은 글이 `ESC[200~` … `ESC[201~` 로 감싸인다 | <https://invisible-island.net/xterm/xterm-paste64.html> · <https://en.wikipedia.org/wiki/Bracketed-paste> | 1부, 5부 |
| 6 | DEC 사설 모드 1006 = SGR 마우스 인코딩(xterm 확장) | <https://invisible-island.net/xterm/ctlseqs/ctlseqs.html> | 5부 마우스 |
| 7 | DEC 사설 모드 2026 = 동기화 출력. 켜는 동안 터미널이 화면 갱신을 미뤄 찢어짐을 막는다 | <https://github.com/contour-terminal/vt-extensions/blob/master/synchronized-output.md> | 6부 렌더러 |
| 8 | kitty 키보드 프로토콜은 옛 인코딩의 모호함을 없애는 점진적 확장이며, 기본값은 옛 터미널과 같은 바이트를 낸다 | <https://sw.kovidgoyal.net/kitty/keyboard-protocol/> | 5부 "우리가 안 만든 것" |
| 9 | UAX #11 은 각 문자에 Ambiguous·Fullwidth·Halfwidth·Narrow·Wide·Neutral 여섯 값 중 하나를 준다. 모호(A)는 문맥이 있어야 폭이 정해진다 | <http://www.unicode.org/reports/tr11/> | 7부 글자 폭 |
| 10 | wcwidth 의 널리 쓰이는 구현은 Markus Kuhn 이 UAX #11 을 바탕으로 쓴 것이다 | <https://www.cl.cam.ac.uk/~mgk25/ucs/wcwidth.c> | 7부 |
| 11 | Bubble Tea 는 Elm 아키텍처(Evan Czaplicki)와 TJ Holowaychuk 의 go-tea 에서 왔다 | <https://github.com/charmbracelet/bubbletea> | 2부 |
| 12 | Bubble Tea 가 Go 모듈로 처음 공개된 판은 v0.7.0, 2020년 5월 26일이다 | <https://pkg.go.dev/github.com/charmbracelet/bubbletea?tab=versions> | 2부 |
| 13 | Bubble Tea v2 의 Model 은 `Init() Cmd` · `Update(Msg) (Model, Cmd)` · `View() View` 다. View 가 구조체라는 점이 v1 과 다르다 | 이 기계의 모듈 캐시에서 `go doc charm.land/bubbletea/v2.Model`, `.View` | 2부, 12부 |
| 14 | Bubble Tea v2 의 키 이름은 조합키를 ctrl → alt → shift 순으로 적고, `enter tab backspace esc space up down left right home end pgup pgdown insert delete f1..f12` 를 쓴다 | 모듈 캐시의 ultraviolet `key.go` 의 `Keystroke()` 와 `keyTypeString` | 5부, 12부 |
| 15 | Bubble Tea v2 는 특수키를 `unicode.MaxRune + 1` 너머의 rune 으로 나타낸다(`KeyExtended`) | 모듈 캐시의 ultraviolet `key.go` | 5부 |
| 16 | Bubble Tea 의 `Tick`·`Every` 는 한 번만 울린다. 되풀이하려면 다시 걸어야 한다 | `go doc charm.land/bubbletea/v2.Tick`, `.Every` (문서에 "Beginners' note" 로 명시) | 3부, 12부 |
| 17 | 리눅스 `syscall` 패키지에는 `Winsize` 타입이 없다. `TIOCGWINSZ` 로 채울 구조체를 직접 정의해야 한다 | 이 기계에서 `go doc syscall` 확인 (linux/arm64, go 1.27) | 4부 |
| 18 | macOS 는 termios 를 `TIOCGETA`/`TIOCSETA` 로 읽고 쓰고, 구조체 필드가 uint64 다(리눅스는 `TCGETS`/`TCSETS`, uint32) | Go 소스의 `zerrors_darwin_arm64.go`, `go doc syscall.Termios` 를 GOOS 별로 | 4부 |
| 19 | D2Coding 은 SIL OFL 1.1 이고, 라틴·박스·블록이 반각(500), 한글이 전각(1000)이다 | 글꼴 파일의 `name` 표와 `hmtx` 를 fontTools 로 직접 확인 | 7부, 13부 |
| 20 | D2Coding 은 동그라미 숫자(U+2460~)를 전각(1000)으로 그린다 — 우리 표는 모호(A)를 1칸으로 센다 | 같은 방법으로 확인 (`deck/gen_fonts.py` 가 빌드마다 경고로 남긴다) | 7부 |

## 돌려 보지 못한 것

- **macOS**: `term/termios_darwin.go` 는 `GOOS=darwin GOARCH=arm64 go build` 로 컴파일만 확인했다.
  실행해 본 적이 없다. 슬라이드에도 그렇게 적는다.
- **윈도우**: `term/term_windows.go` 는 `ErrUnsupported` 를 돌려주는 스텁이다. 콘솔 API 로
  같은 일을 하려면 무엇이 필요한지는 4부의 슬라이드 한 장으로만 다룬다.
- **경합 검출기**: `-race` 는 android/arm64 에서 지원하지 않는다(`-race is not supported on
  android/arm64`). 동시성은 설계와 타이밍 시험으로만 논증했다.
