package mygit

// 작업 트리 (SPEC.md §8) — 경로 따옴표, 훑기, status.
//
// status 는 세 가지를 견준다: HEAD 트리, 인덱스, 디스크의 파일. 두 칸
// 글자(XY)가 곧 "어느 두 곳이 다른가" 다 — X 는 HEAD 와 인덱스, Y 는
// 인덱스와 작업 트리.

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

// \a \b \t \n \v \f \r 와 따옴표·역슬래시는 두 글자로 쓴다
var short = map[byte]byte{7: 'a', 8: 'b', 9: 't', 10: 'n', 11: 'v',
	12: 'f', 13: 'r', 34: '"', 92: '\\'}

// QuotePath 는 경로 → git 이 사람에게 찍는 꼴 (core.quotePath=true).
// 제어 문자·DEL·따옴표·역슬래시·0x80 이상 바이트가 하나라도 있으면
// 전체를 따옴표로 감싸고 C 식으로 쓴다(8진 세 자리). space 는 status
// 의 규칙 — 공백만 있어도 감싼다. O(경로 길이).
func QuotePath(path string, space bool) string {
	need := space && strings.IndexByte(path, ' ') >= 0
	var b strings.Builder
	for i := 0; i < len(path); i++ {
		c := path[i]
		if s, ok := short[c]; ok {
			b.WriteByte('\\')
			b.WriteByte(s)
			need = true
		} else if c < 32 || c >= 127 {
			fmt.Fprintf(&b, "\\%03o", c)
			need = true
		} else {
			b.WriteByte(c)
		}
	}
	if need {
		return "\"" + b.String() + "\""
	}
	return b.String()
}

// WalkWorktree 는 작업 트리의 보통 파일 경로들, 전체 경로의 바이트
// 차례. 어느 깊이에서든 '.git' 은 건너뛰고, 심볼릭 링크와 장치 파일은
// 없는 것으로 본다(SPEC.md §8.1). O(파일 수 · log).
func WalkWorktree(root string) []string {
	var out []string
	var visit func(dir, prefix string)
	visit = func(dir, prefix string) {
		ents, _ := os.ReadDir(dir)
		for _, e := range ents {
			switch {
			case e.Name() == ".git":
			case e.Type()&fs.ModeSymlink != 0:
			case e.IsDir():
				visit(filepath.Join(dir, e.Name()),
					prefix+e.Name()+"/")
			case e.Type().IsRegular():
				out = append(out, prefix+e.Name())
			}
		}
	}
	visit(root, "")
	sort.Strings(out)
	return out
}

// Blob 은 경로 하나의 (모드, 이름) — 트리·인덱스·디스크를 견줄 때의
// 값. 비교할 수 있는 구조체라 == 로 견준다.
type Blob struct {
	Mode uint32
	Oid  string
}

// FileState 는 디스크 파일의 (모드, blob 이름), 없으면 false. 늘
// 해시한다 — stat 캐시를 믿지 않으니 racy git 이 없다(SPEC.md §7.2).
func FileState(root, path string) (Blob, bool) {
	p := filepath.Join(root, path)
	st, err := os.Lstat(p)
	if err != nil || !st.Mode().IsRegular() {
		return Blob{}, false
	}
	data, err := os.ReadFile(p)
	if err != nil {
		return Blob{}, false
	}
	mode := uint32(0o100644)
	if st.Mode()&0o100 != 0 {
		mode = 0o100755
	}
	return Blob{mode, HashObject("blob", data)}, true
}

// unmerged 는 충돌 경로의 두 글자 — 단계 1·2·3 이 있는가(비트 0·1·2)
// → XY (git 과 같다).
var unmerged = map[int]string{6: "AA", 7: "UU", 3: "UD", 5: "DU",
	2: "AU", 4: "UA", 1: "DD"}

// untracked 는 추적하지 않는 파일들을 git 의 normal 모드로 접는다
// (§8.3). 파일마다 위쪽 디렉터리부터 보며, 그 아래에 인덱스 항목이
// 하나도 없는 첫 디렉터리가 있으면 "그 디렉터리/" 로 접는다.
// O(파일 × 깊이).
func untracked(files []string, tracked map[string]bool) []string {
	dirs := map[string]bool{}
	for t := range tracked {
		for i := 0; i < len(t); i++ {
			if t[i] == '/' {
				dirs[t[:i]] = true
			}
		}
	}
	seen := map[string]bool{}
	var out []string
	for _, f := range files {
		if tracked[f] {
			continue
		}
		shown := f
		for i := 0; i < len(f); i++ {
			if f[i] == '/' && !dirs[f[:i]] {
				shown = f[:i+1]
				break
			}
		}
		if !seen[shown] {
			seen[shown] = true
			out = append(out, shown)
		}
	}
	sort.Strings(out)
	return out
}

