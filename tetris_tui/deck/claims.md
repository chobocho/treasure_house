# claims.md — 이 덱이 하는 "우리 코드 밖의 주장"과 그 출처

이 저장소 안에서 확인할 수 있는 것(코드·테스트·기록)은 여기 적지 않는다.
바깥 세계에 대한 주장만 적는다. 확인은 2026-09-06 에 했다.

| # | 주장 | 출처 | 슬라이드 |
|---|------|------|----------|
| C1 | Bubble Tea 는 Evan Czaplicki 등의 The Elm Architecture 와 TJ Holowaychuk 의 go-tea 를 바탕으로 한다 | https://github.com/charmbracelet/bubbletea (README) · https://pkg.go.dev/github.com/charmbracelet/bubbletea | 2부 |
| C2 | pkg.go.dev 에 남아 있는 bubbletea 의 가장 오래된 공개 버전은 v0.7.0, 2020-05-26 | https://pkg.go.dev/github.com/charmbracelet/bubbletea?tab=versions | 2부 |
| C3 | SRS 는 Tetris Guideline 의 회전 표준이며, 회전 전이마다 킥 후보가 5개이고 I 조각만 다른 표를 쓴다 | https://tetris.wiki/Super_Rotation_System · https://harddrop.com/wiki/SRS | 4부 |
| C4 | 월킥과 SRS 는 2001년 Tetris Worlds 에서 도입됐다 | https://tetris.wiki/Super_Rotation_System | 4부 |
| C5 | 7-bag = 일곱 조각을 한 봉지에서 무작위로 모두 뽑은 뒤 다음 봉지를 채우는 방식이 Guideline 의 표준 랜더마이저다 | https://tetris.wiki/Tetris_Guideline | 4부 |
| C6 | Pierre Dellacherie 의 여섯 특징: 구멍 수, 착지 높이, 행 전이, 열 전이, 우물 누적, 지워진 칸(eroded cells) | https://ar5iv.labs.arxiv.org/html/1905.01652 (The Game of Tetris in Machine Learning) | 6부 |
| C7 | 행 전이는 한 줄을 끝에서 끝까지 훑을 때 "찬 칸↔빈 칸"이 뒤집히는 횟수, 열 전이는 열 방향으로 같은 것 | 같은 논문 | 6부 |
| C8 | ECMA-48 초판은 1976년, ANSI 가 X3.64 로 채택한 것은 1981년(1997년 철회) | https://en.wikipedia.org/wiki/ANSI_escape_code | 1부 |
| C9 | 이 시퀀스를 지원한 첫 인기 비디오 터미널은 1978년의 DEC VT100 | https://en.wikipedia.org/wiki/VT100 · https://en.wikipedia.org/wiki/ANSI_escape_code | 1부 |
| C10 | SGR 30–37 이 글자색, 40–47 이 배경색 | https://en.wikipedia.org/wiki/ANSI_escape_code | 1부 |
| C11 | 대체 화면 버퍼는 `ESC[?1049h` 로 들어가고 `ESC[?1049l` 로 나온다 | https://en.wikipedia.org/wiki/ANSI_escape_code | 1부 |
| C12 | 전통적인 터미널 입력에서는 Esc, Alt+[, Ctrl+[ 가 모두 같은 한 바이트(0x1b)로 온다 | https://sw.kovidgoyal.net/kitty/keyboard-protocol/ | 1부·7부 |
| C13 | Kitty 키보드 프로토콜은 누름·자동반복·뗌을 구분한다. 플래그 2를 켜면 `CSI … ; 수정자:이벤트종류 u` 형태로 오고 이벤트 종류 3이 "뗌"이다 | https://sw.kovidgoyal.net/kitty/keyboard-protocol/ | 7부 |
| C14 | Kitty 키보드 프로토콜을 지원하는 터미널로 kitty·alacritty·foot·ghostty·iTerm2·rio·WezTerm 이 알려져 있다 | https://sw.kovidgoyal.net/kitty/keyboard-protocol/ | 7부 |

## 확인하지 못한 것 (그래서 덱에 안 적은 것)

- Bubble Tea 의 **최초** 공개 시점. pkg.go.dev 에 v0.7.0(2020-05-26)이 가장 오래된 것으로
  남아 있을 뿐, 그 이전 태그가 있었는지는 확인하지 못했다. 그래서 덱에는
  "가장 오래된 공개 버전이 2020년 5월"이라고만 적는다.
- Charm(Charmbracelet)의 설립 연도. 찾지 못해 덱에서 아예 뺐다.
