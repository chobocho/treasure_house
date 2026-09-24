// 슬라이드 p4-v15-small — os.LookupEnv 와 base64 Raw, Go 1.5
package main

import (
	"encoding/base64"
	"fmt"
	"os"
)

func main() {
	os.Setenv("EMPTY", "")
	os.Unsetenv("MISSING")
	for _, k := range []string{"EMPTY", "MISSING"} {
		v, ok := os.LookupEnv(k)
		fmt.Printf("%-7s Getenv=%q LookupEnv=(%q, %v)\n",
			k, os.Getenv(k), v, ok)
	}
	b := []byte("gopher!")
	fmt.Println(base64.StdEncoding.EncodeToString(b))
	fmt.Println(base64.RawStdEncoding.EncodeToString(b))
}
