// miniapp — 학식 예약 앱의 로그인 부분.
//
// OIDC 에서 앱 쪽을 **RP**(Relying Party, 믿고 맡기는 쪽)라고 부른다.
// 이름 그대로다 — 이 앱은 비밀번호를 보지 않고, 누가 누구인지를
// IdP 에게 맡긴다.
//
// 앱이 하는 일은 다섯 줄로 끝난다.
//
//  1. 로그인 단추 → state·nonce·PKCE 를 만들고 IdP 로 보낸다
//  2. 돌아온 코드 → state 를 확인하고, 코드+verifier 를 토큰으로 바꾼다
//  3. ID 토큰의 서명·발급자·대상·nonce 를 확인한다
//  4. 확인됐으면 **앱 자신의 세션 쿠키**를 심는다 (0부의 B)
//  5. 그 뒤로는 1부에서 배운 그 세션 그대로다
//
// 8부에서 이 코드가 그대로 학식 예약 앱이 된다. issuer 만 진짜
// Keycloak 으로 바꾸면 된다 — 그게 표준을 쓰는 이유다.
package main

import (
	"encoding/json"
	"fmt"
	"html"
	"io"
	mathrand "math/rand"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"

	"treasure/keycloak_ad/oidc/jwt"
	"treasure/keycloak_ad/oidc/pkce"
)

type AppConfig struct {
	SelfURL      string // 이 앱의 바깥 주소
	IssuerURL    string // IdP 의 issuer
	ClientID     string
	ClientSecret string
	AdminGroup   string // 이 그룹만 관리자 화면을 본다
}

// discovery 는 IdP 의 안내문에서 읽어 온 주소들이다.
// 손으로 적지 않는 이유는 4부 2장에 있다 — IdP 가 바뀌어도 앱은
// 그대로다.
type discovery struct {
	Issuer   string `json:"issuer"`
	AuthURL  string `json:"authorization_endpoint"`
	TokenURL string `json:"token_endpoint"`
	JWKSURL  string `json:"jwks_uri"`
	UserURL  string `json:"userinfo_endpoint"`
	EndURL   string `json:"end_session_endpoint"`
}

// pending 은 "지금 나가 있는 로그인 한 건" 이다.
//
// state 와 nonce 와 verifier 를 **앱이 기억하고 있어야** 돌아왔을 때
// 확인할 수 있다. 기억하지 않으면 세 장치가 전부 무용지물이 된다.
type pending struct {
	nonce    string
	verifier string
	dies     time.Time
}

type session struct {
	claims  jwt.Claims
	idToken string // 로그아웃할 때 IdP 에 보여 줄 것
	dies    time.Time
}

type App struct {
	cfg  AppConfig
	disc discovery
	keys *jwt.KeySet
	mux  *http.ServeMux
	http *http.Client

	mu       sync.Mutex
	pend     map[string]pending
	sessions map[string]session
	now      func() time.Time
	newID    func() string
}

// FixForCapture 는 시계와 난수를 못 박는다. **캡처 전용이다** —
// 왜 필요하고 왜 위험한지는 miniidp 쪽 같은 이름의 함수에 적어 두었다.
func (a *App) FixForCapture(at time.Time, seed int64) {
	a.now = func() time.Time { return at }
	r := mathrand.New(mathrand.NewSource(seed))
	a.newID = func() string {
		b := make([]byte, 32)
		// math/rand 의 Read 는 실패하지 않는다
		r.Read(b) //nolint:errcheck
		return jwt.B64URLEncode(b)
	}
}

const cookieName = "lunch_app_session"

