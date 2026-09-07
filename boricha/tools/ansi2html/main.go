// ansi2html — 터미널 화면(ANSI 이스케이프가 섞인 문자열)을 덱에 실을 HTML 로 바꾼다.
//
//	go run ./tools/ansi2html -in out/frames_1p.json -out out/frames_1p.html.json
//	go run ./tools/ansi2html -in out/tmux_1p.txt   -out out/tmux_1p.html
//
// 왜 브라우저에서 안 풀고 여기서 푸는가. 덱 안의 재생기(deck/player.js)를 80줄쯤으로
// 유지하고 싶기 때문이다. ANSI 파서는 생각보다 손이 많이 가고, 한 번만 돌면 되는 일을
// 화면을 넘길 때마다 다시 할 이유가 없다. 미리 풀어 두면 재생기는 문자열을 갈아 끼우기만 한다.
//
// 색은 클래스가 아니라 인라인 style 로 적는다. 터미널 화면은 "그 터미널이 낸 색"
// 그대로여야 증거가 된다 — 덱의 배색으로 바꿔치기하면 그건 더 이상 캡처가 아니다.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"html"
	"os"
	"strconv"
	"strings"
	"unicode"
)

// Frame 은 tools/record 가 남긴 프레임 하나. 필드 이름을 그쪽과 맞춰 둔다.
type Frame struct {
	I       int    `json:"i"`
	Label   string `json:"label"`
	Content string `json:"content"`
}

// Recording 은 프레임 묶음.
type Recording struct {
	Name   string  `json:"name"`
	Script string  `json:"script"`
	Frames []Frame `json:"frames"`
}

// LineDiff 는 "이 줄이 이렇게 바뀌었다" 한 개.
//
// JSON 에는 [줄번호, HTML] 두 칸짜리 배열로 나간다. 키 이름("y", "html")을
// 수만 번 되풀이하지 않으려는 것이다 — 프레임 수백 장이면 그것만으로 수백 KB 다.
type LineDiff struct {
	Y    int
	HTML string
}

func (d LineDiff) MarshalJSON() ([]byte, error) {
	return json.Marshal([]any{d.Y, d.HTML})
}

func (d *LineDiff) UnmarshalJSON(b []byte) error {
	var raw []any
	if err := json.Unmarshal(b, &raw); err != nil {
		return err
	}
	if len(raw) != 2 {
		return fmt.Errorf("줄 차이는 두 칸이어야 한다: %s", b)
	}
	y, _ := raw[0].(float64)
	h, _ := raw[1].(string)
	d.Y, d.HTML = int(y), h
	return nil
}

// HTMLFrame 은 변환된 프레임 하나.
//
// 화면을 통째로 담지 않고 **앞 프레임과 달라진 줄만** 담는다.
// 터미널 화면은 프레임 사이에 대부분 그대로다 — 조각 하나가 한 칸 내려갈 뿐인데
// 24줄을 전부 저장하면 파일이 열 배로 부푼다.
// (Bubble Tea 의 렌더러도 같은 이유로 바뀐 줄만 다시 그린다)
type HTMLFrame struct {
	I     int        `json:"i"`
	Label string     `json:"label"`
	N     int        `json:"n"` // 이 프레임의 총 줄 수
	D     []LineDiff `json:"d"`
}

// HTMLRecording 은 덱이 읽는 형식. Cols/Rows 는 재생기가 자리를 미리 잡는 데 쓴다.
//
// Styles 는 클래스 이름 → CSS 표다. 같은 색이 프레임마다 수백 번 되풀이되는데
// 그때마다 style="color:#5050a0;" 를 적으면 파일이 두 배 이상 커진다.
type HTMLRecording struct {
	Name   string            `json:"name"`
	Script string            `json:"script"`
	Cols   int               `json:"cols"`
	Rows   int               `json:"rows"`
	Styles map[string]string `json:"styles"`
	Frames []HTMLFrame       `json:"frames"`
}

// classTable 은 CSS 조각에 짧은 클래스 이름을 붙여 준다.
type classTable struct {
	idx map[string]string
}

func newClassTable() *classTable { return &classTable{idx: map[string]string{}} }

func (t *classTable) class(css string) string {
	if c, ok := t.idx[css]; ok {
		return c
	}
	c := "a" + strconv.Itoa(len(t.idx))
	t.idx[css] = c
	return c
}

// styles 는 클래스 → CSS 로 뒤집은 표.
func (t *classTable) styles() map[string]string {
	out := make(map[string]string, len(t.idx))
	for css, c := range t.idx {
		out[c] = css
	}
	return out
}

// style 은 지금까지 쌓인 SGR 상태.
type style struct {
	fg, bg    string
	bold      bool
	faint     bool
	underline bool
}

