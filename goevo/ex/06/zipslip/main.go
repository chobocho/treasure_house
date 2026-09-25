// 슬라이드 p6-v120-zipslip — 위험한 zip 경로, Go 1.20
package main

import (
	"archive/zip"
	"bytes"
	"fmt"
	"path/filepath"
)

func main() {
	// An archive whose entry would land outside the target directory.
	var buf bytes.Buffer
	zw := zip.NewWriter(&buf)
	w, _ := zw.Create("../../etc/evil.conf")
	w.Write([]byte("x"))
	zw.Close()

	data := buf.Bytes()
	r, err := zip.NewReader(bytes.NewReader(data), int64(len(data)))
	fmt.Println("NewReader error:", err)
	if r != nil {
		name := r.File[0].Name
		fmt.Printf("%q local=%v\n", name, filepath.IsLocal(name))
	}
	fmt.Println(filepath.IsLocal("a/b.ini"), filepath.IsLocal("/etc"))
}
