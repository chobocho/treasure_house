package jwt

import (
	"crypto/rand"
	"crypto/rsa"
	"strings"
	"testing"
	"time"
)

// ── base64url ────────────────────────────────────────────────────────

// RFC 7515 부록 A.1 과 RFC 7519 §3.1 에 실린 실제 값이다.
// 여기가 어긋나면 우리가 만든 토큰을 아무도 못 읽는다.
func TestB64URLGolden(t *testing.T) {
	cases := []struct {
		raw, want string
	}{
		{"{\"typ\":\"JWT\",\r\n \"alg\":\"HS256\"}",
			"eyJ0eXAiOiJKV1QiLA0KICJhbGciOiJIUzI1NiJ9"},
		{"{\"iss\":\"joe\",\r\n \"exp\":1300819380,\r\n " +
			"\"http://example.com/is_root\":true}",
			"eyJpc3MiOiJqb2UiLA0KICJleHAiOjEzMDA4MTkzODAsDQogImh0dHA6Ly9l" +
				"eGFtcGxlLmNvbS9pc19yb290Ijp0cnVlfQ"},
	}
	for _, c := range cases {
		if got := B64URLEncode([]byte(c.raw)); got != c.want {
			t.Errorf("인코딩이 다르다\n  got  %s\n  want %s", got, c.want)
		}
		back, err := B64URLDecode(c.want)
		if err != nil || string(back) != c.raw {
			t.Errorf("되돌리기 실패: %v", err)
		}
	}
}

// base64url 은 + / = 를 쓰지 않는다. 주소에 그대로 실어야 하기
// 때문이다.
func TestB64URLHasNoUnsafeChars(t *testing.T) {
	raw := []byte{0xFB, 0xFF, 0xBE, 0x3E, 0x00, 0x7F}
	got := B64URLEncode(raw)
	for _, bad := range []string{"+", "/", "="} {
		if strings.Contains(got, bad) {
			t.Errorf("%q 가 들어 있다: %s", bad, got)
		}
	}
	back, err := B64URLDecode(got)
	if err != nil || string(back) != string(raw) {
		t.Errorf("되돌리기 실패: %v", err)
	}
}

func TestB64URLRejectsGarbage(t *testing.T) {
	for _, s := range []string{"!!!", "eyJ*", "a"} {
		if _, err := B64URLDecode(s); err == nil {
			t.Errorf("%q: 오류가 나야 한다", s)
		}
	}
}

// ── 서명과 확인 ──────────────────────────────────────────────────────

func testKey(t *testing.T) *rsa.PrivateKey {
	t.Helper()
	// 2048비트를 매번 만들면 시험이 느려진다. 1024비트는 실무에서 쓰면
	// 안 되지만 시험에서는 충분하다 — 여기서 보는 것은 길이가 아니라
	// 규칙이다.
	k, err := rsa.GenerateKey(rand.Reader, 1024)
	if err != nil {
		t.Fatal(err)
	}
	return k
}

func TestSignAndVerify(t *testing.T) {
	key := testKey(t)
	ks := &KeySet{Keys: []JWK{PublicJWK("k1", &key.PublicKey)}}
	tok, err := Sign(Header{Alg: "RS256", Typ: "JWT", Kid: "k1"},
		Claims{Iss: "https://sso.campus.example/realms/campus",
			Sub: "minji", Aud: "lunch-web", Exp: 1 << 40, Nonce: "n-0S6"},
		key)
	if err != nil {
		t.Fatal(err)
	}
	if n := strings.Count(tok, "."); n != 2 {
		t.Fatalf("점이 %d개 — 토큰은 세 조각이다", n)
	}
	h, c, err := Verify(tok, ks)
	if err != nil {
		t.Fatal(err)
	}
	if h.Alg != "RS256" || h.Kid != "k1" {
		t.Errorf("헤더 = %+v", h)
	}
	if c.Sub != "minji" || c.Nonce != "n-0S6" {
		t.Errorf("클레임 = %+v", c)
	}
}

// 서명을 확인하지 않고도 내용은 읽을 수 있다. 그게 base64url 이라는
// 뜻이고, **토큰에 비밀을 담으면 안 되는 이유**다.
func TestParseWithoutVerifying(t *testing.T) {
	key := testKey(t)
	tok, _ := Sign(Header{Alg: "RS256", Kid: "k1"},
		Claims{Sub: "minji", Email: "minji@campus.example"}, key)
	_, c, err := Parse(tok)
	if err != nil {
		t.Fatal(err)
	}
	if c.Sub != "minji" || c.Email != "minji@campus.example" {
		t.Errorf("읽은 것 = %+v", c)
	}
}

