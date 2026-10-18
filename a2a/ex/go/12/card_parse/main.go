// 보안 요구를 적는 세 가지 꼴을 SDK 의 카드 해석(agentcard.Resolver 가
// 받은 몸통에 쓰는 json.Unmarshal)에 넣어 본다.
//
//	① v1.0 proto 꼴   ② 목록을 StringList 로 싸지 않은 꼴
//	③ 스펙 §8.5 예시의 꼴("security", OpenAPI 와 같은 모양)
package main

import (
	"encoding/json"
	"fmt"

	"github.com/a2aproject/a2a-go/v2/a2a"
)

const oauth = `"securitySchemes": {"oauth": {"oauth2SecurityScheme":
  {"flows": {"clientCredentials": {
    "tokenUrl": "https://127.0.0.1/oauth/token",
    "scopes": {"payment:read": "정산 조회"}}}}}}`

var forms = [][2]string{
	{"①", `"securityRequirements":
	  [{"schemes": {"oauth": {"list": ["payment:read"]}}}]`},
	{"②", `"securityRequirements":
	  [{"schemes": {"oauth": ["payment:read"]}}]`},
	{"③", `"security": [{"oauth": ["payment:read"]}]`},
}

// region: parse
func main() {
	for _, f := range forms {
		raw := `{"name": "정산", ` + oauth + `, ` + f[1] + `}`
		var c a2a.AgentCard
		if err := json.Unmarshal([]byte(raw), &c); err != nil {
			fmt.Println(f[0], "오류", err)
			continue
		}
		reqs := []map[a2a.SecuritySchemeName]a2a.SecuritySchemeScopes{}
		for _, r := range c.SecurityRequirements {
			reqs = append(reqs, r)
		}
		fmt.Printf("%s 요구 %d개 %v\n", f[0], len(reqs), reqs)
	}
}

// endregion
