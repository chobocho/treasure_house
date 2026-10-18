// HTTPS 로 카드를 두 번 읽는다 — 기본 신뢰 목록으로 한 번, 시험 CA 를
// 믿게 하고 한 번. 서버 인증서 검사는 SDK 가 아니라 net/http 의 일이다.
//
//	go run ./12/tls_card https://127.0.0.1:P/ CA파일
package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"errors"
	"fmt"
	"net/http"
	"os"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

// region: main
func card(hc *http.Client, url string) (*a2a.AgentCard, error) {
	return agentcard.NewResolver(hc).Resolve(context.Background(), url)
}

func main() {
	url, ca := os.Args[1], os.Args[2]
	// http.DefaultClient = 운영체제의 공인 CA 목록
	if _, err := card(http.DefaultClient, url); err != nil {
		var unknown x509.UnknownAuthorityError
		ok := errors.As(err, &unknown)
		fmt.Println("① 기본 신뢰 목록 → x509.UnknownAuthorityError", ok)
		fmt.Println("   원인:", unknown.Error())
	}
	// 시험 CA 하나만 믿는 TLS 설정
	pem, err := os.ReadFile(ca)
	check(err)
	pool := x509.NewCertPool()
	pool.AppendCertsFromPEM(pem)
	hc := &http.Client{Transport: &http.Transport{
		TLSClientConfig: &tls.Config{RootCAs: pool},
	}}
	c, err := card(hc, url)
	check(err)
	oauth := c.SecuritySchemes["oauth"].(a2a.OAuth2SecurityScheme)
	flow := oauth.Flows.(a2a.ClientCredentialsOAuthFlow)
	fmt.Println("② 시험 CA 를 믿으면 →", c.Name)
	fmt.Println("   인터페이스", c.SupportedInterfaces[0].URL)
	fmt.Println("   토큰 주소", flow.TokenURL)
}

// endregion

func check(err error) {
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

//@ norun
