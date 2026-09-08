package main

import (
	"crypto/rand"
	"crypto/rsa"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/cookiejar"
	"net/http/httptest"
	"net/url"
	"regexp"
	"strings"
	"sync"
	"testing"

	"treasure/keycloak_ad/oidc/jwt"
	"treasure/keycloak_ad/oidc/miniidp"
)

// 여기서 시험하는 것은 앱 혼자가 아니라 **앱과 IdP 가 주고받는 전부**다.
// 진짜 miniidp 를 띄워 놓고 브라우저처럼 따라간다. 그래서 이 시험이
// 깨지면 둘 중 어느 쪽이든 규격에서 벗어난 것이다.

type fakeDir struct{}

func (fakeDir) Authenticate(user, pass string) (miniidp.User, error) {
	if pass != "Passw0rd!-demo" {
		return miniidp.User{}, errors.New("틀렸다 (data 52e)")
	}
	switch user {
	case "minji":
		return miniidp.User{
			DN:       "CN=Kim Minji,OU=Students,DC=ad,DC=campus,DC=example",
			Username: "minji", Email: "minji@campus.example",
			Name:   "Kim Minji",
			Groups: []string{"lunch-users", "campus-all"},
		}, nil
	case "yuna.han":
		return miniidp.User{
			DN:       "CN=Han Yuna,OU=Staff,DC=ad,DC=campus,DC=example",
			Username: "yuna.han", Email: "yuna.han@campus.example",
			Name:   "Han Yuna",
			Groups: []string{"lunch-users", "lunch-admins"},
		}, nil
	}
	return miniidp.User{}, errors.New("없는 사람 (data 52e)")
}

// 열쇠 만들기가 느려서 한 번만 만들어 돌려 쓴다.
var (
	keyOnce sync.Once
	testKey *rsa.PrivateKey
)

func signingKey(t *testing.T) *rsa.PrivateKey {
	t.Helper()
	keyOnce.Do(func() {
		k, err := rsa.GenerateKey(rand.Reader, 2048)
		if err != nil {
			panic(err)
		}
		testKey = k
	})
	return testKey
}

// lateHandler 는 "주소를 먼저 알아야 앱을 만들 수 있는" 닭과 달걀을 푼다.
//
// IdP 는 앱의 콜백 주소를 미리 등록해야 하고, 앱은 IdP 의 안내문을 읽어야
// 태어난다. 그래서 앱 자리를 먼저 열어 주소를 얻고 나중에 채운다.
type lateHandler struct{ h http.Handler }

func (l *lateHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	l.h.ServeHTTP(w, r)
}

type pair struct {
	app *httptest.Server
	idp *httptest.Server
}

func startPair(t *testing.T) pair { return startPairWith(t, nil) }

// startPairWith 는 IdP 앞에 훼방꾼을 한 겹 끼울 수 있게 한다.
// "앱이 정말로 확인하고 있는가" 를 보려면 틀린 답을 줘 봐야 한다.
func startPairWith(t *testing.T,
	wrap func(http.Handler) http.Handler) pair {
	t.Helper()
	late := &lateHandler{}
	appSrv := httptest.NewServer(late)
	t.Cleanup(appSrv.Close)

	idpSrv := httptest.NewUnstartedServer(nil)
	issuer := "http://" + idpSrv.Listener.Addr().String() + "/realms/campus"
	idpSrv.Config.Handler = miniidp.NewIDP(miniidp.Config{
		Issuer: issuer, Realm: "campus",
		ClientID: "lunch-web", ClientSecret: "lunch-secret-demo",
		RedirectURIs:   []string{appSrv.URL + "/callback"},
		PostLogoutURIs: []string{appSrv.URL + "/"},
		Key:            signingKey(t), Kid: "demo-1",
	}, fakeDir{}).Handler()
	if wrap != nil {
		idpSrv.Config.Handler = wrap(idpSrv.Config.Handler)
	}
	idpSrv.Start()
	t.Cleanup(idpSrv.Close)

	app, err := NewApp(AppConfig{
		SelfURL: appSrv.URL, IssuerURL: issuer,
		ClientID: "lunch-web", ClientSecret: "lunch-secret-demo",
		AdminGroup: "lunch-admins",
	}, nil)
	if err != nil {
		t.Fatalf("앱 준비 실패: %v", err)
	}
	late.h = app.Handler()
	return pair{app: appSrv, idp: idpSrv}
}

