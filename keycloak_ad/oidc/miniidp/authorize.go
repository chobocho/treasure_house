// authorize.go — 로그인 화면과 인가 코드 발급.
//
// 사용자가 브라우저로 오는 유일한 자리다. 여기서 비밀번호를 받고,
// 성공하면 **인가 코드**를 주소에 실어 앱으로 돌려보낸다.
//
// 앱은 비밀번호를 보지 못한다 — 그게 이 흐름의 전부다.
package miniidp

import (
	"fmt"
	"html"
	"net/http"
	"net/url"
	"strings"

	"treasure/keycloak_ad/oidc/pkce"
)

// authzParams 는 앱이 보낸 요청을 읽어 담은 것.
type authzParams struct {
	responseType string
	clientID     string
	redirectURI  string
	scope        string
	state        string
	nonce        string
	challenge    string
	method       string
}

func readParams(v url.Values) authzParams {
	return authzParams{
		responseType: v.Get("response_type"),
		clientID:     v.Get("client_id"),
		redirectURI:  v.Get("redirect_uri"),
		scope:        v.Get("scope"),
		state:        v.Get("state"),
		nonce:        v.Get("nonce"),
		challenge:    v.Get("code_challenge"),
		method:       v.Get("code_challenge_method"),
	}
}

func hasScope(scope, want string) bool {
	for _, s := range strings.Fields(scope) {
		if s == want {
			return true
		}
	}
	return false
}

// handleAuthorize 는 GET 이면 로그인 화면을, POST 면 그 폼의 처리다.
func (i *IDP) handleAuthorize(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodPost {
		i.authorizeSubmit(w, r)
		return
	}
	p := readParams(r.URL.Query())
	if !i.checkAuthzRequest(w, r, p) {
		return
	}
	i.loginForm(w, p, "")
}

// checkAuthzRequest 는 로그인 화면을 보여 주기 전에 걸러야 할 것들이다.
//
// 순서에 뜻이 있다. **client_id 와 redirect_uri 가 멀쩡할 때만** 오류를
// 그 주소로 돌려보낸다. 아니면 우리 화면에서 끝낸다 — 모르는 주소로
// 오류를 보내 주면 그것 자체가 정보를 흘리는 통로가 된다
// (RFC 6749 §4.1.2.1 이 그렇게 하라고 적었다).
func (i *IDP) checkAuthzRequest(w http.ResponseWriter, r *http.Request,
	p authzParams) bool {
	if p.clientID != i.cfg.ClientID {
		http.Error(w, "모르는 client_id 입니다", http.StatusBadRequest)
		return false
	}
	if !i.knownRedirect(p.redirectURI) {
		// 여기서 그 주소로 보내면 안 된다. 등록되지 않은 주소니까.
		http.Error(w, "등록되지 않은 redirect_uri 입니다",
			http.StatusBadRequest)
		return false
	}

	// 여기서부터는 앱으로 돌려보내도 된다.
	if p.responseType != "code" {
		i.backToApp(w, r, p.redirectURI, p.state,
			"unsupported_response_type",
			"이 서버는 인가 코드 흐름(code)만 합니다")
		return false
	}
	if !hasScope(p.scope, "openid") {
		i.backToApp(w, r, p.redirectURI, p.state, "invalid_scope",
			"scope 에 openid 가 있어야 ID 토큰을 발급합니다")
		return false
	}
	if p.challenge == "" {
		i.backToApp(w, r, p.redirectURI, p.state, "invalid_request",
			"code_challenge 가 필요합니다 (PKCE 필수)")
		return false
	}
	if p.method != "" && p.method != pkce.Method {
		i.backToApp(w, r, p.redirectURI, p.state, "invalid_request",
			"code_challenge_method 는 S256 만 됩니다")
		return false
	}
	return true
}

