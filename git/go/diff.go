package mygit

// diff (SPEC.md §11) — 두 줄 목록 사이의 가장 짧은 편집 스크립트.
//
// 세 단계다. (1) 앞뒤의 같은 줄을 떼어 둔다. (2) 남은 가운데서 Myers
// 의 탐욕 탐색으로 가장 짧은 스크립트를 찾는다. (3) 바뀐 줄 묶음을
// git 처럼 위아래로 밀어 자리를 정한다 — 같은 줄이 되풀이되는 곳에서는
// 어디를 바뀐 줄로 칠지가 여럿이라, 이 단계가 없으면 git 과 덩어리
// 자리가 달라진다.
//
// 줄은 string(바이트 열)이고 줄바꿈까지 품는다. rchg 는 줄마다
// "바뀌었나" 의 bool 목록이다.

import (
	"bytes"
	"fmt"
	"os"
	"strings"
)

const (
	context     = 3
	binaryProbe = 8000
)

// SplitLines 는 바이트 → 줄 목록. 줄마다 '\n' 을 품고, 마지막 줄만
// 없을 수 있다.
func SplitLines(data []byte) []string {
	var lines []string
	for len(data) > 0 {
		i := bytes.IndexByte(data, '\n')
		if i < 0 {
			lines = append(lines, string(data))
			break
		}
		lines = append(lines, string(data[:i+1]))
		data = data[i+1:]
	}
	return lines
}

// ── 2 단계: Myers 앞방향 탐욕 탐색 (SPEC.md §11.2) ─────────────────

// forward 는 가운데 a·b 의 (ra, rb). 대각선 k 마다 가장 멀리 간 x 를
// v[k] 에 둔다. d 마다 v 의 [-d, d] 조각을 남겨 두었다가 (N, M) 에서
// 거꾸로 같은 판정을 되밟아 편집을 표시한다.
// O((N+M)·D) 시간, O(D²) 공간.
func forward(a, b []string) ([]bool, []bool) {
	n, m := len(a), len(b)
	off := n + m + 1
	v := make([]int, 2*off+1)
	var trace [][]int
	for d := 0; d <= n+m; d++ {
		trace = append(trace, append([]int(nil), v[off-d:off+d+1]...))
		for k := -d; k <= d; k += 2 {
			var x int
			if k == -d || (k != d && v[off+k-1] < v[off+k+1]) {
				x = v[off+k+1] // 아래로: b 의 줄을 끼움
			} else {
				x = v[off+k-1] + 1 // 오른쪽: a 의 줄을 지움
			}
			y := x - k
			for x < n && y < m && a[x] == b[y] {
				x, y = x+1, y+1
			}
			v[off+k] = x
			if x >= n && y >= m {
				return backtrack(trace, n, m, d)
			}
		}
	}
	panic("Myers 탐색이 끝나지 않았다")
}

func backtrack(trace [][]int, n, m, dfin int) ([]bool, []bool) {
	ra, rb := make([]bool, n), make([]bool, m)
	x, y := n, m
	for d := dfin; d > 0; d-- {
		v := func(k int) int { return trace[d][k+d] }
		k := x - y
		down := k == -d || (k != d && v(k-1) < v(k+1))
		pk := k - 1
		if down {
			pk = k + 1
		}
		px := v(pk)
		py := px - pk
		if down {
			rb[py] = true
		} else {
			ra[px] = true
		}
		x, y = px, py
	}
	return ra, rb
}

// Myers 는 1·2 단계 — 앞뒤를 깎고 가운데를 앞방향 Myers 로.
func Myers(a, b []string) ([]bool, []bool) {
	n, m := len(a), len(b)
	s := 0
	for s < n && s < m && a[s] == b[s] {
		s++
	}
	e := 0
	for e < n-s && e < m-s && a[n-1-e] == b[m-1-e] {
		e++
	}
	ma, mb := forward(a[s:n-e], b[s:m-e])
	ra, rb := make([]bool, n), make([]bool, m)
	copy(ra[s:], ma)
	copy(rb[s:], mb)
	return ra, rb
}

// ── 3 단계: 밀어 붙이기 (git 의 xdl_change_compact, 휴리스틱 없이) ──

// group 은 바뀐 줄 묶음 [start, end). 빈 묶음(start == end)도 자리다.
type group struct {
	chg        []bool
	n          int // 끝의 가짜 줄 하나를 뺀 길이
	start, end int
}

func newGroup(chg []bool) *group {
	g := &group{chg: chg, n: len(chg) - 1}
	for g.end < g.n && chg[g.end] {
		g.end++
	}
	return g
}

func (g *group) next() bool {
	if g.end == g.n {
		return false
	}
	g.end++
	g.start = g.end
	for g.end < g.n && g.chg[g.end] {
		g.end++
	}
	return true
}