func (s style) css() string {
	var b strings.Builder
	if s.fg != "" {
		b.WriteString("color:" + s.fg + ";")
	}
	if s.bg != "" {
		b.WriteString("background:" + s.bg + ";")
	}
	if s.bold {
		b.WriteString("font-weight:700;")
	}
	if s.faint {
		b.WriteString("opacity:.55;")
	}
	if s.underline {
		b.WriteString("text-decoration:underline;")
	}
	return b.String()
}

// 기본 16색. xterm 의 관례값이다.
var basic16 = [16]string{
	"#000000", "#cd0000", "#00cd00", "#cdcd00",
	"#0000ee", "#cd00cd", "#00cdcd", "#e5e5e5",
	"#7f7f7f", "#ff0000", "#00ff00", "#ffff00",
	"#5c5cff", "#ff00ff", "#00ffff", "#ffffff",
}

// xterm256 은 256색 인덱스를 #rrggbb 로 푼다.
//
//	0~15    기본 16색
//	16~231  6×6×6 색 큐브
//	232~255 24단계 회색
func xterm256(n int) string {
	switch {
	case n < 0 || n > 255:
		return ""
	case n < 16:
		return basic16[n]
	case n < 232:
		n -= 16
		lv := [6]int{0, 95, 135, 175, 215, 255}
		return fmt.Sprintf("#%02x%02x%02x", lv[n/36], lv[(n/6)%6], lv[n%6])
	default:
		v := 8 + (n-232)*10
		return fmt.Sprintf("#%02x%02x%02x", v, v, v)
	}
}

// applySGR 은 SGR 파라미터 목록을 스타일에 적용한다.
//
// 38/48 뒤에는 색 지정이 이어진다: `38;2;R;G;B`(24비트) 또는 `38;5;N`(256색).
// 그래서 파라미터를 하나씩 보는 게 아니라 커서를 옮겨 가며 읽는다.
func applySGR(s style, params []int) style {
	if len(params) == 0 {
		return style{}
	}
	for i := 0; i < len(params); i++ {
		p := params[i]
		switch {
		case p == 0:
			s = style{}
		case p == 1:
			s.bold = true
		case p == 2:
			s.faint = true
		case p == 4:
			s.underline = true
		case p == 22:
			s.bold, s.faint = false, false
		case p == 24:
			s.underline = false
		case p == 39:
			s.fg = ""
		case p == 49:
			s.bg = ""
		case p >= 30 && p <= 37:
			s.fg = basic16[p-30]
		case p >= 40 && p <= 47:
			s.bg = basic16[p-40]
		case p >= 90 && p <= 97:
			s.fg = basic16[p-90+8]
		case p >= 100 && p <= 107:
			s.bg = basic16[p-100+8]
		case p == 38 || p == 48:
			c, used := readColor(params[i+1:])
			if used == 0 {
				return s
			}
			if p == 38 {
				s.fg = c
			} else {
				s.bg = c
			}
			i += used
		}
	}
	return s
}

// readColor 는 38/48 뒤에 오는 색 지정을 읽고, 소비한 파라미터 수를 돌려준다.
func readColor(rest []int) (string, int) {
	if len(rest) == 0 {
		return "", 0
	}
	switch rest[0] {
	case 2:
		if len(rest) < 4 {
			return "", 0
		}
		return fmt.Sprintf("#%02x%02x%02x", clamp8(rest[1]), clamp8(rest[2]), clamp8(rest[3])), 4
	case 5:
		if len(rest) < 2 {
			return "", 0
		}
		return xterm256(rest[1]), 2
	}
	return "", 0
}

func clamp8(v int) int {
	if v < 0 {
		return 0
	}
	if v > 255 {
		return 255
	}
	return v
}

// Convert 는 ANSI 가 섞인 화면 한 장을 HTML 로 바꾼다.
//
// 두 가지를 챙긴다:
//   - 같은 스타일이 이어지면 span 하나로 합친다. tmux 캡처는 칸마다 이스케이프를
//     넣기 때문에, 안 합치면 파일이 몇 배로 커진다.
//   - 줄 끝 공백을 지운다. 80칸 캡처는 줄마다 공백이 수십 개씩 붙어 있다.
func Convert(s string) string { return convert(s, nil) }

