package mygit

// commit·tag·신원 줄과 참조의 시험 — SPEC.md §4.4 · §4.5 · §6, 5단계.
// 가장 강한 오라클은 "같은 입력에서 같은 이름" 이다. golden/objects
// 의 커밋과 태그는 고정 환경에서 진짜 git 이 만들었다 — 같은 트리·
// 같은 환경으로 만든 mygit 의 것은 바이트까지 같아야 한다.

import (
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"
)

const (
	goldCommit = "b23b7a5fefc32902eb83feac2800cf158140dcb1"
	goldTag    = "5702a431dba432bfe47c3b3fdda3835a8f542f5c"
	mitter     = "C O Mitter <committer@example.com> 1700000000 +0900"
)

func identEnv() map[string]string {
	return map[string]string{"GIT_AUTHOR_NAME": "A U Thor",
		"GIT_AUTHOR_EMAIL":    "author@example.com",
		"GIT_AUTHOR_DATE":     "1700000000 +0900",
		"GIT_COMMITTER_NAME":  "C O Mitter",
		"GIT_COMMITTER_EMAIL": "committer@example.com",
		"GIT_COMMITTER_DATE":  "1700000000 +0900"}
}

func TestS44ParseIdent(t *testing.T) {
	n, m, s, z, err := ParseIdent("A U Thor <author@example.com> " +
		"1700000000 +0900")
	if err != nil || n != "A U Thor" || m != "author@example.com" ||
		s != 1700000000 || z != "+0900" {
		t.Fatal(n, m, s, z, err)
	}
}

func TestS91DateMatchesGitLog(t *testing.T) {
	// golden/scen/hello.scn: git log 이 찍은 두 날짜
	if FormatDate(1700000000, "+0900") !=
		"Wed Nov 15 07:13:20 2023 +0900" ||
		FormatDate(1700000060, "+0900") !=
			"Wed Nov 15 07:14:20 2023 +0900" {
		t.Fatal(FormatDate(1700000000, "+0900"))
	}
	// 달력 계산은 손으로 한다 — 표준 time 은 증인으로만
	for _, secs := range []int64{0, 86399, 951782400, 1700000000,
		2000000000, 1709251199, 4102444800} {
		for _, tz := range []string{"+0000", "-0700", "+0530",
			"-1200", "+1400"} {
			var h, m int
			fmt.Sscanf(tz[1:], "%02d%02d", &h, &m)
			off := h*3600 + m*60
			if tz[0] == '-' {
				off = -off
			}
			d := time.Unix(secs, 0).In(time.FixedZone("", off))
			want := fmt.Sprintf("%s %d %s %s", d.Format("Mon Jan"),
				d.Day(), d.Format("15:04:05 2006"), tz)
			if got := FormatDate(secs, tz); got != want {
				t.Errorf("%d %s: %s ≠ %s", secs, tz, got, want)
			}
		}
	}
}

func TestS13MissingEnvIsAnError(t *testing.T) {
	env := identEnv()
	delete(env, "GIT_AUTHOR_DATE")
	_, err := IdentFromEnv(env, "AUTHOR")
	if e := assertGitError(t, err); e.Msg !=
		"fatal: mygit: GIT_AUTHOR_DATE is not set" {
		t.Fatal(e.Msg)
	}
	env["GIT_AUTHOR_DATE"] = "yesterday"
	_, err = IdentFromEnv(env, "AUTHOR")
	if e := assertGitError(t, err); e.Msg != "fatal: mygit: "+
		"GIT_AUTHOR_DATE is not '<seconds> <+hhmm>'" {
		t.Fatal(e.Msg)
	}
}

func TestS44CleanupAndSubject(t *testing.T) {
	// SPEC.md §4.4 의 예 — 진짜 git commit -m 으로 확인한 것
	for in, want := range map[string]string{
		"\n\n  lead  \n\nx   \n \n\n\ny\n\n": "  lead\n\nx\n\ny\n",
		"one":                                "one\n", " \n \n": ""} {
		if got := CleanupMessage(in); got != want {
			t.Errorf("%q → %q", in, got)
		}
	}
	if SubjectOf("second\n\nbody line\n") != "second" ||
		SubjectOf("second\nbody line\n\npara2\n") !=
			"second body line" {
		t.Fatal(SubjectOf("second\nbody line\n\npara2\n"))
	}
}

