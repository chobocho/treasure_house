package mygit

// 전송 (SPEC.md §14) — 저장소끼리 객체와 참조를 나누는 법.
//
// pkt-line 은 "길이 네 자리 16진 + 데이터" 다. 길이가 자기 4바이트를
// 품는 까닭은 0000(flush)·0001(delim) 같은 특별한 값을 데이터와
// 헷갈리지 않게 하려는 것이다. 여기에는 두 가지가 있다: 협상 없이
// 객체 파일을 그대로 복사하는 "멍청한" 로컬 clone, 그리고 진짜 git
// upload-pack 을 자식으로 띄워 프로토콜 v2 로 말하는 fetch-pack(서버는
// 짜지 않는다 — PLAN.md §9 결정 8).

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
)

var (
	flush = []byte("0000")
	delim = []byte("0001")
)

// PktLine 은 데이터 → pkt-line 한 개.
func PktLine(data []byte) ([]byte, error) {
	if len(data) > 65516 {
		return nil, Fail("fatal: mygit: pkt-line too long")
	}
	return append([]byte(fmt.Sprintf("%04x", len(data)+4)), data...),
		nil
}

// Render 는 대화 기록의 꼴(SPEC.md §14.3) — 길이 + 파이썬 repr 식
// 이스케이프. 기준 기록을 파이썬이 썼으므로 따옴표 고르기까지 따른다:
// 작은따옴표만 있고 큰따옴표가 없으면 repr 은 큰따옴표로 감싸고 '
// 를 그대로 둔다.
func Render(data []byte) string {
	quote := byte('\'')
	if bytes.IndexByte(data, '\'') >= 0 &&
		bytes.IndexByte(data, '"') < 0 {
		quote = '"'
	}
	var b strings.Builder
	fmt.Fprintf(&b, "%04x", len(data)+4)
	for _, c := range data {
		switch {
		case c == '\\' || c == quote:
			b.WriteByte('\\')
			b.WriteByte(c)
		case c == '\t':
			b.WriteString(`\t`)
		case c == '\n':
			b.WriteString(`\n`)
		case c == '\r':
			b.WriteString(`\r`)
		case c < 32 || c >= 127:
			fmt.Fprintf(&b, `\x%02x`, c)
		default:
			b.WriteByte(c)
		}
	}
	return b.String()
}

// ── 멍청한 로컬 clone (SPEC.md §14.2) ─────────────────────────────

func srcGitdir(src string) string {
	g := filepath.Join(src, ".git")
	if st, err := os.Stat(g); err == nil && st.IsDir() {
		return g
	}
	return src
}

func copyFile(from, to string) error {
	data, err := os.ReadFile(from)
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(to), 0o755); err != nil {
		return err
	}
	return os.WriteFile(to, data, 0o644)
}

