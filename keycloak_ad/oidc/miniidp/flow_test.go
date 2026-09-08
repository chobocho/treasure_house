package miniidp

import (
	"crypto/rand"
	"crypto/rsa"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"

	"treasure/keycloak_ad/oidc/jwt"
	"treasure/keycloak_ad/oidc/pkce"
)

const (
	testVerifier = "v-abcdefghijklmnopqrstuvwxyz0123456789"
	testRedirect = "http://localhost:9001/callback"
)

// login 은 로그인 폼을 채워 보내고, 돌아온 인가 코드를 뽑아 준다.
func login(t *testing.T, i *IDP, user, pass string) string {
	t.Helper()
	rec := post(t, i, "/realms/campus/protocol/openid-connect/auth",
		url.Values{
			"user": {user}, "pass": {pass},
			"redirect_uri":   {testRedirect},
			"client_id":      {"lunch-web"},
			"state":          {"st-123"},
			"nonce":          {"no-456"},
			"scope":          {"openid profile email"},
			"code_challenge": {pkce.Challenge(testVerifier)},
		})
	if rec.Code != http.StatusFound {
		t.Fatalf("상태 = %d · %s", rec.Code, rec.Body.String())
	}
	loc, err := url.Parse(rec.Header().Get("Location"))
	if err != nil {
		t.Fatal(err)
	}
	return loc.Query().Get("code")
}

// bearer 는 Authorization 헤더를 붙여 한 번 부른다.
func bearer(i *IDP, path, token string) *httptest.ResponseRecorder {
	r := httptest.NewRequest("GET", path, nil)
	r.Header.Set("Authorization", "Bearer "+token)
	w := httptest.NewRecorder()
	i.Handler().ServeHTTP(w, r)
	return w
}

func exchange(t *testing.T, i *IDP, form url.Values) (int, map[string]any) {
	t.Helper()
	w := post(t, i, "/realms/campus/protocol/openid-connect/token", form)
	var out map[string]any
	json.Unmarshal(w.Body.Bytes(), &out)
	return w.Code, out
}

func tokenForm(code, verifier string) url.Values {
	return url.Values{
		"grant_type":    {"authorization_code"},
		"code":          {code},
		"redirect_uri":  {testRedirect},
		"client_id":     {"lunch-web"},
		"client_secret": {"lunch-secret-demo"},
		"code_verifier": {verifier},
	}
}

// ── 전 과정 ──────────────────────────────────────────────────────────

func TestFullCodeFlow(t *testing.T) {
	i, dir := newTestIDP(t)
	code := login(t, i, "minji", "Passw0rd!-demo")
	if code == "" {
		t.Fatal("인가 코드가 없다")
	}
	if dir.calls != 1 {
		t.Errorf("AD 를 %d번 물었다 — 한 번이어야 한다", dir.calls)
	}

	status, tok := exchange(t, i, tokenForm(code, testVerifier))
	if status != 200 {
		t.Fatalf("상태 = %d · %v", status, tok)
	}
	for _, k := range []string{"access_token", "id_token", "refresh_token",
		"token_type", "expires_in"} {
		if tok[k] == nil {
			t.Errorf("%q 가 없다", k)
		}
	}
	if tok["token_type"] != "Bearer" {
		t.Errorf("token_type = %v", tok["token_type"])
	}

	// ID 토큰은 서명이 맞아야 하고, 클레임이 우리가 보낸 값과 맞아야 한다.
	ks := keySet(t, i)
	_, c, err := jwt.Verify(tok["id_token"].(string), ks)
	if err != nil {
		t.Fatal(err)
	}
	if err := c.Validate(jwt.Options{
		Issuer:   "http://localhost:9000/realms/campus",
		Audience: "lunch-web", Nonce: "no-456",
	}); err != nil {
		t.Fatalf("클레임 검사 실패: %v", err)
	}
	if c.PreferredUsername != "minji" {
		t.Errorf("preferred_username = %q", c.PreferredUsername)
	}
	if len(c.Groups) != 2 {
		t.Errorf("groups = %v", c.Groups)
	}
}

func keySet(t *testing.T, i *IDP) *jwt.KeySet {
	t.Helper()
	w := get(t, i, "/realms/campus/protocol/openid-connect/certs")
	var ks jwt.KeySet
	if err := json.Unmarshal(w.Body.Bytes(), &ks); err != nil {
		t.Fatal(err)
	}
	return &ks
}

// 코드는 **한 번만** 쓸 수 있다. 두 번째는 거절해야 한다 —
// 가로챈 쪽이 뒤늦게 쓰는 것을 막는 마지막 방어선이다.
func TestCodeIsSingleUse(t *testing.T) {
	i, _ := newTestIDP(t)
	code := login(t, i, "minji", "Passw0rd!-demo")
	if s, _ := exchange(t, i, tokenForm(code, testVerifier)); s != 200 {
		t.Fatalf("첫 교환이 실패했다: %d", s)
	}
	s, out := exchange(t, i, tokenForm(code, testVerifier))
	if s == 200 {
		t.Error("같은 코드가 두 번 통했다")
	}
	if out["error"] != "invalid_grant" {
		t.Errorf("error = %v", out["error"])
	}
}

