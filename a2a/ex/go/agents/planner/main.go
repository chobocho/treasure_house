// 기획 에이전트 — 총무팀의 한 문장을 받아 워크숍 전체를 꾸린다.
//
// 서버이면서 클라이언트다. 카드로 동료를 찾고(스킬 태그), 숙소·식사·
// 교통을 동시에 맡기고, 견적을 정산 에이전트에 넘겨 결재를 받는다.
// 정산이 결재를 요구하면 그 요구를 자기 사용자에게 넘긴다(§7.6.2 의
// AUTH_REQUIRED 사슬).
package main

import (
	"context"
	"crypto"
	"crypto/ed25519"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"iter"
	"net/http"
	"net/url"
	"os"
	"slices"
	"strings"
	"sync"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
	"github.com/a2aproject/a2a-go/v2/a2acrypto"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/agents/common"
	"example.com/workshop/workshop"
)

// region: roles
// 맡길 일 → 그 일을 하는 에이전트의 스킬 태그(순서가 곧 찾는 순서)
var roles = [][2]string{
	{"lodging", "lodging"},
	{"meals", "meals"},
	{"bus", "transport"},
	{"settle", "budget"},
}

// endregion

const working = a2a.TaskStateWorking

var ask = map[string]string{
	"date":      "날짜(예: 2026-10-30)",
	"nights":    "박 수(예: 1박)",
	"headcount": "인원(예: 30명)",
	"budget":    "예산(예: 예산 6,000,000원)",
}

func card(url string) *a2a.AgentCard {
	return &a2a.AgentCard{
		Name: "보물상사 기획 에이전트",
		Description: "한 문장 요청으로 워크숍 숙소·식사·교통·정산을 " +
			"꾸립니다.",

		Version:             "1.0.0",
		Provider:            common.Provider,
		SupportedInterfaces: common.JSONRPCInterface(url),
		Capabilities:        a2a.AgentCapabilities{Streaming: true},
		DefaultInputModes:   []string{"text/plain"},
		DefaultOutputModes: []string{
			"text/markdown", "application/json",
		},
		Skills: []a2a.AgentSkill{{
			ID:          "plan-workshop",
			Name:        "워크숍 기획",
			Description: "동료 에이전트에게 일을 나눠 맡깁니다.",
			Tags:        []string{"workshop", "orchestration"},
			Examples: []string{
				"2026-10-30부터 1박 2일, 30명(채식 2명), " +
					"예산 6,000,000원, 출발 강남역",
			},
		}},
	}
}

// readJWKS 는 JWKS 파일에서 kid → 공개 키를 읽는다.
// 이 책의 키는 Ed25519(OKP) 뿐이라 그것만 읽는다.
func readJWKS(path string) map[string]crypto.PublicKey {
	raw, err := os.ReadFile(path)
	check(err)
	var jwks struct {
		Keys []struct{ Kid, Kty, Crv, X string }
	}
	check(json.Unmarshal(raw, &jwks))
	keys := map[string]crypto.PublicKey{}
	for _, k := range jwks.Keys {
		x, err := base64.RawURLEncoding.DecodeString(k.X)
		if err == nil && k.Kty == "OKP" && k.Crv == "Ed25519" {
			keys[k.Kid] = ed25519.PublicKey(x)
		}
	}
	return keys
}

// region: discover
// pinnedKeys: 카드 서명은 미리 받아 둔 공개 키로만 검증한다.
// 카드 안의 jku 를 따라가 키를 받으면, 카드를 위조한 쪽이 자기 키를
// 가리키게 할 수 있다 — 그래서 jku 는 보지 않는다(KeyResolverFunc
// 는 kid 만 받는다).
func pinnedKeys() a2acrypto.KeyResolverFunc {
	keys := readJWKS(workshop.FixturePath("keys/jwks.json"))
	return func(_ context.Context, kid string) (
		crypto.PublicKey, error) {
		if k, ok := keys[kid]; ok {
			return k, nil
		}
		return nil, fmt.Errorf("모르는 키: %s", kid)
	}
}

