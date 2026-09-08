package pkce

import (
	"strings"
	"testing"
)

// RFC 7636 부록 B 에 실린 값이다. 이 표준 문서를 읽는 누구나 같은 값을
// 손으로 확인할 수 있다 — 우리 구현이 맞는지 보는 가장 확실한 자다.
func TestRFC7636AppendixB(t *testing.T) {
	const (
		verifier  = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
		challenge = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
	)
	if got := Challenge(verifier); got != challenge {
		t.Errorf("challenge = %s\n원하는 것    %s", got, challenge)
	}
}

// 만든 verifier 는 매번 달라야 하고, 규격이 정한 길이·글자 안에 있어야
// 한다.
func TestNewVerifier(t *testing.T) {
	seen := map[string]bool{}
	for i := 0; i < 200; i++ {
		v, err := NewVerifier()
		if err != nil {
			t.Fatal(err)
		}
		// RFC 7636 §4.1 — 43~128글자, [A-Za-z0-9-._~] 만
		if len(v) < 43 || len(v) > 128 {
			t.Fatalf("길이가 %d — 43~128 이어야 한다", len(v))
		}
		for _, c := range v {
			if !strings.ContainsRune(
				"ABCDEFGHIJKLMNOPQRSTUVWXYZ"+
					"abcdefghijklmnopqrstuvwxyz0123456789-._~", c) {
				t.Fatalf("못 쓰는 글자 %q 가 있다: %s", c, v)
			}
		}
		if seen[v] {
			t.Fatalf("같은 값이 두 번 나왔다: %s", v)
		}
		seen[v] = true
	}
}

func TestVerifyMatches(t *testing.T) {
	v, _ := NewVerifier()
	c := Challenge(v)
	if !Verify(v, c) {
		t.Error("자기 짝인데 안 맞는다고 한다")
	}
	other, _ := NewVerifier()
	if Verify(other, c) {
		t.Error("남의 verifier 가 통과했다")
	}
	if Verify(v, "") || Verify("", c) {
		t.Error("빈 값이 통과했다")
	}
}

// challenge 도 base64url 이라 + / = 가 없어야 한다 — 주소에 실려 가기
// 때문이다.
func TestChallengeIsURLSafe(t *testing.T) {
	for i := 0; i < 50; i++ {
		v, _ := NewVerifier()
		c := Challenge(v)
		for _, bad := range []string{"+", "/", "="} {
			if strings.Contains(c, bad) {
				t.Fatalf("%q 가 들어 있다: %s", bad, c)
			}
		}
	}
}

// 우리는 S256 만 받는다. "plain" 은 verifier 를 그대로 보내는 방식이라
// 가로챈 쪽이 그대로 쓸 수 있어 보호가 되지 않는다 (RFC 7636 §4.2).
func TestMethodIsS256(t *testing.T) {
	if Method != "S256" {
		t.Errorf("Method = %q", Method)
	}
}
