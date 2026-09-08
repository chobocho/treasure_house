// 02_form_cookie — 로그인이란 무엇인가를 가장 작게 만든 것.
//
// HTTP 는 한 번 주고받으면 끝이다. 방금 비밀번호를 맞힌 사람이 다음
// 요청에서도 같은 사람인지 서버는 알 방법이 없다. 그래서 손목밴드를
// 하나 채운다 — 그게 쿠키다. 밴드에는 뜻이 없는 번호만 적혀 있고, 그
// 번호가 누구인지는 서버의 장부(sessions)에만 있다.
//
// 이 세 줄이 이 프로그램의 전부이며, 4부에서 Keycloak 이 하는 일의
// 절반이다.
//
//	go run ./web/02_form_cookie -addr :8082
//	curl -v -c jar.txt -d 'user=minji&pass=Passw0rd!-demo' \
//	     http://localhost:8082/login
//	curl -v -b jar.txt http://localhost:8082/me
//
// ⚠ 여기 적힌 비밀번호는 시연용 가짜다. 진짜 서비스에서 사람 이름과
// 비밀번호를 소스에 적어 두는 일은 절대 없어야 한다 — 그래서 3부부터
// 그 일을 AD 에게 넘긴다.
package main

import (
	"crypto/rand"
	"crypto/subtle"
	"encoding/hex"
	"flag"
	"fmt"
	"html"
	"log"
	"net/http"
	"sync"
	"time"
)

// 쿠키 이름. 값이 아니라 이름이다 — 이 이름으로 브라우저가 쿠키를 찾아
// 붙인다.
const cookieName = "lunch_session"

// 시연용 계정 넷. 아이디는 대소문자를 가린다(AD 는 안 가리는데, 그
// 차이가 7부에서 사고가 된다 — 여기서는 먼저 엄격한 쪽을 보여 준다).
var demoUsers = map[string]string{
	"minji":     "Passw0rd!-demo",
	"prof.kim":  "Passw0rd!-demo",
	"admin.lee": "Passw0rd!-demo",
}

type session struct {
	user string
	dies time.Time // 이 시각이 지나면 없는 것으로 친다
}

// store 는 서버가 들고 있는 장부다.
//
// now 를 함수로 둔 것은 시험 때문이다. 시계를 우리가 쥐고 있어야 "30분
// 뒤"를 30분 기다리지 않고 확인할 수 있다. 실제로는 time.Now 가
// 들어간다.
type store struct {
	mu   sync.Mutex
	rows map[string]session
	life time.Duration
	now  func() time.Time
}

func newStore(life time.Duration) *store {
	return &store{rows: map[string]session{}, life: life, now: time.Now}
}

// newSessionID 는 아무도 찍어 맞힐 수 없는 번호를 만든다.
//
// crypto/rand 다. math/rand 가 아니다 — 그쪽은 씨앗을 알면 다음 값을
// 계산할 수 있어서, 남의 세션 번호를 만들어 낼 수 있다. 16바이트를
// 16진수로 적으면 32글자가 되고, 경우의 수는 2^128 이다.
func newSessionID() string {
	b := make([]byte, 16)
	if _, err := rand.Read(b); err != nil {
		// 운영체제의 난수원이 죽었다면 더 할 수 있는 일이 없다
		panic(err)
	}
	return hex.EncodeToString(b)
}

func (s *store) create(user string) string {
	id := newSessionID()
	s.mu.Lock()
	defer s.mu.Unlock()
	s.rows[id] = session{user: user, dies: s.now().Add(s.life)}
	return id
}

// get 은 살아 있는 세션만 돌려준다. 시간이 지난 줄은 지도에 남아 있어도
// 없는 것으로 친다 — 그리고 지나는 김에 치운다.
func (s *store) get(id string) (session, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	row, ok := s.rows[id]
	if !ok {
		return session{}, false
	}
	if !s.now().Before(row.dies) {
		delete(s.rows, id)
		return session{}, false
	}
	return row, true
}

func (s *store) remove(id string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.rows, id)
}

// checkPassword 는 아이디와 비밀번호를 맞춰 본다.
//
// subtle.ConstantTimeCompare 를 쓰는 이유: 보통의 == 는 글자가 처음
// 어긋나는 자리에서 바로 끝난다. 그래서 "앞 세 글자가 맞았을 때"가 "첫
// 글자부터 틀렸을 때"보다 아주 조금 더 오래 걸린다. 그 차이를 수만 번
// 재면 비밀번호를 한 글자씩 알아낼 수 있다. 이 함수는 길이가 같으면
// 언제나 끝까지 다 본다.
func checkPassword(user, pass string) bool {
	want, ok := demoUsers[user]
	if !ok {
		// 없는 아이디여도 시간을 비슷하게 쓴다 — 아이디가 있는지
		// 없는지가 응답 속도로 새어 나가지 않게.
		subtle.ConstantTimeCompare([]byte(pass), []byte(pass))
		return false
	}
	return subtle.ConstantTimeCompare([]byte(pass), []byte(want)) == 1
}

type app struct{ sessions *store }

