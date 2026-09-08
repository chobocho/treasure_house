package miniidp

import (
	"crypto/rand"
	"crypto/rsa"
	"testing"
	"time"
)

// 덱의 검은 화면은 두 번 떠서 md5 가 같아야 실린다(tools/record.sh).
// 그 약속을 코드로 못 박아 둔다 — 시계와 난수를 고정하면 같은 흐름이
// **글자 하나까지 같은** 토큰을 내야 한다.
func TestFixForCaptureIsReproducible(t *testing.T) {
	key, err := rsa.GenerateKey(rand.Reader, 1024)
	if err != nil {
		t.Fatal(err)
	}
	at := time.Date(2026, 9, 8, 12, 0, 0, 0, time.UTC)

	run := func() map[string]any {
		cfg := Config{
			Issuer: "http://localhost:9000/realms/campus",
			Realm:  "campus", ClientID: "lunch-web",
			ClientSecret: "lunch-secret-demo",
			RedirectURIs: []string{testRedirect},
			Key:          key, Kid: "demo-1",
		}
		i := NewIDP(cfg, &fakeDir{})
		i.FixForCapture(at, 7)
		code := login(t, i, "minji", "Passw0rd!-demo")
		status, tok := exchange(t, i, tokenForm(code, testVerifier))
		if status != 200 {
			t.Fatalf("상태 = %d · %v", status, tok)
		}
		return tok
	}

	a, b := run(), run()
	for _, k := range []string{"access_token", "id_token", "refresh_token"} {
		if a[k] != b[k] {
			t.Errorf("%s 가 두 번 달랐다 — 캡처를 재현할 수 없다\n"+
				"  1회: %v\n  2회: %v", k, a[k], b[k])
		}
	}
}

// 고정하지 않으면 달라야 한다. 안 그러면 위 시험이 아무것도 안 지킨다.
func TestTokensDifferWithoutFixing(t *testing.T) {
	i, _ := newTestIDP(t)
	code1 := login(t, i, "minji", "Passw0rd!-demo")
	_, t1 := exchange(t, i, tokenForm(code1, testVerifier))
	code2 := login(t, i, "minji", "Passw0rd!-demo")
	_, t2 := exchange(t, i, tokenForm(code2, testVerifier))
	if t1["refresh_token"] == t2["refresh_token"] {
		t.Fatal("리프레시 토큰이 두 번 같다 — 난수가 아니다")
	}
}