// PKCE 가 실제로 막는지 — verifier 가 틀리면 코드가 있어도 소용없다.
func TestWrongVerifierRejected(t *testing.T) {
	i, _ := newTestIDP(t)
	code := login(t, i, "minji", "Passw0rd!-demo")
	s, out := exchange(t, i, tokenForm(code, "다른-verifier-값-입니다-123456"))
	if s == 200 {
		t.Fatal("틀린 verifier 가 통과했다")
	}
	if out["error"] != "invalid_grant" {
		t.Errorf("error = %v", out["error"])
	}
}

func TestMissingVerifierRejected(t *testing.T) {
	i, _ := newTestIDP(t)
	code := login(t, i, "minji", "Passw0rd!-demo")
	f := tokenForm(code, "")
	f.Del("code_verifier")
	if s, _ := exchange(t, i, f); s == 200 {
		t.Error("verifier 없이 통과했다")
	}
}

func TestWrongClientSecretRejected(t *testing.T) {
	i, _ := newTestIDP(t)
	code := login(t, i, "minji", "Passw0rd!-demo")
	f := tokenForm(code, testVerifier)
	f.Set("client_secret", "틀린비밀")
	s, out := exchange(t, i, f)
	if s == 200 {
		t.Fatal("틀린 client_secret 이 통과했다")
	}
	if out["error"] != "invalid_client" {
		t.Errorf("error = %v", out["error"])
	}
}

// 코드를 발급받을 때 쓴 redirect_uri 와 교환할 때의 것이 같아야 한다.
func TestRedirectURIMustMatch(t *testing.T) {
	i, _ := newTestIDP(t)
	code := login(t, i, "minji", "Passw0rd!-demo")
	f := tokenForm(code, testVerifier)
	f.Set("redirect_uri", "http://localhost:9001/other")
	if s, _ := exchange(t, i, f); s == 200 {
		t.Error("다른 redirect_uri 가 통과했다")
	}
}

func TestBadLoginNoCode(t *testing.T) {
	i, _ := newTestIDP(t)
	w := post(t, i, "/realms/campus/protocol/openid-connect/auth",
		url.Values{
			"user": {"minji"}, "pass": {"틀린것"},
			"redirect_uri": {testRedirect}, "client_id": {"lunch-web"},
			"state": {"st-123"}, "nonce": {"no-456"},
			"scope":          {"openid"},
			"code_challenge": {pkce.Challenge(testVerifier)},
		})
	// 실패는 앱으로 돌려보내지 않고 로그인 화면을 다시 보여 준다.
	if w.Code == http.StatusFound {
		t.Errorf("실패인데 앱으로 보냈다: %s", w.Header().Get("Location"))
	}
	if !strings.Contains(w.Body.String(), "다시") &&
		!strings.Contains(w.Body.String(), "틀렸") {
		t.Errorf("다시 시도하라는 말이 없다")
	}
}

// ── /userinfo ────────────────────────────────────────────────────────

func TestUserinfoNeedsBearer(t *testing.T) {
	i, _ := newTestIDP(t)
	w := get(t, i, "/realms/campus/protocol/openid-connect/userinfo")
	if w.Code != http.StatusUnauthorized {
		t.Errorf("상태 = %d, 원하는 것 401", w.Code)
	}
	if !strings.Contains(w.Header().Get("WWW-Authenticate"), "Bearer") {
		t.Errorf("WWW-Authenticate = %q",
			w.Header().Get("WWW-Authenticate"))
	}
}

func TestUserinfoWithAccessToken(t *testing.T) {
	i, _ := newTestIDP(t)
	code := login(t, i, "minji", "Passw0rd!-demo")
	_, tok := exchange(t, i, tokenForm(code, testVerifier))

	w := bearer(i, "/realms/campus/protocol/openid-connect/userinfo",
		tok["access_token"].(string))
	if w.Code != 200 {
		t.Fatalf("상태 = %d · %s", w.Code, w.Body.String())
	}
	var out map[string]any
	json.Unmarshal(w.Body.Bytes(), &out)
	if out["sub"] == nil || out["preferred_username"] != "minji" {
		t.Errorf("userinfo = %v", out)
	}
}

// ID 토큰으로 /userinfo 를 부르면 안 된다. 둘은 쓰임이 다르다 —
// ID 토큰은 "누구인지" 를 앱에게 알리는 것이고,
// 액세스 토큰은 "무엇을 해도 되는지" 를 자원 서버에 보이는 것이다.
func TestIDTokenIsNotAnAccessToken(t *testing.T) {
	i, _ := newTestIDP(t)
	code := login(t, i, "minji", "Passw0rd!-demo")
	_, tok := exchange(t, i, tokenForm(code, testVerifier))
	w := bearer(i, "/realms/campus/protocol/openid-connect/userinfo",
		tok["id_token"].(string))
	if w.Code == 200 {
		t.Error("ID 토큰이 액세스 토큰으로 통했다")
	}
}

