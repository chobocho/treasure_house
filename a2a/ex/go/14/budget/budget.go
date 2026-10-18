// Package budget 는 이 책의 예산 확장(budget/v1)이다. 완성 에이전트의
// 카드에 확장을 적고(Declare), 실행기를 감싸(Wrap) 아티팩트에 예산
// 판정을 덧붙인다. 에이전트 코드는 고치지 않는다.
package budget

import (
	"context"
	"fmt"
	"iter"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
)

const URI = "https://treasure-house.example/a2a/ext/budget/v1"

// region: declare
// Declare 는 카드의 Capabilities.Extensions 에 예산 확장을 적는다.
func Declare(card *a2a.AgentCard, required bool) {
	card.Capabilities.Extensions = append(card.Capabilities.Extensions,
		a2a.AgentExtension{
			URI:         URI,
			Description: "예산 상한(원)을 받아 견적과 견줍니다.",
			Required:    required,
			Params:      map[string]any{"currency": "KRW"},
		})
}

// endregion

// region: mark
// mark 는 지나가는 아티팩트에 예산 판정을 덧붙인다.
func mark(ev a2a.Event, limit float64) {
	e, ok := ev.(*a2a.TaskArtifactUpdateEvent)
	if !ok {
		return
	}
	data, _ := e.Artifact.Parts[0].Data().(map[string]any)
	total, _ := data["total"].(float64)
	e.Artifact.Extensions = append(e.Artifact.Extensions, URI)
	if e.Artifact.Metadata == nil {
		e.Artifact.Metadata = map[string]any{}
	}
	e.Artifact.Metadata[URI] = map[string]any{
		"limit": limit, "within": total <= limit,
	}
}

// endregion

// region: executor
type executor struct{ inner a2asrv.AgentExecutor }

func Wrap(inner a2asrv.AgentExecutor) a2asrv.AgentExecutor {
	return executor{inner}
}

func (b executor) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	// required 인데 머리글이 없으면 SDK 가 여기 오기 전에 막았다
	// (WithCapabilityChecks 가 준 카드의 확장 목록으로).
	ext, _ := a2asrv.ExtensionsFrom(ctx)
	if !ext.Requested(&a2a.AgentExtension{URI: URI}) {
		return b.inner.Execute(ctx, ec)
	}
	meta, _ := ec.Message.Metadata[URI].(map[string]any)
	limit, ok := meta["limit"].(float64)
	if !ok {
		return func(yield func(a2a.Event, error) bool) {
			err := fmt.Errorf("예산 확장: limit 이 없습니다: %w",
				a2a.ErrInvalidParams)
			yield(nil, err)
		}
	}
	ext.Activate(&a2a.AgentExtension{URI: URI}) // gRPC 에서만 알린다
	return func(yield func(a2a.Event, error) bool) {
		for ev, err := range b.inner.Execute(ctx, ec) {
			mark(ev, limit)
			if !yield(ev, err) {
				return
			}
		}
	}
}

func (b executor) Cancel(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return b.inner.Cancel(ctx, ec)
}

// endregion
