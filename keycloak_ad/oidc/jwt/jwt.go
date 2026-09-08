// jwt — 토큰 한 장을 만들고 확인하는 데 필요한 전부.
//
// 4부의 심장이다. 1부 8장에서 본 두 도구(base64url 과 공개키 서명)를
// 합치면 토큰이 된다. 그것뿐이다.
//
//	머리.내용.서명
//	└┬┘ └┬┘ └┬┘
//	 │   │   └── 앞의 두 조각을 개인키로 서명한 것
//	 │   └────── 누구인지·언제까지인지 (JSON, 누구나 읽는다)
//	 └────────── 어떤 알고리즘·어느 열쇠인지 (JSON)
//
// 세 조각을 점으로 이어 붙인다. 이 모양의 이름이 JWS Compact
// Serialization 이고, 그 안에 담긴 내용이 JWT 다 (RFC 7515 · RFC 7519).
//
// **내용은 암호화되지 않는다.** base64url 은 누구나 되돌릴 수 있다.
// 서명이 지키는 것은 "아무도 못 읽는다" 가 아니라 "아무도 못 고친다"
// 다. 토큰에 비밀을 담으면 안 되는 이유가 이것이다.
package jwt

import (
	"crypto"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"math/big"
	"strings"
	"time"
)

// 이 덱이 쓰는 서명 방식은 하나뿐이다.
//
//	RS256 = RSASSA-PKCS1-v1_5 + SHA-256 (RFC 7518 §3.3)
//
// Keycloak 의 기본값이기도 하다. 다른 방식(ES256·PS256·HS256)도 있지만
// 하나만 제대로 이해하면 나머지는 이름만 다르다.
const AlgRS256 = "RS256"

// B64URLEncode 는 패딩 없는 base64url 이다 (RFC 4648 §5).
//
// 보통의 base64 와 다른 점 셋: + 를 - 로, / 를 _ 로, 끝의 = 를 뗀다.
// 토큰이 주소(URL)에도 실리기 때문이다 — 1부 8장에서 본 그 이야기다.
func B64URLEncode(b []byte) string {
	return base64.RawURLEncoding.EncodeToString(b)
}

func B64URLDecode(s string) ([]byte, error) {
	return base64.RawURLEncoding.DecodeString(s)
}

// Header 는 첫 조각이다. "어떤 방법으로 서명했고 어느 열쇠를 썼는가".
type Header struct {
	Alg string `json:"alg"`
	Typ string `json:"typ,omitempty"`
	// 열쇠 이름 — 키 회전에 꼭 필요하다
	Kid string `json:"kid,omitempty"`
}

// Claims 는 둘째 조각이다. "주장" 이라는 이름이 정확하다 —
// 발급자가 그렇다고 말하는 것이고, 믿을지는 서명을 보고 정한다.
//
// 앞의 일곱은 RFC 7519 §4.1 이 정한 이름이고(등록된 클레임),
// 뒤의 것들은 OIDC 와 우리가 더 싣는 것이다.
type Claims struct {
	Iss   string `json:"iss,omitempty"` // 누가 발급했나
	Sub   string `json:"sub,omitempty"` // 누구에 대한 것인가
	Aud   string `json:"aud,omitempty"` // 누구에게 주는 것인가
	Exp   int64  `json:"exp,omitempty"` // 언제까지 (1970년부터 센 초)
	Nbf   int64  `json:"nbf,omitempty"` // 언제부터
	Iat   int64  `json:"iat,omitempty"` // 언제 발급했나
	Jti   string `json:"jti,omitempty"` // 이 토큰 한 장의 일련번호
	Nonce string `json:"nonce,omitempty"`

	PreferredUsername string   `json:"preferred_username,omitempty"`
	Email             string   `json:"email,omitempty"`
	Name              string   `json:"name,omitempty"`
	Groups            []string `json:"groups,omitempty"`
}

// signingInput 은 서명 대상이다 — 머리와 내용을 점으로 이은 **글자
// 그대로**. 다시 JSON 으로 만들지 않고 받은 글자를 그대로 쓰는 것이
// 중요하다. JSON 은 같은 뜻을 여러 모양으로 적을 수 있어서(빈칸·키
// 순서), 다시 만들면 서명이 안 맞는다.
func signingInput(head, body string) []byte {
	return []byte(head + "." + body)
}

