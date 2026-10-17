// 9장의 서버 하나 — TS SDK 만의 손잡이를 한 express 앱에 모았다.
//   node 08/only_server.ts --port P [--url U]
// /rpc·/rest 다중 전송, /big 우리 파서를 앞에 둔 JSON-RPC,
// /secure 토큰을 묻는 문지기, /old1·/old v0.3 호환을 켠 JSON-RPC.
import { parseArgs } from "node:util";
import express from "express";
import { AgentCard } from "@a2a-js/sdk";
import {
  DefaultRequestHandler,
  InMemoryTaskStore,
} from "@a2a-js/sdk/server";
import {
  agentCardHandler,
  jsonRpcHandler,
  restHandler,
  UserBuilder,
} from "@a2a-js/sdk/server/express";
import { EchoExecutor, card as echoCard } from "./step1_echo.ts";
import { QuoteExecutor, card as quoteCard } from "./step2_task.ts";

const { values } = parseArgs({
  options: { port: { type: "string" }, url: { type: "string" } },
});
const port = Number(values.port);
const base = values.url ?? `http://127.0.0.1:${port}/`;
const userBuilder = UserBuilder.noAuthentication;
const app = express();

// region: log
// 맨 앞의 우리 미들웨어 — 모든 요청이 SDK 처리기보다 먼저 지난다
app.use((req, _res, next) => {
  const v = req.get("A2A-Version") ?? "없음";
  console.log(`[mw] ${req.method} ${req.path} A2A-Version=${v}`);
  next();
});
// endregion

// region: transports
// 같은 처리기를 두 바인딩에 — 카드에 인터페이스 둘을 적는다
const card = AgentCard.fromJSON({
  ...(AgentCard.toJSON(echoCard(base)) as object),
  supportedInterfaces: [
    { url: base + "rpc", protocolBinding: "JSONRPC" },
    { url: base + "rest", protocolBinding: "HTTP+JSON" },
  ].map((i) => ({ ...i, protocolVersion: "1.0" })),
});
const store = new InMemoryTaskStore();
const echo = new DefaultRequestHandler(card, store, new EchoExecutor());
const wire = AgentCard.toJSON(card) as AgentCard;
app.use(
  "/.well-known/agent-card.json",
  agentCardHandler({ agentCardProvider: async () => wire }),
);
app.use("/rpc", jsonRpcHandler({ requestHandler: echo, userBuilder }));
app.use("/rest", restHandler({ requestHandler: echo, userBuilder }));
// endregion

// region: big
// SDK 의 express.json() 은 본문 한도가 기본 100 KB 다(4부). 앞에 우리
// 파서를 두면 SDK 쪽 파서는 이미 읽은 본문을 건너뛴다.
const ours = express.json({ limit: "1mb" });
app.use(
  "/big",
  ours,
  jsonRpcHandler({ requestHandler: echo, userBuilder }),
);
// endregion

// region: gate
// 문지기 — 토큰이 없으면 401 과 WWW-Authenticate. 진짜 토큰은 12부.
app.use("/secure", (req, res, next) => {
  if (req.get("Authorization") === "Bearer workshop-demo")
    return next();
  res.status(401).set("WWW-Authenticate", 'Bearer realm="workshop"');
  res.json({ error: "토큰이 필요합니다" });
});
app.use(
  "/secure",
  jsonRpcHandler({ requestHandler: echo, userBuilder }),
);
// endregion

// region: compat
// v0.3 호환을 켠 JSON-RPC 둘 — 견적 에이전트로. /old1 은 스위치만,
// /old 는 카드에 판 0.3 인터페이스를 하나 더 적었다.
function legacy(path: string, also03: boolean) {
  const c = AgentCard.toJSON(quoteCard(base + path)) as {
    supportedInterfaces: object[];
  };
  const old = { url: base + path, protocolBinding: "JSONRPC" };
  if (also03)
    c.supportedInterfaces.push({ ...old, protocolVersion: "0.3" });
  const requestHandler = new DefaultRequestHandler(
    AgentCard.fromJSON(c),
    new InMemoryTaskStore(),
    new QuoteExecutor(),
  );
  const legacyCompat = { enabled: true };
  const rpc = jsonRpcHandler({
    requestHandler,
    userBuilder,
    legacyCompat,
  });
  app.use("/" + path, rpc);
}
legacy("old1", false);
legacy("old", true);
// endregion

app.listen(port, "127.0.0.1");
//@ norun
