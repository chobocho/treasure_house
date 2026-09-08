package miniidp

import (
	"crypto/rand"
	"crypto/rsa"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"

	"treasure/keycloak_ad/oidc/jwt"
	"treasure/keycloak_ad/oidc/pkce"
)

// fakeDir 은 AD 대신 쓰는 아주 작은 명부다.
//
// Directory 를 인터페이스로 둔 덕분에 시험이 LDAP 없이 돈다 —
// 그리고 그 인터페이스가 곧 Keycloak 의 "User Federation" 이 하는 일이다.
type fakeDir struct{ calls int }

func (f *fakeDir) Authenticate(user, pass string) (User, error) {
	f.calls++
	if user == "minji" && pass == "Passw0rd!-demo" {
		return User{
			DN:       "CN=Kim Minji,OU=Students,DC=ad,DC=campus,DC=example",
			Username: "minji", Email: "minji@campus.example",
			Name:   "Kim Minji",
			Groups: []string{"lunch-users", "campus-all"},
		}, nil
	}
	if user == "jisoo.oh" {
		return User{}, errors.New("계정이 꺼져 있다 (data 533)")
	}
	return User{}, errors.New("아이디나 비밀번호가 틀렸다 (data 52e)")
}

func newTestIDP(t *testing.T) (*IDP, *fakeDir) {
	t.Helper()
	key, err := rsa.GenerateKey(rand.Reader, 1024)
	if err != nil {
		t.Fatal(err)
	}
	dir := &fakeDir{}
	cfg := Config{
		Issuer: "http://localhost:9000/realms/campus",
		Realm:  "campus", ClientID: "lunch-web",
		ClientSecret: "lunch-secret-demo",
		RedirectURIs: []string{"http://localhost:9001/callback"},
		Key:          key, Kid: "demo-1",
	}
	return NewIDP(cfg, dir), dir
}

func get(t *testing.T, i *IDP, path string) *httptest.ResponseRecorder {
	t.Helper()
	w := httptest.NewRecorder()
	i.Handler().ServeHTTP(w, httptest.NewRequest("GET", path, nil))
	return w
}

func post(t *testing.T, i *IDP, path string, form url.Values,
	cookies ...*http.Cookie) *httptest.ResponseRecorder {
	t.Helper()
	r := httptest.NewRequest("POST", path, strings.NewReader(form.Encode()))
	r.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	for _, c := range cookies {
		r.AddCookie(c)
	}
	w := httptest.NewRecorder()
	i.Handler().ServeHTTP(w, r)
	return w
}

// ── 안내문 ───────────────────────────────────────────────────────────

// 주소를 손으로 적지 않아도 되게, 서버가 자기 주소들을 알려 주는 문서.
func TestDiscovery(t *testing.T) {
	i, _ := newTestIDP(t)
	w := get(t, i, "/realms/campus/.well-known/openid-configuration")
	if w.Code != 200 {
		t.Fatalf("상태 = %d", w.Code)
	}
	var d map[string]any
	if err := json.Unmarshal(w.Body.Bytes(), &d); err != nil {
		t.Fatal(err)
	}
	for _, k := range []string{"issuer", "authorization_endpoint",
		"token_endpoint", "jwks_uri", "userinfo_endpoint",
		"end_session_endpoint", "response_types_supported",
		"code_challenge_methods_supported"} {
		if d[k] == nil {
			t.Errorf("%q 가 없다", k)
		}
	}
	if d["issuer"] != "http://localhost:9000/realms/campus" {
		t.Errorf("issuer = %v", d["issuer"])
	}
}

func TestJWKS(t *testing.T) {
	i, _ := newTestIDP(t)
	w := get(t, i, "/realms/campus/protocol/openid-connect/certs")
	if w.Code != 200 {
		t.Fatalf("상태 = %d", w.Code)
	}
	var ks jwt.KeySet
	if err := json.Unmarshal(w.Body.Bytes(), &ks); err != nil {
		t.Fatal(err)
	}
	if len(ks.Keys) != 1 || ks.Keys[0].Kid != "demo-1" {
		t.Fatalf("열쇠 = %+v", ks.Keys)
	}
	// 개인키가 새어 나가면 안 된다. d·p·q 는 JWK 에 없어야 한다.
	for _, bad := range []string{`"d"`, `"p"`, `"q"`} {
		if strings.Contains(w.Body.String(), bad) {
			t.Errorf("개인키 조각 %s 가 실려 있다", bad)
		}
	}
}

