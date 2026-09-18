package mygit

// 객체 (SPEC.md §4.1 · §4.6) — 이름은 내용의 SHA-1 이다.
//
// 이름 = SHA-1("<형식> <크기>\0" + 몸). 느슨한 객체는 그 바이트를
// zlib 으로 눌러 .git/objects/<앞 2글자>/<나머지 38글자> 에 둔다.
// 느슨한 객체에 없으면 팩에서 찾는다 — PackedObjects 는 11단계가
// 채우는 갈고리다(SPEC.md §5.2).

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

var Types = []string{"blob", "tree", "commit", "tag"}

// PackedObjects 는 팩 안 객체 전부 {이름: 객체}. 11단계 전에는 비었다.
var PackedObjects = func(gitdir string) (map[string]Object, error) {
	return nil, nil
}

type Object struct {
	Type string
	Body []byte
}

func header(typ string, body []byte) []byte {
	return []byte(fmt.Sprintf("%s %d\x00", typ, len(body)))
}

// HashObject 는 객체 이름(16진 40글자). 저장소를 건드리지 않는다.
func HashObject(typ string, body []byte) string {
	h := NewSha1()
	h.Update(header(typ, body))
	h.Update(body)
	return fmt.Sprintf("%x", h.Digest())
}

func ObjectPath(gitdir, oid string) string {
	return filepath.Join(gitdir, "objects", oid[:2], oid[2:])
}

// WriteObject 는 느슨한 객체 하나를 쓰고 이름을 돌려준다. 이미
// 있으면 아무것도 하지 않는다 — 이름이 같으면 내용도 같다. 임시
// 파일에 다 쓴 뒤 이름을 바꿔 넣어, 도중에 죽어도 반쪽이 남지 않는다.
func WriteObject(gitdir, typ string, body []byte) (string, error) {
	oid := HashObject(typ, body)
	path := ObjectPath(gitdir, oid)
	if _, err := os.Stat(path); err == nil {
		return oid, nil
	}
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		return "", err
	}
	f, err := os.CreateTemp(dir, "tmp_obj_")
	if err != nil {
		return "", err
	}
	tmp := f.Name()
	_, err = f.Write(Compress(append(header(typ, body), body...)))
	if cerr := f.Close(); err == nil {
		err = cerr
	}
	if err == nil {
		err = os.Chmod(tmp, 0o444)
	}
	if err == nil {
		err = os.Rename(tmp, path)
	}
	if err != nil {
		os.Remove(tmp)
		return "", err
	}
	return oid, nil
}

// parseRaw 는 풀린 바이트 → (형식, 몸). 머리의 크기가 몸과 다르면
// 오류.
func parseRaw(raw []byte, oid string) (string, []byte, error) {
	head, body, ok := bytes.Cut(raw, []byte{0})
	parts := strings.Split(string(head), " ")
	bad := Fail("fatal: mygit: bad object header in " + oid)
	if !ok || len(parts) != 2 || parts[1] == "" {
		return "", nil, bad
	}
	n, err := strconv.Atoi(parts[1])
	if err != nil || strings.Trim(parts[1], "0123456789") != "" {
		return "", nil, bad
	}
	if !isType(parts[0]) || n != len(body) {
		return "", nil, Fail("fatal: mygit: object " + oid +
			" is corrupt")
	}
	return parts[0], body, nil
}

func isType(t string) bool {
	for _, x := range Types {
		if x == t {
			return true
		}
	}
	return false
}

// ReadObject 는 (형식, 몸) — 느슨한 객체를 먼저, 없으면 팩.
func ReadObject(gitdir, oid string) (string, []byte, error) {
	data, err := os.ReadFile(ObjectPath(gitdir, oid))
	if err == nil {
		raw, err := Decompress(data)
		if err != nil {
			return "", nil, err
		}
		return parseRaw(raw, oid)
	}
	packed, err := PackedObjects(gitdir)
	if err != nil {
		return "", nil, err
	}
	if o, ok := packed[oid]; ok {
		return o.Type, o.Body, nil
	}
	return "", nil, Fail("fatal: mygit: object " + oid + " not found")
}

// AllLoose 는 느슨한 객체의 이름 전부, 차례대로.
func AllLoose(gitdir string) []string {
	root := filepath.Join(gitdir, "objects")
	var out []string
	dirs, _ := os.ReadDir(root)
	for _, d := range dirs {
		if len(d.Name()) != 2 {
			continue
		}
		files, _ := os.ReadDir(filepath.Join(root, d.Name()))
		for _, f := range files {
			if len(f.Name()) == 38 {
				out = append(out, d.Name()+f.Name())
			}
		}
	}
	return out
}

// FindObject 는 앞부분(4글자 이상)으로 찾는다: 하나면 그 이름, 없으면
// "". 둘 이상이면 git 처럼 모호하다고 멈춘다. O(객체 수).
func FindObject(gitdir, prefix string) (string, error) {
	p := strings.ToLower(prefix)
	if len(p) < 4 || strings.Trim(p, "0123456789abcdef") != "" {
		return "", nil
	}
	ids := map[string]bool{}
	for _, o := range AllLoose(gitdir) {
		ids[o] = true
	}
	packed, err := PackedObjects(gitdir)
	if err != nil {
		return "", err
	}
	for o := range packed {
		ids[o] = true
	}
	if len(p) == 40 {
		if ids[p] {
			return p, nil
		}
		return "", nil
	}
	var hits []string
	for o := range ids {
		if strings.HasPrefix(o, p) {
			hits = append(hits, o)
		}
	}
	sort.Strings(hits)
	if len(hits) > 1 {
		return "", Fail("error: short object ID " + prefix +
			" is ambiguous")
	}
	if len(hits) == 0 {
		return "", nil
	}
	return hits[0], nil
}
