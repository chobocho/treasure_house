// record — Bubble Tea 모델을 터미널 없이 돌려서 화면을 한 장씩 기록한다.
//
// 왜 필요한가. 덱에 "이렇게 보입니다" 하고 손으로 그린 화면을 실으면 그건 거짓말이 된다.
// 코드가 바뀌어도 그림은 안 바뀌기 때문이다. 그래서 화면은 전부 여기서 뽑는다 —
// 스크립트(키와 시간)를 정해 두고, 진짜 모델을 돌려서, 진짜 View 문자열을 저장한다.
//
//	go run ./tools/record -mode 1p -script "left left space wait" -out out/frames_1p.json
//
// 결정론이 이 도구의 전부다. 같은 스크립트를 두 번 돌리면 파일이 바이트까지 같아야
// `make record` 뒤의 git diff 가 비어 있고, 덱의 그림이 소스와 어긋나지 않는다.
// 그래서 시각(time.Now)도, 난수도 여기서는 쓰지 않는다. 틱은 스크립트가 준다.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"

	tea "charm.land/bubbletea/v2"
)

// TickMsg 는 레코더가 스스로 만들어 넣는 시간 진행 신호다.
//
// 진짜 프로그램에서는 tea.Tick 이 만든 메시지가 이 자리에 온다. 하지만 tea.Tick 은
// 실제로 잠을 자므로 기록에 쓸 수 없다 — 300프레임이면 30초가 걸린다.
// 그래서 모델은 "틱 메시지의 *타입*"만 보고 판단하도록 만들어져 있고,
// 레코더는 같은 타입을 시간 없이 즉시 밀어 넣는다.
type TickMsg struct{}

// Frame 하나 = 어떤 조작 직후의 화면 전체.
type Frame struct {
	I       int    `json:"i"`
	Label   string `json:"label"`
	Content string `json:"content"`
}

// Recording 은 한 번의 기록 전체. 덱의 프레임 재생기가 이 JSON 을 그대로 읽는다.
type Recording struct {
	Name   string  `json:"name"`
	Script string  `json:"script"`
	Frames []Frame `json:"frames"`
}

// 스텝 종류. 하나의 구조체에 종류 태그를 두는 편이 인터페이스보다 JSON 과 궁합이 좋다.
type stepKind int

const (
	stepKey stepKind = iota
	stepTick
	stepResize
)

type Step struct {
	Kind stepKind
	Name string // 키 이름 ("left", "space", "z" …) 또는 라벨
	W, H int    // stepResize 일 때만
}

// "100x40" 처럼 생긴 스텝은 창 크기 변경이다.
var sizeRe = regexp.MustCompile(`^(\d+)x(\d+)$`)

// 특수 키 이름 → Code. 여기 없는 한 글자짜리 이름은 그 글자 자체로 취급한다.
var specialKeys = map[string]rune{
	"left":      tea.KeyLeft,
	"right":     tea.KeyRight,
	"up":        tea.KeyUp,
	"down":      tea.KeyDown,
	"space":     tea.KeySpace,
	"enter":     tea.KeyEnter,
	"esc":       tea.KeyEscape,
	"tab":       tea.KeyTab,
	"backspace": tea.KeyBackspace,
	"f1":        tea.KeyF1,
}

// ParseScript 는 공백으로 나뉜 스크립트를 스텝 목록으로 바꾼다.
//
//	left right space   키 누르기
//	wait               틱 하나 (시간 진행)
//	100x40             창 크기 변경
//
// 모르는 낱말은 오류다. 조용히 무시하면 "왜 이 키가 기록에 없지?"로 한나절을 쓴다.
func ParseScript(s string) ([]Step, error) {
	var out []Step
	for _, tok := range strings.Fields(s) {
		switch {
		case tok == "wait":
			out = append(out, Step{Kind: stepTick, Name: "wait"})
		case sizeRe.MatchString(tok):
			m := sizeRe.FindStringSubmatch(tok)
			w, _ := strconv.Atoi(m[1])
			h, _ := strconv.Atoi(m[2])
			out = append(out, Step{Kind: stepResize, Name: tok, W: w, H: h})
		default:
			if _, ok := specialKeys[tok]; !ok && len([]rune(tok)) != 1 {
				return nil, fmt.Errorf("모르는 스텝: %q", tok)
			}
			out = append(out, Step{Kind: stepKey, Name: tok})
		}
	}
	return out, nil
}

