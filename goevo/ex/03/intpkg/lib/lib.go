// 슬라이드 p3-v14-internal — 부모 lib 는 internal 을 쓸 수 있다, Go 1.4
package lib

import (
	"strconv"

	"ex/03/intpkg/lib/internal/secret"
)

// Masked reveals only the length of the key.
func Masked() string {
	return "key length " + strconv.Itoa(len(secret.Key))
}