func browser(t *testing.T) *http.Client {
	t.Helper()
	jar, err := cookiejar.New(nil)
	if err != nil {
		t.Fatal(err)
	}
	return &http.Client{Jar: jar}
}

var hiddenRE = regexp.MustCompile(
	`<input type="hidden" name="([^"]*)" value="([^"]*)">`)

func body(t *testing.T, res *http.Response) string {
	t.Helper()
	defer res.Body.Close()
	var sb strings.Builder
	buf := make([]byte, 4096)
	for {
		n, err := res.Body.Read(buf)
		sb.Write(buf[:n])
		if err != nil {
			break
		}
	}
	return sb.String()
}

// signIn 은 브라우저가 하는 일을 그대로 한다.
// /login → IdP 로그인 화면 → 폼 제출 → 콜백 → /me.
func signIn(t *testing.T, c *http.Client, p pair, user string) *http.Response {
	t.Helper()
	res, err := c.Get(p.app.URL + "/login")
	if err != nil {
		t.Fatal(err)
	}
	form := body(t, res)
	if res.StatusCode != 200 {
		t.Fatalf("로그인 화면 상태 = %d", res.StatusCode)
	}
	if !strings.HasPrefix(res.Request.URL.String(), p.idp.URL) {
		t.Fatalf("로그인 화면이 IdP 가 아니다: %s", res.Request.URL)
	}
	v := url.Values{}
	for _, m := range hiddenRE.FindAllStringSubmatch(form, -1) {
		v.Set(m[1], m[2])
	}
	if v.Get("state") == "" || v.Get("code_challenge") == "" {
		t.Fatalf("숨은 칸이 모자라다: %v", v)
	}
	v.Set("user", user)
	v.Set("pass", "Passw0rd!-demo")
	out, err := c.PostForm(res.Request.URL.String(), v)
	if err != nil {
		t.Fatal(err)
	}
	return out
}

func TestLoginEndToEnd(t *testing.T) {
	p := startPair(t)
	c := browser(t)
	res := signIn(t, c, p, "minji")
	if res.StatusCode != 200 {
		t.Fatalf("상태 = %d", res.StatusCode)
	}
	if got := res.Request.URL.Path; got != "/me" {
		t.Fatalf("끝난 자리 = %s (원하는 곳 /me)", got)
	}
	page := body(t, res)
	for _, want := range []string{"Kim Minji", "minji", "lunch-users"} {
		if !strings.Contains(page, want) {
			t.Errorf("/me 에 %q 가 없다", want)
		}
	}

	// 앱은 **자기 쿠키**를 심는다. 토큰이 아니라 세션이다(1부 6장).
	u, _ := url.Parse(p.app.URL)
	var found bool
	for _, ck := range c.Jar.Cookies(u) {
		if ck.Name == cookieName {
			found = true
		}
	}
	if !found {
		t.Error("앱 세션 쿠키가 없다")
	}
}

// 로그인은 됐는데 못 들어오는 화면 — 401 이 아니라 403 이다.
func TestAdminNeedsGroup(t *testing.T) {
	p := startPair(t)

	c := browser(t)
	body(t, signIn(t, c, p, "minji"))
	res, err := c.Get(p.app.URL + "/admin")
	if err != nil {
		t.Fatal(err)
	}
	if res.StatusCode != http.StatusForbidden {
		t.Fatalf("minji 의 /admin 상태 = %d (원하는 값 403)", res.StatusCode)
	}
	body(t, res)

	c2 := browser(t)
	body(t, signIn(t, c2, p, "yuna.han"))
	res2, err := c2.Get(p.app.URL + "/admin")
	if err != nil {
		t.Fatal(err)
	}
	if res2.StatusCode != 200 {
		t.Fatalf("yuna.han 의 /admin 상태 = %d", res2.StatusCode)
	}
	body(t, res2)
}

func TestMeRedirectsWhenLoggedOut(t *testing.T) {
	p := startPair(t)
	c := &http.Client{CheckRedirect: func(*http.Request, []*http.Request) error {
		return http.ErrUseLastResponse
	}}
	res, err := c.Get(p.app.URL + "/me")
	if err != nil {
		t.Fatal(err)
	}
	body(t, res)
	if res.StatusCode != http.StatusFound {
		t.Fatalf("상태 = %d (원하는 값 302)", res.StatusCode)
	}
	if got := res.Header.Get("Location"); got != "/login" {
		t.Fatalf("Location = %q", got)
	}
}