// keyMsg 는 스텝 이름을 진짜 키 메시지로 바꾼다.
// Text 는 인쇄 가능한 문자에만 채운다 — 특수 키는 실제로도 비어 있기 때문이다(03_keys 참고).
func keyMsg(name string) tea.KeyPressMsg {
	if code, ok := specialKeys[name]; ok {
		return tea.KeyPressMsg{Code: code}
	}
	r := []rune(name)[0]
	return tea.KeyPressMsg{Code: r, Text: name}
}

// Run 은 모델에 스텝을 순서대로 먹이고 매번 화면을 한 장씩 남긴다.
//
// 첫 프레임은 아무것도 누르기 전의 화면이다. 이게 없으면 재생기에서
// "무엇이 어떻게 바뀌었나"의 출발점이 사라진다.
//
// Cmd 는 일부러 실행하지 않는다. 대부분의 Cmd 는 시간을 먹는 예약이라
// 기록의 결정론을 깨뜨린다. 시간이 필요한 모델은 TickMsg 를 직접 받도록 만들었고,
// 그 틱은 스크립트의 wait 가 준다.
func Run(name string, m tea.Model, steps []Step) Recording {
	rec := Recording{Name: name, Frames: []Frame{{I: 0, Label: "시작", Content: m.View().Content}}}
	var script []string
	for i, st := range steps {
		var msg tea.Msg
		switch st.Kind {
		case stepKey:
			msg = keyMsg(st.Name)
		case stepTick:
			msg = TickMsg{}
		case stepResize:
			msg = tea.WindowSizeMsg{Width: st.W, Height: st.H}
		}
		m, _ = m.Update(msg)
		rec.Frames = append(rec.Frames, Frame{I: i + 1, Label: st.Name, Content: m.View().Content})
		script = append(script, st.Name)
	}
	rec.Script = strings.Join(script, " ")
	return rec
}

// WriteRecording 은 들여쓴 JSON 으로 저장한다.
// 한 줄짜리로 쓰면 파일은 작아지지만 git diff 가 읽을 수 없는 물건이 된다 —
// 이 파일들은 커밋되고 리뷰되는 증거물이므로 읽히는 쪽이 중요하다.
func WriteRecording(path string, r Recording) error {
	raw, err := json.MarshalIndent(r, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(raw, '\n'), 0o644)
}

// 기록할 수 있는 모드의 등록부.
// 4~6단계에서 1인용·2인용·AI 대전 모델이 여기 등록된다.
var registry = map[string]func() tea.Model{}

func Lookup(name string) (func() tea.Model, bool) {
	f, ok := registry[name]
	return f, ok
}

func modes() []string {
	out := make([]string, 0, len(registry))
	for k := range registry {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

func main() {
	mode := flag.String("mode", "", "기록할 모드 이름")
	script := flag.String("script", "", "스크립트 (예: \"left left space wait\")")
	out := flag.String("out", "", "저장할 JSON 경로")
	flag.Parse()

	if *mode == "" {
		fmt.Fprintf(os.Stderr, "기록할 모드를 -mode 로 골라라. 등록된 모드: %s\n",
			strings.Join(modes(), " "))
		os.Exit(2)
	}
	newModel, ok := Lookup(*mode)
	if !ok {
		fmt.Fprintf(os.Stderr, "모르는 모드 %q. 등록된 모드: %s\n", *mode, strings.Join(modes(), " "))
		os.Exit(2)
	}
	steps, err := ParseScript(*script)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	rec := Run(*mode, newModel(), steps)
	if *out == "" {
		*out = "out/frames_" + *mode + ".json"
	}
	if err := WriteRecording(*out, rec); err != nil {
		fmt.Fprintln(os.Stderr, "저장 실패:", err)
		os.Exit(1)
	}
	fmt.Printf("%s — 프레임 %d장 → %s\n", *mode, len(rec.Frames), *out)
}