func TestS44S45GitBytes(t *testing.T) {
	body := bodyOf(t, goldCommit)
	c, err := ParseCommit(body)
	if err != nil || len(c.Parents) != 0 ||
		string(SerializeCommit(c)) != string(body) {
		t.Fatal(c, err)
	}
	if string(SerializeTag(goldCommit, "commit", "v1", mitter,
		"tag message\n")) != string(bodyOf(t, goldTag)) {
		t.Fatal("태그 바이트")
	}
}

// repoSandbox 는 mygit init 으로 만든 저장소와 golden 객체 전부.
func repoSandbox(t *testing.T) (*sandbox, string) {
	s := newSandbox(t, false)
	for k, v := range identEnv() {
		s.env[k] = v
	}
	if code, _, err := s.mygit("init"); code != 0 {
		t.Fatal(err)
	}
	g := filepath.Join(s.root, ".git")
	for _, r := range gtsv(t, "objects", "objects.tsv") {
		plant(t, g, r["id"])
	}
	return s, g
}

func TestS51Init(t *testing.T) {
	s := newSandbox(t, false)
	code, out, err := s.mygit("init")
	g := filepath.Join(s.root, ".git")
	if code != 0 || err != "" || out != "Initialized empty Git "+
		"repository in "+g+"/\n" {
		t.Fatalf("%d %q %q", code, out, err)
	}
	head, _ := os.ReadFile(filepath.Join(g, "HEAD"))
	conf, _ := os.ReadFile(filepath.Join(g, "config"))
	if string(head) != "ref: refs/heads/main\n" || string(conf) !=
		"[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n"+
			"\tbare = false\n\tlogallrefupdates = true\n" {
		t.Fatalf("%q %q", head, conf)
	}
	for _, d := range []string{"objects/pack", "refs/heads",
		"refs/tags"} {
		if st, err := os.Stat(filepath.Join(g, d)); err != nil ||
			!st.IsDir() {
			t.Fatal(d)
		}
	}
	dev := []byte("ref: refs/heads/dev\n")
	os.WriteFile(filepath.Join(g, "HEAD"), dev, 0o644)
	_, out, _ = s.mygit("init")
	head, _ = os.ReadFile(filepath.Join(g, "HEAD"))
	if out != "Reinitialized existing Git repository in "+g+"/\n" ||
		string(head) != "ref: refs/heads/dev\n" {
		t.Fatalf("%q %q", out, head)
	}
	if code, _, _ := s.mygit("init", "sub"); code != 0 {
		t.Fatal("init sub")
	}
	if _, err := os.Stat(filepath.Join(s.root, "sub", ".git")); err !=
		nil {
		t.Fatal(err)
	}
}

func TestS44CommitTreeReproducesGit(t *testing.T) {
	s, g := repoSandbox(t)
	c, _ := ParseCommit(bodyOf(t, goldCommit))
	code, out, err := s.mygit("commit-tree", c.Tree, "-m", "objects")
	if code != 0 || out != goldCommit+"\n" || err != "" {
		t.Fatalf("%d %q %q", code, out, err)
	}
	_, out, _ = s.mygit("commit-tree", c.Tree, "-p", goldCommit, "-m",
		"a", "-m", "b")
	_, body, _ := ReadObject(g, strings.TrimSpace(out))
	c2, _ := ParseCommit(body)
	if !reflect.DeepEqual(c2.Parents, []string{goldCommit}) ||
		c2.Message != "a\n\nb\n" {
		t.Fatal(c2)
	}
	_, out, _ = s.mygit("commit-tree", c.Tree, "-m", "  m1  ")
	_, body, _ = ReadObject(g, strings.TrimSpace(out))
	if c3, _ := ParseCommit(body); c3.Message != "  m1  \n" {
		t.Fatalf("%q", c3.Message)
	}
}

func TestS45AnnotatedTagReproducesGit(t *testing.T) {
	s, g := repoSandbox(t)
	s.mygit("branch", "main", goldCommit)
	code, out, err := s.mygit("tag", "-a", "v1", "-m", "tag message")
	if code != 0 || out != "" || err != "" {
		t.Fatalf("%d %q %q", code, out, err)
	}
	if oid, _ := ResolveRef(g, "refs/tags/v1"); oid != goldTag {
		t.Fatal(oid)
	}
}