func (g *group) previous() bool {
	if g.start == 0 {
		return false
	}
	g.start--
	g.end = g.start
	for g.start > 0 && g.chg[g.start-1] {
		g.start--
	}
	return true
}

func (g *group) slideDown(recs []string) bool {
	if g.end < g.n && recs[g.start] == recs[g.end] {
		g.chg[g.start], g.chg[g.end] = false, true
		g.start, g.end = g.start+1, g.end+1
		for g.end < g.n && g.chg[g.end] {
			g.end++
		}
		return true
	}
	return false
}

func (g *group) slideUp(recs []string) bool {
	if g.start > 0 && recs[g.start-1] == recs[g.end-1] {
		g.start, g.end = g.start-1, g.end-1
		g.chg[g.start], g.chg[g.end] = true, false
		for g.start > 0 && g.chg[g.start-1] {
			g.start--
		}
		return true
	}
	return false
}

// compact 는 한 쪽 파일의 바뀐 줄 묶음을 밀어 자리를 정한다(§11.2).
// 묶음마다 위로 끝까지, 다시 아래로 끝까지 민다(밀다가 이웃 묶음과
// 붙으면 처음부터). 상대 파일의 바뀐 묶음과 끝이 맞는 자리가
// 있었으면 그리로 되올리고, 없으면 맨 아래에 둔다. 상대 쪽 묶음 표지
// go 는 묶음과 발을 맞춰 움직인다. O(줄 수 × 미는 거리).
func compact(recs []string, rchg []bool, ochg []bool) []bool {
	chg := append(append([]bool(nil), rchg...), false)
	g := newGroup(chg)
	gother := newGroup(append(append([]bool(nil), ochg...), false))
	for {
		if g.end != g.start {
			var earliest, matchEnd int
			for {
				size := g.end - g.start
				matchEnd = -1
				for g.slideUp(recs) {
					gother.previous()
				}
				earliest = g.end
				if gother.end > gother.start {
					matchEnd = g.end
				}
				for g.slideDown(recs) {
					gother.next()
					if gother.end > gother.start {
						matchEnd = g.end
					}
				}
				if size == g.end-g.start {
					break
				}
			}
			if g.end != earliest && matchEnd != -1 {
				for gother.end == gother.start {
					g.slideUp(recs)
					gother.previous()
				}
			}
		}
		if !g.next() {
			break
		}
		gother.next()
	}
	return chg[:len(chg)-1]
}

// EditFlags 는 세 단계를 다 거친 (ra, rb) — 계약의 전부(§11.2).
func EditFlags(a, b []string) ([]bool, []bool) {
	ra, rb := Myers(a, b)
	ra = compact(a, ra, rb)
	rb = compact(b, rb, ra)
	return ra, rb
}

// Change 는 바뀐 곳 하나 — a·b 의 자리와 줄 수.
type Change struct{ A, B, NA, NB int }

// BuildChanges 는 바뀐 곳들, 앞에서부터. 끝에서 앞으로 훑으며 같은
// 자리에서 만나는 지운 묶음과 끼운 묶음을 한 바뀐 곳으로 묶는다
// (git 의 xdl_build_script).
func BuildChanges(ra, rb []bool) []Change {
	var out []Change
	i1, i2 := len(ra), len(rb)
	for i1 > 0 || i2 > 0 {
		if (i1 > 0 && ra[i1-1]) || (i2 > 0 && rb[i2-1]) {
			l1, l2 := i1, i2
			for i1 > 0 && ra[i1-1] {
				i1--
			}
			for i2 > 0 && rb[i2-1] {
				i2--
			}
			out = append(out, Change{i1, i2, l1 - i1, l2 - i2})
		} else {
			i1, i2 = i1-1, i2-1
		}
	}
	for i, j := 0, len(out)-1; i < j; i, j = i+1, j-1 {
		out[i], out[j] = out[j], out[i]
	}
	return out
}

// isFunc 는 git 기본 드라이버의 함수 줄 — 첫 바이트가 영문자·'_'·'$'.
func isFunc(line string) bool {
	if line == "" {
		return false
	}
	c := line[0]
	return c|0x20 >= 'a' && c|0x20 <= 'z' || c == '_' || c == '$'
}

func span(start, count int) string {
	first := start
	if count > 0 {
		first++
	}
	if count == 1 {
		return fmt.Sprint(first)
	}
	return fmt.Sprintf("%d,%d", first, count)
}

const asciiSpace = " \t\n\r\v\f"