// NewApp 은 IdP 의 안내문과 공개키를 받아 온 뒤 준비를 마친다.
func NewApp(cfg AppConfig, hc *http.Client) (*App, error) {
	if hc == nil {
		hc = &http.Client{Timeout: 10 * time.Second}
	}
	a := &App{
		cfg: cfg, http: hc,
		pend: map[string]pending{}, sessions: map[string]session{},
		now: time.Now, newID: randomID,
	}
	if err := a.fetchDiscovery(); err != nil {
		return nil, err
	}
	if err := a.fetchKeys(); err != nil {
		return nil, err
	}
	a.routes()
	return a, nil
}

func (a *App) Handler() http.Handler { return a.mux }

func (a *App) routes() {
	a.mux = http.NewServeMux()
	a.mux.HandleFunc("/login", a.handleLogin)
	a.mux.HandleFunc("/callback", a.handleCallback)
	a.mux.HandleFunc("/me", a.handleMe)
	a.mux.HandleFunc("/admin", a.handleAdmin)
	a.mux.HandleFunc("/logout", a.handleLogout)
	a.mux.HandleFunc("/", a.handleHome)
}

func (a *App) getJSON(url string, into any) error {
	res, err := a.http.Get(url)
	if err != nil {
		return err
	}
	defer res.Body.Close()
	if res.StatusCode != http.StatusOK {
		return fmt.Errorf("%s → %d", url, res.StatusCode)
	}
	return json.NewDecoder(res.Body).Decode(into)
}

func (a *App) fetchDiscovery() error {
	u := strings.TrimSuffix(a.cfg.IssuerURL, "/") +
		"/.well-known/openid-configuration"
	if err := a.getJSON(u, &a.disc); err != nil {
		return fmt.Errorf("안내문: %w", err)
	}
	// 안내문의 issuer 가 우리가 부른 주소와 같아야 한다 — 아니면
	// 남의 안내문을 읽은 것이다 (OIDC Discovery §4.3).
	if a.disc.Issuer != strings.TrimSuffix(a.cfg.IssuerURL, "/") {
		return fmt.Errorf("안내문의 issuer 가 다르다: %q",
			a.disc.Issuer)
	}
	return nil
}

func (a *App) fetchKeys() error {
	var ks jwt.KeySet
	if err := a.getJSON(a.disc.JWKSURL, &ks); err != nil {
		return fmt.Errorf("JWKS: %w", err)
	}
	a.keys = &ks
	return nil
}

func randomID() string {
	v, err := pkce.NewVerifier()
	if err != nil {
		panic(err)
	}
	return v
}

// ── 1. 로그인 시작 ───────────────────────────────────────────────────

func (a *App) handleLogin(w http.ResponseWriter, r *http.Request) {
	state := a.newID()
	nonce := a.newID()
	verifier, err := pkce.NewVerifier()
	if err != nil {
		http.Error(w, "준비 실패", http.StatusInternalServerError)
		return
	}
	a.mu.Lock()
	a.pend[state] = pending{nonce: nonce, verifier: verifier,
		dies: a.now().Add(10 * time.Minute)}
	a.mu.Unlock()

	q := url.Values{
		"response_type":         {"code"},
		"client_id":             {a.cfg.ClientID},
		"redirect_uri":          {a.cfg.SelfURL + "/callback"},
		"scope":                 {"openid profile email"},
		"state":                 {state},
		"nonce":                 {nonce},
		"code_challenge":        {pkce.Challenge(verifier)},
		"code_challenge_method": {pkce.Method},
	}
	http.Redirect(w, r, a.disc.AuthURL+"?"+q.Encode(), http.StatusFound)
}

// ── 2·3·4. 돌아온 자리 ───────────────────────────────────────────────