func TestS14Errors5(t *testing.T) {
	s, _ := repoSandbox(t)
	s.mygit("branch", "main", goldCommit)
	for _, cmd := range []string{"commit-tree nope -m x",
		"branch x nope", "tag t nope", "branch main", "branch a..b",
		"tag t"} {
		if cmd == "tag t" {
			s.mygit("tag", "t")
		}
		want, exit := errRow(t, cmd)
		code, _, err := s.mygit(strings.Fields(cmd)...)
		if code != exit || firstLine(err) != want {
			t.Errorf("%s: %d %q", cmd, code, err)
		}
	}
}

func TestS92BranchAndS63Reflog(t *testing.T) {
	s, g := repoSandbox(t)
	if code, _, _ := s.mygit("branch", "main", goldCommit); code != 0 {
		t.Fatal(code)
	}
	s.mygit("branch", "topic", "main")
	if _, out, _ := s.mygit("branch"); out != "* main\n  topic\n" {
		t.Fatalf("%q", out)
	}
	log := ReadReflog(g, "refs/heads/topic")
	want := []ReflogEntry{{strings.Repeat("0", 40), goldCommit, mitter,
		"branch: Created from main"}}
	if !reflect.DeepEqual(log, want) {
		t.Fatal(log)
	}
	_, out, _ := s.mygit("reflog", "topic")
	if out != goldCommit[:7]+" topic@{0}: branch: Created from main\n" {
		t.Fatalf("%q", out)
	}
}

func TestS63ReflogLineBytes(t *testing.T) {
	_, g := repoSandbox(t)
	AppendReflog(g, "HEAD", strings.Repeat("0", 40), goldCommit,
		"X <x@y> 1 +0000", "commit (initial): t")
	b, _ := os.ReadFile(filepath.Join(g, "logs", "HEAD"))
	if string(b) != strings.Repeat("0", 40)+" "+goldCommit+
		" X <x@y> 1 +0000\tcommit (initial): t\n" {
		t.Fatalf("%q", b)
	}
}

// dagEqual 은 golden/dag/equal 의 사본과, 거기서 git log --oneline
// 이 찍은 "<차례>:<제목>" → 7글자.
func dagEqual(t *testing.T) (string, map[string]string) {
	g := filepath.Join(t.TempDir(), ".git")
	src := filepath.Join(goldenDir, "dag", "equal", "git")
	filepath.Walk(src, func(p string, i os.FileInfo, e error) error {
		rel, _ := filepath.Rel(src, p)
		if i.IsDir() {
			return os.MkdirAll(filepath.Join(g, rel), 0o755)
		}
		b, _ := os.ReadFile(p)
		return os.WriteFile(filepath.Join(g, rel), b, 0o644)
	})
	os.MkdirAll(filepath.Join(g, "objects", "pack"), 0o755)
	text := string(gread(t, "dag", "equal", "expect.txt"))
	block := strings.Split(strings.Split(text,
		"$ git log --oneline\n")[1], "= 0")[0]
	ids := map[string]string{}
	for k, line := range strings.Split(strings.TrimSpace(block),
		"\n") {
		abbrev, subject, _ := strings.Cut(line, " ")
		ids[fmt.Sprintf("%d:%s", k, subject)] = abbrev
	}
	return g, ids
}

func TestS62RevParse(t *testing.T) {
	g, i := dagEqual(t)
	rp := func(spec string) string {
		oid, err := RevParse(g, spec)
		if err != nil {
			t.Fatal(err)
		}
		if len(oid) > 7 {
			return oid[:7]
		}
		return oid
	}
	for spec, want := range map[string]string{"HEAD": i["0:I"],
		"main": i["0:I"], "refs/heads/main": i["0:I"],
		"main~1": i["1:Merge branch 't'"], "HEAD~2": i["2:G"],
		"HEAD~1^2": i["3:H"], "HEAD^^": i["2:G"], "t": i["3:H"],
		i["2:G"]: i["2:G"], "HEAD^0": i["0:I"], "nope": "",
		"HEAD~99": ""} {
		if got := rp(spec); got != want {
			t.Errorf("%s: %s ≠ %s", spec, got, want)
		}
	}
	oid, _ := RevParse(g, "HEAD^{tree}")
	if typ, _, _ := ReadObject(g, oid); typ != "tree" {
		t.Fatal(typ)
	}
}