// UnifiedDiff 는 덩어리들(SPEC.md §11.3). 같으면 빈 것.
func UnifiedDiff(a, b []string) []byte {
	ra, rb := EditFlags(a, b)
	ch := BuildChanges(ra, rb)
	var out []string
	for i := 0; i < len(ch); {
		j := i
		for j+1 < len(ch) && ch[j+1].A-(ch[j].A+ch[j].NA) <= 2*context {
			j++
		}
		first, last := ch[i], ch[j]
		s1, s2 := max(first.A-context, 0), max(first.B-context, 0)
		e1 := min(last.A+last.NA+context, len(a))
		e2 := min(last.B+last.NB+context, len(b))
		fn := ""
		for q := s1 - 1; q >= 0; q-- {
			if isFunc(a[q]) {
				l := strings.TrimRight(a[q], asciiSpace)
				fn = " " + strings.TrimRight(l[:min(len(l), 80)],
					asciiSpace)
				break
			}
		}
		out = append(out, fmt.Sprintf("@@ -%s +%s @@%s\n",
			span(s1, e1-s1), span(s2, e2-s2), fn))
		p1 := s1
		for _, c := range ch[i : j+1] {
			for q := p1; q < c.A; q++ {
				out = append(out, " "+a[q])
			}
			for q := c.A; q < c.A+c.NA; q++ {
				out = append(out, "-"+a[q])
			}
			for q := c.B; q < c.B+c.NB; q++ {
				out = append(out, "+"+b[q])
			}
			p1 = c.A + c.NA
		}
		for q := p1; q < e1; q++ {
			out = append(out, " "+a[q])
		}
		i = j + 1
	}
	var buf bytes.Buffer
	for _, line := range out {
		buf.WriteString(line)
		if !strings.HasSuffix(line, "\n") {
			buf.WriteString("\n\\ No newline at end of file\n")
		}
	}
	return buf.Bytes()
}

// Side 는 diff 의 한 쪽 — (모드, 이름, 바이트).
type Side struct {
	Mode uint32
	Oid  string
	Data []byte
}

// FileDiff 는 파일 하나의 diff 전체(SPEC.md §11.4). old·new 가 nil
// 이면 새로 생김·지워짐. 같으면 빈 것.
func FileDiff(pa, pb string, old, new *Side) []byte {
	if old != nil && new != nil && old.Mode == new.Mode &&
		old.Oid == new.Oid {
		return nil
	}
	qa, qb := QuotePath("a/"+pa, false), QuotePath("b/"+pb, false)
	rows := []string{"diff --git " + qa + " " + qb}
	z := "0000000"
	switch {
	case old == nil:
		rows = append(rows, fmt.Sprintf("new file mode %06o",
			new.Mode), "index "+z+".."+new.Oid[:7])
	case new == nil:
		rows = append(rows, fmt.Sprintf("deleted file mode %06o",
			old.Mode), "index "+old.Oid[:7]+".."+z)
	default:
		if old.Mode != new.Mode {
			rows = append(rows, fmt.Sprintf("old mode %06o", old.Mode),
				fmt.Sprintf("new mode %06o", new.Mode))
		}
		if old.Oid == new.Oid {
			return []byte(strings.Join(rows, "\n") + "\n") // 모드만
		}
		idx := "index " + old.Oid[:7] + ".." + new.Oid[:7]
		if old.Mode == new.Mode {
			idx += fmt.Sprintf(" %06o", old.Mode)
		}
		rows = append(rows, idx)
	}
	var da, db []byte
	na, nb := "/dev/null", "/dev/null"
	if old != nil {
		da, na = old.Data, qa
	}
	if new != nil {
		db, nb = new.Data, qb
	}
	if bytes.IndexByte(da[:min(len(da), binaryProbe)], 0) >= 0 ||
		bytes.IndexByte(db[:min(len(db), binaryProbe)], 0) >= 0 {
		rows = append(rows, "Binary files "+na+" and "+nb+" differ")
		return []byte(strings.Join(rows, "\n") + "\n")
	}
	rows = append(rows, "--- "+na, "+++ "+nb)
	return append([]byte(strings.Join(rows, "\n")+"\n"),
		UnifiedDiff(SplitLines(da), SplitLines(db))...)
}

// BlobSide 는 저장소의 blob 에서 한 쪽을 만든다.
func BlobSide(gitdir string, b Blob) (*Side, error) {
	_, data, err := ReadObject(gitdir, b.Oid)
	if err != nil {
		return nil, err
	}
	return &Side{b.Mode, b.Oid, data}, nil
}

// DiskSide 는 디스크의 파일에서 한 쪽을 만든다. 없으면 nil.
func DiskSide(path string) *Side {
	st, err := os.Stat(path)
	if err != nil || !st.Mode().IsRegular() {
		return nil
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil
	}
	mode := uint32(0o100644)
	if st.Mode()&0o100 != 0 {
		mode = 0o100755
	}
	return &Side{mode, HashObject("blob", data), data}
}