// convert 는 표가 있으면 클래스를, 없으면 인라인 style 을 쓴다.
// 캡처 한 장짜리는 표를 둘 곳이 없어서 인라인이 낫고, 묶음은 표가 훨씬 작다.
func convert(s string, tab *classTable) string {
	s = trimRawLines(s)

	var out strings.Builder
	var cur style
	var buf strings.Builder
	bufCSS := "" // buf 에 쌓인 글자에 적용될 스타일

	flush := func() {
		if buf.Len() == 0 {
			return
		}
		text := html.EscapeString(buf.String())
		buf.Reset()
		if bufCSS == "" {
			out.WriteString(text)
			return
		}
		if tab != nil {
			out.WriteString(`<span class="` + tab.class(bufCSS) + `">` + text + `</span>`)
			return
		}
		out.WriteString(`<span style="` + bufCSS + `">` + text + `</span>`)
	}

	r := []rune(s)
	for i := 0; i < len(r); i++ {
		if r[i] != 0x1b {
			// 스타일은 **글자를 쓸 때** 확정한다.
			// 이스케이프를 볼 때마다 끊으면, 리셋했다가 같은 색을 다시 켜는 흔한
			// 패턴에서 span 이 칸 수만큼 생긴다(tmux 캡처가 딱 그렇다).
			if css := cur.css(); css != bufCSS {
				flush()
				bufCSS = css
			}
			buf.WriteRune(r[i])
			continue
		}
		// 이스케이프 시퀀스. CSI(`ESC [`) 만 해석하고 나머지는 버린다.
		j := i + 1
		if j >= len(r) || r[j] != '[' {
			i = skipEscape(r, i)
			continue
		}
		j++
		start := j
		for j < len(r) && !isFinal(r[j]) {
			j++
		}
		if j >= len(r) {
			break
		}
		body, final := string(r[start:j]), r[j]
		i = j
		if final != 'm' {
			continue // 커서 이동·화면 지우기 등은 캡처에 뜻이 없다
		}
		cur = applySGR(cur, parseParams(body))
	}
	flush()
	return trimLines(out.String())
}

// trimRawLines 는 변환 **전에** 각 줄 끝의 공백을 지운다.
//
// 변환 뒤에 지우려 하면 공백이 span 안에 갇혀 있어서 손댈 수가 없다.
// 이스케이프는 폭이 0 이므로 그대로 둔다 — 지우면 스타일 상태가 어긋난다.
func trimRawLines(s string) string {
	lines := strings.Split(s, "\n")
	for i, l := range lines {
		lines[i] = trimTrailingSpaces(l)
	}
	return strings.Join(lines, "\n")
}

// trimTrailingSpaces 는 한 줄에서 "마지막으로 눈에 보이는 글자" 뒤의 공백만 버린다.
func trimTrailingSpaces(line string) string {
	r := []rune(line)
	type tok struct {
		text    string
		visible bool // 공백이 아닌 진짜 글자
		space   bool
	}
	var toks []tok
	for i := 0; i < len(r); i++ {
		if r[i] == 0x1b {
			j := i + 1
			if j < len(r) && r[j] == '[' {
				j++
				for j < len(r) && !isFinal(r[j]) {
					j++
				}
			}
			if j >= len(r) {
				j = len(r) - 1
			}
			toks = append(toks, tok{text: string(r[i : j+1])})
			i = j
			continue
		}
		toks = append(toks, tok{text: string(r[i]), visible: r[i] != ' ', space: r[i] == ' '})
	}
	last := -1
	for i, t := range toks {
		if t.visible {
			last = i
		}
	}
	var b strings.Builder
	for i, t := range toks {
		if i > last && t.space {
			continue
		}
		b.WriteString(t.text)
	}
	return b.String()
}

// isFinal 은 CSI 시퀀스를 끝내는 글자인지 본다 (@ ~ 범위).
func isFinal(c rune) bool { return c >= 0x40 && c <= 0x7e }

// skipEscape 는 CSI 가 아닌 이스케이프를 건너뛴다. 다음 글자 하나만 먹으면 충분하다.
func skipEscape(r []rune, i int) int {
	if i+1 < len(r) {
		return i + 1
	}
	return i
}

// parseParams 는 "38;2;255;0;0" 을 정수 목록으로. 빈 자리는 0 이다(ANSI 규약).
func parseParams(body string) []int {
	body = strings.ReplaceAll(body, ":", ";") // 하위 파라미터 구분자도 같게 취급
	if body == "" {
		return []int{0}
	}
	parts := strings.Split(body, ";")
	out := make([]int, 0, len(parts))
	for _, p := range parts {
		if p == "" {
			out = append(out, 0)
			continue
		}
		n, err := strconv.Atoi(p)
		if err != nil {
			return nil
		}
		out = append(out, n)
	}
	return out
}

// trimLines 는 줄 끝의 공백을 지운다. HTML 태그 안쪽은 건드리지 않는다 —
// 태그가 줄 끝에 걸치는 경우가 없도록 Convert 가 줄 단위로 span 을 닫기 때문이다.
func trimLines(s string) string {
	lines := strings.Split(s, "\n")
	for i, l := range lines {
		lines[i] = strings.TrimRight(l, " ")
	}
	return strings.Join(lines, "\n")
}

