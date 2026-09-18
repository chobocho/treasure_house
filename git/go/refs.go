package mygit

// 참조 (SPEC.md §6) — 브랜치는 40글자가 든 파일 하나다.
//
// refs/heads/main 은 커밋 이름 한 줄이고, HEAD 는 보통 "ref: refs/
// heads/main" 이라는 이름표를 가리키는 이름표다. gc 뒤의 저장소는
// 참조를 packed-refs 한 파일에 모아 두므로 읽을 때는 둘 다 본다
// (느슨한 파일이 이긴다). 쓸 때는 느슨한 파일만 쓴다.

import (
	"errors"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

var Zero = strings.Repeat("0", 40)

func readText(path string) (string, bool) {
	b, err := os.ReadFile(path)
	return string(b), err == nil
}

// PackedRefs 는 packed-refs → {이름: 40글자}. '#' 머리와 '^' 줄은
// 건너뛴다.
func PackedRefs(gitdir string) map[string]string {
	text, _ := readText(filepath.Join(gitdir, "packed-refs"))
	out := map[string]string{}
	for _, line := range strings.Split(text, "\n") {
		if line == "" || line[0] == '#' || line[0] == '^' {
			continue
		}
		oid, name, _ := strings.Cut(line, " ")
		out[name] = oid
	}
	return out
}

// Ref 는 참조 파일 하나의 값 — Sym 이면 대상 이름, 아니면 Oid.
type Ref struct {
	Sym bool
	Val string
}

// ReadRef 는 참조 하나. 없으면 nil. 느슨한 파일이 먼저다.
func ReadRef(gitdir, name string) *Ref {
	if text, ok := readText(filepath.Join(gitdir, name)); ok {
		text = strings.TrimSpace(text)
		if strings.HasPrefix(text, "ref: ") {
			return &Ref{true, text[5:]}
		}
		return &Ref{false, text}
	}
	if oid := PackedRefs(gitdir)[name]; oid != "" {
		return &Ref{false, oid}
	}
	return nil
}

// ResolveRef 는 심볼릭 참조를 따라가 40글자. 없거나 태어나지 않았으면
// "".
func ResolveRef(gitdir, name string) (string, error) {
	for i := 0; i < 5; i++ {
		r := ReadRef(gitdir, name)
		if r == nil {
			return "", nil
		}
		if !r.Sym {
			return r.Val, nil
		}
		name = r.Val
	}
	return "", Fail("fatal: mygit: symbolic ref loop at " + name)
}

// ReadHead 는 (HEAD 가 가리키는 브랜치 참조 이름 또는 "", 커밋 또는
// "").
func ReadHead(gitdir string) (string, string, error) {
	r := ReadRef(gitdir, "HEAD")
	if r == nil {
		return "", "", Fail("fatal: mygit: HEAD is missing")
	}
	if !r.Sym {
		return "", r.Val, nil
	}
	oid, err := ResolveRef(gitdir, r.Val)
	return r.Val, oid, err
}

type NamedRef struct{ Name, Oid string }

// ListRefs 는 prefix 아래 참조들, 이름의 바이트 차례.
func ListRefs(gitdir, prefix string) []NamedRef {
	found := map[string]string{}
	for n, o := range PackedRefs(gitdir) {
		if strings.HasPrefix(n, prefix) {
			found[n] = o
		}
	}
	filepath.WalkDir(filepath.Join(gitdir, prefix),
		func(p string, d fs.DirEntry, err error) error {
			if err != nil || d.IsDir() ||
				strings.HasSuffix(p, ".lock") {
				return nil
			}
			rel, _ := filepath.Rel(gitdir, p)
			name := filepath.ToSlash(rel)
			if oid, _ := ResolveRef(gitdir, name); oid != "" {
				found[name] = oid
			}
			return nil
		})
	var out []NamedRef
	for n, o := range found {
		out = append(out, NamedRef{n, o})
	}
	sort.Slice(out, func(i, j int) bool {
		return out[i].Name < out[j].Name
	})
	return out
}

// writeLocked 는 <경로>.lock 에 쓰고 이름을 바꿔 넣는다(SPEC §6.1).
func writeLocked(path, text string) error {
	os.MkdirAll(filepath.Dir(path), 0o755)
	lock := path + ".lock"
	f, err := os.OpenFile(lock, os.O_WRONLY|os.O_CREATE|os.O_EXCL,
		0o666)
	if errors.Is(err, fs.ErrExist) {
		return Fail("fatal: mygit: unable to lock " + path)
	}
	if err != nil {
		return err
	}
	_, err = f.WriteString(text)
	f.Close()
	if err != nil {
		return err
	}
	return os.Rename(lock, path)
}

// AppendReflog 는 reflog 한 줄(SPEC.md §6.3) — "옛 새 신원<TAB>메시지".
func AppendReflog(gitdir, name, old, new, ident, msg string) error {
	path := filepath.Join(gitdir, "logs", name)
	os.MkdirAll(filepath.Dir(path), 0o755)
	f, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_APPEND,
		0o644)
	if err != nil {
		return err
	}
	defer f.Close()
	if old == "" {
		old = Zero
	}
	if new == "" {
		new = Zero
	}
	_, err = fmt.Fprintf(f, "%s %s %s\t%s\n", old, new, ident, msg)
	return err
}