// TreeMap 은 트리 → {경로: Blob}. 트리가 없으면(첫 커밋 전) 빈 것.
func TreeMap(gitdir, tree string) (map[string]Blob, error) {
	out := map[string]Blob{}
	if tree == "" {
		return out, nil
	}
	ents, err := FlattenTree(gitdir, tree, "")
	if err != nil {
		return nil, err
	}
	for _, e := range ents {
		m, _ := strconv.ParseUint(e.Mode, 8, 32)
		out[e.Path] = Blob{uint32(m), e.Oid}
	}
	return out, nil
}

// headTree 는 HEAD 커밋의 트리, 태어나지 않았으면 "".
func headTree(gitdir string) (string, error) {
	_, head, err := ReadHead(gitdir)
	if err != nil || head == "" {
		return "", err
	}
	return Peel(gitdir, head, "tree")
}

// Status 는 git status --porcelain 과 같은 줄들(SPEC.md §8.3).
// X = HEAD 트리 ↔ 인덱스, Y = 인덱스 ↔ 작업 트리. 추적 중인 것을
// 경로 차례로 먼저, 그다음 '?? ' 줄들. O(파일 수 × 해시).
func Status(root, gitdir string) ([]string, error) {
	t, err := headTree(gitdir)
	if err != nil {
		return nil, err
	}
	base, err := TreeMap(gitdir, t)
	if err != nil {
		return nil, err
	}
	ents, err := ReadIndex(gitdir)
	if err != nil {
		return nil, err
	}
	stage0, stages := map[string]Blob{}, map[string]int{}
	all := map[string]bool{}
	for p := range base {
		all[p] = true
	}
	for _, e := range ents {
		all[e.Path] = true
		if e.Stage > 0 {
			stages[e.Path] |= 1 << (e.Stage - 1)
		} else {
			stage0[e.Path] = Blob{e.Mode, e.Oid}
		}
	}
	var rows []string
	tracked := map[string]bool{}
	for _, p := range sortedKeys(all) {
		var xy string
		if bits, ok := stages[p]; ok {
			xy = unmerged[bits]
			tracked[p] = true
		} else {
			cur, inIdx := stage0[p]
			old, inBase := base[p]
			x, y := " ", " "
			switch {
			case !inIdx:
				x = "D"
			case !inBase:
				x = "A"
			case cur != old:
				x = "M"
			}
			if inIdx {
				tracked[p] = true
				now, ok := FileState(root, p)
				if !ok {
					y = "D"
				} else if now != cur {
					y = "M"
				}
			}
			xy = x + y
		}
		if xy != "  " {
			rows = append(rows, xy+" "+QuotePath(p, true))
		}
	}
	for _, p := range untracked(WalkWorktree(root), tracked) {
		rows = append(rows, "?? "+QuotePath(p, true))
	}
	return rows, nil
}

func sortedKeys[V any](m map[string]V) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}

const (
	overwriteMsg = "error: Your local changes to the following files " +
		"would be overwritten by checkout:"
	untrackedMsg = "error: The following untracked working tree " +
		"files would be overwritten by checkout:"
)

func writeFile(root, path string, mode uint32, data []byte) error {
	full := filepath.Join(root, path)
	if err := os.MkdirAll(filepath.Dir(full), 0o755); err != nil {
		return err
	}
	os.Remove(full)
	// 0666/0777 로 열고 umask 를 따른다 — git 과 같다(SPEC.md §9.3)
	perm := os.FileMode(0o666)
	if mode&0o100 != 0 {
		perm = 0o777
	}
	return os.WriteFile(full, data, perm)
}

// removeFile 은 파일을 지우고, 그래서 비게 된 디렉터리들도 지운다.
func removeFile(root, path string) {
	full := filepath.Join(root, path)
	os.Remove(full)
	for d := filepath.Dir(full); d != root; d = filepath.Dir(d) {
		if os.Remove(d) != nil { // 비지 않았으면 실패한다
			break
		}
	}
}

