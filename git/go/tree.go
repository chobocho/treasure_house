package mygit

// tree (SPEC.md §4.3) — 디렉터리 하나를 객체 하나로.
//
// 항목 = "<모드> <이름>\0<객체 이름 20바이트>". 이름과 권한은 blob 이
// 아니라 트리가 갖는다 — 같은 내용의 파일 둘은 blob 하나를 나눠 쓴다.
//
// 정렬 규칙이 전부다. 항목은 이름의 바이트로 정렬하되 하위 트리는
// 이름 뒤에 '/' 가 붙은 것처럼 비교한다. Go 의 string 은 바이트
// 열이라 < 비교가 곧 SPEC 의 바이트 비교다.

import (
	"bytes"
	"encoding/hex"
	"sort"
	"strings"
)

const Dir = "40000"

// TreeEntry 는 트리 몸의 항목 하나, PathEntry 는 인덱스처럼 경로
// 전체를 가진 항목 하나다.
type TreeEntry struct{ Mode, Name, Oid string }
type PathEntry struct{ Mode, Oid, Path string }

// TreeEntryKey 는 정렬 열쇠. 하위 트리는 이름에 '/' 를 붙여 비교한다.
func TreeEntryKey(mode, name string) string {
	if mode == Dir {
		return name + "/"
	}
	return name
}

// ParseTree 는 트리 몸 → 항목들, 적힌 차례 그대로. O(몸의 길이).
func ParseTree(body []byte) ([]TreeEntry, error) {
	var out []TreeEntry
	for i := 0; i < len(body); {
		sp := bytes.IndexByte(body[i:], ' ')
		nul := -1
		if sp >= 0 {
			sp += i
			nul = bytes.IndexByte(body[sp+1:], 0)
		}
		if sp < 0 || nul < 0 || sp+1+nul+21 > len(body) {
			return nil, Fail("fatal: mygit: corrupt tree object")
		}
		nul += sp + 1
		out = append(out, TreeEntry{string(body[i:sp]),
			string(body[sp+1 : nul]),
			hex.EncodeToString(body[nul+1 : nul+21])})
		i = nul + 21
	}
	return out, nil
}

// SerializeTree 는 항목들 → 트리 몸. 정렬은 여기서 한다. 모드는 앞에
// 0 을 붙이지 않는다 — '040000' 은 cat-file -p 가 찍는 꼴일 뿐이다.
func SerializeTree(ents []TreeEntry) []byte {
	s := append([]TreeEntry(nil), ents...)
	sort.Slice(s, func(i, j int) bool {
		return TreeEntryKey(s[i].Mode, s[i].Name) <
			TreeEntryKey(s[j].Mode, s[j].Name)
	})
	var buf bytes.Buffer
	for _, e := range s {
		raw, _ := hex.DecodeString(e.Oid)
		buf.WriteString(e.Mode + " " + e.Name + "\x00")
		buf.Write(raw)
	}
	return buf.Bytes()
}

// WriteTree 는 (모드, blob 이름, 경로) 들 → 뿌리 트리 이름. 경로를
// '/' 로 나눠 디렉터리마다 트리를 짓고 아래에서 위로 쓴다. blob 이
// 있는지는 보지 않는다 — 부르는 쪽이 인덱스에 올릴 때 써 두었다.
// O(항목 수 × 깊이 + 정렬).
func WriteTree(gitdir string, ents []PathEntry) (string, error) {
	var here []TreeEntry
	var order []string
	subdirs := map[string][]PathEntry{}
	for _, e := range ents {
		head, rest, sep := strings.Cut(e.Path, "/")
		if !sep {
			here = append(here, TreeEntry{e.Mode, head, e.Oid})
			continue
		}
		if _, ok := subdirs[head]; !ok {
			order = append(order, head)
		}
		subdirs[head] = append(subdirs[head],
			PathEntry{e.Mode, e.Oid, rest})
	}
	for _, name := range order {
		oid, err := WriteTree(gitdir, subdirs[name])
		if err != nil {
			return "", err
		}
		here = append(here, TreeEntry{Dir, name, oid})
	}
	return WriteObject(gitdir, "tree", SerializeTree(here))
}

// FlattenTree 는 트리를 재귀로 펼친다. 하위 트리는 항목으로 남기지
// 않고 그 안을 펼친다. 차례는 전체 경로의 바이트 차례와 같다.
func FlattenTree(gitdir, oid, prefix string) ([]PathEntry, error) {
	typ, body, err := ReadObject(gitdir, oid)
	if err != nil {
		return nil, err
	}
	if typ != "tree" {
		return nil, Fail("fatal: mygit: " + oid + " is not a tree")
	}
	ents, err := ParseTree(body)
	if err != nil {
		return nil, err
	}
	var out []PathEntry
	for _, e := range ents {
		path := prefix + e.Name
		if e.Mode != Dir {
			out = append(out, PathEntry{e.Mode, e.Oid, path})
			continue
		}
		sub, err := FlattenTree(gitdir, e.Oid, path+"/")
		if err != nil {
			return nil, err
		}
		out = append(out, sub...)
	}
	return out, nil
}

// TypeOfMode 는 cat-file -p 가 찍는 형식 — 모드에서 정해진다.
func TypeOfMode(mode string) string {
	switch mode {
	case Dir:
		return "tree"
	case "160000":
		return "commit"
	}
	return "blob"
}
