# 보안 요구를 적는 세 가지 꼴을 SDK 의 카드 해석(parse_agent_card —
# A2ACardResolver 가 받은 JSON 에 쓰는 것)에 넣어 본다.
#   ① v1.0 proto 꼴   ② 목록을 StringList 로 싸지 않은 꼴
#   ③ 스펙 §8.5 예시의 꼴("security", OpenAPI 와 같은 모양)
from a2a.client.card_resolver import parse_agent_card

OAUTH = {
    "oauth2SecurityScheme": {
        "flows": {
            "clientCredentials": {
                "tokenUrl": "https://127.0.0.1/oauth/token",
                "scopes": {"payment:read": "정산 조회"},
            }
        }
    }
}
FORMS = {
    "①": {
        "securityRequirements": [
            {"schemes": {"oauth": {"list": ["payment:read"]}}}
        ]
    },
    "②": {
        "securityRequirements": [
            {"schemes": {"oauth": ["payment:read"]}}
        ]
    },
    "③": {"security": [{"oauth": ["payment:read"]}]},
}

# region: parse
for mark, form in FORMS.items():
    card = {"name": "정산", "securitySchemes": {"oauth": OAUTH}, **form}
    c = parse_agent_card(card)
    reqs = [
        {k: list(v.list) for k, v in r.schemes.items()}
        for r in c.security_requirements
    ]
    print(f"{mark} 요구 {len(reqs)}개 {reqs}")
# endregion
