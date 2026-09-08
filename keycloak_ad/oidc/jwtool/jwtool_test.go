package main

import (
	"crypto/rand"
	"crypto/rsa"
	"strings"
	"testing"
	"time"

	"treasure/keycloak_ad/oidc/jwt"
)

var (
	testKey *rsa.PrivateKey
	testNow = time.Date(2026, 9, 8, 12, 0, 0, 0, time.UTC)
)

func key(t *testing.T) *rsa.PrivateKey {
	t.Helper()
	if testKey == nil {
		k, err := rsa.GenerateKey(rand.Reader, 2048)
		if err != nil {
			t.Fatal(err)
		}
		testKey = k
	}
	return testKey
}

func mint(t *testing.T, c jwt.Claims) string {
	t.Helper()
	tok, err := jwt.Sign(jwt.Header{Alg: jwt.AlgRS256, Typ: "JWT",
		Kid: "demo-1"}, c, key(t))
	if err != nil {
		t.Fatal(err)
	}
	return tok
}

func sample(t *testing.T) jwt.Claims {
	t.Helper()
	return jwt.Claims{
		Iss: "http://localhost:9000/realms/campus",
		Sub: "CN=Kim Minji,OU=Students,DC=ad,DC=campus,DC=example",
		Aud: "lunch-web",
		Iat: testNow.Unix(), Exp: testNow.Add(5 * time.Minute).Unix(),
		Nonce: "no-456", PreferredUsername: "minji",
		Email: "minji@campus.example", Name: "Kim Minji",
		Groups: []string{"lunch-users", "campus-all"},
	}
}

func keySet(t *testing.T) *jwt.KeySet {
	t.Helper()
	return &jwt.KeySet{Keys: []jwt.JWK{
		jwt.PublicJWK("demo-1", &key(t).PublicKey)}}
}

func run(t *testing.T, f func(w *strings.Builder) error) (string, error) {
	t.Helper()
	var sb strings.Builder
	err := f(&sb)
	return sb.String(), err
}

func TestDecodeShowsAllThreePieces(t *testing.T) {
	tok := mint(t, sample(t))
	out, err := run(t, func(w *strings.Builder) error {
		return decode(w, tok, testNow.Add(time.Minute))
	})
	if err != nil {
		t.Fatalf("decode: %v", err)
	}
	for _, want := range []string{
		"RS256", "demo-1", "lunch-web", "minji@campus.example",
		"lunch-users", "no-456",
	} {
		if !strings.Contains(out, want) {
			t.Errorf("%q 가 없다\n%s", want, out)
		}
	}
}

// decode 는 서명을 **확인하지 않는다**. 그 사실이 화면에 적혀야 한다 —
// "읽었다" 를 "믿는다" 로 착각하는 것이 4부에서 가장 위험한 오해다.
func TestDecodeSaysItDidNotVerify(t *testing.T) {
	tok := mint(t, sample(t))
	out, _ := run(t, func(w *strings.Builder) error {
		return decode(w, tok, testNow.Add(time.Minute))
	})
	if !strings.Contains(out, "확인하지 않") {
		t.Errorf("확인하지 않았다는 말이 없다\n%s", out)
	}
}

// 서명이 망가진 토큰도 decode 는 읽어 낸다. 그게 요점이다.
func TestDecodeReadsBrokenSignature(t *testing.T) {
	tok := mint(t, sample(t))
	broken := tok[:strings.LastIndex(tok, ".")+1] + "AAAA"
	out, err := run(t, func(w *strings.Builder) error {
		return decode(w, broken, testNow)
	})
	if err != nil {
		t.Fatalf("망가진 서명에서 멈췄다: %v", err)
	}
	if !strings.Contains(out, "minji") {
		t.Errorf("내용을 못 읽었다\n%s", out)
	}
}

func TestDecodeShowsExpiryInHumanTime(t *testing.T) {
	tok := mint(t, sample(t))
	out, _ := run(t, func(w *strings.Builder) error {
		return decode(w, tok, testNow.Add(time.Minute))
	})
	if !strings.Contains(out, "2026-09-08 12:05:00 UTC") {
		t.Errorf("사람이 읽는 시각이 없다\n%s", out)
	}
	// 못 박은 시각 기준이라 "4분 뒤" 가 언제 돌려도 같아야 한다.
	if !strings.Contains(out, "4분 뒤") {
		t.Errorf("남은 시간이 안 나온다\n%s", out)
	}
}

