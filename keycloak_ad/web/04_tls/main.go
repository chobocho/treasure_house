// 04_tls — 자물쇠 표시 안에서 실제로 일어나는 일.
//
// HTTPS 는 두 가지를 한꺼번에 한다. 사람들은 첫째만 기억한다.
//
//  1. 남이 못 읽게 한다 (암호화)
//  2. 상대가 진짜 그 사람인지 확인한다 (신원 확인)
//
// 둘째가 이 덱에서 훨씬 중요하다. 3부의 LDAPS, 6부의 Ingress, 7부의
// truststore 에서 막히는 사고는 전부 둘째 때문이지 첫째 때문이 아니다.
// "인증서가 신뢰되지 않습니다" 는 암호가 약하다는 말이 아니라 "이
// 사람이 자기가 말하는 그 사람인지 내가 확인할 길이 없다" 는 말이다.
//
//	sh certs/make_certs.sh
//	go run ./web/04_tls -addr :8443 -http :8084
//	curl -v https://localhost:8443/tls                      # 실패한다
//	curl -v --cacert certs/demo-ca.crt \
//	     --resolve sso.campus.example:8443:127.0.0.1 \
//	     https://sso.campus.example:8443/tls                # 통한다
package main

import (
	"crypto/tls"
	"flag"
	"fmt"
	"log"
	"net"
	"net/http"
)

func main() {
	addr := flag.String("addr", ":8443", "HTTPS 로 듣는 주소")
	plain := flag.String("http", "", "평문으로 듣고 https 로 보낼 주소")
	certFile := flag.String("cert", "certs/sso.crt", "인증서")
	keyFile := flag.String("key", "certs/sso.key", "개인키")
	flag.Parse()

	cert, err := loadCert(*certFile, *keyFile)
	if err != nil {
		log.Fatalf("인증서: %v", err)
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/tls", handleWhoami)
	mux.HandleFunc("/", handleHome)

	if *plain != "" {
		// 평문 문을 아예 닫지 않고 "저쪽으로 가세요" 만 하는 이유:
		// 사람은 주소창에 https:// 를 안 친다. 문을 닫아 버리면
		// "사이트가 안 열려요" 가 되고, 열어 두면 한 번 옮겨 주고
		// 끝난다.
		// 안내 문구는 고루틴 밖에서 먼저 찍는다. 안에서 찍으면 아래
		// "듣는 중" 과 순서가 그때그때 바뀌어, 캡처가 매번 달라진다.
		log.Printf("평문 %s → https 로 안내", *plain)
		go func() {
			h := redirectToHTTPS(*addr)
			log.Print(http.ListenAndServe(*plain, h))
		}()
	}

	srv := &http.Server{
		Addr:    *addr,
		Handler: mux,
		TLSConfig: &tls.Config{
			Certificates: []tls.Certificate{cert},
			// 1.2 아래는 받지 않는다. 1.0/1.1 은 오래전에 깨졌고,
			// 6부에서 Ingress 에 같은 설정을 넣게 된다.
			MinVersion: tls.VersionTLS12,
		},
	}
	log.Printf("듣는 중 https://localhost%s", *addr)
	// 파일 이름을 빈 문자열로 주면 위 TLSConfig 의 것을 쓴다.
	if err := srv.ListenAndServeTLS("", ""); err != nil {
		log.Fatal(err)
	}
}

// loadCert 는 인증서와 개인키를 짝지어 읽는다.
//
// X509KeyPair 는 둘이 같은 짝인지도 확인한다. 안 맞으면 여기서 죽는
// 것이 맞다 — 그냥 뜨면 서버는 멀쩡해 보이고 접속하는 쪽만 알 수 없는
// 오류로 죽어서, 원인이 서버에 있다는 것을 아무도 눈치채지 못한다.
func loadCert(certFile, keyFile string) (tls.Certificate, error) {
	return tls.LoadX509KeyPair(certFile, keyFile)
}

// versionNames 는 규약 판번호를 사람이 읽는 이름으로 바꾼다.
var versionNames = map[uint16]string{
	tls.VersionTLS10: "TLS 1.0",
	tls.VersionTLS11: "TLS 1.1",
	tls.VersionTLS12: "TLS 1.2",
	tls.VersionTLS13: "TLS 1.3",
}

// tlsSummary 는 이 연결이 어떻게 암호화됐는지 한 줄로 말한다.
// cs 가 nil 이면 암호화가 아예 없었다는 뜻이다 — 그것도 분명히 말한다.
func tlsSummary(cs *tls.ConnectionState) string {
	if cs == nil {
		return "평문(HTTP) — 중간에서 누구나 읽고 고칠 수 있습니다"
	}
	ver, ok := versionNames[cs.Version]
	if !ok {
		ver = fmt.Sprintf("알 수 없는 판(0x%04x)", cs.Version)
	}
	name := cs.ServerName
	if name == "" {
		// SNI 를 안 보낸 상대다. IP 로 바로 붙었을 때 그렇다.
		name = "(이름 없이 붙음)"
	}
	return fmt.Sprintf("%s · 암호 %s · 요청한 이름 %s",
		ver, tls.CipherSuiteName(cs.CipherSuite), name)
}

func handleWhoami(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	fmt.Fprintf(w, "%s\n", tlsSummary(r.TLS))
}

func handleHome(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	fmt.Fprintf(w, `<!doctype html><meta charset="utf-8">
<h1>학식 예약 (HTTPS)</h1>
<p>%s</p>
`, tlsSummary(r.TLS))
}

// redirectToHTTPS 는 평문으로 온 요청을 같은 주소의 https 로 보낸다.
//
// 301(영구)을 쓰는 이유: 브라우저가 기억해 둬서 다음부터는 평문으로
// 나가지도 않는다. 평문 요청이 한 번이라도 나가면 그 한 번에 쿠키가
// 실려 나갈 수 있다.
func redirectToHTTPS(tlsAddr string) http.Handler {
	_, port, err := net.SplitHostPort(tlsAddr)
	if err != nil {
		port = "443"
	}
	return http.HandlerFunc(func(w http.ResponseWriter,
		r *http.Request) {
		host := r.Host
		if h, _, err := net.SplitHostPort(host); err == nil {
			host = h // 들어온 쪽 포트는 버리고 https 쪽 포트를 붙인다
		}
		target := "https://" + host
		if port != "443" {
			target += ":" + port
		}
		target += r.URL.RequestURI()
		http.Redirect(w, r, target, http.StatusMovedPermanently)
	})
}