// 내용을 한 글자만 바꿔도 서명이 깨져야 한다.
func TestTamperedPayloadRejected(t *testing.T) {
	key := testKey(t)
	ks := &KeySet{Keys: []JWK{PublicJWK("k1", &key.PublicKey)}}
	tok, _ := Sign(Header{Alg: "RS256", Kid: "k1"},
		Claims{Sub: "minji", Groups: []string{"lunch-users"}}, key)

	parts := strings.Split(tok, ".")
	raw, _ := B64URLDecode(parts[1])
	evil := strings.Replace(string(raw), "lunch-users", "lunch-admins", 1)
	parts[1] = B64URLEncode([]byte(evil))
	bad := strings.Join(parts, ".")

	if _, c, err := Parse(bad); err != nil || c.Groups[0] != "lunch-admins" {
		t.Fatalf("고친 토큰을 읽지 못했다: %v", err)
	}
	if _, _, err := Verify(bad, ks); err == nil {
		t.Error("고친 토큰이 서명 확인을 통과했다")
	}
}

func TestWrongKeyRejected(t *testing.T) {
	key, other := testKey(t), testKey(t)
	ks := &KeySet{Keys: []JWK{PublicJWK("k1", &other.PublicKey)}}
	tok, _ := Sign(Header{Alg: "RS256", Kid: "k1"}, Claims{Sub: "minji"}, key)
	if _, _, err := Verify(tok, ks); err == nil {
		t.Error("남의 열쇠로 확인이 통과했다")
	}
}

// alg 를 none 으로 바꾸고 서명을 지우는 공격. 초창기 JWT 라이브러리들이
// 무더기로 뚫린 방식이다. 헤더의 alg 를 그대로 믿으면 안 된다.
func TestAlgNoneRejected(t *testing.T) {
	key := testKey(t)
	ks := &KeySet{Keys: []JWK{PublicJWK("k1", &key.PublicKey)}}
	head := B64URLEncode([]byte(`{"alg":"none","kid":"k1"}`))
	body := B64URLEncode([]byte(`{"sub":"admin.lee"}`))
	if _, _, err := Verify(head+"."+body+".", ks); err == nil {
		t.Error("alg=none 이 통과했다")
	}
}

// alg 를 HS256 으로 바꿔 **공개키를 비밀키로 쓰게 하는** 공격.
// 공개키는 누구나 아니까, 이게 통하면 아무나 토큰을 만들 수 있다.
func TestAlgConfusionRejected(t *testing.T) {
	key := testKey(t)
	ks := &KeySet{Keys: []JWK{PublicJWK("k1", &key.PublicKey)}}
	head := B64URLEncode([]byte(`{"alg":"HS256","kid":"k1"}`))
	body := B64URLEncode([]byte(`{"sub":"admin.lee"}`))
	sig := B64URLEncode([]byte("아무 서명"))
	if _, _, err := Verify(head+"."+body+"."+sig, ks); err == nil {
		t.Error("HS256 으로 바꾼 토큰이 통과했다")
	}
}

func TestVerifyRejectsMalformed(t *testing.T) {
	key := testKey(t)
	ks := &KeySet{Keys: []JWK{PublicJWK("k1", &key.PublicKey)}}
	for _, s := range []string{
		"", "a.b", "a.b.c.d", "...", "!!!.!!!.!!!",
	} {
		if _, _, err := Verify(s, ks); err == nil {
			t.Errorf("%q: 오류가 나야 한다", s)
		}
	}
}

// 모르는 kid 는 거절한다. 열쇠가 여럿일 때 어느 것으로 확인할지
// 헤더의 kid 가 알려 주고, 그게 없으면 확인할 수 없다.
func TestUnknownKidRejected(t *testing.T) {
	key := testKey(t)
	ks := &KeySet{Keys: []JWK{PublicJWK("k1", &key.PublicKey)}}
	tok, _ := Sign(Header{Alg: "RS256", Kid: "k9"}, Claims{Sub: "x"}, key)
	if _, _, err := Verify(tok, ks); err == nil {
		t.Error("모르는 kid 가 통과했다")
	}
}

// ── 클레임 검사 ──────────────────────────────────────────────────────