func main() {
	addr := flag.String("addr", ":8082", "듣는 주소")
	life := flag.Duration("life", 30*time.Minute, "세션 수명")
	flag.Parse()

	a := &app{sessions: newStore(*life)}
	mux := http.NewServeMux()
	mux.HandleFunc("/login", a.handleLogin)
	mux.HandleFunc("/logout", a.handleLogout)
	mux.HandleFunc("/me", a.handleMe)
	mux.HandleFunc("/", a.handleHome)

	log.Printf("듣는 중 http://localhost%s  세션 수명 %s", *addr, *life)
	if err := http.ListenAndServe(*addr, mux); err != nil {
		log.Fatal(err)
	}
}

// current 는 요청에 붙어 온 손목밴드를 보고 누구인지 알아낸다. 쿠키가
// 없거나, 번호가 장부에 없거나, 수명이 지났으면 "모르는 사람" 이다.
func (a *app) current(r *http.Request) (string, bool) {
	c, err := r.Cookie(cookieName)
	if err != nil { // 쿠키가 아예 없다
		return "", false
	}
	row, ok := a.sessions.get(c.Value)
	if !ok {
		return "", false
	}
	return row.user, true
}

func (a *app) handleHome(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if user, ok := a.current(r); ok {
		fmt.Fprintf(w, `<!doctype html><meta charset="utf-8">
<h1>학식 예약</h1>
<p>안녕하세요, %s 님.</p>
<form method="post" action="/logout"><button>로그아웃</button></form>
`, html.EscapeString(user))
		return
	}
	fmt.Fprint(w, `<!doctype html><meta charset="utf-8">
<h1>학식 예약</h1>
<form method="post" action="/login">
<label>아이디 <input name="user"></label>
<label>비밀번호 <input name="pass" type="password"></label>
<button>로그인</button>
</form>
`)
}

// handleLogin 은 이 프로그램에서 유일하게 비밀번호를 보는 곳이다.
func (a *app) handleLogin(w http.ResponseWriter, r *http.Request) {
	// POST 만 받는다. 주소만 눌러도 로그인이 된다면 남의 사이트가
	// <img src="…/login?user=…"> 한 줄로 남을 로그인시킬 수 있다.
	if r.Method != http.MethodPost {
		w.Header().Set("Allow", "POST")
		http.Error(w, "POST 로만 됩니다", http.StatusMethodNotAllowed)
		return
	}
	user := r.PostFormValue("user")
	if !checkPassword(user, r.PostFormValue("pass")) {
		// 어느 쪽이 틀렸는지 말하지 않는다. "그런 아이디 없음" 이라고
		// 알려 주면 아이디 목록을 만들 수 있다.
		http.Error(w, "아이디나 비밀번호가 틀렸습니다",
			http.StatusUnauthorized)
		return
	}
	http.SetCookie(w, &http.Cookie{
		Name:  cookieName,
		Value: a.sessions.create(user),
		Path:  "/",
		// 자바스크립트가 못 읽게 한다. 페이지에 남의 스크립트가 한
		// 줄이라도 끼어들면 이게 없는 쿠키는 그대로 새어 나간다.
		HttpOnly: true,
		// 남의 사이트에서 시작된 요청에는 쿠키를 붙이지 않는다.
		SameSite: http.SameSiteLaxMode,
		// 진짜 서비스에서는 Secure: true 도 켠다. 여기는 http 로도
		// 실습해야 해서 껐다 — 4부에서 다시 이야기한다.
		MaxAge: int(a.sessions.life.Seconds()),
	})
	// 303 See Other: "다 됐으니 저 주소를 GET 으로 가 보라".
	// POST 한 자리에 그대로 머물면 새로고침이 로그인을 또 보낸다.
	http.Redirect(w, r, "/me", http.StatusSeeOther)
}

func (a *app) handleMe(w http.ResponseWriter, r *http.Request) {
	user, ok := a.current(r)
	if !ok {
		http.Error(w, "로그인이 필요합니다", http.StatusUnauthorized)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	fmt.Fprintf(w, `<!doctype html><meta charset="utf-8">
<h1>내 예약</h1>
<p>%s 님의 이번 주 예약: 화요일 점심.</p>
`, html.EscapeString(user))
}

// handleLogout 은 반드시 양쪽을 다 지운다.
//
// 브라우저의 쿠키만 지우면, 그 번호를 어딘가에 적어 둔 사람은 계속
// 들어온다. 서버의 장부만 지우면, 브라우저는 죽은 번호를 계속 들고
// 다닌다.
func (a *app) handleLogout(w http.ResponseWriter, r *http.Request) {
	if c, err := r.Cookie(cookieName); err == nil {
		a.sessions.remove(c.Value)
	}
	// 쿠키를 지우는 방법은 "지우라는 명령"이 아니라 "수명이 이미 끝난
	// 같은 이름의 쿠키를 다시 주는 것" 이다. Path 가 심을 때와 같아야
	// 지워진다.
	http.SetCookie(w, &http.Cookie{
		Name:     cookieName,
		Value:    "",
		Path:     "/",
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
		MaxAge:   -1,
	})
	http.Redirect(w, r, "/", http.StatusSeeOther)
}
