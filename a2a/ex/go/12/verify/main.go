// 정산 카드의 서명을 SDK 로 검증한다 — 진짜 카드, 고친 카드 둘,
// 가짜 카드를 미리 받아 둔 키로, 마지막엔 가짜 카드의 jku 를 따라가서.
//
//	go run ./12/verify 진짜주소 가짜주소
package main

import (
	"context"
	"crypto"
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2acrypto"

	"example.com/workshop/workshop"
)

var ctx = context.Background()

func cardBytes(url string) []byte {
	resp, err := http.Get(url + ".well-known/agent-card.json")
	check(err)
	defer resp.Body.Close()
	raw, err := io.ReadAll(resp.Body)
	check(err)
	return raw
}

// region: verifiers
// pinned: 미리 받아 둔 공개 키(ex/fixtures/keys/jwks.json)만 믿는다.
// KeyResolverFunc 는 kid 만 받는다 — jku 는 보지도 않는다.
func pinned() a2acrypto.KeyResolverFunc {
	raw, err := os.ReadFile(workshop.FixturePath("keys/jwks.json"))
	check(err)
	var set struct{ Keys []struct{ Kid, X string } }
	check(json.Unmarshal(raw, &set))
	return func(_ context.Context, kid string) (
		crypto.PublicKey, error) {
		for _, k := range set.Keys {
			if k.Kid == kid {
				x, err := base64.RawURLEncoding.DecodeString(k.X)
				return ed25519.PublicKey(x), err
			}
		}
		return nil, fmt.Errorf("모르는 키 %s", kid)
	}
}

// trusting: 카드가 가리키는 jku 를 허용 목록에 그대로 넣는다.
type trusting struct{}

func (trusting) ResolveKey(ctx context.Context, kid, jku string) (
	crypto.PublicKey, error) {
	r := a2acrypto.NewJWKSKeyResolver(nil, []string{jku})
	return r.ResolveKey(ctx, kid, jku)
}

// endregion

// region: main
func verify(label string, raw []byte, kr a2acrypto.KeyResolver) {
	var c a2a.AgentCard
	check(json.Unmarshal(raw, &c))
	cfg := a2acrypto.VerifierConfig{KeyResolver: kr}
	v := a2acrypto.NewVerifier(cfg)
	err := v.Verify(ctx, raw, &c.Signatures[0]) // 받은 바이트 그대로
	if err != nil {
		fmt.Printf("%s → 틀림: %v\n", label, err)
		return
	}
	fmt.Printf("%s → 맞음\n", label)
}

func edit(raw []byte, change func(map[string]any)) []byte {
	var m map[string]any
	check(json.Unmarshal(raw, &m))
	change(m)
	out, err := json.Marshal(m)
	check(err)
	return out
}

func main() {
	real, fake := cardBytes(os.Args[1]), cardBytes(os.Args[2])
	moved := edit(real, func(m map[string]any) {
		at := m["securitySchemes"].(map[string]any)["oauth"]
		at = at.(map[string]any)["oauth2SecurityScheme"]
		at = at.(map[string]any)["flows"]
		cc := at.(map[string]any)["clientCredentials"]
		cc.(map[string]any)["tokenUrl"] = os.Args[2] + "oauth/token"
	})
	noted := edit(real, func(m map[string]any) { m["note"] = "덧붙임" })
	verify("① 진짜 카드", real, pinned())
	verify("② tokenUrl 을 바꾼 진짜 카드", moved, pinned())
	verify("③ 모르는 필드를 더한 진짜 카드", noted, pinned())
	verify("④ 가짜 카드", fake, pinned())
	verify("⑤ 가짜 카드, jku 를 따라가면", fake, trusting{})
}

// endregion

func check(err error) {
	if err != nil {
		fmt.Println("오류:", err)
		os.Exit(1)
	}
}

//@ norun
