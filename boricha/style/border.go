package style

// Border 는 상자를 그릴 글자 여덟 개다.
//
// 왜 글자를 구조체에 담는가. 테두리 모양을 코드에 박아 두면 "둥근 모서리로 바꿔 줘" 라는
// 요청에 렌더러를 고쳐야 한다. 모양이 값이면 부르는 쪽이 골라 넣기만 하면 된다.
type Border struct {
	Top, Bottom, Left, Right                   string
	TopLeft, TopRight, BottomLeft, BottomRight string
}

// 미리 만들어 둔 모양들.
//
// 여기 쓰인 박스 그리기 문자(U+2500 부터)는 East_Asian_Width 가 "모호(A)" 다.
// 우리는 그것을 1칸으로 센다(width 패키지 참고). 2칸으로 세는 순간 이 모든 상자가
// 두 배로 벌어진다 — 한글 TUI 에서 상자가 깨지는 가장 흔한 원인이 바로 이 판단이다.
var (
	NormalBorder  = Border{"─", "─", "│", "│", "┌", "┐", "└", "┘"}
	RoundedBorder = Border{"─", "─", "│", "│", "╭", "╮", "╰", "╯"}
	ThickBorder   = Border{"━", "━", "┃", "┃", "┏", "┓", "┗", "┛"}
	DoubleBorder  = Border{"═", "═", "║", "║", "╔", "╗", "╚", "╝"}

	// 박스 문자가 없는 환경(로그 파일, 옛 터미널)을 위한 대비책.
	ASCIIBorder = Border{"-", "-", "|", "|", "+", "+", "+", "+"}

	// 자리는 차지하되 보이지 않는 테두리. 여러 상자의 높이를 맞출 때 쓴다.
	HiddenBorder = Border{" ", " ", " ", " ", " ", " ", " ", " "}
)
