// 보안 요구의 AND 와 OR — Go SDK 의 AuthInterceptor 는 헤더를 몇 개
// 다나. 자격 증명은 둘(oauth 토큰, API 키) 다 쥐여 준다. 연결은 없다 —
// 인터셉터의 Before 만 불러 본다. 맵을 도는 차례가 부를 때마다 달라
// 200번 불러 나온 결과를 모은다.
package main

import (
	"context"
	"fmt"
	"maps"
	"slices"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
)

var schemes = a2a.NamedSecuritySchemes{
	"oauth": a2a.OAuth2SecurityScheme{
		Flows: a2a.ClientCredentialsOAuthFlow{}},
	"key": a2a.APIKeySecurityScheme{
		Location: a2a.APIKeySecuritySchemeLocationHeader,
		Name:     "X-Api-Key"},
}

var cases = []struct {
	name string
	reqs a2a.SecurityRequirementsOptions
}{
	{"AND(요구 하나에 스킴 둘)", a2a.SecurityRequirementsOptions{
		{"oauth": {}, "key": {}}}},
	{"OR(스킴 하나씩 요구 둘)", a2a.SecurityRequirementsOptions{
		{"oauth": {}}, {"key": {}}}},
}

// region: main
func main() {
	store := a2aclient.NewInMemoryCredentialsStore()
	store.Set("s1", "oauth", "tok-planner-1")
	store.Set("s1", "key", "key-123")
	auth := &a2aclient.AuthInterceptor{Service: store}
	ctx := a2aclient.AttachSessionID(context.Background(), "s1")
	for _, c := range cases {
		card := &a2a.AgentCard{
			SecuritySchemes: schemes, SecurityRequirements: c.reqs}
		seen := []string{}
		for range 200 {
			req := &a2aclient.Request{
				Card: card, ServiceParams: a2aclient.ServiceParams{}}
			_, _, _ = auth.Before(ctx, req)
			keys := slices.Sorted(maps.Keys(req.ServiceParams))
			got := strings.Join(keys, "+")
			if !slices.Contains(seen, got) {
				seen = append(seen, got)
			}
		}
		slices.Sort(seen)
		fmt.Printf("%s → 200번 중 나온 헤더 %v\n", c.name, seen)
	}
}

// endregion
