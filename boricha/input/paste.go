package input

// PasteMsg 는 붙여넣기로 들어온 글 덩어리 하나.
type PasteMsg string

// FocusMsg / BlurMsg 는 터미널 창이 앞으로 오거나 뒤로 갈 때.
type FocusMsg struct{}
type BlurMsg struct{}

// UnknownMsg 는 우리가 알아보지 못한 시퀀스 그대로.
type UnknownMsg string
