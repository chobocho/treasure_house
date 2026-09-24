// 슬라이드 p5-v116-embedfs — 디렉터리 트리를 embed.FS 로, Go 1.16
package main

import (
	"embed"
	"fmt"
	"io/fs"
)

//go:embed static
var site embed.FS

func main() {
	fs.WalkDir(site, ".", func(p string, d fs.DirEntry, _ error) error {
		if !d.IsDir() {
			fmt.Println(p)
		}
		return nil
	})
	b, _ := site.ReadFile("static/css/site.css")
	fmt.Print(string(b))
}
