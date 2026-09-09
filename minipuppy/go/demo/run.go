//go:build ignore

// 덱에 실을 시연을 재현한다. 매번 같은 결과가 나오게 작업 파일을 되돌린다.
//
//	go run demo/run.go          # 전체
//	go run demo/run.go fix      # 버그 고치기 한 판만
//
// 대본 모델을 쓰므로 네트워크도 API 키도 필요 없다 — 그런데도
// "모델 -> 도구 -> 결과 -> 모델" 루프는 실물 그대로 돈다.
package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

const buggy = `package calc

// Add 는 두 수를 더한다 — 고 해 놓고 빼고 있다.
func Add(a, b int) int {
	return a - b
}

func Mul(a, b int) int {
	return a * b
}
`

const test = `package calc

import "testing"

func TestAdd(t *testing.T) {
	if Add(2, 3) != 5 {
		t.Fatalf("2+3 이 %d 로 나왔다", Add(2, 3))
	}
}
`

var line = strings.Repeat("─", 62)

func reset(work string) {
	os.MkdirAll(work, 0o755)
	os.WriteFile(filepath.Join(work, "calc.go"), []byte(buggy), 0o644)
	os.WriteFile(filepath.Join(work, "calc_test.go"), []byte(test), 0o644)
	os.WriteFile(filepath.Join(work, "go.mod"), []byte("module calc\n\ngo 1.21\n"), 0o644)
}

func run(bin, cfg, work, title string, args ...string) {
	fmt.Printf("\n%s\n[%s]  minipuppy %s\n%s\n", line, title, strings.Join(args, " "), line)
	full := append([]string{"--config-dir", cfg, "-C", work, "--quiet"}, args...)
	cmd := exec.Command(bin, full...)
	cmd.Stdout, cmd.Stderr = os.Stdout, os.Stderr
	cmd.Run()
}

func main() {
	here, _ := filepath.Abs(filepath.Dir(os.Args[0]))
	if _, err := os.Stat("demo"); err == nil {
		here, _ = filepath.Abs("demo")
	}
	cfg := filepath.Join(here, ".minipuppy")
	work := filepath.Join(here, "work")
	bin := filepath.Join(here, "..", "minipuppy.exe")
	if _, err := os.Stat(bin); err != nil {
		bin = filepath.Join(here, "..", "minipuppy")
	}

	scenes := map[string]func(){
		"fix": func() {
			run(bin, cfg, work, "버그를 찾아 고치고 go test 까지",
				"-p", "calc.Add 가 이상하다. 고쳐줘")
		},
		"guard": func() {
			run(bin, cfg, work, "도구 목록이 가드레일이다",
				"--agent", "go-tutor", "--model", "허용목록-시험",
				"-p", "Mul 이름을 바꿔줘")
		},
	}
	want := os.Args[1:]
	if len(want) == 0 {
		want = []string{"fix", "guard"}
	}
	for _, name := range want {
		reset(work)
		if fn, ok := scenes[name]; ok {
			fn()
		}
	}
}
