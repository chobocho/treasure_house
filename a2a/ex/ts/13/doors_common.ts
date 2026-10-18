// 한 서버, 세 바인딩 — agents/common.ts 대신 끼우는 모듈
// (13/bind_agent.ts 가 바꿔 끼운다).
// JSON-RPC(/)·HTTP+JSON(/rest)·gRPC(--grpc-port) 세 문을 한꺼번에 연다.
// 요청 처리기와 작업 저장소는 하나다. 어느 문으로 들어왔는지 한 줄씩
// 찍는다(카드 요청은 [카드]).
import * as grpc from "@grpc/grpc-js";
import express from "express";
import { AgentCard, TaskState } from "@a2a-js/sdk";
import {
  DefaultRequestHandler,
  InMemoryTaskStore,
  type AgentExecutor,
} from "@a2a-js/sdk/server";
import {
  agentCardHandler,
  jsonRpcHandler,
  restHandler,
} from "@a2a-js/sdk/server/express";
import {
  A2AService,
  UserBuilder,
  grpcService,
} from "@a2a-js/sdk/server/grpc";

export * from "../agents/common.ts";

function take(flag: string) {
  const at = process.argv.indexOf(flag);
  return at < 0 ? undefined : process.argv.splice(at, 2)[1];
}
const grpcPort = Number(take("--grpc-port"));
const grpcUrl = take("--grpc-url") ?? `127.0.0.1:${grpcPort}`;

function door(path: string) {
  if (path.startsWith("/.well-known/")) return "카드";
  return path.startsWith("/rest/") ? "HTTP+JSON" : "JSONRPC";
}

// gRPC 쪽 기록: 서비스 구현의 메서드마다 한 겹 씌운다
function logged(impl: grpc.UntypedServiceImplementation) {
  for (const [name, fn] of Object.entries(impl)) {
    impl[name] = (call: { getPath(): string }, ...rest: unknown[]) => {
      console.log(`[GRPC] ${call.getPath()}`);
      return (fn as Function)(call, ...rest);
    };
  }
  return impl;
}

// region: mount
export function serve(
  card: object,
  executor: AgentExecutor,
  port: number,
) {
  const typed = AgentCard.fromJSON(card);
  const httpUrl = typed.supportedInterfaces[0].url;
  // 카드에 세 문을 모두 적는다(§5.2 MUST) — 차례가 서버의 선호다
  typed.supportedInterfaces.push(
    { ...typed.supportedInterfaces[0], url: httpUrl + "rest" },
    { ...typed.supportedInterfaces[0], url: grpcUrl },
  );
  typed.supportedInterfaces[1].protocolBinding = "HTTP+JSON";
  typed.supportedInterfaces[2].protocolBinding = "GRPC";
  const handler = new DefaultRequestHandler(
    typed,
    new InMemoryTaskStore(),
    executor,
    ...[undefined, undefined, undefined, undefined, undefined],
    { keepBusAliveStates: [TaskState.TASK_STATE_INPUT_REQUIRED] },
  );
  const requestHandler = handler;
  const userBuilder = UserBuilder.noAuthentication;
  const wire = AgentCard.toJSON(typed) as AgentCard;
  const app = express();
  app.use((req, _res, next) => {
    console.log(`[${door(req.path)}] ${req.method} ${req.path}`);
    next();
  });
  app.use(
    "/.well-known/agent-card.json",
    agentCardHandler({ agentCardProvider: async () => wire }),
  );
  app.use("/rest", restHandler({ requestHandler, userBuilder }));
  app.use("/", jsonRpcHandler({ requestHandler, userBuilder }));
  app.listen(port, "127.0.0.1");
  const server = new grpc.Server();
  const impl = grpcService({ requestHandler, userBuilder });
  server.addService(A2AService, logged(impl));
  const creds = grpc.ServerCredentials.createInsecure();
  server.bindAsync(`127.0.0.1:${grpcPort}`, creds, () => {});
}
// endregion
//@ norun