// Sign 은 토큰 한 장을 만든다.
func Sign(h Header, c Claims, key *rsa.PrivateKey) (string, error) {
	if h.Alg == "" {
		h.Alg = AlgRS256
	}
	if h.Alg != AlgRS256 {
		return "", fmt.Errorf("이 구현은 %s 만 만든다", AlgRS256)
	}
	hj, err := json.Marshal(h)
	if err != nil {
		return "", err
	}
	cj, err := json.Marshal(c)
	if err != nil {
		return "", err
	}
	head, body := B64URLEncode(hj), B64URLEncode(cj)

	sum := sha256.Sum256(signingInput(head, body))
	sig, err := rsa.SignPKCS1v15(rand.Reader, key,
		crypto.SHA256, sum[:])
	if err != nil {
		return "", err
	}
	return head + "." + body + "." + B64URLEncode(sig), nil
}

func split(tok string) (head, body, sig string, err error) {
	parts := strings.Split(tok, ".")
	if len(parts) != 3 {
		return "", "", "", fmt.Errorf(
			"조각이 %d개 — 토큰은 세 조각이다", len(parts))
	}
	if parts[0] == "" || parts[1] == "" {
		return "", "", "", errors.New("머리나 내용이 비었다")
	}
	return parts[0], parts[1], parts[2], nil
}

// Parse 는 **서명을 확인하지 않고** 내용만 읽는다.
//
// 이 함수가 따로 있는 이유는 두 가지다. 하나는 진단 — 토큰이 왜
// 거절됐는지 보려면 일단 읽어야 한다. 다른 하나는 교육 — 누구나 읽을 수
// 있다는 사실을 코드로 못 박아 두려는 것이다.
//
// **결정을 내릴 때는 절대 이 함수를 쓰지 말 것.** Verify 를 쓴다.
func Parse(tok string) (Header, Claims, error) {
	head, body, _, err := split(tok)
	if err != nil {
		return Header{}, Claims{}, err
	}
	var h Header
	hj, err := B64URLDecode(head)
	if err != nil {
		return Header{}, Claims{}, fmt.Errorf("머리: %w", err)
	}
	if err := json.Unmarshal(hj, &h); err != nil {
		return Header{}, Claims{}, fmt.Errorf("머리 JSON: %w", err)
	}
	var c Claims
	cj, err := B64URLDecode(body)
	if err != nil {
		return h, Claims{}, fmt.Errorf("내용: %w", err)
	}
	if err := json.Unmarshal(cj, &c); err != nil {
		return h, Claims{}, fmt.Errorf("내용 JSON: %w", err)
	}
	return h, c, nil
}

// Verify 는 서명을 확인한 뒤에야 내용을 돌려준다.
//
// 헤더의 alg 를 **믿지 않는 것**이 이 함수의 핵심이다.
// 초창기 라이브러리들은 "헤더에 적힌 방법대로 확인" 했고, 그래서
// alg 를 none 으로 바꾸거나 HS256 으로 바꾼 토큰에 무더기로 뚫렸다.
// 우리는 우리가 기대하는 방법(RS256)이 아니면 그 자리에서 거절한다.
func Verify(tok string, ks *KeySet) (Header, Claims, error) {
	h, c, err := Parse(tok)
	if err != nil {
		return Header{}, Claims{}, err
	}
	if h.Alg != AlgRS256 {
		return h, c, fmt.Errorf(
			"서명 방식이 %q — 우리는 %s 만 받는다", h.Alg, AlgRS256)
	}
	pub, err := ks.Find(h.Kid)
	if err != nil {
		return h, c, err
	}
	head, body, sig, _ := split(tok)
	raw, err := B64URLDecode(sig)
	if err != nil {
		return h, c, fmt.Errorf("서명: %w", err)
	}
	sum := sha256.Sum256(signingInput(head, body))
	err = rsa.VerifyPKCS1v15(pub, crypto.SHA256, sum[:], raw)
	if err != nil {
		return h, c, fmt.Errorf("서명이 맞지 않는다: %w", err)
	}
	return h, c, nil
}

// ── 클레임 검사 ──────────────────────────────────────────────────────

// Options 는 "무엇과 견줄 것인가" 다. 서명이 맞다는 것만으로는 부족하다
// — **남에게 발급된 멀쩡한 토큰**을 가져와 쓰는 공격이 있기 때문이다.
type Options struct {
	Issuer   string        // 이 발급자가 준 것이어야 한다
	Audience string        // 나에게 준 것이어야 한다
	Nonce    string        // 내가 보낸 그 값이어야 한다 (ID 토큰)
	Now      time.Time     // 비어 있으면 지금
	Leeway   time.Duration // 시계 오차를 봐주는 폭
}

