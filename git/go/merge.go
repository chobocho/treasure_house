package mygit

// merge (SPEC.md §12) — 공통 조상 B 에서 갈라진 O(우리)와 T(그들).
//
// 파일 하나의 합치기는 git 의 xdl_merge(ZEALOUS 수준)를 따른다:
//  1. B→O, B→T 의 바뀐 곳을 B 좌표로 짝지어 훑는다. 엄격히 앞선
//     쪽은 그대로 받고, 겹치거나 맞닿으면 충돌 후보다(같은 수정이면
//     한 번만).
//  2. 충돌마다 O 쪽과 T 쪽을 다시 diff 해 같은 줄을 표지 밖으로 뺀다.
//  3. 사이가 바뀌지 않은 줄 3개 이하인 이웃 충돌은 하나로 붙인다.
// 진짜 git merge 로 경계를 확인한 규칙들이다(golden/scen/merge-*.scn).

import (
	"bytes"
	"strings"
)

const join = 3 // 이만큼 가까운 충돌은 하나로 붙인다

func changesOf(a, b []string) []Change {
	return BuildChanges(EditFlags(a, b))
}

// sideRange 는 B 의 [start, end) 에 맞는 한쪽 파일의 범위. start 앞에서
// 시작한 바뀐 곳들의 길이 차를 더하면 시작 자리가, end 이하에서 시작한
// 것까지 더하면 끝 자리가 나온다.
func sideRange(cs []Change, start, end int) (int, int) {
	s, e := start, end
	for _, c := range cs {
		if c.A < start {
			s += c.NB - c.NA
		}
		if c.A <= end {
			e += c.NB - c.NA
		}
	}
	return s, e
}

// hunk 는 1 단계의 결과 하나 — 'o'(O 쪽 변경 받기), 't', 'c'(충돌
// 후보). B 의 [s, e) 를 o 또는 t 줄들로 바꾼다.
type hunk struct {
	kind byte
	s, e int
	o, t []string
}

func eqLines(a, b []string) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

// pairUp 은 1 단계 — 두 변경 목록을 B 좌표로 짝짓는다.
func pairUp(base, ours, theirs []string) []hunk {
	c1, c2 := changesOf(base, ours), changesOf(base, theirs)
	var out []hunk
	i, j := 0, 0
	for i < len(c1) || j < len(c2) {
		if j == len(c2) || (i < len(c1) && c1[i].A+c1[i].NA < c2[j].A) {
			x := c1[i]
			out = append(out, hunk{'o', x.A, x.A + x.NA,
				ours[x.B : x.B+x.NB], nil})
			i++
			continue
		}
		if i == len(c1) || c2[j].A+c2[j].NA < c1[i].A {
			y := c2[j]
			out = append(out, hunk{'t', y.A, y.A + y.NA, nil,
				theirs[y.B : y.B+y.NB]})
			j++
			continue
		}
		x, y := c1[i], c2[j]
		if x.A == y.A && x.NA == y.NA && eqLines(ours[x.B:x.B+x.NB],
			theirs[y.B:y.B+y.NB]) {
			// 양쪽이 같은 수정 — 한 번만
			out = append(out, hunk{'o', x.A, x.A + x.NA,
				ours[x.B : x.B+x.NB], nil})
			i, j = i+1, j+1
			continue
		}
		start, end := min(x.A, y.A), max(x.A+x.NA, y.A+y.NA)
		i, j = i+1, j+1
		for { // 맞닿는 것까지 넓힌다
			if i < len(c1) && c1[i].A <= end {
				end = max(end, c1[i].A+c1[i].NA)
				i++
			} else if j < len(c2) && c2[j].A <= end {
				end = max(end, c2[j].A+c2[j].NA)
				j++
			} else {
				break
			}
		}
		os_, oe := sideRange(c1, start, end)
		ts, te := sideRange(c2, start, end)
		out = append(out, hunk{'c', start, end, ours[os_:oe],
			theirs[ts:te]})
	}
	return out
}

// piece 는 결과의 한 조각. same 은 B 그대로(다듬기의 같은 줄 포함),
// clean 은 한쪽에서 받은 변경, conf 는 충돌(o·t 가 양쪽). 붙이기는
// same 만 사이에 둔 충돌끼리 한다 — clean 은 이웃을 끊는다.
type piece struct {
	kind byte // 's'ame · 'c'lean · 'x' 충돌
	o, t []string
}

// refine 은 2 단계 — 충돌 하나를 O·T 의 diff 로 쪼갠다. 같은 줄은
// 표지 밖으로 나온다. O == T 면 충돌이 아니다.
func refine(o, t []string) []piece {
	if eqLines(o, t) {
		return []piece{{'s', o, nil}}
	}
	var out []piece
	p1 := 0
	for _, c := range changesOf(o, t) {
		if c.A > p1 {
			out = append(out, piece{'s', o[p1:c.A], nil})
		}
		out = append(out, piece{'x', o[c.A : c.A+c.NA],
			t[c.B : c.B+c.NB]})
		p1 = c.A + c.NA
	}
	if p1 < len(o) {
		out = append(out, piece{'s', o[p1:], nil})
	}
	return out
}

func cat(parts ...[]string) []string {
	var out []string
	for _, p := range parts {
		out = append(out, p...)
	}
	return out
}

