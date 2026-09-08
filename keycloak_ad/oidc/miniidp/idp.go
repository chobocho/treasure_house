// miniidp — 400줄짜리 Keycloak.
//
// 4부에서 배운 것을 전부 합치면 이것이 된다. 하는 일은 하나다.
//
//	앱에게는 OIDC 로 답하고, 뒤에서는 AD 에게 LDAP 으로 묻는다.
//
// 그게 Keycloak 이 하는 일의 절반이고, 이 프로그램이 그 절반을 실제로
// 한다. 주소도 Keycloak 과 똑같이 뒀다 —
//
//	/realms/{realm}/.well-known/openid-configuration
//	/realms/{realm}/protocol/openid-connect/auth
//	/realms/{realm}/protocol/openid-connect/token
//	/realms/{realm}/protocol/openid-connect/certs
//	/realms/{realm}/protocol/openid-connect/userinfo
//	/realms/{realm}/protocol/openid-connect/logout
//
// 5부에서 진짜 Keycloak 을 만나면 이 주소들이 그대로 나온다.
//
// ⚠ 이것은 배우기 위한 모형이다. 운영에 쓰면 안 된다 —
// 저장소가 메모리뿐이고, 클라이언트가 하나뿐이고, 감사도 없다.
// 무엇을 안 하는지는 §"안 하는 것" 에 적어 두었다.
package miniidp

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/subtle"
	"encoding/base64"
	"encoding/json"
	mathrand "math/rand"
	"net/http"
	"net/url"
	"sync"
	"time"

	"treasure/keycloak_ad/oidc/jwt"
)

// Config 는 이 서버가 아는 전부다. 진짜 Keycloak 에서는 이 값들이
// realm 설정과 client 설정으로 나뉘어 관리 화면에 흩어져 있다(5부).
type Config struct {
	Issuer       string // 토큰의 iss. 이 서버의 바깥 주소여야 한다
	Realm        string
	ClientID     string
	ClientSecret string
	RedirectURIs []string // 돌아갈 수 있는 주소 목록 — 미리 등록한다

	// 로그아웃한 뒤 돌아갈 수 있는 주소. 비면 RedirectURIs 를 쓴다.
	//
	// 왜 목록이 따로인가: 로그인은 콜백으로 돌아오지만 로그아웃은
	// 대개 **첫 화면**으로 돌아간다. 콜백은 인가 코드를 받는 자리라
	// 빈손으로 열면 앱이 거절한다. Keycloak 의 클라이언트 설정에도
	// "Valid post logout redirect URIs" 가 따로 있다(5·7부).
	PostLogoutURIs []string

	Key *rsa.PrivateKey
	Kid string

	AccessTTL  time.Duration
	IDTTL      time.Duration
	RefreshTTL time.Duration
	CodeTTL    time.Duration
}

func (c *Config) fill() {
	if c.Realm == "" {
		c.Realm = "campus"
	}
	if len(c.PostLogoutURIs) == 0 {
		c.PostLogoutURIs = c.RedirectURIs
	}
	// 기본 수명. 액세스 토큰이 짧은 이유는 4부에서 다룬다 —
	// 한 번 나간 토큰은 취소하기 어려우므로 짧게 두고 자주 갱신한다.
	if c.AccessTTL == 0 {
		c.AccessTTL = 5 * time.Minute
	}
	if c.IDTTL == 0 {
		c.IDTTL = 5 * time.Minute
	}
	if c.RefreshTTL == 0 {
		c.RefreshTTL = 30 * time.Minute
	}
	if c.CodeTTL == 0 {
		// 인가 코드는 아주 짧아야 한다. 앱이 받자마자 바꾸기 때문이다.
		c.CodeTTL = time.Minute
	}
}

// User 는 명부에서 찾아온 사람 하나다.
type User struct {
	DN       string
	Username string
	Email    string
	Name     string
	Groups   []string
}