func (a *App) handleCallback(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	if e := q.Get("error"); e != "" {
		http.Error(w, "로그인 실패: "+e+" — "+
			q.Get("error_description"), http.StatusUnauthorized)
		return
	}

	// state 확인. **이것을 빼면** 남이 자기 코드를 우리 콜백에 던져
	// 사용자를 남의 계정으로 로그인시킬 수 있다 (로그인 CSRF).
	state := q.Get("state")
	a.mu.Lock()
	p, ok := a.pend[state]
	delete(a.pend, state) // 한 번만 쓴다
	a.mu.Unlock()
	if !ok || !a.now().Before(p.dies) {
		http.Error(w, "내가 시작한 로그인이 아닙니다 (state 불일치)",
			http.StatusBadRequest)
		return
	}

	tok, err := a.exchange(q.Get("code"), p.verifier)
	if err != nil {
		http.Error(w, "토큰 교환 실패: "+err.Error(),
			http.StatusBadGateway)
		return
	}

	// ID 토큰 확인 — 서명, 그리고 서명만으로는 부족한 것들.
	_, claims, err := jwt.Verify(tok.IDToken, a.keys)
	if err != nil {
		http.Error(w, "ID 토큰 서명이 맞지 않습니다: "+err.Error(),
			http.StatusUnauthorized)
		return
	}
	if err := claims.Validate(jwt.Options{
		Issuer: a.disc.Issuer, Audience: a.cfg.ClientID,
		Nonce: p.nonce, Now: a.now(), Leeway: 30 * time.Second,
	}); err != nil {
		http.Error(w, "ID 토큰 내용이 맞지 않습니다: "+err.Error(),
			http.StatusUnauthorized)
		return
	}

	// 여기서부터는 1부 6장의 그 세션이다. 앱은 자기 쿠키를 심고,
	// 그 뒤로 토큰을 다시 꺼내 볼 일이 없다.
	sid := a.newID()
	a.mu.Lock()
	a.sessions[sid] = session{claims: claims, idToken: tok.IDToken,
		dies: a.now().Add(30 * time.Minute)}
	a.mu.Unlock()
	http.SetCookie(w, &http.Cookie{
		Name: cookieName, Value: sid, Path: "/",
		HttpOnly: true, SameSite: http.SameSiteLaxMode,
	})
	http.Redirect(w, r, "/me", http.StatusFound)
}

