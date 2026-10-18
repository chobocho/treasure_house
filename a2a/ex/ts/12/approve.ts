// 큰 정산을 조회 토큰으로 맡겨 AUTH_REQUIRED 를 받고, 결재 스코프가
// 든 새 토큰으로 같은 작업에 이어 말해 끝낸다. SDK 클라이언트 하나,
// fetch 가 다는 토큰만 바꾼다.
//   node 12/approve.ts 에이전트주소
import {
  Message,
  taskStateToJSON,
  type AgentCard,
  type Task,
} from "@a2a-js/sdk";
import {
  ClientFactory,
  DefaultAgentCardResolver,
  JsonRpcTransportFactory,
  createAuthenticatingFetchWithRetry,
} from "@a2a-js/sdk/client";

const BIG = {
  items: [
    { name: "숙소", amount: 2100000 },
    { name: "식사", amount: 1542000 },
    { name: "교통", amount: 1200000 },
  ],
  budget: 6000000,
};

async function token(card: AgentCard, scope: string) {
  const scheme = card.securitySchemes["oauth"]?.scheme;
  if (scheme?.$case !== "oauth2SecurityScheme") throw Error("oauth?");
  const flow = scheme.value.flows?.flow;
  if (flow?.$case !== "clientCredentials") throw Error("flow?");
  const body = new URLSearchParams({
    ...{ grant_type: "client_credentials", client_id: "planner" },
    ...{ client_secret: "planner-secret", scope },
  });
  const r = await fetch(flow.value.tokenUrl, { method: "POST", body });
  return ((await r.json()) as { access_token: string }).access_token;
}

function text(m: Message | undefined) {
  const c = m?.parts[0]?.content;
  return c?.$case === "text" ? c.value : "";
}

// region: main
const card = await new DefaultAgentCardResolver().resolve(
  process.argv[2]!,
);
let current = ""; // fetch 가 매번 이 토큰을 단다
const fetchImpl = createAuthenticatingFetchWithRetry(fetch, {
  headers: async () => ({ Authorization: `Bearer ${current}` }),
  shouldRetryWithHeaders: async () => undefined,
});
const client = await new ClientFactory({
  transports: [new JsonRpcTransportFactory({ fetchImpl })],
}).createFromAgentCard(card);
const send = async (m: object) =>
  (await client.sendMessage({
    ...{ tenant: "", message: Message.fromJSON(m) },
    ...{ configuration: undefined, metadata: {} },
  })) as Task;

current = await token(card, "payment:read");
let task = await send({
  ...{ messageId: "a-1", role: "ROLE_USER" },
  parts: [{ data: BIG }],
});
console.log(`① ${current} → ${taskStateToJSON(task.status!.state)}`);
console.log(`   ${text(task.status!.message)}`);
current = await token(card, "payment:read payment:approve");
task = await send({
  ...{ messageId: "a-2", role: "ROLE_USER", taskId: task.id },
  ...{ contextId: task.contextId, parts: [{ text: "결재합니다" }] },
});
const c = task.artifacts[0]?.parts[0]?.content;
const sheet = c?.$case === "data" ? c.value : {};
const state = taskStateToJSON(task.status!.state);
console.log(
  `② ${current} → ${state}, approvedBy ${sheet["approvedBy"]}`,
);
// endregion
//@ norun
