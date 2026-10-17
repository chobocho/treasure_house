package steps

import (
	"context"
	"encoding/json"
	"iter"
	"maps"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/workshop"
)

// Quote 는 2단계 — DataPart 로 받은 조건으로 숙소 견적을 낸다.
type Quote struct{}

// region: quote
func (Quote) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		// ① Task 를 먼저 — 받는 쪽이 그만 받겠다면(false) 멈춘다
		if !yield(a2a.NewSubmittedTask(ec, ec.Message), nil) {
			return
		}
		working := a2a.NewStatusUpdateEvent(ec,
			a2a.TaskStateWorking, nil)
		if !yield(working, nil) { // ② WORKING
			return
		}
		quote, fail := workshop.ChooseLodging(RequestOf(ec.Message))
		if fail != nil { // ③ 거절 — 까닭을 상태 메시지로
			why := a2a.NewMessageForTask(a2a.MessageRoleAgent, ec,
				a2a.NewTextPart(fail.Reason))
			yield(a2a.NewStatusUpdateEvent(ec,
				a2a.TaskStateRejected, why), nil)
			return
		}
		// ③ 견적은 아티팩트로(JSON 모양으로 바꿔서 — 4장), 그다음 끝
		art := a2a.NewArtifactEvent(ec, a2a.NewDataPart(Plain(quote)))
		art.Artifact.Name = "숙소 견적"
		if !yield(art, nil) {
			return
		}
		yield(a2a.NewStatusUpdateEvent(ec,
			a2a.TaskStateCompleted, nil), nil)
	}
}

// endregion

// Cancel — 멈출 일이 없다(Execute 는 곧바로 끝난다). CANCELED 만.
func (Quote) Cancel(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		yield(a2a.NewStatusUpdateEvent(ec,
			a2a.TaskStateCanceled, nil), nil)
	}
}

// region: request
// RequestOf 는 DataPart 들을 앞에서부터 합쳐 구조체로 읽는다.
// 받은 수는 float64 라서(2장) JSON 을 한 번 거쳐 int 칸에 넣는다.
func RequestOf(m *a2a.Message) workshop.LodgingRequest {
	merged := map[string]any{}
	for _, p := range m.Parts {
		if d, ok := p.Data().(map[string]any); ok {
			maps.Copy(merged, d)
		}
	}
	var req workshop.LodgingRequest
	b, _ := json.Marshal(merged)
	_ = json.Unmarshal(b, &req) // 모자라면 영값 — 규칙이 거절한다
	return req
}

// endregion

// region: plain
// Plain 은 값을 JSON 의 모양(map·[]any·float64)으로 바꾼다. SDK 의
// 저장소는 gob 으로 사본을 뜨는데, 등록하지 않은 구조체가 DataPart 에
// 있으면 거기서 실패해 작업이 FAILED 가 된다.
func Plain(v any) any {
	var out any
	b, _ := json.Marshal(v)
	_ = json.Unmarshal(b, &out)
	return out
}

// endregion

// QuoteCard 는 견적 에이전트의 카드다.
func QuoteCard(url string) *a2a.AgentCard {
	return &a2a.AgentCard{
		Name:        "보물상사 견적 에이전트",
		Description: "날짜·박 수·인원으로 숙소 견적을 냅니다.",
		Version:     "0.2.0",
		SupportedInterfaces: []*a2a.AgentInterface{
			a2a.NewAgentInterface(url, a2a.TransportProtocolJSONRPC),
		},
		DefaultInputModes:  []string{"application/json"},
		DefaultOutputModes: []string{"application/json"},
		Skills: []a2a.AgentSkill{{
			ID: "quote-lodging", Name: "숙소 견적",
			Tags:        []string{"lodging"},
			Description: "DataPart 의 조건에 맞는 숙소를 고릅니다.",
		}},
	}
}
