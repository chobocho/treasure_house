// 슬라이드 p8-v126-secret — runtime/secret 실험, Go 1.26

//go:build goexperiment.runtimesecret

package main

import (
	"crypto/sha256"
	"fmt"
	"runtime"
	"runtime/secret"
)

func main() {
	var digest [32]byte
	inside := false
	// Temporaries created inside Do (registers, stack, new heap
	// allocations) are erased when it returns; digest is ours.
	secret.Do(func() {
		key := []byte("do not leave me in memory")
		digest = sha256.Sum256(key)
		inside = secret.Enabled()
	})
	fmt.Printf("digest %x…\n", digest[:4])
	fmt.Println(runtime.GOOS+"/"+runtime.GOARCH,
		"secret mode inside Do:", inside)
}
