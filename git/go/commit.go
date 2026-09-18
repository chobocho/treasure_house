package mygit

// commit·tag 객체와 신원 줄 (SPEC.md §4.4 · §4.5 · §1.3 · §9.1).
//
// 커밋 = 트리 하나 + 부모 목록 + 누가·언제 + 메시지. 커밋의 이름에는
// 작성 시각과 시간대까지 들어가므로, 같은 트리라도 1초만 달라도 다른
// 커밋이다 — 그래서 mygit 은 시계를 읽지 않고 환경 변수만 믿는다.

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"
)

var (
	days   = []string{"Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"}
	months = []string{"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
		"Aug", "Sep", "Oct", "Nov", "Dec"}
	identRe = regexp.MustCompile(`^(.*) <(.*)> (-?\d+) ([+-]\d{4})$`)
	dateRe  = regexp.MustCompile(`^\d+ [+-]\d{4}$`)
)

type Commit struct {
	Tree, Author, Committer, Message string
	Parents                          []string
}

// ParseIdent 는 '이름 <메일> 초 ±hhmm' → (이름, 메일, 초, 시간대).
func ParseIdent(line string) (string, string, int64, string, error) {
	m := identRe.FindStringSubmatch(line)
	if m == nil {
		return "", "", 0, "", Fail("fatal: mygit: bad ident line: " +
			line)
	}
	sec, _ := strconv.ParseInt(m[3], 10, 64)
	return m[1], m[2], sec, m[4], nil
}

// IdentFromEnv 는 GIT_<who>_NAME·EMAIL·DATE → 신원 줄 (SPEC.md §1.3).
// 설정 파일도 시계도 보지 않는다 — 캡처가 세 번 같으려면 입력이
// 전부 드러나 있어야 하기 때문이다.
func IdentFromEnv(env map[string]string, who string) (string, error) {
	var vals []string
	for _, part := range []string{"NAME", "EMAIL", "DATE"} {
		key := "GIT_" + who + "_" + part
		v, ok := env[key]
		if !ok {
			return "", Fail("fatal: mygit: " + key + " is not set")
		}
		vals = append(vals, v)
	}
	if !dateRe.MatchString(vals[2]) {
		return "", Fail("fatal: mygit: GIT_" + who + "_DATE is not " +
			"'<seconds> <+hhmm>'")
	}
	return fmt.Sprintf("%s <%s> %s", vals[0], vals[1], vals[2]), nil
}

// floorDiv 는 음수에서도 내림 나눗셈 — Go 의 / 는 0 쪽으로 자른다.
func floorDiv(a, b int64) int64 {
	q := a / b
	if (a%b != 0) && ((a < 0) != (b < 0)) {
		q--
	}
	return q
}

// civilFromDays 는 1970-01-01 부터의 날 수 → (해, 달, 일). Howard
// Hinnant 의 그레고리력 공식 — 표준 달력 함수를 쓰지 않는다. O(1).
func civilFromDays(z int64) (int64, int64, int64) {
	z += 719468
	era := floorDiv(z, 146097)
	doe := z - era*146097
	yoe := (doe - doe/1460 + doe/36524 - doe/146096) / 365
	y := yoe + era*400
	doy := doe - (365*yoe + yoe/4 - yoe/100)
	mp := (5*doy + 2) / 153
	d := doy - (153*mp+2)/5 + 1
	m := mp + 3
	if mp >= 10 {
		m = mp - 9
	}
	if m <= 2 {
		y++
	}
	return y, m, d
}

// FormatDate 는 git log 의 Date 꼴 — 'Wed Nov 15 07:13:20 2023 +0900'.
// 시각을 그 시간대로 옮겨 찍는다. 일은 앞에 0 을 붙이지 않는다.
func FormatDate(sec int64, tz string) string {
	h, _ := strconv.Atoi(tz[1:3])
	m, _ := strconv.Atoi(tz[3:5])
	off := int64(h*3600 + m*60)
	if tz[0] == '-' {
		off = -off
	}
	local := sec + off
	dn := floorDiv(local, 86400)
	rest := local - dn*86400
	y, mo, d := civilFromDays(dn)
	return fmt.Sprintf("%s %s %d %02d:%02d:%02d %d %s",
		days[(dn%7+11)%7], months[mo-1], d, rest/3600, rest/60%60,
		rest%60, y, tz)
}

// CleanupMessage 는 commit -m 의 공백 정리(cleanup=whitespace). 줄마다
// 끝 공백을 지우고, 이어진 빈 줄은 하나로, 앞뒤의 빈 줄은 지운다.
// 줄 앞의 공백은 남긴다.
func CleanupMessage(text string) string {
	var out []string
	for _, line := range strings.Split(text, "\n") {
		line = strings.TrimRight(line, " \t\r\v\f")
		if line != "" || (len(out) > 0 && out[len(out)-1] != "") {
			out = append(out, line)
		}
	}
	for len(out) > 0 && out[len(out)-1] == "" {
		out = out[:len(out)-1]
	}
	if len(out) == 0 {
		return ""
	}
	return strings.Join(out, "\n") + "\n"
}

// SubjectOf 는 첫 문단의 줄들을 공백 하나로 이은 것(SPEC.md §4.4).
// 줄 끝의 공백은 떼지만 앞의 공백은 남긴다.
func SubjectOf(message string) string {
	var lines []string
	for _, line := range strings.Split(message, "\n") {
		if strings.TrimSpace(line) == "" {
			break
		}
		lines = append(lines, strings.TrimRight(line, " \t\r\v\f"))
	}
	return strings.Join(lines, " ")
}

// ParseCommit 은 커밋 몸 → Commit. 모르는 머리 줄(gpgsig·mergetag 와
// 그 이어진 줄)은 건너뛴다.
func ParseCommit(body []byte) (*Commit, error) {
	head, msg, _ := strings.Cut(string(body), "\n\n")
	c := &Commit{Message: msg}
	for _, line := range strings.Split(head, "\n") {
		key, val, _ := strings.Cut(line, " ")
		switch key {
		case "tree":
			c.Tree = val
		case "parent":
			c.Parents = append(c.Parents, val)
		case "author":
			c.Author = val
		case "committer":
			c.Committer = val
		}
	}
	if c.Tree == "" || c.Committer == "" {
		return nil, Fail("fatal: mygit: corrupt commit object")
	}
	return c, nil
}

func SerializeCommit(c *Commit) []byte {
	var b strings.Builder
	b.WriteString("tree " + c.Tree + "\n")
	for _, p := range c.Parents {
		b.WriteString("parent " + p + "\n")
	}
	b.WriteString("author " + c.Author + "\ncommitter " + c.Committer +
		"\n\n" + c.Message)
	return []byte(b.String())
}

func SerializeTag(obj, typ, name, tagger, msg string) []byte {
	return []byte(fmt.Sprintf("object %s\ntype %s\ntag %s\ntagger %s"+
		"\n\n%s", obj, typ, name, tagger, msg))
}

// ParseTag 는 태그 몸 → 머리 칸들과 "message".
func ParseTag(body []byte) map[string]string {
	head, msg, _ := strings.Cut(string(body), "\n\n")
	t := map[string]string{"message": msg}
	for _, line := range strings.Split(head, "\n") {
		k, v, _ := strings.Cut(line, " ")
		t[k] = v
	}
	return t
}
