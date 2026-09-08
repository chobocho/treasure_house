// pkce — 가로챈 인가 코드를 못 쓰게 만드는 장치 (RFC 7636).
//
// 인가 코드는 주소에 실려 브라우저를 거쳐 돌아온다(4부 3장). 그 짧은
// 순간에 코드를 훔친 쪽이 그것으로 토큰을 받아 가면, 로그인을 통째로
// 가로챈 것이 된다. 실제로 모바일 앱에서 그런 사고가 있었다.
//
// 막는 방법이 놀랍도록 단순하다.
//
//  1. 앱이 아무도 모르는 값을 하나 만든다        → verifier
//  2. 그 값의 해시를 로그인 시작 주소에 실어 보낸다 → challenge
//  3. 나중에 코드를 토큰으로 바꿀 때 **원래 값**을 함께 낸다
//  4. 서버가 해시해 보고 아까 받은 것과 같은지 확인한다
//
// 코드를 훔쳐도 verifier 를 모르면 쓸 수 없다. 그리고 challenge 에서
// verifier 를 되돌릴 수는 없다 — 해시의 성질이다(1부 8장).
//
// 원래는 비밀을 숨길 수 없는 앱(모바일·SPA)을 위해 만들어졌지만,
// 지금은 **모든 종류의 앱에 권장**된다(OAuth 2.1 초안). Keycloak 도
// 클라이언트마다 "PKCE 필수" 를 켤 수 있고, 이 덱은 켠다.
package pkce

import (
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
)

// Method 는 challenge 를 만드는 방법이다.
//
// 규격에는 "plain"(verifier 를 그대로 보냄)도 있지만 쓰면 안 된다 —
// 가로챈 쪽이 그 값을 그대로 다시 쓰면 되니 아무것도 막지 못한다.
// RFC 7636 §4.2 도 S256 을 쓸 수 있으면 반드시 쓰라고 적었다.
const Method = "S256"

// verifierBytes 는 만들어 낼 무작위 바이트 수.
// 32바이트를 base64url 로 적으면 43글자가 되는데, 그게 규격이 정한
// 최소 길이다(§4.1: 43~128글자).
const verifierBytes = 32

// NewVerifier 는 아무도 못 맞히는 값을 하나 만든다.
//
// crypto/rand 다 — 6장의 세션 번호와 같은 이유다. 씨앗을 알면 다음 값을
// 계산할 수 있는 난수로 만들면, 그 순간 이 장치가 아무 일도 안 하게
// 된다.
func NewVerifier() (string, error) {
	b := make([]byte, verifierBytes)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(b), nil
}

// Challenge 는 verifier 를 SHA-256 으로 해시해 base64url 로 적는다.
//
//	code_challenge = BASE64URL(SHA256(ASCII(code_verifier)))
//
// 규격의 이 한 줄이 함수 하나가 됐다. 시간·공간 모두 O(글자 수).
func Challenge(verifier string) string {
	sum := sha256.Sum256([]byte(verifier))
	return base64.RawURLEncoding.EncodeToString(sum[:])
}

// Verify 는 서버 쪽에서 확인하는 자리다.
//
// 견줄 때 ConstantTimeCompare 를 쓰는 이유는 1부 5장의 비밀번호와 같다
// — 글자가 어디서 어긋났는지가 걸린 시간으로 새어 나가면 안 된다.
func Verify(verifier, challenge string) bool {
	if verifier == "" || challenge == "" {
		return false
	}
	got := Challenge(verifier)
	want := []byte(challenge)
	return subtle.ConstantTimeCompare([]byte(got), want) == 1
}
