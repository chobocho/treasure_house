// 진짜 토큰은 이렇게 만든다 — 운영체제의 난수로 32바이트(256비트).
// 값은 실행마다 달라 화면에는 모양만 찍는다.
package main

import (
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"regexp"
)

func token() string {
	b := make([]byte, 32)
	// 오류를 돌려주지 않는다(go doc crypto/rand.Read)
	_, _ = rand.Read(b)
	return base64.RawURLEncoding.EncodeToString(b)
}

func main() {
	a, b := token(), token()
	safe := regexp.MustCompile(`^[A-Za-z0-9_-]+$`).MatchString(a)
	fmt.Printf("길이 %d | URL 에 안전한 글자뿐 %v\n", len(a), safe)
	fmt.Printf("두 번 같나 %v\n", a == b)
}
