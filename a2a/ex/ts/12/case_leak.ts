// 보안 스킴이 든 카드를 ts-proto 객체로 읽은 뒤 JSON.stringify 하면
// 와이어에 무엇이 나가나 — SDK 의 agentCardHandler 가 하는 일이 바로
// JSON.stringify 다(3부). toJSON 을 거친 것과 견준다.
import { AgentCard } from "@a2a-js/sdk";

const wire = {
  securitySchemes: {
    oauth: {
      oauth2SecurityScheme: {
        flows: {
          clientCredentials: {
            tokenUrl: "http://127.0.0.1/oauth/token",
            scopes: { "payment:read": "정산 조회" },
          },
        },
      },
    },
  },
};

// region: leak
const typed = AgentCard.fromJSON(wire);
console.log("JSON.stringify(ts-proto 객체):");
console.log(JSON.stringify(typed.securitySchemes, null, 1));
console.log("AgentCard.toJSON 을 거치면:");
const back = AgentCard.toJSON(typed) as typeof wire;
console.log(JSON.stringify(back.securitySchemes, null, 1));
// endregion
