// 슬라이드 p4-v17-cancel — 취소는 트리를 타고 내려간다, Go 1.7
package main

import (
	"context"
	"fmt"
)

type ctxKey string

const reqID ctxKey = "request-id"

func main() {
	root, cancel := context.WithCancel(context.Background())
	child, cancelChild := context.WithCancel(root)
	defer cancelChild()
	leaf := context.WithValue(child, reqID, "req-42")

	cancel() // cancel only the root
	<-leaf.Done()
	fmt.Println("leaf:", leaf.Err())
	fmt.Println("value kept:", leaf.Value(reqID))
	fmt.Println("background:", context.Background().Err())
}
