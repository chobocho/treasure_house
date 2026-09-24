// 슬라이드 p4-v19-aliasrepair — 별칭으로 점진적 이사, Go 1.9
package main

import (
	"fmt"

	"ex/04/aliasrepair/newpkg"
	"ex/04/aliasrepair/oldpkg"
)

func main() {
	// A client not yet migrated still uses the old name ...
	old := oldpkg.Config{Name: "legacy"}
	// ... and can pass it where the new name is expected.
	fmt.Println(newpkg.Describe(old))
	fmt.Printf("%T\n", old)
}