func TestDecodeRejectsNonToken(t *testing.T) {
	_, err := run(t, func(w *strings.Builder) error {
		return decode(w, "이건 토큰이 아니다", testNow)
	})
	if err == nil {
		t.Fatal("토큰이 아닌 것을 받아들였다")
	}
}

func TestVerifyAccepts(t *testing.T) {
	tok := mint(t, sample(t))
	out, err := run(t, func(w *strings.Builder) error {
		return verify(w, tok, keySet(t), verifyOptions{
			Issuer:   "http://localhost:9000/realms/campus",
			Audience: "lunch-web", Now: testNow.Add(time.Minute)})
	})
	if err != nil {
		t.Fatalf("멀쩡한 토큰을 거절했다: %v\n%s", err, out)
	}
	if !strings.Contains(out, "demo-1") {
		t.Errorf("어느 열쇠로 확인했는지 안 나온다\n%s", out)
	}
}

func TestVerifyRejectsBrokenSignature(t *testing.T) {
	tok := mint(t, sample(t))
	broken := tok[:strings.LastIndex(tok, ".")+1] +
		jwt.B64URLEncode(make([]byte, 256))
	_, err := run(t, func(w *strings.Builder) error {
		return verify(w, broken, keySet(t), verifyOptions{
			Issuer:   "http://localhost:9000/realms/campus",
			Audience: "lunch-web", Now: testNow})
	})
	if err == nil {
		t.Fatal("망가진 서명을 통과시켰다")
	}
}

func TestVerifyRejectsExpired(t *testing.T) {
	tok := mint(t, sample(t))
	_, err := run(t, func(w *strings.Builder) error {
		return verify(w, tok, keySet(t), verifyOptions{
			Issuer:   "http://localhost:9000/realms/campus",
			Audience: "lunch-web", Now: testNow.Add(time.Hour)})
	})
	if err == nil {
		t.Fatal("기한 지난 토큰을 통과시켰다")
	}
	if !strings.Contains(err.Error(), "기한") {
		t.Errorf("이유가 기한이 아니다: %v", err)
	}
}

// 서명이 맞아도 **나에게 준 토큰이 아니면** 쓰면 안 된다.
func TestVerifyRejectsWrongAudience(t *testing.T) {
	tok := mint(t, sample(t))
	_, err := run(t, func(w *strings.Builder) error {
		return verify(w, tok, keySet(t), verifyOptions{
			Issuer:   "http://localhost:9000/realms/campus",
			Audience: "다른-앱", Now: testNow})
	})
	if err == nil {
		t.Fatal("남에게 준 토큰을 통과시켰다")
	}
}

func TestVerifyRejectsWrongIssuer(t *testing.T) {
	tok := mint(t, sample(t))
	_, err := run(t, func(w *strings.Builder) error {
		return verify(w, tok, keySet(t), verifyOptions{
			Issuer:   "https://남의-서버.example/realms/campus",
			Audience: "lunch-web", Now: testNow})
	})
	if err == nil {
		t.Fatal("남이 발급한 토큰을 통과시켰다")
	}
}

// alg=none — 서명을 아예 뗀 토큰. 옛 라이브러리들이 여기서 뚫렸다.
func TestVerifyRejectsAlgNone(t *testing.T) {
	head := jwt.B64URLEncode([]byte(`{"alg":"none"}`))
	body := jwt.B64URLEncode([]byte(`{"sub":"admin","aud":"lunch-web"}`))
	_, err := run(t, func(w *strings.Builder) error {
		return verify(w, head+"."+body+".", keySet(t), verifyOptions{
			Issuer:   "http://localhost:9000/realms/campus",
			Audience: "lunch-web", Now: testNow})
	})
	if err == nil {
		t.Fatal("alg=none 을 통과시켰다")
	}
}

func TestVerifyReportsUnknownKid(t *testing.T) {
	tok := mint(t, sample(t))
	ks := &jwt.KeySet{Keys: []jwt.JWK{
		jwt.PublicJWK("다른-열쇠", &key(t).PublicKey)}}
	_, err := run(t, func(w *strings.Builder) error {
		return verify(w, tok, ks, verifyOptions{
			Issuer:   "http://localhost:9000/realms/campus",
			Audience: "lunch-web", Now: testNow})
	})
	if err == nil {
		t.Fatal("모르는 kid 를 통과시켰다")
	}
}
