// 슬라이드 p8-v126-linker — 실행 파일의 섹션이 바뀌다, Go 1.26
package main

import (
	"debug/elf"
	"fmt"
	"os"
	"strings"
)

func main() {
	exe, _ := os.Executable()
	f, err := elf.Open(exe)
	if err != nil {
		panic(err)
	}

	// Go-specific sections, in section-header order.
	var prev uint64
	sorted := true
	for _, s := range f.Sections {
		if s.Addr != 0 && s.Addr < prev {
			sorted = false
		}
		if s.Addr != 0 {
			prev = s.Addr
		}
		if strings.Contains(s.Name, "go") {
			fmt.Printf("%-16s %s\n", s.Name, s.Type)
		}
	}
	fmt.Println(".gosymtab present:", f.Section(".gosymtab") != nil)

	pcln := f.Section(".gopclntab")
	relro, inRelro := false, false
	for _, p := range f.Progs {
		if p.Type == elf.PT_GNU_RELRO {
			relro = true
			a := pcln.Addr
			inRelro = inRelro || a >= p.Vaddr && a < p.Vaddr+p.Memsz
		}
	}
	fmt.Println("RELRO segment:", relro, " .gopclntab in it:", inRelro)
	fmt.Println("sorted by address:", sorted)
}
