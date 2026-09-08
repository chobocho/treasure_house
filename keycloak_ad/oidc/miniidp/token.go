// token.go — 코드를 토큰으로 바꾸고, 토큰으로 사람을 알려 주고, 끝낸다.
//
// /authorize 가 브라우저와 이야기하는 자리라면, 여기는 **앱과 직접**
// 이야기하는 자리다. 브라우저를 거치지 않으므로 토큰이 주소에 실리지
// 않고, 그래서 기록에도 안 남는다.
package miniidp

import (
	"crypto/subtle"
	"net/http"
	"strings"
	"time"

	"treasure/keycloak_ad/oidc/jwt"
	"treasure/keycloak_ad/oidc/pkce"
)

// handleToken 은 두 가지 교환을 받는다.
//
//	authorization_code  인가 코드 → 토큰 세 장
//	refresh_token       리프레시 토큰 → 새 토큰 세 장
func (i *IDP) handleToken(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		w.Header().Set("Allow", "POST")
		oauthError(w, http.StatusMethodNotAllowed, "invalid_request",
			"토큰 주소는 POST 로만 받습니다")
		return
	}
	if err := r.ParseForm(); err != nil {
		oauthError(w, http.StatusBadRequest, "invalid_request",
			"폼을 못 읽었습니다")
		return
	}
	if !i.checkClient(w, r) {
		return
	}
	switch r.PostFormValue("grant_type") {
	case "authorization_code":
		i.grantByCode(w, r)
	case "refresh_token":
		i.grantByRefresh(w, r)
	default:
		oauthError(w, http.StatusBadRequest, "unsupported_grant_type",
			"authorization_code 와 refresh_token 만 됩니다")
	}
}

// checkClient 는 앱 자신을 확인한다.
//
// PKCE 가 있는데 왜 또 확인하나: PKCE 는 **코드를 훔친 쪽**을 막고,
// client_secret 은 **앱을 사칭하는 쪽**을 막는다. 막는 것이 다르다.
// (비밀을 숨길 수 없는 앱은 secret 없이 PKCE 만 쓴다 — 8부에서 다룬다.)
func (i *IDP) checkClient(w http.ResponseWriter, r *http.Request) bool {
	id := r.PostFormValue("client_id")
	secret := r.PostFormValue("client_secret")
	okID := subtle.ConstantTimeCompare(
		[]byte(id), []byte(i.cfg.ClientID)) == 1
	okSecret := subtle.ConstantTimeCompare(
		[]byte(secret), []byte(i.cfg.ClientSecret)) == 1
	if !okID || !okSecret {
		// 401 과 함께 이 헤더를 붙이는 것이 규격이다 (RFC 6749 §5.2).
		w.Header().Set("WWW-Authenticate",
			`Basic realm="`+i.cfg.Realm+`"`)
		oauthError(w, http.StatusUnauthorized, "invalid_client",
			"client_id 나 client_secret 이 맞지 않습니다")
		return false
	}
	return true
}

func (i *IDP) grantByCode(w http.ResponseWriter, r *http.Request) {
	code := r.PostFormValue("code")

	i.mu.Lock()
	ac, ok := i.codes[code]
	// **찾자마자 지운다.** 코드는 한 번만 쓸 수 있다 — 가로챈 쪽이
	// 뒤늦게 쓰는 것을 막는 마지막 방어선이다 (RFC 6749 §4.1.2).
	delete(i.codes, code)
	i.mu.Unlock()

	if !ok || !i.now().Before(ac.dies) {
		oauthError(w, http.StatusBadRequest, "invalid_grant",
			"코드가 없거나 이미 썼거나 기한이 지났습니다")
		return
	}
	if ac.redirectURI != r.PostFormValue("redirect_uri") {
		oauthError(w, http.StatusBadRequest, "invalid_grant",
			"redirect_uri 가 코드를 받을 때와 다릅니다")
		return
	}
	// PKCE — 코드를 훔쳤어도 verifier 를 모르면 여기서 막힌다.
	if !pkce.Verify(r.PostFormValue("code_verifier"), ac.challenge) {
		oauthError(w, http.StatusBadRequest, "invalid_grant",
			"code_verifier 가 code_challenge 와 맞지 않습니다")
		return
	}
	i.issue(w, ac.user, ac.nonce)
}

func (i *IDP) grantByRefresh(w http.ResponseWriter, r *http.Request) {
	rt := r.PostFormValue("refresh_token")

	i.mu.Lock()
	row, ok := i.refresh[rt]
	// 리프레시 토큰도 쓰는 즉시 지운다 — **회전**(rotation)이라고 한다.
	// 같은 토큰이 두 번 오면 그건 누가 훔쳐 갔다는 신호다.
	delete(i.refresh, rt)
	i.mu.Unlock()

	if !ok || !i.now().Before(row.dies) {
		oauthError(w, http.StatusBadRequest, "invalid_grant",
			"리프레시 토큰이 없거나 이미 썼거나 기한이 지났습니다")
		return
	}
	// 갱신할 때는 nonce 를 새로 싣지 않는다 — nonce 는 브라우저가
	// 시작한 그 한 번의 로그인에만 뜻이 있기 때문이다.
	i.issue(w, row.user, "")
}

