// 이 책의 캡처를 찍은 Go 쪽 판 — 바이너리에 새겨진 정보에게 묻는다.
package main

import (
	"fmt"
	"runtime"
	"runtime/debug"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"google.golang.org/grpc"
)

// region: show
func main() {
	fmt.Println("go       ", runtime.Version(),
		runtime.GOOS+"/"+runtime.GOARCH)
	fmt.Println("프로토콜 ", a2a.Version)
	fmt.Println("grpc     ", grpc.Version)
	// go build 가 바이너리에 적어 둔 모듈 목록(go.mod 의 판)
	info, _ := debug.ReadBuildInfo()
	fmt.Println("모듈     ", info.Main.Path)
	for _, d := range info.Deps {
		if d.Path == "github.com/a2aproject/a2a-go/v2" {
			fmt.Println("a2a-go   ", d.Version)
		}
	}
}

// endregion
