// 슬라이드 p3-v12-fmtindex — 서식 지정자의 인자 번호 %[n], Go 1.2
package main

import "fmt"

func main() {
	fmt.Printf("%c %c %c\n", 'a', 'b', 'c')
	fmt.Printf("%[3]c %[1]c %c\n", 'a', 'b', 'c') // [1] then next is 2

	// one argument, formatted twice
	v := 1.5
	fmt.Printf("value %v of type %[1]T\n", v)

	// the width can come from an indexed argument too
	fmt.Printf("[%[2]*[1]d]\n", 42, 6)

	// localization: same arguments, different word order
	for _, f := range []string{
		"%[1]s bought %[2]d apples\n",
		"%[2]d apples were bought by %[1]s\n",
	} {
		fmt.Printf(f, "Kim", 3)
	}
}
