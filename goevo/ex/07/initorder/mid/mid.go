// 슬라이드 p7-v121-initorder — 패키지 초기화 순서의 명세, Go 1.21
package mid

import (
	"fmt"

	_ "ex/07/initorder/zeta" // mid must wait for zeta
)

func init() { fmt.Println("init mid") }