// Merge3 은 세 판의 바이트 → (합친 바이트, 충돌 수). SPEC.md §12.3.
// O(줄 수 × 편집 거리) — diff 두 번과 충돌마다 diff 한 번.
func Merge3(base, ours, theirs []byte, label string) ([]byte, int) {
	if bytes.Equal(ours, theirs) || bytes.Equal(base, theirs) {
		return ours, 0
	}
	if bytes.Equal(base, ours) {
		return theirs, 0
	}
	b := SplitLines(base)
	o, t := SplitLines(ours), SplitLines(theirs)
	var pieces []piece
	pos := 0
	for _, h := range pairUp(b, o, t) {
		if h.s > pos {
			pieces = append(pieces, piece{'s', b[pos:h.s], nil})
		}
		switch h.kind {
		case 'o':
			pieces = append(pieces, piece{'c', h.o, nil})
		case 't':
			pieces = append(pieces, piece{'c', h.t, nil})
		default:
			pieces = append(pieces, refine(h.o, h.t)...)
		}
		pos = h.e
	}
	if pos < len(b) {
		pieces = append(pieces, piece{'s', b[pos:], nil})
	}
	// 3 단계 — 바뀌지 않은 줄 join 개 이하로 떨어진 충돌을 붙인다
	var joined []piece
	for _, p := range pieces {
		n := len(joined)
		switch {
		case p.kind == 'x' && n >= 2 && joined[n-1].kind == 's' &&
			joined[n-2].kind == 'x' && len(joined[n-1].o) <= join:
			mid, prev := joined[n-1].o, joined[n-2]
			p = piece{'x', cat(prev.o, mid, p.o), cat(prev.t, mid, p.t)}
			joined = joined[:n-2]
		case p.kind == 's' && n > 0 && joined[n-1].kind == 's':
			p = piece{'s', cat(joined[n-1].o, p.o), nil}
			joined = joined[:n-1]
		}
		joined = append(joined, p)
	}
	var buf bytes.Buffer
	n := 0
	for _, p := range joined {
		if p.kind != 'x' {
			buf.WriteString(strings.Join(p.o, ""))
			continue
		}
		n++
		buf.WriteString("<<<<<<< HEAD\n" + strings.Join(p.o, "") +
			"=======\n" + strings.Join(p.t, "") + ">>>>>>> " + label +
			"\n")
	}
	return buf.Bytes(), n
}

// MergeResult 는 경로 하나의 트리 합치기 결과. Gone 이면 지움,
// Conflict 면 Text 가 표지 든 내용이고 Stages 가 단계 1‥3.
type MergeResult struct {
	Gone, Conflict bool
	Blob           Blob
	Text           []byte
	Stages         map[int]Blob
}

// pick 은 세 줄 규칙(O = T → O, B = T → O, B = O → T). 없음(nil)도
// 값이다 — 한쪽만 지웠으면 지움이 이긴다. 못 고르면 ok 가 거짓.
func pick[T comparable](b, o, t *T) (*T, bool) {
	eq := func(x, y *T) bool {
		return x == nil && y == nil || x != nil && y != nil && *x == *y
	}
	if eq(o, t) || eq(b, t) {
		return o, true
	}
	if eq(b, o) {
		return t, true
	}
	return nil, false
}

func lookup(m map[string]Blob, p string) *Blob {
	if v, ok := m[p]; ok {
		return &v
	}
	return nil
}

// MergeTrees 는 트리 단위 합치기(SPEC.md §12.2). → (결과, 안내 줄들,
// 충돌 경로). 모드는 내용과 따로 같은 세 줄 규칙.
func MergeTrees(gitdir string, base, ours, theirs map[string]Blob,
	label string) (map[string]MergeResult, []string, []string, error) {
	all := map[string]bool{}
	for _, m := range []map[string]Blob{base, ours, theirs} {
		for p := range m {
			all[p] = true
		}
	}
	result := map[string]MergeResult{}
	var notes, conflicts []string
	for _, p := range sortedKeys(all) {
		bv, ov := lookup(base, p), lookup(ours, p)
		tv := lookup(theirs, p)
		if whole, ok := pick(bv, ov, tv); ok {
			if whole == nil {
				result[p] = MergeResult{Gone: true}
			} else {
				result[p] = MergeResult{Blob: *whole}
			}
			continue
		}
		if ov == nil || tv == nil {
			return nil, nil, nil, Fail("fatal: mygit: unsupported " +
				"merge case (modify/delete) in " + p)
		}
		var bm *uint32
		if bv != nil {
			bm = &bv.Mode
		}
		mode, ok := pick(bm, &ov.Mode, &tv.Mode)
		if !ok {
			return nil, nil, nil, Fail("fatal: mygit: unsupported " +
				"merge case (mode) in " + p)
		}
		notes = append(notes, "Auto-merging "+p)
		var data [3][]byte
		for k, v := range []*Blob{bv, ov, tv} {
			if v == nil {
				continue
			}
			_, body, err := ReadObject(gitdir, v.Oid)
			if err != nil {
				return nil, nil, nil, err
			}
			data[k] = body
		}
		text, n := Merge3(data[0], data[1], data[2], label)
		if n == 0 {
			oid, err := WriteObject(gitdir, "blob", text)
			if err != nil {
				return nil, nil, nil, err
			}
			result[p] = MergeResult{Blob: Blob{*mode, oid}}
			continue
		}
		kind := "add/add"
		stages := map[int]Blob{2: *ov, 3: *tv}
		if bv != nil {
			kind = "content"
			stages[1] = *bv
		}
		notes = append(notes, "CONFLICT ("+kind+"): Merge conflict in "+
			p)
		result[p] = MergeResult{Conflict: true, Text: text,
			Stages: stages, Blob: Blob{Mode: *mode}}
		conflicts = append(conflicts, p)
	}
	return result, notes, conflicts, nil
}