// Directory 는 "이 사람이 맞는가" 에 답하는 무엇이다.
//
// 이 인터페이스 하나가 Keycloak 의 **User Federation** 이 하는 일이다.
// 진짜 구현은 AD 에 LDAP 으로 묻고(directory.go), 시험은 가짜를 끼운다.
// 여기가 갈라져 있어서 4부를 AD 없이도 읽을 수 있다.
type Directory interface {
	Authenticate(username, password string) (User, error)
}

// authCode 는 발급한 인가 코드 한 장이다.
//
// 코드에 딸려 다니는 값들이 왜 필요한지가 4부의 절반이다.
// challenge 는 PKCE, nonce 는 재생 공격, redirectURI 는 발급 때와 같은
// 주소로만 돌려주기 위한 것이다.
type authCode struct {
	user        User
	clientID    string
	redirectURI string
	nonce       string
	challenge   string
	dies        time.Time
}

type refreshToken struct {
	user     User
	clientID string
	dies     time.Time
}

// IDP 는 서버 하나다. 저장소가 전부 메모리에 있다 —
// 진짜 Keycloak 은 이것들을 데이터베이스(6부)와 Infinispan 에 둔다.
type IDP struct {
	cfg Config
	dir Directory
	mux *http.ServeMux

	mu      sync.Mutex
	codes   map[string]authCode
	refresh map[string]refreshToken
	now     func() time.Time
	newID   func() string
	jwks    jwt.KeySet
	// 브라우저↔IdP 세션(0부의 A). SSO 가 여기서 난다
	sessions map[string]User
}

func NewIDP(cfg Config, dir Directory) *IDP {
	cfg.fill()
	i := &IDP{
		cfg: cfg, dir: dir,
		codes:    map[string]authCode{},
		refresh:  map[string]refreshToken{},
		sessions: map[string]User{}, now: time.Now, newID: randomID,
		jwks: jwt.KeySet{Keys: []jwt.JWK{
			jwt.PublicJWK(cfg.Kid, &cfg.Key.PublicKey)}},
	}
	i.routes()
	return i
}

func (i *IDP) Handler() http.Handler { return i.mux }

func (i *IDP) path(suffix string) string {
	return "/realms/" + i.cfg.Realm +
		"/protocol/openid-connect/" + suffix
}

func (i *IDP) routes() {
	i.mux = http.NewServeMux()
	i.mux.HandleFunc("/realms/"+i.cfg.Realm+
		"/.well-known/openid-configuration", i.handleDiscovery)
	i.mux.HandleFunc(i.path("auth"), i.handleAuthorize)
	i.mux.HandleFunc(i.path("token"), i.handleToken)
	i.mux.HandleFunc(i.path("certs"), i.handleCerts)
	i.mux.HandleFunc(i.path("userinfo"), i.handleUserinfo)
	i.mux.HandleFunc(i.path("logout"), i.handleLogout)
}

// randomID 는 코드·토큰·세션 번호를 만든다. 1부 6장의 그 규칙이다 —
// crypto/rand 로 32바이트, 찍어 맞힐 수 없는 값.
func randomID() string {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		panic(err)
	}
	return base64.RawURLEncoding.EncodeToString(b)
}

// FixForCapture 는 시계와 난수를 못 박는다. **캡처 전용이다.**
//
// 덱의 검은 화면은 두 번 떠서 md5 가 같아야 실린다(tools/record.sh).
// 토큰에는 발급 시각(iat)과 일련번호(jti)가 들어가므로, 시계와 난수를
// 묶어 두지 않으면 같은 명령이 매번 다른 글자를 낸다.
//
// 운영에서 이걸 켜면 그 순간 끝난다 — 인가 코드도 세션 번호도 남이
// 순서대로 찍어 맞힐 수 있다. math/rand 는 암호용이 아니다.
// 이름을 길고 불편하게 지은 이유가 그것이다.
func (i *IDP) FixForCapture(at time.Time, seed int64) {
	i.now = func() time.Time { return at }
	r := mathrand.New(mathrand.NewSource(seed))
	i.newID = func() string {
		b := make([]byte, 32)
		// math/rand 의 Read 는 실패하지 않는다
		r.Read(b) //nolint:errcheck
		return base64.RawURLEncoding.EncodeToString(b)
	}
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	// 캐시하면 안 된다 — 토큰이 프록시에 남는다 (RFC 6749 §5.1).
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("Pragma", "no-cache")
	w.WriteHeader(code)
	enc := json.NewEncoder(w)
	enc.SetIndent("", "  ")
	enc.Encode(v)
}

