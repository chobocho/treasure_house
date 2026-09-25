// 슬라이드 p8-v125-dwarf5 — 디버그 정보가 DWARF 5 로, Go 1.25
package main

import (
	"debug/elf"
	"fmt"
	"os"
	"strings"
)

// Lists the DWARF sections of this very binary. go run strips
// debug info by default, so run it with -ldflags='-s=false -w=false'.
func main() {
	exe, err := os.Executable()
	if err != nil {
		fmt.Println(err)
		return
	}
	f, err := elf.Open(exe)
	if err != nil {
		fmt.Println(err)
		return
	}
	defer f.Close()
	var names []string
	for _, s := range f.Sections {
		if strings.Contains(s.Name, "debug_") {
			names = append(names, s.Name)
		}
	}
	fmt.Println(len(names), "DWARF sections:")
	fmt.Println(strings.Join(names, " "))
}
