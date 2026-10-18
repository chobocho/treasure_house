// 정산 에이전트를 SDK 클라이언트로 부른다 — 토큰 없이 한 번, 그다음
// 401 을 받으면 카드의 tokenUrl 에서 토큰을 받아 다시 보내는 fetch 로.
//   node 12/settle_client.ts 에이전트주소 client_id client_secret
import { Message, taskStateToJSON, type Task } from "@a2a-js/sdk";
import {
  ClientFactory,
  DefaultAgentCardResolver,
  JsonRpcTransportFactory,
  createAuthenticatingFetchWithRetry,
  type AuthenticationHandler,
  type HttpHeaders,
} from "@a2a-js/sdk/client";

const [url, clientId, secret] = process.argv.slice(2) as string[];
const SMALL = {
  items: [{ name: "숙소", amount: 2100000 }],
  budget: 6000000,
};

function request(messageId: string) {
  const message = Message.fromJSON({
    ...{ messageId, role: "ROLE_USER" },
    parts: [{ data: SMALL }],
  });
  return {
    tenant: "",
    message,
    configuration: undefined,
    metadata: {},
  };
}

const card = await new DefaultAgentCardResolver().resolve(url!);
const scheme = card.securitySchemes["oauth"]?.scheme;
if (scheme?.$case !== "oauth2SecurityScheme") throw Error("no oauth");
const flow = scheme.value.flows?.flow;
if (flow?.$case !== "clientCredentials") throw Error("no flow");
const tokenUrl = flow.value.tokenUrl;

// region: token
async function getToken(): Promise<string> {
  const body = new URLSearchParams({
    ...{ grant_type: "client_credentials", client_id: clientId! },
    client_secret: secret!,
  });
  const r = await fetch(tokenUrl, { method: "POST", body });
  if (!r.ok) throw Error(`토큰 발급 ${r.status}`);
  return ((await r.json()) as { access_token: string }).access_token;
}

let token = "";
const handler: AuthenticationHandler = {
  headers: async (): Promise<HttpHeaders> =>
    token ? { Authorization: `Bearer ${token}` } : {},
  shouldRetryWithHeaders: async (_req, res) => {
    if (res.status !== 401) return undefined;
    const t = await getToken(); // 401 을 본 뒤에야 받으러 간다
    console.log(`② 401 을 보고 받은 토큰 ${t}`);
    return { Authorization: `Bearer ${t}` };
  },
  onSuccessfulRetry: async (h) => {
    token = h.Authorization!.slice("Bearer ".length);
  },
};
// endregion

// region: main
const plain = await new ClientFactory().createFromAgentCard(card);
try {
  await plain.sendMessage(request("ts-1"));
} catch (e) {
  const err = e as Error;
  console.log(`① 토큰 없이 → ${err.constructor.name}:`, err.message);
}
const fetchImpl = createAuthenticatingFetchWithRetry(fetch, handler);
const client = await new ClientFactory({
  transports: [new JsonRpcTransportFactory({ fetchImpl })],
}).createFromAgentCard(card);
const task = (await client.sendMessage(request("ts-2"))) as Task;
const part = task.artifacts[0]?.parts[0]?.content;
const sheet = part?.$case === "data" ? part.value : {};
const state = taskStateToJSON(task.status!.state);
console.log(
  `③ 토큰 달고 → ${state}, approvedBy ${sheet["approvedBy"]}`,
);
// endregion
//@ norun