// 콜백은 한 번만 먹혀야 한다. 같은 주소를 다시 열면 거절이다.
//
// state 를 찾자마자 지우기 때문이다(handleCallback). 지우지 않으면
// 가로챈 콜백 주소를 남이 다시 열어 볼 수 있다.
func TestCallbackIsSingleUse(t *testing.T) {
	p := startPair(t)
	c := browser(t)
	var callback string
	c.CheckRedirect = func(r *http.Request, via []*http.Request) error {
		if strings.HasPrefix(r.URL.Path, "/callback") {
			callback = r.URL.String()
		}
		return nil
	}
	body(t, signIn(t, c, p, "minji"))
	if callback == "" {
		t.Fatal("콜백 주소를 못 잡았다")
	}

	again, err := c.Get(callback)
	if err != nil {
		t.Fatal(err)
	}
	msg := body(t, again)
	if again.StatusCode != http.StatusBadRequest {
		t.Fatalf("두 번째 콜백 상태 = %d (원하는 값 400)", again.StatusCode)
	}
	if !strings.Contains(msg, "state") {
		t.Errorf("state 이야기가 없다: %q", msg)
	}
}

func TestCallbackRejectsUnknownState(t *testing.T) {
	p := startPair(t)
	res, err := http.Get(p.app.URL + "/callback?code=x&state=남이-준-값")
	if err != nil {
		t.Fatal(err)
	}
	body(t, res)
	if res.StatusCode != http.StatusBadRequest {
		t.Fatalf("상태 = %d (원하는 값 400)", res.StatusCode)
	}
}

func TestCallbackShowsIDPError(t *testing.T) {
	p := startPair(t)
	res, err := http.Get(p.app.URL +
		"/callback?error=access_denied&error_description=거절")
	if err != nil {
		t.Fatal(err)
	}
	msg := body(t, res)
	if res.StatusCode != http.StatusUnauthorized {
		t.Fatalf("상태 = %d (원하는 값 401)", res.StatusCode)
	}
	if !strings.Contains(msg, "access_denied") {
		t.Errorf("오류 이름이 없다: %q", msg)
	}
}

// 안내문의 issuer 가 부른 주소와 다르면 붙지 않는다.
func TestDiscoveryIssuerMustMatch(t *testing.T) {
	var srv *httptest.Server
	srv = httptest.NewServer(http.HandlerFunc(
		func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.Write([]byte(`{"issuer":"https://남의-서버.example"}`))
		}))
	defer srv.Close()
	_, err := NewApp(AppConfig{SelfURL: "http://localhost:1",
		IssuerURL: srv.URL, ClientID: "lunch-web"}, nil)
	if err == nil {
		t.Fatal("남의 안내문을 받아들였다")
	}
	if !strings.Contains(err.Error(), "issuer") {
		t.Fatalf("이유가 issuer 가 아니다: %v", err)
	}
}

// ── 앱이 정말 확인하는지 — 틀린 답을 줘서 본다 ────────────────────────

// IdP 가 앱이 보낸 것과 다른 nonce 로 토큰을 발급하면 앱은 받으면 안 된다.
//
// nonce 는 "이 토큰이 **내가 방금 시작한** 로그인의 것인가" 를 묻는
// 장치다. 옛 토큰을 다시 밀어 넣는 재생 공격이 여기서 막힌다.
func TestRejectsWrongNonce(t *testing.T) {
	p := startPairWith(t, func(h http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter,
			r *http.Request) {
			if r.Method == http.MethodGet &&
				r.URL.Query().Get("nonce") != "" {
				q := r.URL.Query()
				q.Set("nonce", "남이-바꿔치기한-값")
				r.URL.RawQuery = q.Encode()
			}
			h.ServeHTTP(w, r)
		})
	})
	res := signIn(t, browser(t), p, "minji")
	msg := body(t, res)
	if res.StatusCode != http.StatusUnauthorized {
		t.Fatalf("상태 = %d (원하는 값 401)", res.StatusCode)
	}
	if !strings.Contains(msg, "nonce") {
		t.Errorf("이유가 nonce 가 아니다: %q", msg)
	}
}

