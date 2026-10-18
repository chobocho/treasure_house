// 정산 에이전트 — 견적을 모아 예산과 대 보고, 결재를 받는다.
//
// 보여 주는 것: securitySchemes(OAuth2 client-credentials), Bearer
// 토큰 검사와 401, 스코프에 따른 권한, 확장 Agent Card, 서명된 카드
// (JWS EdDSA + JCS), 작업 중 권한 요청(AUTH_REQUIRED).
// 같은 서버가 시험용 OAuth2 토큰 발급기(/oauth/token)도 겸한다.
package main

import (
	"bytes"
	"context"
	"crypto"
	"crypto/x509"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"iter"
	"net/http"
	"os"
	"slices"
	"strings"
	"sync"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2acrypto"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/agents/common"
	"example.com/workshop/workshop"
)

const approve = "payment:approve"

var scopes = map[string]string{
	"payment:read": "정산 조회", approve: "결재 승인",
}

// needed 는 카드의 SecurityRequirements 가 요구하는 스코프 — 문지기도
// 이것을 본다.
var needed = []string{"payment:read"}

// grant 는 토큰 하나로 받은 것: 클라이언트와 스코프.
type grant struct {
	client string
	scopes []string
}

// region: tokens
// 발급한 토큰 → grant. 시험용이라 메모리에만 둔다.
var (
	mu     sync.Mutex
	tokens = map[string]grant{}
	issued = map[string]int{}
)

// tokenEndpoint: OAuth2 client-credentials 토큰 발급(RFC 6749 4.4절).
func tokenEndpoint(w http.ResponseWriter, r *http.Request) {
	// 몸통은 application/x-www-form-urlencoded. 표준 라이브러리로 푼다.
	_ = r.ParseForm()
	form := r.PostForm
	if form.Get("grant_type") != "client_credentials" {
		oops(w, 400, "unsupported_grant_type")
		return
	}
	who, ok := findClient(form.Get("client_id"),
		form.Get("client_secret"))
	if !ok {
		oops(w, 401, "invalid_client")
		return
	}
	asked := strings.Fields(form.Get("scope"))
	if len(asked) == 0 {
		asked = who.Scopes
	}
	for _, s := range asked {
		if !slices.Contains(who.Scopes, s) {
			oops(w, 400, "invalid_scope")
			return
		}
	}
	cid, scope := who.ClientID, strings.Join(asked, " ")
	mu.Lock()
	issued[cid]++
	// 진짜 토큰은 추측할 수 없는 난수여야 한다. 여기서는 캡처가
	// 매번 같도록 일부러 '클라이언트-순번'으로 만든다.
	token := fmt.Sprintf("tok-%s-%d", cid, issued[cid])
	tokens[token] = grant{cid, asked}
	mu.Unlock()
	common.Say("[정산] 토큰 발급: %s %s", cid, scope)
	reply(w, 200, tokenJSON{token, "Bearer", 3600, scope})
}

// endregion

// tokenJSON 은 토큰 응답. 구조체로 써야 필드 순서가 파이썬 응답과
// 같다(map 은 키가 정렬된다).
type tokenJSON struct {
	AccessToken string `json:"access_token"`
	TokenType   string `json:"token_type"`
	ExpiresIn   int    `json:"expires_in"`
	Scope       string `json:"scope"`
}

func findClient(id, secret string) (workshop.OAuthClient, bool) {
	for _, c := range workshop.Clients() {
		if c.ClientID == id && c.ClientSecret == secret {
			return c, true
		}
	}
	return workshop.OAuthClient{}, false
}

func oops(w http.ResponseWriter, status int, code string) {
	reply(w, status, map[string]string{"error": code})
}

func reply(w http.ResponseWriter, status int, body any) {
	b, _ := json.Marshal(body)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_, _ = w.Write(b)
}

// lookup 은 Authorization: Bearer <토큰> 을 읽어 발급 기록을 찾는다.
func lookup(header string) (grant, bool) {
	scheme, token, _ := strings.Cut(header, " ")
	if !strings.EqualFold(scheme, "bearer") {
		return grant{}, false
	}
	mu.Lock()
	defer mu.Unlock()
	g, ok := tokens[token]
	return g, ok
}