// discover 는 카드를 읽어 역할별로 하나씩 고른다. 서명이 있으면
// 리졸버가 받은 바이트 그대로 검증한다 — 틀리면 오류, 위조 카드는
// 쓰지 않는다. 카드를 못 받거나 서명이 틀린 주소는 건너뛴다 — 그
// 역할이 비면 plan 이 맡기기 전에 알린다. 주소는 서버 기록에만.
func discover(ctx context.Context,
	urls []string) map[string]*a2a.AgentCard {
	r := agentcard.NewResolver(common.HTTPClient(""))
	r.Verifier = a2acrypto.NewVerifier(
		a2acrypto.VerifierConfig{KeyResolver: pinnedKeys()})
	found := map[string]*a2a.AgentCard{}
	for _, u := range urls {
		c, err := r.Resolve(ctx, u)
		if err != nil {
			common.Say("[기획] 카드를 쓸 수 없어 건너뜁니다: %s", u)
			continue
		}
		var tags []string
		for _, s := range c.Skills {
			tags = append(tags, s.Tags...)
		}
		for _, rt := range roles {
			_, taken := found[rt[0]]
			if slices.Contains(tags, rt[1]) && !taken {
				found[rt[0]] = c
			}
		}
	}
	return found
}

// endregion

// region: lost
// 사용자에게 알릴 때 쓰는 역할 이름
var labelOf = map[string]string{
	"lodging": "숙소", "meals": "식사", "bus": "교통", "settle": "정산",
}

// lostRoles 는 찾지 못한 역할의 이름들이다(역할표 차례). 비었으면
// 넷 다 찾았다 — 이 검사 뒤로는 cards[역할] 이 nil 일 수 없다.
func lostRoles(cards map[string]*a2a.AgentCard) []string {
	var lost []string
	for _, rt := range roles {
		if cards[rt[0]] == nil {
			lost = append(lost, labelOf[rt[0]])
		}
	}
	return lost
}

// endregion

// region: delegate
// send 는 막는 호출 하나로 보내고 끝(또는 멈춤) 상태의 Task 를 받는다.
func send(ctx context.Context, c *a2a.AgentCard, m *a2a.Message,
	token string) (*a2a.Task, error) {
	client, err := a2aclient.NewFromCard(ctx, c,
		a2aclient.WithJSONRPCTransport(common.HTTPClient(token)))
	if err != nil {
		return nil, err
	}
	defer client.Destroy()
	res, err := client.SendMessage(ctx,
		&a2a.SendMessageRequest{Message: m})
	if err != nil {
		return nil, err
	}
	if t, ok := res.(*a2a.Task); ok {
		return t, nil
	}
	return nil, fmt.Errorf("Task 대신 Message 가 왔습니다")
}

// delegate 는 같은 contextId 로 묶어 맡긴다. refs 는 근거가 된 작업들.
func delegate(ctx context.Context, c *a2a.AgentCard, data any,
	contextID, token string, refs ...a2a.TaskID) (*a2a.Task, error) {
	m := a2a.NewMessage(a2a.MessageRoleUser, common.DataPart(data))
	m.ContextID, m.ReferenceTasks = contextID, refs
	return send(ctx, c, m, token)
}

// followUp 은 멈춘 작업에 같은 taskId·contextId 로 한마디 더 한다.
func followUp(ctx context.Context, c *a2a.AgentCard, t *a2a.Task,
	text, token string) (*a2a.Task, error) {
	m := a2a.NewMessage(a2a.MessageRoleUser, common.TextPart(text))
	m.TaskID, m.ContextID = t.ID, t.ContextID
	return send(ctx, c, m, token)
}

// endregion

