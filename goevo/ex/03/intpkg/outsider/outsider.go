// 슬라이드 p3-v14-internal — lib 바깥에서 가져오면 거절, Go 1.4
package outsider

import "ex/03/intpkg/lib/internal/secret"

// Leak tries to reach past lib's boundary.
func Leak() string { return secret.Key }
