// miniapp 를 띄우는 자리.
//
//	go run ./oidc/miniapp -addr :9001 \
//	    -issuer http://localhost:9000/realms/campus
//
// 앱이 아는 것은 issuer 하나뿐이다. 나머지 주소는 안내문에서 읽어 온다.
// 8부에서 이 깃발의 issuer 만 진짜 Keycloak 으로 바꾸면 그대로 돈다.
package main

import (
	"flag"
	"log"
	"net/http"
	"time"
)

func main() {
	addr := flag.String("addr", ":9001", "듣는 주소")
	self := flag.String("self", "",
		"이 앱의 바깥 주소 (비면 주소에서 만든다)")
	issuer := flag.String("issuer",
		"http://localhost:9000/realms/campus", "IdP 의 issuer")
	clientID := flag.String("client", "lunch-web", "클라이언트 이름")
	secret := flag.String("secret", "lunch-secret-demo",
		"클라이언트 비밀")
	admin := flag.String("admin-group", "lunch-admins",
		"관리자 화면을 볼 수 있는 그룹")
	wait := flag.Duration("wait", 10*time.Second, "IdP 를 기다릴 시간")
	fixedNow := flag.String("fixed-now", "",
		"캡처용: 시계를 이 시각으로 못 박는다 (RFC3339)")
	fixedSeed := flag.Int64("fixed-seed", 1, "캡처용: 난수 씨앗")
	flag.Parse()

	base := *self
	if base == "" {
		base = "http://localhost" + *addr
	}
	cfg := AppConfig{
		SelfURL: base, IssuerURL: *issuer, ClientID: *clientID,
		ClientSecret: *secret, AdminGroup: *admin,
	}

	app, err := waitForIDP(cfg, *wait)
	if err != nil {
		log.Fatalf("IdP 를 찾지 못했습니다: %v", err)
	}
	if *fixedNow != "" {
		at, err := time.Parse(time.RFC3339, *fixedNow)
		if err != nil {
			log.Fatalf("-fixed-now: %v", err)
		}
		app.FixForCapture(at, *fixedSeed)
		log.Print("⚠ 캡처 모드 — 시계와 난수를 고정했다. 운영 금지.")
	}

	log.Printf("miniapp 듣는 중 %s", *addr)
	log.Printf("  나      %s", base)
	log.Printf("  IdP     %s", *issuer)
	log.Printf("  관리자  %s 그룹", *admin)
	if err := http.ListenAndServe(*addr, app.Handler()); err != nil {
		log.Fatal(err)
	}
}

// waitForIDP 는 IdP 가 뜰 때까지 기다렸다가 준비한다.
//
// 앱이 IdP 보다 먼저 뜨는 일은 흔하다 — 특히 6부에서 둘을 컨테이너로
// 띄우면 순서를 보장할 수 없다. 죽는 대신 기다리는 편이 낫다.
func waitForIDP(cfg AppConfig, limit time.Duration) (*App, error) {
	dead := time.Now().Add(limit)
	var err error
	for {
		var app *App
		app, err = NewApp(cfg, nil)
		if err == nil {
			return app, nil
		}
		if !time.Now().Before(dead) {
			return nil, err
		}
		time.Sleep(200 * time.Millisecond)
	}
}