// CheckoutTree 는 두 갈래 합치기로 작업 트리·인덱스를 old → new 로
// (SPEC.md §9.3). 경로마다: 옛 트리와 새 트리에서 같으면 손대지
// 않는다(손댄 내용이 따라온다). 다르면 인덱스가 옛 트리와 같고 작업
// 트리가 인덱스와 같아야 한다. 옛 트리에 없던 경로에 추적 안 하는
// 파일이 있으면 그것도 막는다. 하나라도 걸리면 아무것도 바꾸지 않고
// 멈춘다. O(경로 수 × 해시).
func CheckoutTree(root, gitdir, oldTree, newTree string) error {
	old, err := TreeMap(gitdir, oldTree)
	if err != nil {
		return err
	}
	nw, err := TreeMap(gitdir, newTree)
	if err != nil {
		return err
	}
	ents, err := ReadIndex(gitdir)
	if err != nil {
		return err
	}
	idx := map[string]*IndexEntry{}
	conflicted := map[string]bool{}
	all := map[string]bool{}
	for _, e := range ents {
		all[e.Path] = true
		if e.Stage > 0 {
			conflicted[e.Path] = true
		} else {
			idx[e.Path] = e
		}
	}
	for p := range old {
		all[p] = true
	}
	for p := range nw {
		all[p] = true
	}
	var local, stray []string
	for _, p := range sortedKeys(all) {
		o, inOld := old[p]
		n, inNew := nw[p]
		if inOld == inNew && o == n {
			continue
		}
		e, inIdx := idx[p]
		disk, onDisk := FileState(root, p)
		switch {
		case conflicted[p]:
			local = append(local, p)
		case !inIdx && !inOld:
			if onDisk && inNew {
				stray = append(stray, p)
			}
		case !inIdx || Blob{e.Mode, e.Oid} != o || !inOld ||
			!onDisk || disk != (Blob{e.Mode, e.Oid}):
			local = append(local, p)
		}
	}
	if len(local)+len(stray) > 0 {
		var rows []string
		for _, part := range []struct {
			head  string
			paths []string
		}{{overwriteMsg, local}, {untrackedMsg, stray}} {
			if len(part.paths) == 0 {
				continue
			}
			rows = append(rows, part.head)
			for _, q := range part.paths {
				rows = append(rows, "\t"+QuotePath(q, false))
			}
			rows = append(rows, "")
		}
		rows = append(rows, "Aborting")
		return &GitError{strings.Join(rows, "\n"), 1}
	}
	for _, p := range sortedKeys(all) {
		o, inOld := old[p]
		n, inNew := nw[p]
		if inOld == inNew && o == n {
			continue
		}
		if !inNew {
			if inOld {
				removeFile(root, p)
				delete(idx, p)
			}
			continue
		}
		_, data, err := ReadObject(gitdir, n.Oid)
		if err != nil {
			return err
		}
		if err := writeFile(root, p, n.Mode, data); err != nil {
			return err
		}
		e, err := EntryFromStat(p, filepath.Join(root, p), n.Oid)
		if err != nil {
			return err
		}
		idx[p] = e
	}
	var out []*IndexEntry
	for _, e := range idx {
		out = append(out, e)
	}
	return WriteIndex(gitdir, out)
}

// LocalChanges 는 바꾼 뒤 남은 변경 — "M\t경로" 줄들(§9.3 끝). 새
// HEAD 트리와 견주어 인덱스나 작업 트리가 다른 추적 경로. M 은 내용·
// 모드, D 는 작업 트리에 없음, A 는 인덱스에만 있음.
func LocalChanges(root, gitdir, headTree string) ([]string, error) {
	head, err := TreeMap(gitdir, headTree)
	if err != nil {
		return nil, err
	}
	ents, err := ReadIndex(gitdir)
	if err != nil {
		return nil, err
	}
	var rows []string
	for _, e := range ents {
		if e.Stage > 0 {
			continue
		}
		cur := Blob{e.Mode, e.Oid}
		disk, onDisk := FileState(root, e.Path)
		h, inHead := head[e.Path]
		letter := ""
		switch {
		case !onDisk:
			letter = "D"
		case !inHead:
			letter = "A"
		case h != cur || disk != cur:
			letter = "M"
		default:
			continue
		}
		rows = append(rows, letter+"\t"+QuotePath(e.Path, false))
	}
	return rows, nil
}
