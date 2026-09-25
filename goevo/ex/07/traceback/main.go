// 슬라이드 p7-v123-traceback — 여러 줄 패닉 메시지의 들여쓰기, Go 1.23
package main

import "errors"

func main() {
	panic(errors.New("config invalid:\nport: missing\nhost: empty"))
}
