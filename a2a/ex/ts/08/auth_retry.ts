// 401 을 받으면 머리글을 바꿔 한 번 더 — TS SDK 의 인증 fetch.
//   node 08/auth_retry.ts BASE
import { Message } from "@a2a-js/sdk";
import {
  ClientFactory,
  JsonRpcTransportFactory,
  createAuthenticatingFetchWithRetry,
  type AuthenticationHandler,
  type HttpHeaders,
} from "@a2a-js/sdk/client";
import { card } from "./step1_echo.ts";

// region: handler
let token = ""; // 처음엔 아무것도 없다
const handler: AuthenticationHandler = {
  headers: async (): Promise<HttpHeaders> =>
    token ? { Authorization: `Bearer ${token}` } : {},
  shouldRetryWithHeaders: async (_req, res) => {
    if (res.status !== 401) return undefined; // 다시 하지 않는다
    console.log("  401 —", res.headers.get("WWW-Authenticate"));
    return { Authorization: "Bearer workshop-demo" }; // 받아 온 셈
  },
  onSuccessfulRetry: async (headers) => {
    token = headers.Authorization!.slice("Bearer ".length);
    console.log("  다시 해서 됐다 — 토큰을 쥐어 둔다");
  },
};
const fetchImpl = createAuthenticatingFetchWithRetry(fetch, handler);
const transports = [new JsonRpcTransportFactory({ fetchImpl })];
// endregion

const base = process.argv[2]!;
const client = await new ClientFactory({
  transports,
}).createFromAgentCard(card(base + "secure"));
for (const n of [1, 2]) {
  console.log(`요청 ${n}`);
  const message = Message.fromJSON({
    ...{ messageId: `a-${n}`, role: "ROLE_USER" },
    parts: [{ text: `${n}번째` }],
  });
  const req = { tenant: "", message, configuration: undefined };
  const r = await client.sendMessage({ ...req, metadata: undefined });
  console.log("  답:", "messageId" in r ? "Message" : "Task");
}
//@ norun