// ── /authorize 의 검사들 ─────────────────────────────────────────────

func authzURL(extra url.Values) string {
	q := url.Values{
		"response_type":         {"code"},
		"client_id":             {"lunch-web"},
		"redirect_uri":          {"http://localhost:9001/callback"},
		"scope":                 {"openid profile email"},
		"state":                 {"st-123"},
		"nonce":                 {"no-456"},
		"code_challenge":        {pkce.Challenge("v-abcdefghijklmnopqrstuvwxyz0123456789")},
		"code_challenge_method": {"S256"},
	}
	for k, v := range extra {
		if len(v) == 1 && v[0] == "" {
			q.Del(k)
			continue
		}
		q[k] = v
	}
	return "/realms/campus/protocol/openid-connect/auth?" + q.Encode()
}

func TestAuthorizeShowsLoginForm(t *testing.T) {
	i, _ := newTestIDP(t)
	w := get(t, i, authzURL(nil))
	if w.Code != 200 {
		t.Fatalf("상태 = %d · %s", w.Code, w.Body.String())
	}
	if !strings.Contains(w.Body.String(), `method="post"`) {
		t.Errorf("로그인 폼이 없다")
	}
}

// redirect_uri 가 등록된 것과 다르면 **그쪽으로 보내면 안 된다**.
// 오류를 그 주소로 보내 주면 공격자가 오류 화면으로 정보를 받아 간다.
func TestAuthorizeRejectsUnknownRedirect(t *testing.T) {
	i, _ := newTestIDP(t)
	w := get(t, i, authzURL(url.Values{
		"redirect_uri": {"http://evil.example/steal"}}))
	if w.Code != http.StatusBadRequest {
		t.Errorf("상태 = %d, 원하는 것 400", w.Code)
	}
	if loc := w.Header().Get("Location"); loc != "" {
		t.Errorf("모르는 주소로 보냈다: %s", loc)
	}
}

func TestAuthorizeRejectsUnknownClient(t *testing.T) {
	i, _ := newTestIDP(t)
	w := get(t, i, authzURL(url.Values{"client_id": {"남의앱"}}))
	if w.Code != http.StatusBadRequest {
		t.Errorf("상태 = %d", w.Code)
	}
}

// PKCE 는 필수로 둔다. 없으면 로그인 자체를 시작하지 않는다.
func TestAuthorizeRequiresPKCE(t *testing.T) {
	i, _ := newTestIDP(t)
	for _, extra := range []url.Values{
		{"code_challenge": {""}},
		{"code_challenge_method": {"plain"}},
	} {
		w := get(t, i, authzURL(extra))
		if w.Code == 200 {
			t.Errorf("%v 인데 로그인 폼이 나왔다", extra)
		}
	}
}

// 우리는 인가 코드 흐름만 한다. implicit 은 토큰을 주소에 실어 보내는
// 옛 방식이고, 그래서 사라졌다(1부 5장의 그 이유다).
func TestAuthorizeRejectsImplicit(t *testing.T) {
	i, _ := newTestIDP(t)
	w := get(t, i, authzURL(url.Values{"response_type": {"token"}}))
	if w.Code == 200 {
		t.Error("implicit 이 통과했다")
	}
}

// 규격이 정한 대로, 여기서 나는 오류는 redirect_uri 로 돌려보낸다 —
// 다만 redirect_uri·client_id 가 멀쩡할 때만 (위 두 시험 참고).
func TestAuthorizeErrorGoesBackToApp(t *testing.T) {
	i, _ := newTestIDP(t)
	w := get(t, i, authzURL(url.Values{"scope": {"profile"}}))
	if w.Code != http.StatusFound {
		t.Fatalf("상태 = %d · %s", w.Code, w.Body.String())
	}
	loc, _ := url.Parse(w.Header().Get("Location"))
	if loc.Query().Get("error") == "" {
		t.Errorf("error 가 없다: %s", loc)
	}
	if loc.Query().Get("state") != "st-123" {
		t.Errorf("state 를 안 돌려줬다: %s", loc)
	}
}
