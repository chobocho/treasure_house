// 정산 에이전트의 공개 카드와 확장 카드를 SDK 클라이언트로 견준다 —
// intern 토큰으로 확장 카드를 받고, 클라이언트가 들고 있는 카드가
// 바뀌는지 본다.
//   node 12/xcard.ts 에이전트주소
import type { AgentCard } from "@a2a-js/sdk";
import {
  ClientFactory,
  DefaultAgentCardResolver,
  JsonRpcTransportFactory,
  createAuthenticatingFetchWithRetry,
} from "@a2a-js/sdk/client";

function show(label: string, card: AgentCard) {
  const skills = card.skills.map((s) => s.id).join(", ");
  const n = card.signatures.length;
  console.log(`${label}: 스킬 [${skills}] · 서명 ${n}개`);
}

async function token(card: AgentCard, cid: string, secret: string) {
  const scheme = card.securitySchemes["oauth"]?.scheme;
  if (scheme?.$case !== "oauth2SecurityScheme") throw Error("oauth?");
  const flow = scheme.value.flows?.flow;
  if (flow?.$case !== "clientCredentials") throw Error("flow?");
  const body = new URLSearchParams({
    ...{ grant_type: "client_credentials", client_id: cid },
    client_secret: secret,
  });
  const r = await fetch(flow.value.tokenUrl, { method: "POST", body });
  return ((await r.json()) as { access_token: string }).access_token;
}

// region: main
const card = await new DefaultAgentCardResolver().resolve(
  process.argv[2]!,
);
show("① 공개 카드", card);
const t = await token(card, "intern", "intern-secret");
const fetchImpl = createAuthenticatingFetchWithRetry(fetch, {
  headers: async () => ({ Authorization: `Bearer ${t}` }),
  shouldRetryWithHeaders: async () => undefined,
});
const client = await new ClientFactory({
  transports: [new JsonRpcTransportFactory({ fetchImpl })],
}).createFromAgentCard(card);
// 확장 카드를 따로 부르는 메서드는 없다 — getAgentCard 가 카드의
// extendedAgentCard 를 보고 GetExtendedAgentCard 를 부른다.
show("② 확장 카드", await client.getAgentCard());
// private 필드지만, 클라이언트가 이제 어느 카드를 쓰는지 보려고
const held = (client as unknown as { agentCard: AgentCard }).agentCard;
show("③ 클라이언트의 카드", held);
// endregion
//@ norun
