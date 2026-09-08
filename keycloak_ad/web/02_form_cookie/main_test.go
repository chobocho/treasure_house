package main

import (
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
	"time"
)

// 시험용 창고. 시계를 우리가 쥐고 있어야 "30분 뒤" 를 30분 기다리지
// 않고 볼 수 있다.
func newTestStore(now func() time.Time) *store {
	s := newStore(30 * time.Minute)
	s.now = now
	return s
}

func fixedClock(t *time.Time) func() time.Time {
	return func() time.Time { return *t }
}

// 세션 번호는 남이 찍어 맞힐 수 없어야 한다. 최소한 매번 달라야 한다.
func TestNewSessionIDIsUniqueAndLong(t *testing.T) {
	seen := map[string]bool{}
	for i := 0; i < 200; i++ {
		id := newSessionID()
		if len(id) < 32 {
			t.Fatalf("세션 번호가 너무 짧다: %q (%d글자)", id, len(id))
		}
		if seen[id] {
			t.Fatalf("세션 번호가 겹쳤다: %q", id)
		}
		seen[id] = true
	}
}

func TestStoreCreateAndGet(t *testing.T) {
	now := time.Date(2026, 9, 8, 9, 0, 0, 0, time.UTC)
	s := newTestStore(fixedClock(&now))
	id := s.create("minji")
	got, ok := s.get(id)
	if !ok || got.user != "minji" {
		t.Fatalf("만든 세션을 못 찾는다: %+v ok=%v", got, ok)
	}
	if _, ok := s.get("없는번호"); ok {
		t.Error("없는 번호가 통과했다")
	}
}

// 수명이 지난 세션은 지도에 남아 있어도 없는 것으로 친다.
func TestStoreExpiry(t *testing.T) {
	now := time.Date(2026, 9, 8, 9, 0, 0, 0, time.UTC)
	s := newTestStore(fixedClock(&now))
	id := s.create("minji")
	now = now.Add(29 * time.Minute)
	if _, ok := s.get(id); !ok {
		t.Error("29분 뒤에는 아직 살아 있어야 한다")
	}
	now = now.Add(2 * time.Minute)
	if _, ok := s.get(id); ok {
		t.Error("31분 뒤에는 죽어 있어야 한다")
	}
}

func TestStoreDelete(t *testing.T) {
	now := time.Date(2026, 9, 8, 9, 0, 0, 0, time.UTC)
	s := newTestStore(fixedClock(&now))
	id := s.create("minji")
	s.remove(id)
	if _, ok := s.get(id); ok {
		t.Error("지운 세션이 살아 있다")
	}
}

func TestCheckPassword(t *testing.T) {
	cases := []struct {
		user, pass string
		want       bool
	}{
		{"minji", "Passw0rd!-demo", true},
		{"prof.kim", "Passw0rd!-demo", true},
		{"minji", "Passw0rd!-demoX", false},
		{"minji", "", false},
		{"없는사람", "Passw0rd!-demo", false},
		{"", "", false},
		// 아이디는 대소문자를 가린다
		{"MINJI", "Passw0rd!-demo", false},
	}
	for _, c := range cases {
		if got := checkPassword(c.user, c.pass); got != c.want {
			t.Errorf("checkPassword(%q, %q) = %v, 원하는 것 %v",
				c.user, c.pass, got, c.want)
		}
	}
}

func postForm(path string, form url.Values) *http.Request {
	body := strings.NewReader(form.Encode())
	r := httptest.NewRequest("POST", path, body)
	r.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	return r
}

func newTestApp() *app {
	now := time.Date(2026, 9, 8, 9, 0, 0, 0, time.UTC)
	return &app{sessions: newTestStore(fixedClock(&now))}
}

// 로그인에 성공하면 두 가지가 나온다: 쿠키 하나와 303 이동.
func TestLoginSuccessSetsCookieAndRedirects(t *testing.T) {
	a := newTestApp()
	w := httptest.NewRecorder()
	a.handleLogin(w, postForm("/login", url.Values{
		"user": {"minji"}, "pass": {"Passw0rd!-demo"},
	}))
	res := w.Result()
	if res.StatusCode != http.StatusSeeOther {
		t.Errorf("상태 = %d, 원하는 것 303", res.StatusCode)
	}
	if loc := res.Header.Get("Location"); loc != "/me" {
		t.Errorf("Location = %q, 원하는 것 /me", loc)
	}
	c := findCookie(res.Cookies(), cookieName)
	if c == nil {
		t.Fatalf("세션 쿠키가 없다: %v", res.Cookies())
	}
	if _, ok := a.sessions.get(c.Value); !ok {
		t.Error("쿠키가 가리키는 세션이 창고에 없다")
	}
}

