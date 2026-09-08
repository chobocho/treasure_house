package main

import (
	"crypto/tls"
	"crypto/x509"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
)

const (
	certPath = "../../certs/sso.crt"
	keyPath  = "../../certs/sso.key"
	caPath   = "../../certs/demo-ca.crt"
)

func TestLoadCert(t *testing.T) {
	if _, err := loadCert(certPath, keyPath); err != nil {
		t.Fatalf("인증서를 못 읽는다: %v — sh certs/make_certs.sh", err)
	}
}

func TestLoadCertMissingFile(t *testing.T) {
	if _, err := loadCert("없는.crt", "없는.key"); err == nil {
		t.Error("없는 파일인데 오류가 안 났다")
	}
}

// 인증서와 개인키가 서로 다른 짝이면 여기서 걸려야 한다.
// 안 걸리면 서버는 뜨고, 접속하는 쪽에서 알 수 없는 오류로 죽는다.
func TestLoadCertMismatchedPair(t *testing.T) {
	_, err := loadCert(certPath, "../../certs/ldap.key")
	if err == nil {
		t.Error("짝이 안 맞는 키인데 통과했다")
	}
}

func TestTLSSummaryPlain(t *testing.T) {
	got := tlsSummary(nil)
	if !strings.Contains(got, "평문") {
		t.Errorf("암호화가 없을 때 = %q — '평문' 이라 해야 한다", got)
	}
}

func TestTLSSummaryNamesVersion(t *testing.T) {
	cs := &tls.ConnectionState{
		Version:     tls.VersionTLS13,
		CipherSuite: tls.TLS_AES_128_GCM_SHA256,
		ServerName:  "sso.campus.example",
	}
	got := tlsSummary(cs)
	for _, want := range []string{"TLS 1.3", "sso.campus.example"} {
		if !strings.Contains(got, want) {
			t.Errorf("요약에 %q 가 없다: %q", want, got)
		}
	}
}

func TestTLSSummaryKnowsOlderVersions(t *testing.T) {
	cs := &tls.ConnectionState{Version: tls.VersionTLS12}
	if got := tlsSummary(cs); !strings.Contains(got, "TLS 1.2") {
		t.Errorf("1.2 를 못 알아본다: %q", got)
	}
}

func TestHandleWhoamiOverPlainHTTP(t *testing.T) {
	w := httptest.NewRecorder()
	handleWhoami(w, httptest.NewRequest("GET", "/tls", nil))
	if !strings.Contains(w.Body.String(), "평문") {
		t.Errorf("평문인데 그렇게 말하지 않는다: %q", w.Body.String())
	}
}

// 평문으로 들어온 요청은 같은 주소의 https 로 보낸다.
func TestRedirectToHTTPS(t *testing.T) {
	h := redirectToHTTPS(":8443")
	w := httptest.NewRecorder()
	r := httptest.NewRequest("GET", "/me?a=1", nil)
	r.Host = "sso.campus.example:8080"
	h.ServeHTTP(w, r)
	if w.Code != http.StatusMovedPermanently {
		t.Errorf("상태 = %d, 원하는 것 301", w.Code)
	}
	want := "https://sso.campus.example:8443/me?a=1"
	if loc := w.Header().Get("Location"); loc != want {
		t.Errorf("Location = %q, 원하는 것 %q", loc, want)
	}
}

// ── 진짜 악수(handshake) 를 해 본다 ──────────────────────────────────
// 여기서부터가 이 프로그램의 요점이다. 자체 CA 로 만든 인증서는
// "그 CA 를 믿는다" 고 말해 준 상대에게만 통한다. 두 경우를 다 본다.

func testServer(t *testing.T) *httptest.Server {
	t.Helper()
	cert, err := loadCert(certPath, keyPath)
	if err != nil {
		t.Fatalf("인증서: %v", err)
	}
	srv := httptest.NewUnstartedServer(http.HandlerFunc(handleWhoami))
	srv.TLS = &tls.Config{Certificates: []tls.Certificate{cert}}
	srv.StartTLS()
	return srv
}

func demoPool(t *testing.T) *x509.CertPool {
	t.Helper()
	pem, err := os.ReadFile(caPath)
	if err != nil {
		t.Fatalf("CA 를 못 읽는다: %v", err)
	}
	pool := x509.NewCertPool()
	if !pool.AppendCertsFromPEM(pem) {
		t.Fatal("CA 를 못 알아본다")
	}
	return pool
}

// 우리 CA 를 믿게 해 주면 붙는다 — 7부의 truststore 가 하는 일이
// 이것이다.
func TestHandshakeSucceedsWithOurCA(t *testing.T) {
	srv := testServer(t)
	defer srv.Close()

	c := &http.Client{Transport: &http.Transport{
		TLSClientConfig: &tls.Config{
			RootCAs: demoPool(t),
			// 시험 서버는 127.0.0.1 로 뜬다. 인증서의 이름은
			// sso.campus.example 이므로 그 이름으로 확인하라 한다.
			ServerName: "sso.campus.example",
		},
	}}
	res, err := c.Get(srv.URL)
	if err != nil {
		t.Fatalf("우리 CA 를 믿는데도 실패했다: %v", err)
	}
	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)
	if !strings.Contains(string(body), "TLS 1.") {
		t.Errorf("암호화되어 들어왔는데 그렇게 말하지 않는다: %q", body)
	}
}

// 안 믿게 두면 악수 자체가 깨진다. 이게 curl 이 내는 그 오류다.
func TestHandshakeFailsWithoutOurCA(t *testing.T) {
	srv := testServer(t)
	defer srv.Close()

	c := &http.Client{Transport: &http.Transport{
		TLSClientConfig: &tls.Config{
			ServerName: "sso.campus.example",
		},
	}}
	if _, err := c.Get(srv.URL); err == nil {
		t.Fatal("모르는 CA 인데 통과했다 — 검증이 꺼져 있다")
	} else if !strings.Contains(err.Error(), "certificate") {
		t.Errorf("인증서 때문에 실패한 것이 아니다: %v", err)
	}
}

// 이름이 다르면, CA 를 믿어도 거절한다. 인증서는 "누구인가" 를 증명하는
// 물건이지 "암호화" 만 하는 물건이 아니기 때문이다.
func TestHandshakeFailsOnWrongName(t *testing.T) {
	srv := testServer(t)
	defer srv.Close()

	c := &http.Client{Transport: &http.Transport{
		TLSClientConfig: &tls.Config{
			RootCAs:    demoPool(t),
			ServerName: "lunch.campus.example", // 인증서에 없는 이름
		},
	}}
	if _, err := c.Get(srv.URL); err == nil {
		t.Fatal("이름이 다른데 통과했다")
	}
}
