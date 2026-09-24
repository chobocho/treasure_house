// 슬라이드 p5-v113-envw — go env -w 가 쓰는 파일, Go 1.13
package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// goenv runs "go env ARGS..." with GOENV pointing at file.
func goenv(file string, args ...string) string {
	cmd := exec.Command("go", append([]string{"env"}, args...)...)
	cmd.Env = append(os.Environ(), "GOENV="+file, "GOPRIVATE=")
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "error: " + err.Error()
	}
	return strings.TrimSpace(string(out))
}

func main() {
	file := filepath.Join(os.TempDir(), "goenv-demo")
	os.Remove(file)

	goenv(file, "-w", "GOPRIVATE=*.private.example")
	data, _ := os.ReadFile(file)
	fmt.Printf("file after -w: %q\n", data)
	fmt.Println("GOPRIVATE GONOPROXY GONOSUMDB:")
	fmt.Println(goenv(file, "GOPRIVATE", "GONOPROXY", "GONOSUMDB"))

	goenv(file, "-u", "GOPRIVATE")
	data, _ = os.ReadFile(file)
	fmt.Printf("file after -u: %q\n", data)
}