// 쿠키에 붙는 속성 셋은 장식이 아니다. 하나라도 빠지면 실제로 뚫린다.
func TestLoginCookieAttributes(t *testing.T) {
	a := newTestApp()
	w := httptest.NewRecorder()
	a.handleLogin(w, postForm("/login", url.Values{
		"user": {"minji"}, "pass": {"Passw0rd!-demo"},
	}))
	c := findCookie(w.Result().Cookies(), cookieName)
	if c == nil {
		t.Fatal("세션 쿠키가 없다")
	}
	if !c.HttpOnly {
		t.Error("HttpOnly 가 없다 — 자바스크립트가 쿠키를 읽어 간다")
	}
	if c.Path != "/" {
		t.Errorf("Path = %q, 원하는 것 /", c.Path)
	}
	if c.SameSite != http.SameSiteLaxMode {
		t.Error("SameSite=Lax 가 아니다 — 남의 사이트가 요청을 보낸다")
	}
	if strings.Contains(c.Value, "minji") {
		t.Error("쿠키 값에 아이디가 보인다 — 값에는 뜻이 없어야 한다")
	}
}

func TestLoginWrongPasswordGives401AndNoCookie(t *testing.T) {
	a := newTestApp()
	w := httptest.NewRecorder()
	a.handleLogin(w, postForm("/login", url.Values{
		"user": {"minji"}, "pass": {"틀린비밀번호"},
	}))
	res := w.Result()
	if res.StatusCode != http.StatusUnauthorized {
		t.Errorf("상태 = %d, 원하는 것 401", res.StatusCode)
	}
	if findCookie(res.Cookies(), cookieName) != nil {
		t.Error("실패했는데 쿠키를 줬다")
	}
}

// GET 으로는 로그인이 되면 안 된다. 주소만 눌러도 로그인되면
// 남의 사이트가 <img src> 하나로 남을 로그인시킬 수 있다.
func TestLoginRejectsGet(t *testing.T) {
	a := newTestApp()
	w := httptest.NewRecorder()
	r := httptest.NewRequest("GET", "/login?user=minji", nil)
	a.handleLogin(w, r)
	if w.Code != http.StatusMethodNotAllowed {
		t.Errorf("상태 = %d, 원하는 것 405", w.Code)
	}
}

func TestMeWithoutCookieIs401(t *testing.T) {
	a := newTestApp()
	w := httptest.NewRecorder()
	a.handleMe(w, httptest.NewRequest("GET", "/me", nil))
	if w.Code != http.StatusUnauthorized {
		t.Errorf("상태 = %d, 원하는 것 401", w.Code)
	}
}

func TestMeWithCookieShowsName(t *testing.T) {
	a := newTestApp()
	id := a.sessions.create("minji")
	r := httptest.NewRequest("GET", "/me", nil)
	r.AddCookie(&http.Cookie{Name: cookieName, Value: id})
	w := httptest.NewRecorder()
	a.handleMe(w, r)
	if w.Code != http.StatusOK {
		t.Fatalf("상태 = %d, 원하는 것 200", w.Code)
	}
	if !strings.Contains(w.Body.String(), "minji") {
		t.Errorf("본문에 이름이 없다: %q", w.Body.String())
	}
}

// 남이 지어낸 세션 번호를 들고 와도 통과하면 안 된다.
func TestMeWithForgedCookieIs401(t *testing.T) {
	a := newTestApp()
	r := httptest.NewRequest("GET", "/me", nil)
	r.AddCookie(&http.Cookie{Name: cookieName, Value: "aaaabbbbcccc"})
	w := httptest.NewRecorder()
	a.handleMe(w, r)
	if w.Code != http.StatusUnauthorized {
		t.Errorf("지어낸 쿠키가 통과했다: %d", w.Code)
	}
}

// 로그아웃은 둘 다 해야 한다: 브라우저의 쿠키를 지우고, 서버의 세션도
// 지운다. 쿠키만 지우면 그 번호를 적어 둔 사람은 계속 들어올 수 있다.
func TestLogoutClearsBothSides(t *testing.T) {
	a := newTestApp()
	id := a.sessions.create("minji")
	r := postForm("/logout", url.Values{})
	r.AddCookie(&http.Cookie{Name: cookieName, Value: id})
	w := httptest.NewRecorder()
	a.handleLogout(w, r)

	if _, ok := a.sessions.get(id); ok {
		t.Error("서버 쪽 세션이 남아 있다")
	}
	c := findCookie(w.Result().Cookies(), cookieName)
	if c == nil {
		t.Fatal("쿠키를 지우는 Set-Cookie 가 없다")
	}
	if c.MaxAge >= 0 {
		t.Errorf("MaxAge = %d — 지우려면 음수여야 한다", c.MaxAge)
	}
}

func TestHomeShowsFormWhenLoggedOut(t *testing.T) {
	a := newTestApp()
	w := httptest.NewRecorder()
	a.handleHome(w, httptest.NewRequest("GET", "/", nil))
	body := w.Body.String()
	if !strings.Contains(body, `method="post"`) {
		t.Errorf("로그인 폼이 없다: %q", body)
	}
}

func TestHomeGreetsWhenLoggedIn(t *testing.T) {
	a := newTestApp()
	id := a.sessions.create("minji")
	r := httptest.NewRequest("GET", "/", nil)
	r.AddCookie(&http.Cookie{Name: cookieName, Value: id})
	w := httptest.NewRecorder()
	a.handleHome(w, r)
	if !strings.Contains(w.Body.String(), "minji") {
		t.Errorf("인사에 이름이 없다: %q", w.Body.String())
	}
}

func findCookie(cs []*http.Cookie, name string) *http.Cookie {
	for _, c := range cs {
		if c.Name == name {
			return c
		}
	}
	return nil
}