// issue 는 토큰 세 장을 만들어 내준다.
//
// 셋의 쓰임이 다르다는 것이 4부의 핵심이다.
//
//	ID 토큰       "이 사람이 누구인지" 를 **앱에게** 알린다
//	액세스 토큰   "무엇을 해도 되는지" 를 **자원 서버에** 보인다
//	리프레시 토큰 앞의 둘이 만료됐을 때 새로 받는 데만 쓴다
func (i *IDP) issue(w http.ResponseWriter, u User, nonce string) {
	now := i.now()
	base := jwt.Claims{
		Iss: i.cfg.Issuer, Sub: u.DN, Aud: i.cfg.ClientID,
		Iat: now.Unix(), Jti: i.newID(),
		PreferredUsername: u.Username, Email: u.Email, Name: u.Name,
		Groups: u.Groups,
	}
	head := jwt.Header{Alg: jwt.AlgRS256, Typ: "JWT", Kid: i.cfg.Kid}

	idc := base
	idc.Exp = now.Add(i.cfg.IDTTL).Unix()
	idc.Nonce = nonce
	idTok, err := jwt.Sign(head, idc, i.cfg.Key)
	if err != nil {
		oauthError(w, http.StatusInternalServerError, "server_error",
			"ID 토큰을 만들지 못했습니다")
		return
	}

	ac := base
	ac.Exp = now.Add(i.cfg.AccessTTL).Unix()
	// 액세스 토큰에는 nonce 를 싣지 않는다. 그리고 typ 을 달리 둬서
	// ID 토큰을 액세스 토큰 자리에 쓰지 못하게 한다.
	// 둘은 쓰임이 다르다.
	accHead := head
	accHead.Typ = "at+jwt"
	accTok, err := jwt.Sign(accHead, ac, i.cfg.Key)
	if err != nil {
		oauthError(w, http.StatusInternalServerError, "server_error",
			"액세스 토큰을 만들지 못했습니다")
		return
	}

	rt := i.newID()
	i.mu.Lock()
	i.refresh[rt] = refreshToken{
		user: u, clientID: i.cfg.ClientID,
		dies: now.Add(i.cfg.RefreshTTL),
	}
	i.mu.Unlock()

	writeJSON(w, http.StatusOK, map[string]any{
		"access_token":  accTok,
		"id_token":      idTok,
		"refresh_token": rt,
		"token_type":    "Bearer",
		"expires_in":    int(i.cfg.AccessTTL / time.Second),
		"scope":         "openid profile email",
	})
}

// handleUserinfo 는 액세스 토큰을 보고 그 사람의 정보를 준다.
//
// ID 토큰에 이미 다 있는데 왜 또 있나: ID 토큰은 로그인 순간에 한 번
// 발급되고 그 뒤로 바뀌지 않는다. 지금 값이 필요하면 여기로 물어본다.
// 그리고 토큰을 작게 유지하려고 큰 값(사진·많은 그룹)은 여기로 미룬다.
func (i *IDP) handleUserinfo(w http.ResponseWriter, r *http.Request) {
	auth := r.Header.Get("Authorization")
	if !strings.HasPrefix(auth, "Bearer ") {
		// 규격대로, 무엇이 필요한지 헤더로 알린다 (RFC 6750 §3).
		w.Header().Set("WWW-Authenticate",
			`Bearer realm="`+i.cfg.Realm+`"`)
		oauthError(w, http.StatusUnauthorized, "invalid_token",
			"Authorization: Bearer <액세스 토큰> 이 필요합니다")
		return
	}
	tok := strings.TrimPrefix(auth, "Bearer ")
	h, c, err := jwt.Verify(tok, &i.jwks)
	if err != nil {
		w.Header().Set("WWW-Authenticate",
			`Bearer error="invalid_token"`)
		oauthError(w, http.StatusUnauthorized, "invalid_token",
			err.Error())
		return
	}
	// ID 토큰을 여기 들고 오면 안 된다. 쓰임이 다르다.
	if h.Typ != "at+jwt" {
		w.Header().Set("WWW-Authenticate",
			`Bearer error="invalid_token"`)
		oauthError(w, http.StatusUnauthorized, "invalid_token",
			"액세스 토큰이 아닙니다 (ID 토큰은 여기 쓰지 않습니다)")
		return
	}
	if err := c.Validate(jwt.Options{
		Issuer: i.cfg.Issuer, Audience: i.cfg.ClientID, Now: i.now(),
	}); err != nil {
		w.Header().Set("WWW-Authenticate",
			`Bearer error="invalid_token"`)
		oauthError(w, http.StatusUnauthorized, "invalid_token",
			err.Error())
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"sub":                c.Sub,
		"preferred_username": c.PreferredUsername,
		"email":              c.Email,
		"name":               c.Name,
		"groups":             c.Groups,
	})
}

// handleLogout 은 브라우저↔IdP 세션(0부의 A)을 끊는다.
//
// 앱의 세션(B)은 앱이 알아서 끊어야 한다. 그 둘이 따로라는 사실이
// "로그아웃했는데 왜 다시 들어가지나" 의 정체다.
// 8부에서 셋을 다 끊는다.
func (i *IDP) handleLogout(w http.ResponseWriter, r *http.Request) {
	if c, err := r.Cookie("MINIIDP_SESSION"); err == nil {
		i.mu.Lock()
		delete(i.sessions, c.Value)
		i.mu.Unlock()
	}
	http.SetCookie(w, &http.Cookie{
		Name: "MINIIDP_SESSION", Value: "", Path: "/",
		HttpOnly: true, SameSite: http.SameSiteLaxMode, MaxAge: -1,
	})

	back := r.URL.Query().Get("post_logout_redirect_uri")
	if back == "" {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Write([]byte("<!doctype html><meta charset=\"utf-8\">" +
			"<p>로그아웃했습니다.</p>"))
		return
	}
	// 돌아갈 주소도 등록된 것이어야 한다. 아니면 이 링크가
	// 사용자를 아무 데나 보내는 통로(오픈 리다이렉트)가 된다.
	if !i.knownPostLogout(back) {
		http.Error(w, "등록되지 않은 post_logout_redirect_uri 입니다",
			http.StatusBadRequest)
		return
	}
	http.Redirect(w, r, back, http.StatusFound)
}
