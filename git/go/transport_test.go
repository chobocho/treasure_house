package mygit

// 전송의 시험 — SPEC.md §14, 12단계 "pkt-line 으로 진짜 git 과 대화".
// fetch-pack 은 진짜 git upload-pack 을 자식으로 띄워 말한다(PLAN.md
// §9 결정 8 — 서버는 git 이다). golden/pkt/<경우>.log 는 SPEC §14.3 의
// 요청을 그대로 보냈을 때 git 이 돌려준 대화의 기록이고, mygit 의
// 기록은 글자까지 같아야 한다. 받은 팩 바이트와 표준 출력도 같아야
// 한다. 멍청한 clone 은 golden/scen/clone.scn 이 장면 시험으로 본다.

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestS141PktLine(t *testing.T) {
	for in, want := range map[string]string{"a\n": "0006a\n",
		"": "0004"} {
		if got, err := PktLine([]byte(in)); err != nil ||
			string(got) != want {
			t.Errorf("%q → %q %v", in, got, err)
		}
	}
	if got, _ := PktLine(bytes.Repeat([]byte("x"), 65516)); string(
		got[:4]) != "fff0" {
		t.Error("가장 긴 줄")
	}
	_, err := PktLine(bytes.Repeat([]byte("x"), 65517))
	assertGitError(t, err)
	if Render([]byte("command=ls-refs\n")) != `0014command=ls-refs\n` {
		t.Error(Render([]byte("command=ls-refs\n")))
	}
	// 파이썬 repr 의 꼴 — 따옴표 고르기까지 같아야 기록이 같다
	for in, want := range map[string]string{"a'b": `0007a'b`,
		"a'b\"": `0008a\'b"`, "\x00\xff\\\t": `0008\x00\xff\\\t`} {
		if got := Render([]byte(in)); got != want {
			t.Errorf("%q → %s", in, got)
		}
	}
}

// fetchCase 는 golden/pkt/src 를 원본으로, 빈 저장소에서 fetch-pack 을
// 돌린다. → (코드, 표준 출력, 표준 오류, 대화 기록, 로컬 .git).
func fetchCase(t *testing.T, c string) (int, string, string, string,
	string) {
	r := newRepo(t)
	src := filepath.Join(r.tmp, "src", ".git")
	copyTree(t, filepath.Join(goldenDir, "pkt", "src", "git"), src)
	for _, d := range []string{"objects/pack", "refs/tags"} {
		os.MkdirAll(filepath.Join(src, d), 0o755)
	}
	g := filepath.Join(r.root, ".git")
	args := strings.Split(string(gread(t, "pkt", c+".args")), "\n")
	if haves := args[1]; haves != "" {
		// 가진 값 = 로컬 참조. 원본의 객체를 넣고 참조를 세운다
		os.RemoveAll(filepath.Join(g, "objects"))
		copyTree(t, filepath.Join(src, "objects"),
			filepath.Join(g, "objects"))
		UpdateRef(g, "refs/heads/old", haves, "", "test",
			"T <t@t> 0 +0000")
	}
	log := filepath.Join(r.tmp, c+".log")
	r.env["MYGIT_PKT_LOG"] = log
	code, out, err := r.mygit(append([]string{"fetch-pack",
		filepath.Dir(src)}, strings.Fields(args[0])...)...)
	b, _ := os.ReadFile(log)
	return code, out, err, string(b), g
}

func TestS143ConversationMatchesGit(t *testing.T) {
	for _, c := range []string{"full", "two-refs", "have-first"} {
		code, out, err, log, _ := fetchCase(t, c)
		if code != 0 || err != "" ||
			out != string(gread(t, "pkt", c+".stdout")) {
			t.Errorf("%s: %d %q %q", c, code, out, err)
		}
		if log != string(gread(t, "pkt", c+".log")) {
			t.Errorf("%s 대화:\n%s", c, log)
		}
	}
	_, out, _, _, g := fetchCase(t, "full")
	want := gread(t, "pkt", "full.pack")
	name := fmt.Sprintf("pack-%x.pack", want[len(want)-20:])
	got, _ := os.ReadFile(filepath.Join(g, "objects", "pack", name))
	if !bytes.Equal(got, want) {
		t.Fatal("받은 팩이 git 의 것과 다르다")
	}
	if typ, _, err := ReadObject(g, strings.Fields(out)[0]); typ !=
		"commit" {
		t.Fatal(typ, err)
	}
}
