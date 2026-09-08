// fakead — 진짜 Active Directory 인 척하는 아주 작은 LDAP 서버.
//
// 왜 만드나: 이 덱의 독자에게 진짜 AD 가 있을 리 없다. 그런데 AD 없이
// Keycloak 연동을 배우는 것은 불가능하다. 그래서 "Keycloak 이 AD 에게
// 실제로 묻는 것" 만 골라 흉내 내는 서버를 짰다.
//
// Keycloak 은 이것을 진짜 AD 로 알고 붙는다. 덕분에 이 덱의 거의 모든
// 화면이 문서 인용이 아니라 실행 기록이 될 수 있었다.
//
//	go run ./ldap/fakead/cmd/fakead -addr :10389 -ldaps :10636
//	go run ./ldap/ldapcli -h localhost:10389 \
//	    search '(sAMAccountName=minji)'
//
// 로그 파일이 이 프로그램의 진짜 산출물이다. 7부에서 "Keycloak 이 대체
// 무엇을 물었나" 를 알아내는 방법이 그 파일을 읽는 것이다.
package main

import (
	"flag"
	"io"
	"log"
	"os"

	"treasure/keycloak_ad/ldap/fakead"
)

func main() {
	addr := flag.String("addr", ":10389",
		"평문 LDAP 주소 (빈 값이면 안 연다)")
	ldaps := flag.String("ldaps", "", "LDAPS 주소 (빈 값이면 안 연다)")
	cert := flag.String("cert", "certs/ldap.crt", "LDAPS 인증서")
	key := flag.String("key", "certs/ldap.key", "LDAPS 개인키")
	dir := flag.String("dir", "data/campus.ldif", "읽어 들일 LDIF")
	logPath := flag.String("log", "", "로그 파일 (빈 값이면 표준 출력)")
	flag.Parse()

	d, err := fakead.LoadLDIFFile(*dir)
	if err != nil {
		log.Fatalf("LDIF: %v", err)
	}

	var out io.Writer = os.Stdout
	if *logPath != "" {
		f, err := os.Create(*logPath)
		if err != nil {
			log.Fatalf("로그 파일: %v", err)
		}
		defer f.Close()
		out = f
	}

	srv := fakead.NewServer(d, out)
	if *addr != "" {
		if err := srv.ListenPlain(*addr); err != nil {
			log.Fatalf("평문 %s: %v", *addr, err)
		}
		log.Printf("평문 LDAP 듣는 중 %s", srv.Addr())
	}
	if *ldaps != "" {
		if err := srv.ListenTLS(*ldaps, *cert, *key); err != nil {
			log.Fatalf("LDAPS %s: %v", *ldaps, err)
		}
		log.Printf("LDAPS 듣는 중 %s", srv.TLSAddr())
	}
	if *addr == "" && *ldaps == "" {
		log.Fatal("-addr 나 -ldaps 중 하나는 있어야 한다")
	}
	log.Printf("항목 %d개 · %s", d.Count(), *dir)

	// 끝나지 않는다. Ctrl+C 로 끊는다.
	select {}
}