// region: bearer
// requireBearer: JSON-RPC 경로(/)는 토큰 없이는 401 로 돌려보낸다.
// 카드·JWKS·토큰 발급 경로는 누구나 읽어야 하므로 열어 둔다.
func requireBearer(next http.Handler) http.Handler {
	return http.HandlerFunc(func(
		w http.ResponseWriter, r *http.Request,
	) {
		header, sent := r.Header["Authorization"]
		if g, ok := lookup(strings.Join(header, "")); ok {
			if lacks(g.scopes) {
				insufficient(w)
				return
			}
			next.ServeHTTP(w, r)
			return
		}
		// RFC 6750: 토큰이 아예 없으면 error 를 붙이지 않는다.
		challenge, body := `Bearer realm="settlement"`, "unauthorized"
		if sent {
			challenge += `, error="invalid_token"`
			body = "invalid_token"
		}
		w.Header().Set("WWW-Authenticate", challenge)
		oops(w, 401, body)
	})
}

// bearerUser 는 SDK 의 호출 가로채기다. 토큰의 주인과 스코프를
// 호출 맥락의 사용자로 붙여, 실행기가 ExecutorContext.User 로 읽는다.
type bearerUser struct {
	a2asrv.PassthroughCallInterceptor
}

func (bearerUser) Before(
	ctx context.Context, cc *a2asrv.CallContext, _ *a2asrv.Request,
) (context.Context, any, error) {
	header, _ := cc.ServiceParams().Get("authorization")
	if g, ok := lookup(strings.Join(header, "")); ok {
		attrs := map[string]any{"scopes": g.scopes}
		cc.User = a2asrv.NewAuthenticatedUser(g.client, attrs)
	}
	return ctx, nil, nil
}

// endregion

// region: scope
func lacks(granted []string) bool {
	for _, s := range needed {
		if !slices.Contains(granted, s) {
			return true
		}
	}
	return false
}

// insufficient: 토큰은 맞는데 카드가 요구하는 스코프가 없다 → 403.
// RFC 6750 3.1절: insufficient_scope 는 403, 모자란 스코프는
// scope 속성으로 알린다.
func insufficient(w http.ResponseWriter) {
	w.Header().Set("WWW-Authenticate", `Bearer realm="settlement", `+
		`error="insufficient_scope", `+
		`scope="`+strings.Join(needed, " ")+`"`)
	oops(w, 403, "insufficient_scope")
}

// endregion

func skill(id, name, desc string) a2a.AgentSkill {
	return a2a.AgentSkill{ID: id, Name: name, Description: desc,
		Tags: []string{"budget", "workshop"}}
}

// region: card
func card(url string, extended bool) *a2a.AgentCard {
	oauth := a2a.OAuth2SecurityScheme{
		Flows: a2a.ClientCredentialsOAuthFlow{
			TokenURL: url + "oauth/token", Scopes: scopes,
		},
	}
	skills := []a2a.AgentSkill{
		skill("check-budget", "예산 검토",
			"견적 합계를 예산과 대 봅니다."),
	}
	if extended { // 로그인한 클라이언트에게만 보이는 기술
		skills = append(skills, skill("settle-budget", "정산·결재",
			"결재를 받아 정산서를 냅니다."))
	}
	return &a2a.AgentCard{
		Name:        "보물상사 정산 에이전트",
		Description: "견적을 모아 예산과 대 보고 결재를 받습니다.",

		Version:             "1.0.0",
		Provider:            common.Provider,
		SupportedInterfaces: common.JSONRPCInterface(url),
		Capabilities: a2a.AgentCapabilities{
			Streaming: true, ExtendedAgentCard: true,
		},
		SecuritySchemes: a2a.NamedSecuritySchemes{"oauth": oauth},
		SecurityRequirements: a2a.SecurityRequirementsOptions{
			{"oauth": needed},
		},
		DefaultInputModes:  []string{"application/json"},
		DefaultOutputModes: []string{"application/json"},
		Skills:             skills,
	}
}

// endregion

// region: sign
// signed 는 공개 카드에 서명을 달아 내보낼 바이트를 만든다.
// EdDSA 는 결정적이라 매번 같은 값. SDK 의 NewSignedCardProducer 는
// json.Marshal 한 카드("pushNotifications":false 포함)에 서명하는데,
// 파이썬·TS 검증기는 그 false 를 뺀 모양을 정규화하므로 서명이
// 맞지 않는다. 그래서 기본값을 뺀 모양에 서명하고 그대로 내보낸다.
func signed(c *a2a.AgentCard, url string) []byte {
	key := privateKey(workshop.FixturePath(
		"keys/settlement-ed25519.pem"))
	signer, err := a2acrypto.NewSigner(a2acrypto.SignerConfig{
		PrivateKey: key,
		KeyID:      "settlement-2026",
		Algorithm:  "EdDSA",
		JWKSURL:    url + ".well-known/jwks.json",
	})
	check(err)
	// 보호 헤더는 Go 의 map 이라 키가 정렬된다(alg,jku,kid,typ) —
	// 파이썬(PyJWT)과 같은 순서라서 서명까지 바이트가 같다.
	sig, err := signer.Sign(context.Background(), common.ProtoJSON(c))
	check(err)
	c.Signatures = append(c.Signatures, *sig)
	return common.ProtoJSON(c)
}

