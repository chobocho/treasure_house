// miniidp 를 띄우는 자리. 설정은 전부 깃발(flag)로 받는다.
//
//	go run ./ldap/fakead/cmd/fakead -addr :10389 &
//	go run ./oidc/miniidp/cmd/miniidp -addr :9000 \
//	    -key certs/idp-signing.key
//
// 열쇠를 파일에서 읽는 이유: 뜰 때마다 새로 만들면 토큰이 매번 달라져
// 덱의 캡처를 두 번 떠 견주는 검사를 통과할 수 없다. 진짜 Keycloak 도
// 열쇠를 데이터베이스에 두고 재시작해도 유지한다(10부의 키 회전).
package main

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"encoding/pem"
	"flag"
	"log"
	"net/http"
	"os"
	"time"

	"treasure/keycloak_ad/oidc/miniidp"
)

func main() {
	addr := flag.String("addr", ":9000", "듣는 주소")
	issuer := flag.String("issuer", "",
		"토큰의 iss (비면 주소에서 만든다)")
	realm := flag.String("realm", "campus", "realm 이름")
	clientID := flag.String("client", "lunch-web", "클라이언트 이름")
	secret := flag.String("secret", "lunch-secret-demo",
		"클라이언트 비밀")
	redirect := flag.String("redirect",
		"http://localhost:9001/callback", "돌아갈 주소")
	postLogout := flag.String("post-logout",
		"http://localhost:9001/", "로그아웃 뒤 돌아갈 주소")
	keyFile := flag.String("key", "", "서명 열쇠 (비면 새로 만든다)")
	kid := flag.String("kid", "demo-1", "열쇠 이름")

	ldapAddr := flag.String("ldap", "localhost:10389", "AD 주소")
	baseDN := flag.String("base", "DC=ad,DC=campus,DC=example",
		"base DN")
	bindDN := flag.String("binddn",
		"CN=svc-keycloak,OU=Service Accounts,"+
			"DC=ad,DC=campus,DC=example",
		"서비스 계정 DN")
	bindPw := flag.String("bindpw", "Passw0rd!-demo",
		"서비스 계정 비밀번호")
	userAttr := flag.String("userattr", "sAMAccountName",
		"로그인 아이디로 쓸 속성")
	accessTTL := flag.Duration("access-ttl", 5*time.Minute,
		"액세스 토큰 수명")
	fixedNow := flag.String("fixed-now", "",
		"캡처용: 시계를 이 시각으로 못 박는다 (RFC3339)")
	fixedSeed := flag.Int64("fixed-seed", 1, "캡처용: 난수 씨앗")
	flag.Parse()

	key, err := loadOrMakeKey(*keyFile)
	if err != nil {
		log.Fatalf("서명 열쇠: %v", err)
	}
	iss := *issuer
	if iss == "" {
		iss = "http://localhost" + *addr + "/realms/" + *realm
	}

	dir := miniidp.NewLDAPDirectory(miniidp.LDAPConfig{
		Addr: *ldapAddr, BaseDN: *baseDN, BindDN: *bindDN,
		BindPassword: *bindPw, UsernameAttr: *userAttr,
	})
	idp := miniidp.NewIDP(miniidp.Config{
		Issuer: iss, Realm: *realm, ClientID: *clientID,
		ClientSecret: *secret, RedirectURIs: []string{*redirect},
		PostLogoutURIs: []string{*postLogout},
		Key:            key, Kid: *kid, AccessTTL: *accessTTL,
	}, dir)

	if *fixedNow != "" {
		at, err := time.Parse(time.RFC3339, *fixedNow)
		if err != nil {
			log.Fatalf("-fixed-now: %v", err)
		}
		idp.FixForCapture(at, *fixedSeed)
		log.Print("⚠ 캡처 모드 — 시계와 난수를 고정했다. 운영 금지.")
	}

	log.Printf("miniidp 듣는 중 %s", *addr)
	log.Printf("  issuer  %s", iss)
	log.Printf("  안내문  %s/.well-known/openid-configuration", iss)
	log.Printf("  AD      %s (%s)", *ldapAddr, *userAttr)
	if err := http.ListenAndServe(*addr, idp.Handler()); err != nil {
		log.Fatal(err)
	}
}

// loadOrMakeKey 는 PEM 파일에서 개인키를 읽는다. 이름이 비어 있으면
// 새로 만든다 — 그러면 재시작할 때마다 옛 토큰이 전부 무효가 된다.
func loadOrMakeKey(path string) (*rsa.PrivateKey, error) {
	if path == "" {
		log.Print("서명 열쇠를 새로 만든다 " +
			"— 재시작하면 옛 토큰은 죽는다")
		return rsa.GenerateKey(rand.Reader, 2048)
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	block, _ := pem.Decode(raw)
	if block == nil {
		return nil, os.ErrInvalid
	}
	// openssl genrsa 는 판번호에 따라 PKCS#1 이나 PKCS#8 로 낸다.
	// 둘 다 받아 준다 — 사람이 어느 쪽인지 알 필요는 없다.
	if k, err := x509.ParsePKCS1PrivateKey(block.Bytes); err == nil {
		return k, nil
	}
	any, err := x509.ParsePKCS8PrivateKey(block.Bytes)
	if err != nil {
		return nil, err
	}
	k, ok := any.(*rsa.PrivateKey)
	if !ok {
		return nil, os.ErrInvalid
	}
	return k, nil
}
