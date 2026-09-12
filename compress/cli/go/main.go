// compresslib 명령줄 도구 (Go) — 다섯 언어가 같은 사용법을 갖는다.
//
//	gocli <알고리즘> enc|dec <입력> <출력>
//	gocli batch <작업파일>
//	gocli list
//
// batch 가 있는 이유는 파서티 검사다. (알고리즘 × 파일 × 언어) 조합이
// 수천 건이라 건마다 프로세스를 띄우면 JVM 하나로 몇 분이 간다.
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	lib "compresslib/src/go"
)

// 실패하면 사람이 읽을 문장을, 성공하면 빈 문자열을 돌려준다.
func runOne(algo, mode, in, out string) string {
	e := lib.Find(algo)
	if e == nil {
		return "모르는 알고리즘: " + algo
	}
	if mode != "enc" && mode != "dec" {
		return "enc 또는 dec 이어야 한다: " + mode
	}
	if mode == "enc" && e.Encode == nil {
		return algo + " 는 복호기만 있다"
	}
	data, err := os.ReadFile(in)
	if err != nil {
		return "입력을 못 읽는다: " + in
	}
	var result []byte
	if mode == "enc" {
		result, err = e.Encode(data)
	} else {
		result, err = e.Decode(data)
	}
	if err != nil {
		return fmt.Sprintf("%s %s 실패: %v", algo, mode, err)
	}
	if err := os.WriteFile(out, result, 0o644); err != nil {
		return "출력을 못 쓴다: " + out
	}
	return ""
}

func batch(jobPath string) int {
	f, err := os.Open(jobPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, "작업 파일을 못 읽는다:", jobPath)
		return 2
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 1<<20), 1<<20)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.Fields(line)
		if len(parts) != 4 {
			fmt.Println("FAIL 칸이 4개가 아니다")
			continue
		}
		msg := runOne(parts[0], parts[1], parts[2], parts[3])
		if msg != "" {
			fmt.Println("FAIL " + msg)
		} else {
			fmt.Println("OK")
		}
	}
	return 0
}

func main() {
	args := os.Args[1:]
	if len(args) == 1 && args[0] == "list" {
		for _, e := range lib.Entries {
			fmt.Println(e.Name)
		}
		return
	}
	if len(args) == 2 && args[0] == "batch" {
		os.Exit(batch(args[1]))
	}
	if len(args) != 4 {
		fmt.Fprintln(os.Stderr,
			"사용법: gocli <알고리즘> enc|dec <입력> <출력>")
		fmt.Fprintln(os.Stderr, "        gocli batch <작업파일>")
		os.Exit(2)
	}
	if msg := runOne(args[0], args[1], args[2], args[3]); msg != "" {
		fmt.Fprintln(os.Stderr, msg)
		os.Exit(1)
	}
}