// oauthError 는 규격이 정한 오류 모양이다 (RFC 6749 §5.2).
// 사람이 읽을 설명은 description 에, 기계가 볼 이름은 error 에.
func oauthError(w http.ResponseWriter, status int, code, desc string) {
	writeJSON(w, status, map[string]string{
		"error": code, "error_description": desc,
	})
}

// handleDiscovery — "내 주소들은 이렇다" 를 스스로 알려 주는 문서.
//
// 앱이 토큰 주소·JWKS 주소를 손으로 적지 않아도 되게 한다. 7부에서
// Keycloak 을 붙일 때도 이 주소 하나만 알려 주면 나머지가 따라온다.
func (i *IDP) handleDiscovery(w http.ResponseWriter, r *http.Request) {
	at := i.cfg.Issuer + "/protocol/openid-connect/"
	grants := []string{"authorization_code", "refresh_token"}
	scopes := []string{"openid", "profile", "email"}
	claims := []string{"sub", "iss", "aud", "exp", "iat", "nonce",
		"preferred_username", "email", "name", "groups"}
	writeJSON(w, http.StatusOK, map[string]any{
		"issuer":                 i.cfg.Issuer,
		"authorization_endpoint": at + "auth",
		"token_endpoint":         at + "token",
		"jwks_uri":               at + "certs",
		"userinfo_endpoint":      at + "userinfo",
		"end_session_endpoint":   at + "logout",

		"response_types_supported":              []string{"code"},
		"grant_types_supported":                 grants,
		"subject_types_supported":               []string{"public"},
		"id_token_signing_alg_values_supported": []string{jwt.AlgRS256},
		"scopes_supported":                      scopes,
		"claims_supported":                      claims,
		"code_challenge_methods_supported":      []string{"S256"},
		"token_endpoint_auth_methods_supported": []string{
			"client_secret_post"},
	})
}

// handleCerts — 공개키를 내건다. 앱은 이것으로 서명을 확인한다.
// **개인키는 절대 나가지 않는다** — JWK 에는 n·e 만 담긴다.
func (i *IDP) handleCerts(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, i.jwks)
}

// knownRedirect 는 등록된 주소인지 **글자 그대로** 견준다.
//
// "앞부분이 같으면 통과" 같은 느슨한 비교를 하면 안 된다. 공격자가
// 등록된 주소로 시작하는 자기 주소를 만들어 토큰을 가로챌 수 있다.
func (i *IDP) knownRedirect(uri string) bool {
	return listed(i.cfg.RedirectURIs, uri)
}

// knownPostLogout 은 로그아웃 뒤 돌아갈 주소를 견준다. 목록이 다르다는
// 것 말고는 위와 똑같다 — 느슨하게 비교하면 안 되는 이유도 똑같다.
func (i *IDP) knownPostLogout(uri string) bool {
	return listed(i.cfg.PostLogoutURIs, uri)
}

func listed(list []string, uri string) bool {
	for _, u := range list {
		if subtle.ConstantTimeCompare([]byte(u), []byte(uri)) == 1 {
			return true
		}
	}
	return false
}

// backToApp 은 오류를 앱으로 돌려보낸다 (RFC 6749 §4.1.2.1).
//
// state 를 함께 돌려주는 것이 중요하다 — 앱이 "내가 시작한 그
// 로그인" 임을 알아볼 수 있어야 하기 때문이다.
func (i *IDP) backToApp(w http.ResponseWriter, r *http.Request,
	redirectURI, state, code, desc string) {
	u, err := url.Parse(redirectURI)
	if err != nil {
		http.Error(w, desc, http.StatusBadRequest)
		return
	}
	q := u.Query()
	q.Set("error", code)
	q.Set("error_description", desc)
	if state != "" {
		q.Set("state", state)
	}
	u.RawQuery = q.Encode()
	http.Redirect(w, r, u.String(), http.StatusFound)
}