type ReflogEntry struct{ Old, New, Ident, Msg string }

// ReadReflog 는 오래된 것부터. 없으면 빈 목록.
func ReadReflog(gitdir, name string) []ReflogEntry {
	text, _ := readText(filepath.Join(gitdir, "logs", name))
	var out []ReflogEntry
	for _, line := range strings.Split(text, "\n") {
		if line == "" {
			continue
		}
		head, msg, _ := strings.Cut(line, "\t")
		f := strings.SplitN(head, " ", 3)
		out = append(out, ReflogEntry{f[0], f[1], f[2], msg})
	}
	return out
}

// UpdateRef 는 참조 하나를 바꾸고 reflog 를 남긴다. new 가 "" 이면
// 지운다. HEAD 가 이 브랜치를 가리키고 있으면 HEAD 의 reflog 에도 같은
// 줄을 남긴다 — 커밋 하나가 두 로그에 모두 보이는 까닭.
func UpdateRef(gitdir, name, new, old, msg, ident string) error {
	path := filepath.Join(gitdir, name)
	if new == "" {
		if _, err := os.Stat(path); err != nil {
			return Fail("fatal: mygit: cannot delete packed ref " +
				name)
		}
		os.Remove(filepath.Join(gitdir, "logs", name))
		return os.Remove(path)
	}
	if err := writeLocked(path, new+"\n"); err != nil {
		return err
	}
	if err := AppendReflog(gitdir, name, old, new, ident,
		msg); err != nil {
		return err
	}
	if h := ReadRef(gitdir, "HEAD"); name != "HEAD" && h != nil &&
		h.Sym && h.Val == name {
		return AppendReflog(gitdir, "HEAD", old, new, ident, msg)
	}
	return nil
}

// SetHead 는 HEAD 를 브랜치(refs/heads/…)나 커밋(분리)으로. reflog
// 는 부르는 쪽이 적는다 — 메시지가 명령마다 다르다(§6.3 의 표).
func SetHead(gitdir, target string) error {
	if strings.HasPrefix(target, "refs/") {
		target = "ref: " + target
	}
	return writeLocked(filepath.Join(gitdir, "HEAD"), target+"\n")
}

// ── 이름 풀기 (SPEC.md §6.2) ───────────────────────────────────────

func isHex40(s string) bool {
	return len(s) == 40 && strings.Trim(s, "0123456789abcdef") == ""
}

