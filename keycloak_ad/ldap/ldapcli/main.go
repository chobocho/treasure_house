// ldapcli — LDAP 을 눈으로 보게 해 주는 도구.
//
// 널리 쓰이는 ldapsearch 는 결과만 보여 준다. 이 도구는 **오간
// 바이트**를 함께 보여 준다. 3부에서 "LDAP 은 바이트다" 를 증명하는
// 자리이자, 7부에서 Keycloak 이 보낸 것과 우리가 보낸 것을 견주는
// 자리다.
//
// 말을 거는 일은 ldap/client 가 한다. 이 파일은 그 위에 갈고리를 걸어
// 오간 바이트를 풀어 보여 주는 껍데기다 — 같은 클라이언트를 4부의
// miniidp 도 쓰는데, 그쪽은 이런 출력을 원하지 않기 때문이다.
//
//	go run ./ldap/ldapcli -h localhost:10389 \
//	    -D 'CN=svc-keycloak,OU=Service Accounts,\
//	        DC=ad,DC=campus,DC=example' \
//	    -w 'Passw0rd!-demo' \
//	    search '(sAMAccountName=minji)' cn mail
//
//	go run ./ldap/ldapcli -h localhost:10636 -ldaps \
//	    -cacert certs/demo-ca.crt -name ldap.ad.campus.example \
//	    search ...
package main

import (
	"errors"
	"flag"
	"fmt"
	"os"
	"strings"
	"time"

	"treasure/keycloak_ad/ldap/client"
	"treasure/keycloak_ad/ldap/proto"
)

func usage() {
	fmt.Fprint(os.Stderr, `사용법:
  ldapcli [옵션] bind
  ldapcli [옵션] search '(필터)' [속성...]

옵션:
`)
	flag.PrintDefaults()
}

func main() {
	host := flag.String("h", "localhost:10389", "서버 주소")
	bindDN := flag.String("D", "", "바인드 DN (또는 UPN)")
	pass := flag.String("w", "", "비밀번호")
	base := flag.String("b", "DC=ad,DC=campus,DC=example",
		"검색 시작점")
	scope := flag.String("s", "sub", "범위: base · one · sub")
	useTLS := flag.Bool("ldaps", false, "처음부터 TLS 로 붙는다")
	caFile := flag.String("cacert", "", "믿을 CA 인증서")
	srvName := flag.String("name", "", "인증서에서 확인할 이름")
	insecure := flag.Bool("k", false, "인증서를 확인하지 않는다 (위험)")
	quiet := flag.Bool("q", false, "바이트 풀이를 생략하고 결과만")
	flag.Usage = usage
	flag.Parse()

	args := flag.Args()
	if len(args) == 0 {
		usage()
		os.Exit(2)
	}

	c, err := client.Dial(*host, client.Options{
		TLS: *useTLS, CAFile: *caFile, ServerName: *srvName,
		Insecure: *insecure, Timeout: 10 * time.Second,
	})
	if err != nil {
		fmt.Fprintf(os.Stderr, "붙지 못했다: %v\n", err)
		os.Exit(1)
	}
	defer c.Close()

	// 여기가 이 도구의 전부다 — 오간 바이트를 받아 나무로 풀어 찍는다.
	if !*quiet {
		c.Trace = func(dir string, raw []byte) {
			what := "받음"
			if dir == "→" {
				what = "보냄"
			}
			fmt.Printf("%s %s (%d바이트)\n", dir, what, len(raw))
			fmt.Print(Dump(raw))
			fmt.Println()
		}
	}

	if err := c.Bind(*bindDN, *pass); err != nil {
		fmt.Println(explainBind(err))
		os.Exit(1)
	}
	fmt.Println("바인드 성공")
	if args[0] == "bind" {
		return
	}
	if args[0] != "search" || len(args) < 2 {
		usage()
		os.Exit(2)
	}

	got, err := c.Search(*base, scopeNum(*scope), args[1], args[2:])
	if err != nil {
		fmt.Fprintf(os.Stderr, "%v\n", err)
		os.Exit(1)
	}
	for _, e := range got {
		fmt.Printf("  dn: %s\n", e.DN)
		for _, name := range sortedNames(e) {
			for _, v := range e.Attrs[name] {
				fmt.Printf("  %s: %s\n", name, plainValue(v))
			}
		}
		fmt.Println()
	}
	fmt.Printf("찾은 항목 %d개\n", len(got))
}

// explainBind 는 실패를 사람 말로 옮긴다.
// AD 의 진단 문구는 접어서 싣고, data 코드는 뜻까지 풀어 준다.
func explainBind(err error) string {
	var be *client.BindError
	if !errors.As(err, &be) {
		return fmt.Sprintf("%v", err)
	}
	lines := []string{"바인드 실패: " + proto.ResultName(be.Code)}
	if be.Diag != "" {
		lines = append(lines, wrapCells("진단: "+be.Diag, "  ", 72)...)
		if why := ExplainADCode(be.Diag); why != "" {
			lines = append(lines, wrapCells("→ "+why, "  ", 72)...)
		}
	}
	return strings.Join(lines, "\n")
}

// sortedNames 는 속성 이름을 가나다순으로 돌려준다.
// 지도를 그냥 훑으면 돌릴 때마다 순서가 달라져 캡처가 매번 바뀐다.
func sortedNames(e client.Entry) []string {
	names := make([]string, 0, len(e.Attrs))
	for n := range e.Attrs {
		names = append(names, n)
	}
	for i := 1; i < len(names); i++ {
		for j := i; j > 0 && names[j] < names[j-1]; j-- {
			names[j], names[j-1] = names[j-1], names[j]
		}
	}
	return names
}

func scopeNum(s string) int {
	switch strings.ToLower(s) {
	case "base":
		return proto.ScopeBaseObject
	case "one":
		return proto.ScopeSingleLevel
	}
	return proto.ScopeWholeSubtree
}