// 공개키가 다르면 서명이 맞지 않는다 — 토큰의 내용이 아무리 그럴듯해도.
func TestRejectsWrongSigningKey(t *testing.T) {
	other, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		t.Fatal(err)
	}
	p := startPairWith(t, func(h http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter,
			r *http.Request) {
			if strings.HasSuffix(r.URL.Path, "/certs") {
				// 남의 공개키를 내건다. 앱은 이것으로 확인하려다 막힌다.
				writeKeySet(w, other)
				return
			}
			h.ServeHTTP(w, r)
		})
	})
	res := signIn(t, browser(t), p, "minji")
	msg := body(t, res)
	if res.StatusCode != http.StatusUnauthorized {
		t.Fatalf("상태 = %d (원하는 값 401)", res.StatusCode)
	}
	if !strings.Contains(msg, "서명") {
		t.Errorf("이유가 서명이 아니다: %q", msg)
	}
}

func writeKeySet(w http.ResponseWriter, k *rsa.PrivateKey) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(jwt.KeySet{
		Keys: []jwt.JWK{jwt.PublicJWK("demo-1", &k.PublicKey)}})
}

// 로그아웃은 세 세션 중 둘을 끊는다 — 앱의 것과 IdP 의 것.
// 그리고 사용자는 첫 화면으로 돌아와야 한다. 콜백으로 돌려보내면
// 코드도 state 도 없어서 400 이 뜬다 — 실제로 그렇게 만들어 봤다가 고쳤다.
func TestLogoutReturnsHome(t *testing.T) {
	p := startPair(t)
	c := browser(t)
	body(t, signIn(t, c, p, "minji"))

	res, err := c.PostForm(p.app.URL+"/logout", nil)
	if err != nil {
		t.Fatal(err)
	}
	page := body(t, res)
	if res.StatusCode != 200 {
		t.Fatalf("상태 = %d · %s", res.StatusCode, page)
	}
	if got := res.Request.URL.Path; got != "/" {
		t.Fatalf("끝난 자리 = %s (원하는 곳 /)", got)
	}
	if !strings.Contains(page, "로그인") {
		t.Errorf("로그아웃했는데 로그인 화면이 아니다\n%s", page)
	}

	// 앱 세션이 끊겼으므로 /me 는 다시 로그인으로 보낸다.
	noFollow := &http.Client{Jar: c.Jar,
		CheckRedirect: func(*http.Request, []*http.Request) error {
			return http.ErrUseLastResponse
		}}
	after, err := noFollow.Get(p.app.URL + "/me")
	if err != nil {
		t.Fatal(err)
	}
	body(t, after)
	if after.StatusCode != http.StatusFound {
		t.Errorf("로그아웃 뒤 /me 상태 = %d", after.StatusCode)
	}
}

// ── 클라이언트 비밀은 명령줄이 아니라 환경 변수로 받는다 ──────────────
//
// 2부에서 이 앱을 쿠버네티스에 올릴 때, 비밀은 Secret 에 담아
// 환경 변수로 넣어 준다. 명령줄에 적으면 `ps` 에도 뜨고
// `kubectl describe pod` 에도 그대로 뜬다 — 아무나 볼 수 있다.

func TestSecretPrefersEnv(t *testing.T) {
	got, err := pickSecret("깃발로-준-값", "환경변수로-준-값")
	if err != nil {
		t.Fatal(err)
	}
	if got != "환경변수로-준-값" {
		t.Errorf("고른 값 = %q — 환경 변수가 이겨야 한다", got)
	}
}

func TestSecretFallsBackToFlag(t *testing.T) {
	got, err := pickSecret("깃발로-준-값", "")
	if err != nil {
		t.Fatal(err)
	}
	if got != "깃발로-준-값" {
		t.Errorf("고른 값 = %q", got)
	}
}

// 둘 다 비어 있으면 뜨지 않는다. 조용히 빈 비밀로 돌면
// 토큰 교환이 401 로 실패하고, 그 이유를 찾는 데 한나절이 걸린다.
func TestSecretRefusesEmpty(t *testing.T) {
	if _, err := pickSecret("", ""); err == nil {
		t.Fatal("비밀 없이 뜨려 했다")
	}
}