// base 는 뒤붙이 없는 이름 → 40글자 또는 "". §6.2 의 1‥5 차례.
func base(gitdir, name string) (string, error) {
	if isHex40(name) {
		if o, _ := FindObject(gitdir, name); o != "" {
			return o, nil
		}
	}
	switch name {
	case "HEAD", "ORIG_HEAD", "MERGE_HEAD":
		return ResolveRef(gitdir, name)
	}
	if strings.HasPrefix(name, "refs/") {
		if o, err := ResolveRef(gitdir, name); o != "" || err != nil {
			return o, err
		}
	}
	for _, f := range []string{"refs/tags/%s", "refs/heads/%s",
		"refs/remotes/%s", "refs/remotes/%s/HEAD"} {
		o, err := ResolveRef(gitdir, fmt.Sprintf(f, name))
		if o != "" || err != nil {
			return o, err
		}
	}
	o, _ := FindObject(gitdir, name) // 모호한 앞부분은 풀지 못한 것
	return o, nil
}

// Peel 은 태그를 벗겨 want('commit'·'tree')를 얻는다. 못 얻으면 "".
func Peel(gitdir, oid, want string) (string, error) {
	for i := 0; i < 10; i++ {
		typ, body, err := ReadObject(gitdir, oid)
		if err != nil {
			return "", err
		}
		first, _, _ := strings.Cut(string(body), "\n")
		switch {
		case typ == want:
			return oid, nil
		case typ == "tag":
			oid = first[7:]
		case typ == "commit" && want == "tree":
			oid = first[5:]
		default:
			return "", nil
		}
	}
	return "", nil
}

func parentsOf(gitdir, oid string) ([]string, error) {
	_, body, err := ReadObject(gitdir, oid)
	if err != nil {
		return nil, err
	}
	c, err := ParseCommit(body)
	if err != nil {
		return nil, err
	}
	return c.Parents, nil
}

// RevParse 는 <rev> → 40글자 또는 "". ~n · ^n · ^0 · ^{tree} ·
// ^{commit}. 뒤붙이는 왼쪽부터 차례로 적용한다.
// O(뒤붙이의 길이 × 객체 읽기).
func RevParse(gitdir, spec string) (string, error) {
	i := strings.IndexAny(spec, "~^")
	if i < 0 {
		i = len(spec)
	}
	if i == 0 {
		return "", nil
	}
	oid, err := base(gitdir, spec[:i])
	for oid != "" && err == nil && i < len(spec) {
		op := spec[i]
		i++
		if op == '^' && i < len(spec) && spec[i] == '{' {
			end := strings.IndexByte(spec[i:], '}')
			if end < 0 {
				return "", nil
			}
			want := spec[i+1 : i+end]
			i += end + 1
			if want == "" {
				want = "commit"
			}
			oid, err = Peel(gitdir, oid, want)
			continue
		}
		j := i
		for j < len(spec) && spec[j] >= '0' && spec[j] <= '9' {
			j++
		}
		n := 1
		if j > i {
			n, _ = strconv.Atoi(spec[i:j])
		}
		i = j
		if oid, err = Peel(gitdir, oid, "commit"); oid == "" {
			break
		}
		if op == '~' {
			for k := 0; k < n && oid != "" && err == nil; k++ {
				var ps []string
				ps, err = parentsOf(gitdir, oid)
				oid = ""
				if len(ps) > 0 {
					oid = ps[0]
				}
			}
		} else if n > 0 {
			var ps []string
			ps, err = parentsOf(gitdir, oid)
			oid = ""
			if n <= len(ps) {
				oid = ps[n-1]
			}
		}
	}
	if err != nil {
		return "", err
	}
	return oid, nil
}

// ValidBranchName 은 SPEC.md §9.2 의 브랜치 이름 규칙
// (check-ref-format 의 일부).
func ValidBranchName(name string) bool {
	if name == "" || name == "@" || strings.Contains(name, "..") ||
		strings.Contains(name, "@{") ||
		strings.Contains(name, "//") {
		return false
	}
	for i := 0; i < len(name); i++ {
		c := name[i]
		if c < 32 || c == 127 || strings.IndexByte(" ~^:?*[\\",
			c) >= 0 {
			return false
		}
	}
	return !strings.ContainsRune("-./", rune(name[0])) &&
		!strings.HasSuffix(name, "/") &&
		!strings.HasSuffix(name, ".") &&
		!strings.HasSuffix(name, ".lock")
}