func jwksEndpoint(w http.ResponseWriter, r *http.Request) {
	raw, err := os.ReadFile(workshop.FixturePath("keys/jwks.json"))
	var buf bytes.Buffer
	if err == nil {
		err = json.Compact(&buf, raw)
	}
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_, _ = w.Write(buf.Bytes())
}

// endregion

func privateKey(path string) crypto.Signer {
	raw, err := os.ReadFile(path)
	check(err)
	block, _ := pem.Decode(raw)
	key, err := x509.ParsePKCS8PrivateKey(block.Bytes)
	check(err)
	return key.(crypto.Signer)
}

type executor struct{}

// region: executor
func (executor) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		task, up, ok := common.Begin(ec, yield)
		if !ok {
			return
		}
		heard, user := task.History, ec.User // 이번 메시지까지
		for {
			who, granted := identity(user)
			req := common.DataOf(heard...)
			items := itemsOf(req["items"])
			result, over := workshop.Settle(workshop.SettleRequest{
				Items:    items,
				Budget:   common.Int(req["budget"]),
				Approved: slices.Contains(granted, approve),
			})
			if over != nil {
				why := fmt.Sprintf("%s (%s원)", over.Reason,
					common.Comma(over.Over))
				common.Say("[정산] 거절: %s", why)
				up.Status(a2a.TaskStateRejected, common.TextPart(why))
				return
			}
			if result.Status != "auth-required" {
				complete(up, result, items, who)
				return
			}
			note := fmt.Sprintf("합계 %s원은 결재가 필요합니다. "+
				"%s 스코프 토큰으로 다시 보내 주세요.",
				common.Comma(result.Total), approve)
			common.Say("[정산] 결재 요청: %s", who)
			// 실행은 끝나지 않고 여기서 다음 메시지를 기다린다(park.go)
			r, ok := up.AwaitReply(ctx,
				common.TextPart(note), common.DataPart(result))
			if !ok {
				return
			}
			heard = append(slices.Clone(r.Task.History), r.Msg)
			user = r.User
		}
	}
}

// endregion

// complete 는 정산서를 아티팩트로 내고 작업을 끝낸다.
func complete(up *common.Updater, result workshop.SettleResult,
	items []workshop.Item, who string) {
	sheet := common.Plain(result).(map[string]any)
	sheet["items"] = common.Plain(items)
	sheet["approvedBy"] = who
	total := common.Comma(result.Total)
	common.Say("[정산] 완료: %s원 (%s)", total, who)
	up.Artifact("정산서", common.Chunk{ID: "settlement"},
		common.DataPart(sheet))
	up.Status(a2a.TaskStateCompleted)
}

// identity 는 사용자 이름과 토큰의 스코프(bearerUser 가 붙인 것).
func identity(u *a2asrv.User) (string, []string) {
	if u == nil {
		return "", nil
	}
	granted, _ := u.Attributes["scopes"].([]string)
	return u.Name, granted
}

// itemsOf 는 [{name, amount}] 를 읽는다. amount 는 30.0 꼴일 수 있다.
func itemsOf(v any) []workshop.Item {
	rows, _ := v.([]any)
	items := []workshop.Item{}
	for _, row := range rows {
		m, _ := row.(map[string]any)
		name, _ := m["name"].(string)
		items = append(items,
			workshop.Item{Name: name, Amount: common.Int(m["amount"])})
	}
	return items
}

func (executor) Cancel(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return common.Cancel(ec)
}

func check(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func main() {
	args := common.ParseArgs("보물상사 정산 에이전트")
	url := args.URL
	public := signed(card(url, false), url)
	common.Serve(card(url, false), executor{}, args.Port,
		common.Options{
			Routes: func(mux *http.ServeMux) {
				mux.HandleFunc("POST /oauth/token", tokenEndpoint)
				mux.HandleFunc("GET /.well-known/jwks.json",
					jwksEndpoint)
			},
			Guard: requireBearer,
			Card:  a2asrv.NewAgentCardHandler(common.CardBytes(public)),
			Handler: []a2asrv.RequestHandlerOption{
				a2asrv.WithExtendedAgentCard(card(url, true)),
				a2asrv.WithCallInterceptors(bearerUser{}),
			},
		})
}