func TestClaimsValidate(t *testing.T) {
	now := time.Date(2026, 9, 8, 9, 0, 0, 0, time.UTC)
	base := Claims{
		Iss: "https://sso.campus.example/realms/campus",
		Aud: "lunch-web", Sub: "minji",
		Exp: now.Add(5 * time.Minute).Unix(),
		Iat: now.Unix(), Nonce: "n-0S6",
	}
	opt := Options{
		Issuer: base.Iss, Audience: "lunch-web",
		Nonce: "n-0S6", Now: now,
	}
	if err := base.Validate(opt); err != nil {
		t.Fatalf("멀쩡한 토큰이 막혔다: %v", err)
	}

	bad := []struct {
		name  string
		tweak func(*Claims)
	}{
		{"만료됨", func(c *Claims) { c.Exp = now.Add(-time.Second).Unix() }},
		{"아직 유효 시각 전", func(c *Claims) {
			c.Nbf = now.Add(time.Hour).Unix()
		}},
		{"발급자가 다르다", func(c *Claims) { c.Iss = "https://evil.example" }},
		{"대상이 다르다", func(c *Claims) { c.Aud = "다른앱" }},
		{"nonce 가 다르다", func(c *Claims) { c.Nonce = "다른값" }},
		{"sub 가 없다", func(c *Claims) { c.Sub = "" }},
		{"exp 가 없다", func(c *Claims) { c.Exp = 0 }},
	}
	for _, b := range bad {
		c := base
		b.tweak(&c)
		if err := c.Validate(opt); err == nil {
			t.Errorf("%s — 통과하면 안 된다", b.name)
		}
	}
}

// 시계는 서버마다 몇 초씩 어긋난다. 그 폭만큼은 봐준다.
func TestClaimsLeeway(t *testing.T) {
	now := time.Date(2026, 9, 8, 9, 0, 0, 0, time.UTC)
	c := Claims{Iss: "i", Aud: "a", Sub: "s",
		Exp: now.Add(-20 * time.Second).Unix()}
	opt := Options{Issuer: "i", Audience: "a", Now: now}
	if err := c.Validate(opt); err == nil {
		t.Error("여유 없이 20초 지난 토큰이 통과했다")
	}
	opt.Leeway = 60 * time.Second
	if err := c.Validate(opt); err != nil {
		t.Errorf("여유 60초인데 막혔다: %v", err)
	}
}

// nonce 를 확인하라고 해 놓고 토큰에 nonce 가 없으면 거절해야 한다.
// "값이 없으면 통과" 로 두면 검사 자체가 없는 것과 같다.
func TestMissingNonceRejectedWhenExpected(t *testing.T) {
	now := time.Now()
	c := Claims{Iss: "i", Aud: "a", Sub: "s", Exp: now.Add(time.Hour).Unix()}
	err := c.Validate(Options{Issuer: "i", Audience: "a",
		Nonce: "기대값", Now: now})
	if err == nil {
		t.Error("nonce 가 없는데 통과했다")
	}
}

// ── JWKS ─────────────────────────────────────────────────────────────

// 공개키를 JSON 으로 실어 나르는 형식. n 과 e 를 base64url 로 적는다.
func TestJWKRoundTrip(t *testing.T) {
	key := testKey(t)
	jwk := PublicJWK("k1", &key.PublicKey)
	if jwk.Kty != "RSA" || jwk.Alg != "RS256" || jwk.Use != "sig" {
		t.Errorf("JWK = %+v", jwk)
	}
	if jwk.N == "" || jwk.E == "" {
		t.Fatal("n·e 가 비었다")
	}
	ks := &KeySet{Keys: []JWK{jwk}}
	pub, err := ks.Find("k1")
	if err != nil {
		t.Fatal(err)
	}
	if pub.N.Cmp(key.PublicKey.N) != 0 || pub.E != key.PublicKey.E {
		t.Error("되돌린 공개키가 원본과 다르다")
	}
}

func TestKeySetFindMissing(t *testing.T) {
	ks := &KeySet{}
	if _, err := ks.Find("없는열쇠"); err == nil {
		t.Error("빈 열쇠 꾸러미에서 찾아졌다")
	}
}

// 열쇠가 둘일 때 kid 로 골라야 한다 — 키 회전(10부) 중에는 늘 그렇다.
func TestKeySetPicksByKid(t *testing.T) {
	old, cur := testKey(t), testKey(t)
	ks := &KeySet{Keys: []JWK{
		PublicJWK("old", &old.PublicKey),
		PublicJWK("cur", &cur.PublicKey),
	}}
	tok, _ := Sign(Header{Alg: "RS256", Kid: "cur"}, Claims{Sub: "s"}, cur)
	if _, _, err := Verify(tok, ks); err != nil {
		t.Errorf("새 열쇠로 서명한 토큰이 막혔다: %v", err)
	}
	tok2, _ := Sign(Header{Alg: "RS256", Kid: "old"}, Claims{Sub: "s"}, old)
	if _, _, err := Verify(tok2, ks); err != nil {
		t.Errorf("옛 열쇠로 서명한 토큰이 막혔다: %v", err)
	}
}