// ── 리프레시 ─────────────────────────────────────────────────────────

func TestRefreshRotates(t *testing.T) {
	i, _ := newTestIDP(t)
	code := login(t, i, "minji", "Passw0rd!-demo")
	_, first := exchange(t, i, tokenForm(code, testVerifier))
	rt := first["refresh_token"].(string)

	s, second := exchange(t, i, url.Values{
		"grant_type":    {"refresh_token"},
		"refresh_token": {rt},
		"client_id":     {"lunch-web"},
		"client_secret": {"lunch-secret-demo"},
	})
	if s != 200 {
		t.Fatalf("상태 = %d · %v", s, second)
	}
	if second["refresh_token"] == rt {
		t.Error("리프레시 토큰이 그대로다 — 회전해야 한다")
	}
	// 쓴 리프레시 토큰은 죽는다. 재사용은 도난 신호다.
	if s, _ := exchange(t, i, url.Values{
		"grant_type": {"refresh_token"}, "refresh_token": {rt},
		"client_id":     {"lunch-web"},
		"client_secret": {"lunch-secret-demo"},
	}); s == 200 {
		t.Error("쓴 리프레시 토큰이 다시 통했다")
	}
}

// ── 로그아웃 ─────────────────────────────────────────────────────────

func TestLogoutRedirectsBack(t *testing.T) {
	i, _ := newTestIDP(t)
	code := login(t, i, "minji", "Passw0rd!-demo")
	_, tok := exchange(t, i, tokenForm(code, testVerifier))
	q := url.Values{
		"id_token_hint":            {tok["id_token"].(string)},
		"post_logout_redirect_uri": {testRedirect},
	}
	w := get(t, i, "/realms/campus/protocol/openid-connect/logout?"+
		q.Encode())
	if w.Code != http.StatusFound {
		t.Fatalf("상태 = %d · %s", w.Code, w.Body.String())
	}
	if w.Header().Get("Location") != testRedirect {
		t.Errorf("Location = %s", w.Header().Get("Location"))
	}
}

// 로그아웃한 뒤 돌아갈 곳은 콜백이 아니라 대개 **첫 화면**이다.
//
// 콜백은 인가 코드를 받는 자리라, 코드도 state 도 없이 열면 앱이
// "내가 시작한 로그인이 아니다" 로 거절한다. 그래서 Keycloak 에는
// 돌아갈 주소 목록이 따로 있다("Valid post logout redirect URIs").
// 우리도 같은 칸을 둔다.
func TestLogoutUsesPostLogoutList(t *testing.T) {
	key, err := rsa.GenerateKey(rand.Reader, 1024)
	if err != nil {
		t.Fatal(err)
	}
	i := NewIDP(Config{
		Issuer: "http://localhost:9000/realms/campus",
		Realm:  "campus", ClientID: "lunch-web",
		ClientSecret:   "lunch-secret-demo",
		RedirectURIs:   []string{testRedirect},
		PostLogoutURIs: []string{"http://localhost:9001/"},
		Key:            key, Kid: "demo-1",
	}, &fakeDir{})

	q := url.Values{"post_logout_redirect_uri": {"http://localhost:9001/"}}
	w := get(t, i, "/realms/campus/protocol/openid-connect/logout?"+
		q.Encode())
	if w.Code != http.StatusFound {
		t.Fatalf("상태 = %d · %s", w.Code, w.Body.String())
	}
	if got := w.Header().Get("Location"); got != "http://localhost:9001/" {
		t.Errorf("Location = %q", got)
	}

	// 목록을 따로 뒀으면 콜백 주소는 이제 로그아웃 귀환지가 아니다.
	q2 := url.Values{"post_logout_redirect_uri": {testRedirect}}
	w2 := get(t, i, "/realms/campus/protocol/openid-connect/logout?"+
		q2.Encode())
	if w2.Code != http.StatusBadRequest {
		t.Errorf("콜백으로 돌려보냈다 (상태 %d)", w2.Code)
	}
}

// 돌아갈 주소도 등록된 것이어야 한다 — 아니면 로그아웃 링크가
// 사용자를 아무 데나 보내는 통로가 된다(오픈 리다이렉트).
func TestLogoutRejectsUnknownRedirect(t *testing.T) {
	i, _ := newTestIDP(t)
	q := url.Values{"post_logout_redirect_uri": {"http://evil.example/"}}
	w := get(t, i, "/realms/campus/protocol/openid-connect/logout?"+
		q.Encode())
	if w.Header().Get("Location") == "http://evil.example/" {
		t.Error("모르는 주소로 보냈다")
	}
}