// loginForm 은 이 서버가 사용자에게 보여 주는 유일한 화면이다.
//
// 앱이 아니라 **여기서** 비밀번호를 받는 것이 요점이다. 사용자는
// 주소창의 도메인을 보고 "여기가 학교 로그인 화면" 임을 확인할 수 있다.
// 앱이 흉내 낸 화면이라면 그 확인이 불가능하다.
func (i *IDP) loginForm(w http.ResponseWriter, p authzParams,
	msg string) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	warn := ""
	if msg != "" {
		warn = "<p style=\"color:#b00\">" +
			html.EscapeString(msg) + "</p>"
	}
	hidden := func(name, v string) string {
		return fmt.Sprintf(
			"<input type=\"hidden\" name=%q value=%q>\n", name,
			html.EscapeString(v))
	}
	fmt.Fprintf(w, `<!doctype html><meta charset="utf-8">
<title>campus 로그인</title>
<h1>campus 계정으로 로그인</h1>
<p>학식 예약이 당신을 확인하려고 합니다.</p>
%s<form method="post">
%s%s%s%s%s%s<label>아이디 <input name="user" autofocus></label>
<label>비밀번호 <input name="pass" type="password"></label>
<button>로그인</button>
</form>
`, warn,
		hidden("client_id", p.clientID),
		hidden("redirect_uri", p.redirectURI),
		hidden("scope", p.scope),
		hidden("state", p.state),
		hidden("nonce", p.nonce),
		hidden("code_challenge", p.challenge))
}

// authorizeSubmit 은 폼이 돌아온 자리다.
func (i *IDP) authorizeSubmit(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "폼을 못 읽었습니다", http.StatusBadRequest)
		return
	}
	p := readParams(r.PostForm)
	if p.clientID != i.cfg.ClientID || !i.knownRedirect(p.redirectURI) {
		http.Error(w, "요청이 잘못됐습니다", http.StatusBadRequest)
		return
	}
	if p.challenge == "" {
		http.Error(w, "code_challenge 가 없습니다",
			http.StatusBadRequest)
		return
	}

	user, err := i.dir.Authenticate(r.PostFormValue("user"),
		r.PostFormValue("pass"))
	if err != nil {
		// 실패는 **앱으로 돌려보내지 않는다**. 사용자가 다시 칠 수 있게
		// 여기 머문다. 어느 쪽이 틀렸는지는 말하지 않는다(1부 5장).
		i.loginForm(w, p,
			"아이디나 비밀번호가 틀렸습니다. 다시 시도하세요.")
		return
	}

	code := i.newID()
	i.mu.Lock()
	i.codes[code] = authCode{
		user: user, clientID: p.clientID, redirectURI: p.redirectURI,
		nonce: p.nonce, challenge: p.challenge,
		dies: i.now().Add(i.cfg.CodeTTL),
	}
	// 브라우저↔IdP 세션(0부의 A). 이것이 살아 있으면 다음 앱은
	// 비밀번호를 다시 묻지 않는다 — 그게 SSO 다.
	sid := i.newID()
	i.sessions[sid] = user
	i.mu.Unlock()

	http.SetCookie(w, &http.Cookie{
		Name: "MINIIDP_SESSION", Value: sid, Path: "/",
		HttpOnly: true, SameSite: http.SameSiteLaxMode,
	})

	u, _ := url.Parse(p.redirectURI)
	q := u.Query()
	q.Set("code", code)
	if p.state != "" {
		q.Set("state", p.state)
	}
	u.RawQuery = q.Encode()
	// 여기는 302 다. 1부 4장에서 "POST 뒤에는 303" 이라고 배웠는데
	// 왜 302 인가 — OAuth 규격의 예시(RFC 6749 §4.1.2)도, 진짜
	// Keycloak 도 302 를 쓰기 때문이다. 브라우저가 302 도 GET 으로
	// 따라가 주므로 결과가 같고, 그 관행이 굳었다. 5부에서 Keycloak 의
	// 응답을 직접 뜯어보면 여기와 똑같은 302 가 나온다.
	http.Redirect(w, r, u.String(), http.StatusFound)
}
