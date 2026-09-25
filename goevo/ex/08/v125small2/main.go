// 슬라이드 p8-v125-small2 — unicode·regexp·multipart, Go 1.25
package main

import (
	"fmt"
	"mime/multipart"
	"regexp"
	"unicode"
)

func main() {
	// unicode.CategoryAliases: long names for the short category codes.
	fmt.Println(unicode.CategoryAliases["Letter"],
		unicode.CategoryAliases["Decimal_Number"])

	// New tables: LC (cased letter) and Cn (unassigned code point).
	r := rune(0x0378) // not assigned in Unicode
	fmt.Println(unicode.Is(unicode.LC, 'g'),
		unicode.Is(unicode.LC, '가'))
	fmt.Println(unicode.Is(unicode.Cn, r), unicode.Is(unicode.C, r))

	// regexp: \p{Letter} now means \pL; names are matched loosely.
	exprs := []string{`^\p{Letter}+$`, `^\p{decimal number}+$`}
	for _, expr := range exprs {
		re, err := regexp.Compile(expr)
		if err != nil {
			fmt.Println(err)
			continue
		}
		fmt.Println(expr,
			re.MatchString("Go언어"), re.MatchString("2025"))
	}

	// mime/multipart: a Content-Disposition line for a file part.
	cd := multipart.FileContentDisposition("upload", "보고서.pdf")
	fmt.Println(cd)
}