// CloneLocal 은 src 의 객체 파일을 그대로 복사하고 참조를 세운다.
// → 브랜치 이름. 협상이 없다 — 받는 쪽이 이미 가진 것도 다시
// 복사한다. 그래도 객체의 이름이 곧 내용이므로 옮긴 파일은 어느
// 저장소에서나 같은 객체다.
func CloneLocal(src, dst, ident string) (string, error) {
	sg := srcGitdir(src)
	g := filepath.Join(dst, ".git")
	err := filepath.Walk(filepath.Join(sg, "objects"),
		func(p string, i os.FileInfo, err error) error {
			if err != nil || i.IsDir() {
				return err
			}
			rel, _ := filepath.Rel(sg, p)
			if filepath.Base(filepath.Dir(p)) == "pack" &&
				!strings.HasSuffix(p, ".pack") &&
				!strings.HasSuffix(p, ".idx") {
				return nil
			}
			return copyFile(p, filepath.Join(g, rel))
		})
	if err != nil {
		return "", err
	}
	branch := ""
	if h := ReadRef(sg, "HEAD"); h != nil && h.Sym {
		branch = strings.TrimPrefix(h.Val, "refs/heads/")
	}
	for _, r := range ListRefs(sg, "refs/") {
		local := ""
		switch {
		case strings.HasPrefix(r.Name, "refs/heads/"):
			local = "refs/remotes/origin/" +
				strings.TrimPrefix(r.Name, "refs/heads/")
		case strings.HasPrefix(r.Name, "refs/tags/"):
			local = r.Name
		default:
			continue
		}
		path := filepath.Join(g, local)
		os.MkdirAll(filepath.Dir(path), 0o755)
		if err := os.WriteFile(path, []byte(r.Oid+"\n"),
			0o644); err != nil {
			return "", err
		}
	}
	if branch == "" {
		return "", Fail("fatal: mygit: source HEAD is detached")
	}
	err = os.WriteFile(filepath.Join(g, "refs", "remotes", "origin",
		"HEAD"), []byte("ref: refs/remotes/origin/"+branch+"\n"), 0o644)
	if err != nil {
		return "", err
	}
	oid, err := ResolveRef(sg, "refs/heads/"+branch)
	if err != nil {
		return "", err
	}
	abs, _ := filepath.Abs(src)
	if err := SetHead(g, "refs/heads/"+branch); err != nil {
		return "", err
	}
	if err := UpdateRef(g, "refs/heads/"+branch, oid, "",
		"clone: from "+abs, ident); err != nil {
		return "", err
	}
	f, err := os.OpenFile(filepath.Join(g, "config"),
		os.O_WRONLY|os.O_APPEND, 0o644)
	if err != nil {
		return "", err
	}
	fmt.Fprintf(f, "[remote \"origin\"]\n\turl = %s\n"+
		"\tfetch = +refs/heads/*:refs/remotes/origin/*\n"+
		"[branch \"%s\"]\n\tremote = origin\n\tmerge = refs/heads/%s\n",
		abs, branch, branch)
	f.Close()
	t, err := Peel(g, oid, "tree")
	if err != nil {
		return "", err
	}
	return branch, CheckoutTree(dst, g, "", t)
}

// ── fetch-pack: 프로토콜 v2 (SPEC.md §14.3) ───────────────────────

// wire 는 자식 upload-pack 과의 pkt-line 대화. 기록은 §14.3 의 꼴.
type wire struct {
	cmd     *exec.Cmd
	in      io.WriteCloser
	out     io.Reader
	log     []string
	logPath string
}

func newWire(src string, env map[string]string,
	logPath string) (*wire, error) {
	cmd := exec.Command("git", "upload-pack", src)
	for k, v := range env {
		cmd.Env = append(cmd.Env, k+"="+v)
	}
	cmd.Env = append(cmd.Env, "GIT_PROTOCOL=version=2")
	in, err := cmd.StdinPipe()
	if err != nil {
		return nil, err
	}
	out, err := cmd.StdoutPipe()
	if err != nil {
		return nil, err
	}
	if err := cmd.Start(); err != nil {
		return nil, err
	}
	return &wire{cmd: cmd, in: in, out: out, logPath: logPath}, nil
}

func (w *wire) send(items [][]byte) error {
	var buf bytes.Buffer
	for _, it := range items {
		if bytes.Equal(it, flush) || bytes.Equal(it, delim) {
			w.log = append(w.log, "> "+string(it))
			buf.Write(it)
			continue
		}
		w.log = append(w.log, "> "+Render(it))
		p, err := PktLine(it)
		if err != nil {
			return err
		}
		buf.Write(p)
	}
	_, err := w.in.Write(buf.Bytes())
	return err
}

func (w *wire) exact(n int) ([]byte, error) {
	b := make([]byte, n)
	if _, err := io.ReadFull(w.out, b); err != nil {
		return nil, Fail("fatal: mygit: remote hung up unexpectedly")
	}
	return b, nil
}

// read 는 flush 까지의 패킷들. packfile 절 뒤의 사이드밴드 1 은
// packbuf 로 모은다(2 는 진행 안내, 3 은 원격의 오류).
func (w *wire) read(packbuf *bytes.Buffer) ([][]byte, error) {
	var lines [][]byte
	side := false
	for {
		head, err := w.exact(4)
		if err != nil {
			return nil, err
		}
		n64, err := strconv.ParseUint(string(head), 16, 16)
		if err != nil {
			return nil, Fail("fatal: mygit: bad pkt-line length")
		}
		n := int(n64)
		if n < 4 {
			w.log = append(w.log, fmt.Sprintf("< %04x", n))
			if n == 0 {
				return lines, nil
			}
			continue
		}
		data, err := w.exact(n - 4)
		if err != nil {
			return nil, err
		}
		if side && data[0] == 1 {
			packbuf.Write(data[1:])
			w.log = append(w.log, fmt.Sprintf("< %04x [pack %d bytes]",
				n, n-5))
			continue
		}
		if side && data[0] == 3 {
			return nil, Fail("fatal: mygit: remote error: " +
				string(data[1:]))
		}
		w.log = append(w.log, "< "+Render(data))
		if string(data) == "packfile\n" {
			side = packbuf != nil
		}
		lines = append(lines, data)
	}
}