type tokenResponse struct {
	AccessToken  string `json:"access_token"`
	IDToken      string `json:"id_token"`
	RefreshToken string `json:"refresh_token"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int    `json:"expires_in"`
}

// exchange 는 브라우저를 거치지 않고 IdP 와 **직접** 이야기한다.
// 그래서 토큰이 주소에 실리지 않고, 기록에도 안 남는다.
func (a *App) exchange(code, verifier string) (tokenResponse, error) {
	form := url.Values{
		"grant_type":    {"authorization_code"},
		"code":          {code},
		"redirect_uri":  {a.cfg.SelfURL + "/callback"},
		"client_id":     {a.cfg.ClientID},
		"client_secret": {a.cfg.ClientSecret},
		"code_verifier": {verifier},
	}
	res, err := a.http.PostForm(a.disc.TokenURL, form)
	if err != nil {
		return tokenResponse{}, err
	}
	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)
	if res.StatusCode != http.StatusOK {
		return tokenResponse{}, fmt.Errorf("%d %s", res.StatusCode,
			strings.TrimSpace(string(body)))
	}
	var t tokenResponse
	if err := json.Unmarshal(body, &t); err != nil {
		return tokenResponse{}, err
	}
	if t.IDToken == "" {
		return tokenResponse{}, fmt.Errorf("id_token 이 없습니다")
	}
	return t, nil
}

// ── 5. 그 뒤로는 평범한 세션 ─────────────────────────────────────────

func (a *App) current(r *http.Request) (session, bool) {
	c, err := r.Cookie(cookieName)
	if err != nil {
		return session{}, false
	}
	a.mu.Lock()
	s, ok := a.sessions[c.Value]
	a.mu.Unlock()
	if !ok || !a.now().Before(s.dies) {
		return session{}, false
	}
	return s, true
}

func (a *App) handleHome(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if s, ok := a.current(r); ok {
		fmt.Fprintf(w, `<!doctype html><meta charset="utf-8">
<h1>학식 예약</h1><p>안녕하세요, %s 님.</p>
<p><a href="/me">내 예약</a> · <a href="/admin">메뉴 관리</a></p>
<form method="post" action="/logout"><button>로그아웃</button></form>
`, html.EscapeString(s.claims.Name))
		return
	}
	fmt.Fprint(w, `<!doctype html><meta charset="utf-8">
<h1>학식 예약</h1><p>학교 계정으로 로그인하세요.</p>
<p><a href="/login">campus 계정으로 로그인</a></p>
`)
}

func (a *App) handleMe(w http.ResponseWriter, r *http.Request) {
	s, ok := a.current(r)
	if !ok {
		http.Redirect(w, r, "/login", http.StatusFound)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	fmt.Fprintf(w, `<!doctype html><meta charset="utf-8">
<h1>내 예약</h1>
<p>%s (%s)</p>
<p>그룹: %s</p>
<p>이번 주 예약: 화요일 점심</p>
`, html.EscapeString(s.claims.Name),
		html.EscapeString(s.claims.PreferredUsername),
		html.EscapeString(strings.Join(s.claims.Groups, ", ")))
}

// handleAdmin — 9부의 씨앗. 토큰의 groups 클레임 하나로 갈린다.
//
// 로그인은 됐는데 못 들어오는 화면이다 — 401 이 아니라 **403** 인
// 이유가 여기 있다(1부 3장). 누구인지는 알고, 권한이 없을 뿐이다.
func (a *App) handleAdmin(w http.ResponseWriter, r *http.Request) {
	s, ok := a.current(r)
	if !ok {
		http.Redirect(w, r, "/login", http.StatusFound)
		return
	}
	for _, g := range s.claims.Groups {
		if g == a.cfg.AdminGroup {
			w.Header().Set("Content-Type", "text/html; charset=utf-8")
			fmt.Fprint(w, `<!doctype html><meta charset="utf-8">
<h1>메뉴 관리</h1><p>이번 주 메뉴를 고칠 수 있습니다.</p>`)
			return
		}
	}
	http.Error(w, "관리자만 볼 수 있습니다 ("+
		a.cfg.AdminGroup+" 그룹 필요)", http.StatusForbidden)
}

// handleLogout — 앱의 세션(B)을 끊고, IdP 의 세션(A)도 끊으러 보낸다.
//
// 둘을 다 끊어야 하는 이유는 0부의 세 세션 그림에 있다. 앱만 끊으면
// 로그인 단추를 다시 눌렀을 때 IdP 가 비밀번호를 안 묻고 통과시킨다 —
// "로그아웃했는데 왜 그냥 들어가지나" 의 정체다.
func (a *App) handleLogout(w http.ResponseWriter, r *http.Request) {
	var idToken string
	if c, err := r.Cookie(cookieName); err == nil {
		a.mu.Lock()
		if s, ok := a.sessions[c.Value]; ok {
			idToken = s.idToken
		}
		delete(a.sessions, c.Value)
		a.mu.Unlock()
	}
	http.SetCookie(w, &http.Cookie{
		Name: cookieName, Value: "", Path: "/",
		HttpOnly: true, SameSite: http.SameSiteLaxMode, MaxAge: -1,
	})
	// 첫 화면으로 돌아온다. 콜백으로 돌아오면 코드도 state 도 없어서
	// 앱이 "내가 시작한 로그인이 아니다" 로 거절한다.
	q := url.Values{
		"post_logout_redirect_uri": {a.cfg.SelfURL + "/"},
	}
	if idToken != "" {
		// 누구의 세션을 끊는지 알려 준다. 이게 없으면 IdP 가
		// "정말 로그아웃할까요?" 를 사용자에게 물어야 한다.
		q.Set("id_token_hint", idToken)
	}
	http.Redirect(w, r, a.disc.EndURL+"?"+q.Encode(), http.StatusFound)
}