// Validate 는 서명 말고 확인해야 할 것들을 본다.
//
// 순서에 뜻은 없지만 빠뜨리면 안 되는 것들이다. 특히 aud 를 안 보면
// 다른 앱에 발급된 토큰이 우리 앱에서 통한다 — OIDC 사고의 단골이다.
func (c Claims) Validate(o Options) error {
	now := o.Now
	if now.IsZero() {
		now = time.Now()
	}
	if c.Sub == "" {
		return errors.New("sub 가 없다 — 누구 것인지 알 수 없다")
	}
	if c.Exp == 0 {
		return errors.New("exp 가 없다 — 영원한 토큰은 안 받는다")
	}
	exp := time.Unix(c.Exp, 0).Add(o.Leeway)
	if !now.Before(exp) {
		return fmt.Errorf("만료됨 (exp %s)", time.Unix(c.Exp, 0).UTC())
	}
	if c.Nbf != 0 {
		nbf := time.Unix(c.Nbf, 0).Add(-o.Leeway)
		if now.Before(nbf) {
			return fmt.Errorf("아직 유효 시각 전 (nbf %s)",
				time.Unix(c.Nbf, 0).UTC())
		}
	}
	if o.Issuer != "" && c.Iss != o.Issuer {
		return fmt.Errorf("발급자가 다르다: %q (기대 %q)",
			c.Iss, o.Issuer)
	}
	if o.Audience != "" && c.Aud != o.Audience {
		return fmt.Errorf("대상이 다르다: %q (기대 %q)",
			c.Aud, o.Audience)
	}
	// nonce 를 기대한다고 해 놓고 값이 없으면 거절한다.
	// "없으면 통과" 로 두면 검사가 아예 없는 것과 같다.
	if o.Nonce != "" && c.Nonce != o.Nonce {
		return fmt.Errorf("nonce 가 다르다: %q (기대 %q)",
			c.Nonce, o.Nonce)
	}
	return nil
}

// ── JWKS — 공개키를 JSON 으로 실어 나르기 ────────────────────────────

// JWK 는 열쇠 한 개다 (RFC 7517). RSA 공개키는 숫자 둘로 이뤄지는데,
// n(모듈러스)과 e(공개 지수)를 base64url 로 적어 싣는다.
type JWK struct {
	Kty string `json:"kty"`           // 열쇠 종류. 우리는 늘 "RSA"
	Use string `json:"use,omitempty"` // 쓰임새. "sig" = 서명 확인용
	Alg string `json:"alg,omitempty"`
	Kid string `json:"kid,omitempty"`
	N   string `json:"n,omitempty"`
	E   string `json:"e,omitempty"`
}

// KeySet 은 /jwks 주소가 내주는 것 그대로다.
//
// 왜 여럿인가: 열쇠를 바꿀 때(키 회전, 10부) 옛 열쇠로 서명된 토큰이
// 아직 살아 있다. 그래서 한동안 둘을 함께 내걸고, kid 로 골라 쓴다.
type KeySet struct {
	Keys []JWK `json:"keys"`
}

// PublicJWK 는 공개키 하나를 JWK 로 만든다.
func PublicJWK(kid string, pub *rsa.PublicKey) JWK {
	return JWK{
		Kty: "RSA", Use: "sig", Alg: AlgRS256, Kid: kid,
		N: B64URLEncode(pub.N.Bytes()),
		E: B64URLEncode(big.NewInt(int64(pub.E)).Bytes()),
	}
}

// Find 는 kid 로 열쇠를 골라 공개키로 되돌린다.
func (ks *KeySet) Find(kid string) (*rsa.PublicKey, error) {
	if ks == nil || len(ks.Keys) == 0 {
		return nil, errors.New("열쇠 꾸러미가 비었다")
	}
	for _, k := range ks.Keys {
		if k.Kid != kid {
			continue
		}
		if k.Kty != "RSA" {
			return nil, fmt.Errorf("열쇠 종류가 %q — RSA 만 안다",
				k.Kty)
		}
		n, err := B64URLDecode(k.N)
		if err != nil {
			return nil, fmt.Errorf("n: %w", err)
		}
		e, err := B64URLDecode(k.E)
		if err != nil {
			return nil, fmt.Errorf("e: %w", err)
		}
		return &rsa.PublicKey{
			N: new(big.Int).SetBytes(n),
			E: int(new(big.Int).SetBytes(e).Int64()),
		}, nil
	}
	return nil, fmt.Errorf("kid %q 인 열쇠가 없다", kid)
}