// region: token
// getToken 은 카드의 securitySchemes 에서 토큰 주소를 찾아 토큰을
// 받는다.
func (e *executor) getToken(c *a2a.AgentCard, scope string) (
	string, error) {
	oauth, _ := c.SecuritySchemes["oauth"].(a2a.OAuth2SecurityScheme)
	flow, ok := oauth.Flows.(a2a.ClientCredentialsOAuthFlow)
	if !ok {
		return "", fmt.Errorf("client-credentials 흐름이 없습니다")
	}
	r, err := http.PostForm(flow.TokenURL, url.Values{
		"grant_type":    {"client_credentials"},
		"client_id":     {e.clientID},
		"client_secret": {e.secret},
		"scope":         {scope},
	})
	if err != nil {
		return "", err
	}
	defer r.Body.Close()
	if r.StatusCode != http.StatusOK {
		return "", fmt.Errorf("토큰 발급 실패: %s", r.Status)
	}
	var body struct {
		AccessToken string `json:"access_token"`
	}
	err = json.NewDecoder(r.Body).Decode(&body)
	return body.AccessToken, err
}

// endregion

// region: withdraw
// withdraw 는 결재를 받지 못한 정산 작업을 거둔다(CancelTask).
// 거두지 않으면 정산 쪽의 작업은 AUTH_REQUIRED 로 영원히 남는다.
// 거두지 못해도 반려는 반려다 — 서버 기록에만 남긴다.
func (e *executor) withdraw(ctx context.Context, c *a2a.AgentCard,
	settle *a2a.Task) {
	token, err := e.getToken(c, "payment:read")
	var client *a2aclient.Client
	if err == nil {
		client, err = a2aclient.NewFromCard(ctx, c,
			a2aclient.WithJSONRPCTransport(common.HTTPClient(token)))
	}
	var done *a2a.Task
	if err == nil {
		defer client.Destroy()
		done, err = client.CancelTask(ctx,
			&a2a.CancelTaskRequest{ID: settle.ID})
	}
	if err != nil {
		common.Say("[기획] 정산 작업을 거두지 못했습니다")
		return
	}
	common.Say("[기획] 정산 작업을 거뒀습니다: %s", done.Status.State)
}

// endregion

// quoteOf 는 완료된 Task 의 첫 DataPart(견적)를 꺼낸다.
func quoteOf(t *a2a.Task) map[string]any {
	for _, a := range t.Artifacts {
		for _, p := range a.Parts {
			if d, ok := p.Data().(map[string]any); ok {
				return d
			}
		}
	}
	return nil
}

func won(v any) string { return common.Comma(common.Int(v)) + "원" }

func planMarkdown(req workshop.Parsed, quotes []map[string]any,
	sheet map[string]any) string {
	lodging, meals, bus := quotes[0], quotes[1], quotes[2]
	slots, _ := meals["slots"].([]any)
	return strings.Join([]string{
		"# 보물상사 가을 워크숍 계획서",
		"",
		fmt.Sprintf("- 일정: %s부터 %d박", req.Date, req.Nights),
		fmt.Sprintf("- 인원: %d명(채식 %d명)",
			req.Headcount, req.Vegetarians),
		fmt.Sprintf("- 숙소: %s %d실 — %s", lodging["venueName"],
			common.Int(lodging["rooms"]), won(lodging["total"])),
		fmt.Sprintf("- 식사: %d끼 — %s", len(slots),
			won(meals["total"])),
		fmt.Sprintf("- 교통: %d일 — %s", common.Int(bus["days"]),
			won(bus["total"])),
		fmt.Sprintf("- 합계: %s / 예산 %s (남음 %s)",
			won(sheet["total"]), won(sheet["budget"]),
			won(sheet["remaining"])),
		fmt.Sprintf("- 결재: %s", sheet["approvedBy"]),
		"",
	}, "\n")
}

type executor struct {
	urls             []string
	clientID, secret string
	// 파이썬판은 결재를 기다리는 작업을 사전에 적어 두고 새 실행에서
	// 꺼내지만, Go SDK 에서는 실행이 멈춘 채 기다리므로(park.go) 필요
	// 한 것은 모두 이 실행의 지역 변수에 그대로 남아 있다.
}

