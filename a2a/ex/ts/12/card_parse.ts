// 보안 요구를 적는 세 가지 꼴을 SDK 의 카드 리졸버에 넣어 본다.
// fetchImpl 로 받은 셈 치는 JSON 을 건넨다(연결은 없다).
//   ① v1.0 proto 꼴   ② 목록을 StringList 로 싸지 않은 꼴
//   ③ 스펙 §8.5 예시의 꼴("security", OpenAPI 와 같은 모양)
import { DefaultAgentCardResolver } from "@a2a-js/sdk/client";

const OAUTH = {
  oauth2SecurityScheme: {
    flows: {
      clientCredentials: {
        tokenUrl: "https://127.0.0.1/oauth/token",
        scopes: { "payment:read": "정산 조회" },
      },
    },
  },
};
const READ = ["payment:read"];
const FORMS: Record<string, object> = {
  "①": {
    securityRequirements: [{ schemes: { oauth: { list: READ } } }],
  },
  "②": { securityRequirements: [{ schemes: { oauth: READ } }] },
  "③": { security: [{ oauth: READ }] },
};

// region: parse
for (const [mark, form] of Object.entries(FORMS)) {
  const card = {
    name: "정산",
    securitySchemes: { oauth: OAUTH },
    ...form,
  };
  const fetchImpl = async () => Response.json(card);
  const resolver = new DefaultAgentCardResolver({ fetchImpl });
  const c = await resolver.resolve("http://127.0.0.1/");
  const reqs = (c.securityRequirements ?? []).map((r) =>
    Object.fromEntries(
      Object.entries(r.schemes).map(([k, v]) => [k, v.list]),
    ),
  );
  console.log(`${mark} 요구 ${reqs.length}개 ${JSON.stringify(reqs)}`);
}
// endregion