// ConvertRecording 은 프레임 묶음을 통째로 바꾸고 화면 크기를 재어 둔다.
func ConvertRecording(in Recording) HTMLRecording {
	tab := newClassTable()
	out := HTMLRecording{Name: in.Name, Script: in.Script}
	var prev []string

	for _, f := range in.Frames {
		lines := strings.Split(convert(f.Content, tab), "\n")
		hf := HTMLFrame{I: f.I, Label: f.Label, N: len(lines), D: []LineDiff{}}
		for y, l := range lines {
			if y < len(prev) && prev[y] == l {
				continue
			}
			hf.D = append(hf.D, LineDiff{Y: y, HTML: l})
		}
		out.Frames = append(out.Frames, hf)
		prev = lines

		w, h := measure(f.Content)
		if w > out.Cols {
			out.Cols = w
		}
		if h > out.Rows {
			out.Rows = h
		}
	}
	out.Styles = tab.styles()
	return out
}

// measure 는 화면의 칸 수를 잰다. ANSI 는 빼고, 한글 같은 넓은 글자는 두 칸으로 센다.
func measure(s string) (cols, rows int) {
	plain := stripANSI(s)
	lines := strings.Split(plain, "\n")
	rows = len(lines)
	for _, l := range lines {
		if w := cells(strings.TrimRight(l, " ")); w > cols {
			cols = w
		}
	}
	return cols, rows
}

func stripANSI(s string) string {
	var b strings.Builder
	r := []rune(s)
	for i := 0; i < len(r); i++ {
		if r[i] != 0x1b {
			b.WriteRune(r[i])
			continue
		}
		j := i + 1
		if j < len(r) && r[j] == '[' {
			j++
			for j < len(r) && !isFinal(r[j]) {
				j++
			}
		}
		i = j
	}
	return b.String()
}

// cells 는 화면 칸 수. 동아시아 넓은 글자는 두 칸이다.
func cells(s string) int {
	n := 0
	for _, r := range s {
		if isWide(r) {
			n += 2
			continue
		}
		n++
	}
	return n
}

// isWide 는 두 칸을 먹는 글자인지 본다.
//
// 정확한 판정에는 유니코드 East Asian Width 표가 필요하지만, 여기서 다루는 글자는
// ASCII·한글·박스 그리기 문자뿐이다. 한글 영역만 두 칸으로 세면 충분하다.
// (블록 문자 █ 와 ░ 는 터미널에서 한 칸이고, lipgloss 도 그렇게 센다)
func isWide(r rune) bool {
	switch {
	case r >= 0x1100 && r <= 0x115F: // 한글 자모
		return true
	case r >= 0x2E80 && r <= 0xA4CF: // CJK 부수 ~ 이 영역 전반
		return true
	case r >= 0xAC00 && r <= 0xD7A3: // 한글 음절
		return true
	case r >= 0xF900 && r <= 0xFAFF: // CJK 호환 한자
		return true
	case r >= 0xFF00 && r <= 0xFF60: // 전각 기호
		return true
	}
	return unicode.Is(unicode.Hiragana, r) || unicode.Is(unicode.Katakana, r)
}

func main() {
	in := flag.String("in", "", "입력 파일 (.json 이면 프레임 묶음, 그 외는 화면 한 장)")
	out := flag.String("out", "", "출력 파일")
	flag.Parse()

	if *in == "" || *out == "" {
		fmt.Fprintln(os.Stderr, "-in 과 -out 이 모두 필요하다")
		os.Exit(2)
	}
	raw, err := os.ReadFile(*in)
	if err != nil {
		fmt.Fprintln(os.Stderr, "읽기 실패:", err)
		os.Exit(1)
	}

	if strings.HasSuffix(*in, ".json") {
		var rec Recording
		if err := json.Unmarshal(raw, &rec); err != nil {
			fmt.Fprintln(os.Stderr, "파싱 실패:", err)
			os.Exit(1)
		}
		conv := ConvertRecording(rec)
		enc, _ := json.Marshal(conv)
		if err := os.WriteFile(*out, append(enc, '\n'), 0o644); err != nil {
			fmt.Fprintln(os.Stderr, "쓰기 실패:", err)
			os.Exit(1)
		}
		fmt.Printf("%s — 프레임 %d장 %d×%d → %s\n", conv.Name, len(conv.Frames), conv.Cols, conv.Rows, *out)
		return
	}

	body := Convert(string(raw))
	if err := os.WriteFile(*out, []byte(body), 0o644); err != nil {
		fmt.Fprintln(os.Stderr, "쓰기 실패:", err)
		os.Exit(1)
	}
	fmt.Printf("화면 한 장 → %s (%d바이트)\n", *out, len(body))
}