func (w *wire) close() error {
	w.in.Close()
	w.cmd.Wait()
	if w.logPath == "" {
		return nil
	}
	return os.WriteFile(w.logPath,
		[]byte(strings.Join(w.log, "\n")+"\n"), 0o644)
}

// FetchPack 은 wantRefs 를 받아 팩을 저장한다. → "이름 참조" 쌍들.
// 참조는 고치지 않는다 — 그것은 fetch 의 일이다(SPEC.md §14.3 의 5).
func FetchPack(gitdir, src string, wantRefs []string,
	env map[string]string, logPath string) ([][2]string, error) {
	w, err := newWire(src, env, logPath)
	if err != nil {
		return nil, err
	}
	defer w.cmd.Process.Kill()
	caps, err := w.read(nil)
	if err != nil {
		return nil, err
	}
	v2 := len(caps) > 0 && string(caps[0]) == "version 2\n"
	fetch := false
	for _, c := range caps {
		fetch = fetch || bytes.HasPrefix(c, []byte("fetch"))
	}
	if !v2 || !fetch {
		return nil, Fail("fatal: mygit: server does not speak " +
			"protocol v2")
	}
	req := [][]byte{[]byte("command=ls-refs\n"),
		[]byte("object-format=sha1\n"), delim, []byte("peel\n"),
		[]byte("symrefs\n")}
	for _, r := range wantRefs {
		req = append(req, []byte("ref-prefix "+r+"\n"))
	}
	if err := w.send(append(req, flush)); err != nil {
		return nil, err
	}
	lines, err := w.read(nil)
	if err != nil {
		return nil, err
	}
	adv := map[string]string{}
	for _, line := range lines {
		f := strings.Split(strings.TrimSuffix(string(line), "\n"), " ")
		adv[f[1]] = f[0]
	}
	var wants, haves []string
	has := func(xs []string, x string) bool {
		for _, y := range xs {
			if y == x {
				return true
			}
		}
		return false
	}
	for _, r := range wantRefs {
		oid, ok := adv[r]
		if !ok {
			return nil, Fail("fatal: mygit: no such remote ref " + r)
		}
		if !has(wants, oid) {
			wants = append(wants, oid)
		}
	}
	for _, r := range ListRefs(gitdir, "refs/") {
		if !has(haves, r.Oid) {
			haves = append(haves, r.Oid)
		}
	}
	req = [][]byte{[]byte("command=fetch\n"),
		[]byte("object-format=sha1\n"), delim, []byte("ofs-delta\n"),
		[]byte("no-progress\n")}
	for _, o := range wants {
		req = append(req, []byte("want "+o+"\n"))
	}
	for _, o := range haves {
		req = append(req, []byte("have "+o+"\n"))
	}
	req = append(req, []byte("done\n"), flush)
	if err := w.send(req); err != nil {
		return nil, err
	}
	var buf bytes.Buffer
	if _, err := w.read(&buf); err != nil {
		return nil, err
	}
	if err := w.close(); err != nil {
		return nil, err
	}
	data := buf.Bytes()
	ents, err := ReadPack(data, func(o string) (string, []byte, error) {
		return ReadObject(gitdir, o)
	})
	if err != nil {
		return nil, err
	}
	stem := filepath.Join(gitdir, "objects", "pack",
		fmt.Sprintf("pack-%x", data[len(data)-20:]))
	if err := os.MkdirAll(filepath.Dir(stem), 0o755); err != nil {
		return nil, err
	}
	err = os.WriteFile(stem+".pack", data, 0o644)
	if err == nil {
		err = os.WriteFile(stem+".idx", WriteIdx(ents,
			data[len(data)-20:]), 0o644)
	}
	if err != nil {
		return nil, err
	}
	var got [][2]string
	for _, r := range wantRefs {
		got = append(got, [2]string{adv[r], r})
	}
	return got, nil
}
