// 슬라이드 p8-v127-testserver — 시험할 느린 핸들러, Go 1.27
package slow

import (
	"fmt"
	"net/http"
	"time"
)

// Handler answers after a 5-second delay.
func Handler(w http.ResponseWriter, r *http.Request) {
	time.Sleep(5 * time.Second)
	fmt.Fprint(w, "done")
}