// region: say
func (e *executor) say(up *common.Updater, state a2a.TaskState,
	text string) bool {
	common.Say("[기획] %s", text)
	return up.Status(state, common.TextPart(text))
}

// endregion

// region: cannot
// cannot 은 동료에게 맡기지 못한 일을 FAILED 로 끝낸다. 까닭은 역할
// 이름까지만 싣는다 — 오류 글에는 안쪽 명단·카드의 주소가 들어 있다.
func (e *executor) cannot(up *common.Updater, label string) {
	e.say(up, a2a.TaskStateFailed,
		label+" 에이전트에게 맡기지 못했습니다")
}

// endregion

// region: parse
func (e *executor) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		task, up, ok := common.Begin(ec, yield)
		if !ok {
			return
		}
		var said []string // 사용자가 지금까지 한 말 전부
		for _, m := range task.History {
			if m.Role == a2a.MessageRoleUser {
				said = append(said, common.TextOf(m))
			}
		}
		req, miss := workshop.ParseRequest(strings.Join(said, " "))
		var missing []string
		if miss != nil {
			missing = miss.Missing
		} else if req.Budget == nil {
			missing = []string{"budget"}
		}
		if len(missing) > 0 {
			var what []string
			for _, k := range missing {
				what = append(what, ask[k])
			}
			up.Status(a2a.TaskStateInputRequired,
				common.TextPart("알려 주세요: "+
					strings.Join(what, ", ")),
				common.DataPart(map[string]any{"missing": missing}))
			return
		}
		e.plan(ctx, up, task, req) // 실패도 plan 이 상태로 알린다
	}
}

// endregion

// region: fan
// fanOut 은 숙소·식사·교통에 동시에 맡기고 셋이 다 끝나길 기다린다.
// 결과와 오류는 미리 정한 자리(i)에 넣는다 — 도착 순서와 상관없이.
func fanOut(ctx context.Context, cards map[string]*a2a.AgentCard,
	req workshop.Parsed, contextID string) ([]*a2a.Task, []error) {
	tasks, errs := make([]*a2a.Task, 3), make([]error, 3)
	var wg sync.WaitGroup
	for i, role := range []string{"lodging", "meals", "bus"} {
		wg.Go(func() {
			// wg.Go 의 함수는 패닉하면 안 된다 — 아무도 받지 않아
			// 프로세스가 통째로 끝난다. 패닉도 그 자리의 오류로.
			defer func() {
				if r := recover(); r != nil {
					errs[i] = fmt.Errorf("패닉: %v", r)
				}
			}()
			tasks[i], errs[i] = delegate(ctx, cards[role], req,
				contextID, "")
		})
	}
	wg.Wait()
	return tasks, errs
}

// endregion

// region: plan
func (e *executor) plan(ctx context.Context, up *common.Updater,
	task *a2a.Task, req workshop.Parsed) {
	e.say(up, working, "동료 에이전트를 찾는 중")
	cards := discover(ctx, e.urls)
	e.say(up, working, fmt.Sprintf("에이전트 %d곳을 찾았습니다",
		len(cards)))
	if lost := lostRoles(cards); len(lost) > 0 { // 맡기기 전에
		e.say(up, a2a.TaskStateFailed,
			"동료를 찾지 못했습니다: "+strings.Join(lost, ", "))
		return
	}
	// 세 곳에 동시에 맡긴다. 도착 순서는 매번 다를 수 있으므로
	// 알릴 때는 정한 순서대로 알린다.
	labels := []string{"숙소", "식사", "교통"}
	tasks, errs := fanOut(ctx, cards, req, task.ContextID)
	var quotes, items []map[string]any
	for i, t := range tasks {
		if errs[i] != nil {
			e.cannot(up, labels[i])
			return
		}
		if t.Status.State != a2a.TaskStateCompleted {
			why := common.TextOf(t.Status.Message)
			common.Say("[기획] %s 실패: %s", labels[i], why)
			up.Status(a2a.TaskStateRejected,
				common.TextPart(labels[i]+": "+why))
			return
		}
		q := quoteOf(t)
		e.say(up, working, fmt.Sprintf("%s 견적 %s",
			labels[i], won(q["total"])))
		quotes = append(quotes, q)
		items = append(items, map[string]any{
			"name": labels[i], "amount": common.Int(q["total"]),
		})
	}
	e.settle(ctx, up, task, req, cards["settle"], tasks, quotes,
		items)
}

