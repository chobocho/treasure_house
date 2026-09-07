// Package testkit 은 터미널 없이, 시계 없이, 고루틴 없이 모델을 돌린다.
//
// 왜 필요한가. 진짜 Program 은 고루틴 셋과 시계 위에서 돈다. 그 둘은 결정론의 적이다 —
// 같은 각본을 두 번 돌려도 사건이 다른 순서로 도착할 수 있다. 시험과 화면 기록에는
// "두 번 돌리면 바이트까지 같다" 가 필요하다.
//
// 그래서 여기서는 Program 과 **같은 규칙** 으로 도는 작은 루프를 다시 쓴다.
// 사건을 하나씩 Update 에 넣고, 돌려받은 명령을 그 자리에서(순서대로) 돌리고,
// 걸음마다 View 를 프레임으로 남긴다. 진짜 Program 과 결과가 같은지는
// testkit_test.go 의 "두 길 대조" 시험이 지켜본다.
package testkit

import (
	"fmt"
	"strconv"
	"strings"
)

// Step 은 각본의 한 걸음이다.
type Step struct {
	Kind string // size · key · special · text · wait
	Text string
	N    int
	W, H int
}

// Parse 는 사람이 읽고 쓰는 각본을 걸음 목록으로 바꾼다.
//
// 문법은 일부러 아주 작게 뒀다. 이 각본은 시험에도 쓰고, 화면 기록에도 쓰고,
// 덱의 슬라이드에도 그대로 실린다. 읽는 사람이 문법을 배우느라 멈추면 안 된다.
//
//	80x24         화면 크기 (맨 앞에 한 번)
//	j k q         한 글자는 그 글자를 친 것
//	<up> <enter>  꺾쇠 안은 특수키
//	"보리차"       따옴표 안은 그대로 친 글 (공백을 넣을 수 있다)
//	.  .5         한 틱 / 다섯 틱 기다리기 (명령이 돌 틈을 준다)
func Parse(script string) ([]Step, error) {
	var out []Step
	toks, err := tokens(script)
	if err != nil {
		return nil, err
	}
	for _, t := range toks {
		switch {
		case t.quoted:
			out = append(out, Step{Kind: "text", Text: t.s})

		case strings.HasPrefix(t.s, "<") && strings.HasSuffix(t.s, ">"):
			name := t.s[1 : len(t.s)-1]
			if _, ok := specials[name]; !ok {
				return nil, fmt.Errorf("각본: 모르는 특수키 %q", name)
			}
			out = append(out, Step{Kind: "special", Text: name})

		case strings.HasPrefix(t.s, "."):
			n := 1
			if rest := t.s[1:]; rest != "" {
				v, err := strconv.Atoi(rest)
				if err != nil || v < 1 {
					return nil, fmt.Errorf("각본: 기다리는 횟수가 이상하다 %q", t.s)
				}
				n = v
			}
			out = append(out, Step{Kind: "wait", N: n})

		default:
			if w, h, ok := parseSize(t.s); ok {
				if w < 1 || h < 1 {
					return nil, fmt.Errorf("각본: 화면 크기가 이상하다 %q", t.s)
				}
				out = append(out, Step{Kind: "size", W: w, H: h})
				continue
			}
			// 남은 것은 글자 하나씩 친 것으로 본다.
			for _, r := range t.s {
				out = append(out, Step{Kind: "key", Text: string(r)})
			}
		}
	}
	return out, nil
}

type token struct {
	s      string
	quoted bool
}

func tokens(s string) ([]token, error) {
	var out []token
	i := 0
	for i < len(s) {
		c := s[i]
		switch {
		case c == ' ' || c == '\t' || c == '\n' || c == '\r':
			i++
		case c == '"':
			j := strings.IndexByte(s[i+1:], '"')
			if j < 0 {
				return nil, fmt.Errorf("각본: 따옴표가 안 닫혔다")
			}
			out = append(out, token{s: s[i+1 : i+1+j], quoted: true})
			i += j + 2
		default:
			j := i
			for j < len(s) && s[j] != ' ' && s[j] != '\t' && s[j] != '\n' && s[j] != '\r' {
				j++
			}
			out = append(out, token{s: s[i:j]})
			i = j
		}
	}
	return out, nil
}

// parseSize 는 "80x24" 를 푼다. 숫자가 아니면 크기가 아니다.
func parseSize(s string) (int, int, bool) {
	i := strings.IndexByte(s, 'x')
	if i <= 0 || i == len(s)-1 {
		return 0, 0, false
	}
	w, err1 := strconv.Atoi(s[:i])
	h, err2 := strconv.Atoi(s[i+1:])
	if err1 != nil || err2 != nil {
		return 0, 0, false
	}
	return w, h, true
}

// specials 는 특수키 이름을 터미널이 실제로 보내는 바이트로 옮긴다.
//
// 이름과 바이트를 여기 한 번만 적어 두면, 각본이 진짜 입력 경로(파서까지)를
// 그대로 지난다. 파서를 건너뛰고 KeyMsg 를 바로 만들어 넣으면, 파서에 있는 버그를
// 이 도구로는 영영 못 찾는다.
var specials = map[string]string{
	"up": "\x1b[A", "down": "\x1b[B", "right": "\x1b[C", "left": "\x1b[D",
	"home": "\x1b[H", "end": "\x1b[F",
	"pgup": "\x1b[5~", "pgdown": "\x1b[6~",
	"insert": "\x1b[2~", "delete": "\x1b[3~",
	"enter": "\r", "tab": "\t", "esc": "\x1b", "space": " ", "backspace": "\x7f",
	"shift+tab": "\x1b[Z",
	"f1":        "\x1bOP", "f2": "\x1bOQ", "f3": "\x1bOR", "f4": "\x1bOS",
	"f5": "\x1b[15~", "f6": "\x1b[17~", "f7": "\x1b[18~", "f8": "\x1b[19~",
	"f9": "\x1b[20~", "f10": "\x1b[21~", "f11": "\x1b[23~", "f12": "\x1b[24~",
	"ctrl+a": "\x01", "ctrl+c": "\x03", "ctrl+d": "\x04", "ctrl+e": "\x05",
	"ctrl+k": "\x0b", "ctrl+u": "\x15", "ctrl+w": "\x17",
}

// Bytes 는 이 걸음이 터미널에서 왔다면 어떤 바이트였을지 돌려준다.
// 크기·기다리기는 바이트가 없다.
func (s Step) Bytes() []byte {
	switch s.Kind {
	case "key", "text":
		return []byte(s.Text)
	case "special":
		return []byte(specials[s.Text])
	}
	return nil
}
