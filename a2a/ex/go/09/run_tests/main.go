// go test 를 돌려 걸린 시간 없이 찍는다(캡처가 실행마다 같게).
//
//	go run ./09/run_tests [-into DIR] PKG
//
// -into 를 주면 09/testdata 의 시험 파일들이 DIR 에 있는 것처럼
// 보이게 해서(go test -overlay) 돌린다. DIR 의 파일은 고치지 않는다.
package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// region: overlay
// overlay 는 go 명령의 -overlay 설정 파일을 만든다 — "디스크의 이
// 경로에는 저 파일이 있는 것으로 하라" 는 표(Replace)다.
func overlay(into string) string {
	files, _ := filepath.Glob("09/testdata/*_test.go")
	repl := map[string]string{}
	for _, f := range files {
		src, _ := filepath.Abs(f)
		dst, _ := filepath.Abs(filepath.Join(into, filepath.Base(f)))
		repl[dst] = src
	}
	b, _ := json.Marshal(map[string]any{"Replace": repl})
	p := filepath.Join(os.TempDir(), "overlay.json")
	if err := os.WriteFile(p, b, 0o644); err != nil {
		panic(err)
	}
	return p
}

// endregion

// event 는 go test -json 이 내는 줄 하나(Time·Elapsed 는 버린다).
type event struct {
	Action, Test, Output string
}

// region: runner
func main() {
	into := flag.String("into", "", "시험 파일을 놓을 디렉터리")
	flag.Parse()
	args := []string{"test", "-p", "1", "-count=1", "-json"}
	if *into != "" {
		args = append(args, "-overlay", overlay(*into))
	}
	cmd := exec.Command("go", append(args, flag.Args()...)...)
	cmd.Stderr = os.Stderr // 빌드 오류는 그대로 보인다
	out, _ := cmd.Output()
	var order []string            // 처음 돈 차례
	result := map[string]string{} // 시험 → pass·fail
	logs := map[string][]string{} // 시험 → 들여 쓴 출력(t.Error)
	sc := bufio.NewScanner(bytes.NewReader(out))
	for sc.Scan() {
		var e event
		if json.Unmarshal(sc.Bytes(), &e) != nil || e.Test == "" {
			continue // 패키지 줄(걸린 시간이 있다)
		}
		switch e.Action {
		case "run":
			order = append(order, e.Test)
		case "pass", "fail":
			result[e.Test] = e.Action
		case "output":
			if strings.HasPrefix(e.Output, "    ") {
				logs[e.Test] = append(logs[e.Test], e.Output)
			}
		}
	}
	report(order, result, logs)
}

// endregion

// report 는 시험을 들여 써 찍고 잎 시험의 수를 센다.
func report(order []string, result map[string]string,
	logs map[string][]string) {
	leaves, failed := 0, 0
	for i, name := range order {
		leaf := i+1 == len(order) ||
			!strings.HasPrefix(order[i+1], name+"/")
		marks := map[string]string{"pass": "✓", "fail": "✗"}
		mark := marks[result[name]]
		pad := strings.Repeat("  ", strings.Count(name, "/"))
		short := name[strings.LastIndex(name, "/")+1:]
		fmt.Printf("%s%s %s\n", pad, mark, short)
		for _, l := range logs[name] {
			fmt.Print(pad, l)
		}
		if leaf {
			leaves++
			if result[name] == "fail" {
				failed++
			}
		}
	}
	fmt.Printf("시험 %d · 통과 %d · 실패 %d\n", leaves, leaves-failed,
		failed)
	if failed > 0 || leaves == 0 {
		os.Exit(1)
	}
}

//@ norun
