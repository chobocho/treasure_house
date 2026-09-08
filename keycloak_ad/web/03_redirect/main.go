// 03_redirect — "저쪽으로 가 보세요" 라는 대답.
//
// 로그인은 처음부터 끝까지 옮겨 다니는 일이다. 앱이 "Keycloak 으로
// 가라", Keycloak 이 "다 됐으니 앱으로 돌아가라". 4부에서 볼 그 사슬이
// 여기서는 세 칸짜리 장난감으로 줄어 있다.
//
// 상태 번호가 3으로 시작하면 "그 자리에 답이 없고 다른 데 있다" 는
// 뜻이고, 어디로 가야 하는지는 Location 헤더에 적혀 있다. 브라우저는
// 그걸 보고 사용자에게 묻지 않고 알아서 다시 요청한다.
//
//	go run ./web/03_redirect -addr :8083
//	curl -v -L http://localhost:8083/start
//	curl -v -X POST -d 'a=1' 'http://localhost:8083/method?code=303'
package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"strconv"
)

// 옮기라는 뜻으로 쓸 수 있는 번호는 이 다섯뿐이다.
//
//	301 Moved Permanently   아주 바뀌었다. 브라우저가 기억해 버린다
//	302 Found               지금만 저기다. 가장 흔하다
//	303 See Other           "그 결과는 저기 있으니 GET 으로 가라"
//	307 Temporary Redirect  302 인데, 방법과 본문을 그대로 들고 간다
//	308 Permanent Redirect  301 인데, 방법과 본문을 그대로 들고 간다
//
// 300(여러 후보)과 304(안 바뀌었다)는 3으로 시작하지만 옮기라는 뜻이
// 아니다.
var movable = map[int]bool{
	301: true, 302: true, 303: true, 307: true, 308: true,
}

// redirectCode 는 ?code= 값을 검사한다. 아무 번호나 그대로 내보내면
// 브라우저마다 다르게 굴어서 무엇을 배우는 화면인지 알 수 없게 된다.
func redirectCode(s string) (int, bool) {
	if s == "" {
		return http.StatusFound, true // 안 적으면 302
	}
	n, err := strconv.Atoi(s)
	if err != nil || !movable[n] {
		return 0, false
	}
	return n, true
}

func main() {
	addr := flag.String("addr", ":8083", "듣는 주소")
	flag.Parse()

	mux := http.NewServeMux()
	mux.HandleFunc("/start", handleStart)
	mux.HandleFunc("/step2", handleStep2)
	mux.HandleFunc("/step3", handleStep3)
	mux.HandleFunc("/method", handleMethod)
	mux.HandleFunc("/landed", handleLanded)
	mux.HandleFunc("/loop", handleLoop)

	log.Printf("듣는 중 http://localhost%s", *addr)
	if err := http.ListenAndServe(*addr, mux); err != nil {
		log.Fatal(err)
	}
}

// ── 세 칸짜리 사슬 ───────────────────────────────────────────────────
// Location 을 상대 주소로 적었다. RFC 7231 §7.1.2 부터 허용된다 —
// 브라우저가 지금 주소를 기준으로 알아서 붙인다. 이게 편한 이유는
// 6부에서 안다: 안에서는 http, 밖에서는 https 인 Keycloak 이 절대
// 주소를 적으면 사용자를 클러스터 내부 주소로 보내 버린다.

func handleStart(w http.ResponseWriter, r *http.Request) {
	http.Redirect(w, r, "/step2", http.StatusFound)
}

func handleStep2(w http.ResponseWriter, r *http.Request) {
	http.Redirect(w, r, "/step3", http.StatusFound)
}

// 사슬의 끝. 여기만 Location 없이 200 을 낸다.
func handleStep3(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	fmt.Fprint(w, "도착했습니다. 여기가 사슬의 끝입니다.\n")
}

// ── 번호마다 무엇이 달라지는가 ───────────────────────────────────────

// handleMethod 는 시킨 번호로 /landed 에 옮긴다.
// POST 로 불러 보면 303 과 307 의 차이가 도착지에서 그대로 드러난다.
func handleMethod(w http.ResponseWriter, r *http.Request) {
	code, ok := redirectCode(r.URL.Query().Get("code"))
	if !ok {
		http.Error(w, "code 는 301·302·303·307·308 중 하나여야 합니다",
			http.StatusBadRequest)
		return
	}
	http.Redirect(w, r, "/landed", code)
}

// handleLanded 는 자기가 어떻게 불려 왔는지 그대로 말한다.
func handleLanded(w http.ResponseWriter, r *http.Request) {
	// 본문 길이를 알려면 읽어야 한다. 307/308 로 왔으면 여기에 값이
	// 있고, 303 으로 왔으면 브라우저가 GET 으로 바꿔 보내 비어 있다.
	n, _ := readAndCount(r)
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	fmt.Fprintf(w, "도착. 방법=%s 본문=%d바이트\n", r.Method, n)
}

func readAndCount(r *http.Request) (int, error) {
	if r.Body == nil {
		return 0, nil
	}
	defer r.Body.Close()
	buf := make([]byte, 4096)
	total := 0
	for {
		n, err := r.Body.Read(buf)
		total += n
		if err != nil {
			return total, nil
		}
	}
}

// ── 고리 ─────────────────────────────────────────────────────────────

// handleLoop 는 자기 자신으로 옮긴다 — 잘못 만든 로그인 설정에서 실제로
// 벌어지는 일이다(7부·10부의 "로그인 무한 반복"). 다만 캡처를 뜰 수
// 있게 열 번째에 멈춘다. 진짜 무한 고리였다면 curl 은 --max-redirs 로,
// 브라우저는 "너무 많이 이동했습니다" 로 스스로 끊는다.
func handleLoop(w http.ResponseWriter, r *http.Request) {
	n, _ := strconv.Atoi(r.URL.Query().Get("n"))
	if n >= 10 {
		w.Header().Set("Content-Type", "text/plain; charset=utf-8")
		fmt.Fprintf(w, "%d번 돌고 멈췄습니다.\n", n)
		return
	}
	next := fmt.Sprintf("/loop?n=%d", n+1)
	http.Redirect(w, r, next, http.StatusFound)
}
