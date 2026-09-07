// Package widgets 는 앱을 만들 때 늘 다시 쓰게 되는 부품들을 모아 둔 것이다.
//
// 부품은 전부 앱과 **똑같은 모양** 을 하고 있다: 값인 모델, Update, View.
// 다른 점은 Update 가 tea.Model 이 아니라 자기 자신의 타입을 돌려준다는 것뿐이다.
// 그래야 부모가 그 결과를 자기 필드에 그대로 넣을 수 있다.
//
//	m.input, cmd = m.input.Update(msg)   // ← 돌려받은 값을 다시 넣는 것을 잊으면
//	                                     //   입력이 한 글자도 안 들어간다
//
// 인터페이스로 묶지 않은 이유도 같다. tea.Model 로 묶으면 돌려받은 것을 매번
// 타입 단언으로 되돌려야 한다.
package widgets

// Binding 은 키 하나(또는 여럿)와 그 설명을 묶은 것이다.
//
// 왜 이런 것이 필요한가. 키 처리는 Update 에, 도움말 문구는 View 에 흩어져 있으면
// 키를 바꿀 때마다 도움말 고치는 것을 잊는다. 반드시 잊는다.
// 배치를 값 하나로 두면 두 곳이 같은 출처를 보게 된다.
type Binding struct {
	// Keys 는 이 배치가 받아들이는 키 이름들(tea.KeyMsg.String() 의 값).
	Keys []string
	// Help 는 {키 표시, 설명}. 도움말 줄이 이걸 그대로 쓴다.
	Help [2]string

	disabled bool
}

// NewBinding 은 배치를 만든다. keys 는 tea.KeyMsg.String() 이 내놓는 이름 그대로다.
func NewBinding(keyHelp, desc string, keys ...string) Binding {
	return Binding{Keys: keys, Help: [2]string{keyHelp, desc}}
}

// Matches 는 눌린 키가 이 배치에 해당하는지 본다. 꺼 둔 배치는 절대 맞지 않는다.
func (b Binding) Matches(key string) bool {
	if b.disabled {
		return false
	}
	for _, k := range b.Keys {
		if k == key {
			return true
		}
	}
	return false
}

// Enabled 는 이 배치가 지금 쓸 수 있는지.
func (b Binding) Enabled() bool { return !b.disabled }

// SetEnabled 는 켜고 끈 **복사본** 을 돌려준다.
//
// 목록이 비었을 때 "지우기" 를 막는 것과 도움말에서 숨기는 것을 한 번에 처리한다.
// 값이므로 원본은 그대로다 — 부품이 전부 값 의미론을 지키는 것과 같은 이유다.
func (b Binding) SetEnabled(v bool) Binding {
	b.disabled = !v
	return b
}
