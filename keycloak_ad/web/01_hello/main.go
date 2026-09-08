// 01_hello — 웹 서버 가운데 가장 작은 것.
//
// 이 프로그램이 가르치는 것은 하나다: HTTP 는 글자다. 브라우저가 보내는
// 것도, 서버가 돌려주는 것도 사람이 읽을 수 있는 줄들이다. 그래서 /echo
// 는 받은 요청을 그대로 글로 옮겨 돌려준다 — 브라우저가 몰래 무엇을
// 붙여 보내는지 눈으로 보라는 뜻이다.
//
//	go run ./web/01_hello -addr :8081
//	curl -v http://localhost:8081/echo
package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"sort"
	"strings"
)

func main() {
	addr := flag.String("addr", ":8081", "듣는 주소")
	flag.Parse()

	// ServeMux 는 "주소 → 처리 함수" 표다. 웹 서버의 심장은 이 표
	// 하나다.
	mux := http.NewServeMux()
	mux.HandleFunc("/echo", handleEcho)
	mux.HandleFunc("/", handleHello) // 나머지 전부

	log.Printf("듣는 중 http://localhost%s  (Ctrl+C 로 끝)", *addr)
	if err := http.ListenAndServe(*addr, logging(mux)); err != nil {
		log.Fatal(err)
	}
}

// logging 은 들어온 요청 한 줄을 터미널에 남긴다. 이렇게 다른 처리기를
// 감싸는 것을 미들웨어라고 부른다 — 8부에서 이 자리에 "로그인했는지
// 확인" 을 끼워 넣게 된다. 지금은 그 자리만 만들어 둔다.
func logging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter,
		r *http.Request) {
		log.Printf("%s %s", r.Method, r.URL.RequestURI())
		next.ServeHTTP(w, r)
	})
}

// handleHello 는 첫 페이지다.
//
// "/" 로 등록한 처리 함수는 등록되지 않은 모든 주소도 받는다. 그래서
// 여기서 직접 404 를 내야 한다. 빼먹으면 오타 난 주소가 조용히 첫
// 페이지를 보여 준다.
func handleHello(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r) // 404 Not Found
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	fmt.Fprint(w, `<!doctype html>
<meta charset="utf-8">
<h1>학식 예약</h1>
<p>아직 아무나 들어올 수 있습니다.</p>
<p><a href="/echo">내가 보낸 요청 보기</a></p>
`)
}

// handleEcho 는 받은 요청을 글자 그대로 돌려준다.
func handleEcho(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	fmt.Fprint(w, requestDump(r))
}

// requestDump 는 요청 하나를 사람이 읽는 여러 줄로 옮긴다.
//
// 헤더는 지도(map)라 Go 가 돌 때마다 순서를 바꾼다. 그대로 찍으면 같은
// 요청도 매번 다르게 보여서, 캡처를 두 번 떠 비교하는 검사를 통과할 수
// 없다. 그래서 이름순으로 정렬한다. 시간 O(n log n), 공간 O(n) — n 은
// 헤더 수.
func requestDump(r *http.Request) string {
	var b strings.Builder

	// 첫 줄은 요청 줄(request line): 방법 · 주소 · 규약 판번호
	fmt.Fprintf(&b, "%s %s %s\n", r.Method, r.URL.RequestURI(), r.Proto)

	// Host 는 헤더인데도 Go 가 r.Header 에서 빼서 r.Host 에 따로 담아
	// 둔다. 다시 넣어 주지 않으면 캡처에서 Host 줄만 통째로 사라진다.
	fmt.Fprintf(&b, "Host: %s\n", r.Host)

	names := make([]string, 0, len(r.Header))
	for name := range r.Header {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		for _, v := range r.Header[name] {
			fmt.Fprintf(&b, "%s: %s\n", name, v)
		}
	}
	return b.String()
}
