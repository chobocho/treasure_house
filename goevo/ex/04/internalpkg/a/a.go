// 슬라이드 p4-v15-internal — a 는 제 아래 internal 을 쓴다
package a

import "ex/04/internalpkg/a/internal/secret"

// Hello may use a/internal/...: it lives in the same subtree.
func Hello() string { return "a sees " + secret.Name }