// endregion

// region: settle
func (e *executor) settle(ctx context.Context, up *common.Updater,
	task *a2a.Task, req workshop.Parsed, c *a2a.AgentCard,
	refs []*a2a.Task, quotes, items []map[string]any) {
	token, err := e.getToken(c, "payment:read")
	if err != nil {
		e.cannot(up, "정산")
		return
	}
	data := map[string]any{"items": items, "budget": *req.Budget}
	settle, err := delegate(ctx, c, data, task.ContextID, token,
		refs[0].ID, refs[1].ID, refs[2].ID)
	if err != nil {
		e.cannot(up, "정산")
		return
	}
	if settle.Status.State == a2a.TaskStateAuthRequired {
		total := 0
		for _, it := range items {
			total += it["amount"].(int)
		}
		note := fmt.Sprintf("팀장 결재가 필요합니다(합계 %s원). "+
			"'승인'이라고 답하면 결재를 진행합니다.",
			common.Comma(total))
		common.Say("[기획] %s", note)
		r, ok := up.AwaitReply(ctx, common.TextPart(note))
		if !ok {
			return
		}
		if !strings.Contains(common.TextOf(r.Msg), "승인") {
			// 정산 쪽에서 기다리던 작업도 거둔다 — 반려를 알리기 전에
			e.withdraw(ctx, c, settle)
			e.say(up, a2a.TaskStateRejected, "결재가 반려되어 멈춥니다")
			return
		}
		// 결재 토큰도 문지기를 지나니 payment:read 도 받는다
		token, err := e.getToken(c, "payment:read payment:approve")
		if err != nil {
			e.cannot(up, "정산")
			return
		}
		settle, err = followUp(ctx, c, settle, "결재합니다", token)
		if err != nil {
			e.cannot(up, "정산")
			return
		}
	}
	e.finish(up, req, quotes, settle)
}

// endregion

// region: finish
func (e *executor) finish(up *common.Updater, req workshop.Parsed,
	quotes []map[string]any, settle *a2a.Task) {
	if settle.Status.State != a2a.TaskStateCompleted {
		why := common.TextOf(settle.Status.Message)
		up.Status(a2a.TaskStateRejected,
			common.TextPart("정산: "+why))
		return
	}
	sheet := quoteOf(settle)
	doc := &a2a.Part{
		Content:   a2a.Text(planMarkdown(req, quotes, sheet)),
		MediaType: "text/markdown",
	}
	summary := common.Plain(req).(map[string]any)
	summary["total"] = common.Int(sheet["total"])
	up.Artifact("워크숍 계획서", common.Chunk{ID: "workshop-plan"},
		doc, common.DataPart(summary))
	e.say(up, a2a.TaskStateWorking, "계획서를 완성했습니다")
	up.Status(a2a.TaskStateCompleted)
}

// endregion

func (e *executor) Cancel(
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
	agents := flag.String("agents", "", "쉼표로 구분한 URL(필수)")
	id := flag.String("client-id", "planner", "OAuth2 클라이언트")
	secret := flag.String("client-secret", "planner-secret",
		"OAuth2 비밀")
	args := common.ParseArgs("보물상사 기획 에이전트")
	if *agents == "" {
		fmt.Fprintln(os.Stderr, "--agents 가 필요합니다")
		os.Exit(2)
	}
	e := &executor{strings.Split(*agents, ","), *id, *secret}
	common.Serve(card(args.URL), e, args.Port, common.Options{})
}
