// 완성 에이전트가 부르는 agents/common.ts 대신 끼우는 모듈(gRPC 판).
// 나머지는 진짜 common.ts 를 그대로 내보내고, serve 만 바꾼다 —
// 카드는 HTTP 로 내주고, 요청 처리기는 gRPC 서버에 단다.
// --grpc-port·--grpc-url 은 여기서 떼어 낸다: 에이전트의 parseCli 는
// 모르는 옵션을 거절하는데, 이 모듈이 에이전트 본문보다 먼저 돈다.
import * as grpc from "@grpc/grpc-js";
import express from "express";
import { AgentCard, TaskState } from "@a2a-js/sdk";
import {
  DefaultRequestHandler,
  InMemoryTaskStore,
  type AgentExecutor,
} from "@a2a-js/sdk/server";
import { agentCardHandler } from "@a2a-js/sdk/server/express";
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

// region: mount
export function serve(
  card: object,
  executor: AgentExecutor,
  port: number,
) {
  const typed = AgentCard.fromJSON(card);
  // 카드의 문 하나를 GRPC 로 — 주소는 "호스트:포트"(스킴 없음)
  typed.supportedInterfaces[0].protocolBinding = "GRPC";
  typed.supportedInterfaces[0].url = grpcUrl;
  const handler = new DefaultRequestHandler(
    typed,
    new InMemoryTaskStore(),
    executor,
    // 버스 관리자·푸시 저장소·발송기·확장 카드·서명기: 없음
    ...[undefined, undefined, undefined, undefined, undefined],
    // 진짜 serve 와 같은 값(agents/common.ts)
    { keepBusAliveStates: [TaskState.TASK_STATE_INPUT_REQUIRED] },
  );
  const server = new grpc.Server();
  const userBuilder = UserBuilder.noAuthentication;
  server.addService(
    A2AService,
    grpcService({ requestHandler: handler, userBuilder }),
  );
  const creds = grpc.ServerCredentials.createInsecure();
  server.bindAsync(`127.0.0.1:${grpcPort}`, creds, () => {});
  // 발견은 바인딩과 따로 — 카드는 HTTP 의 잘 알려진 경로에
  const wire = AgentCard.toJSON(typed) as AgentCard;
  const app = express();
  app.use(
    "/.well-known/agent-card.json",
    agentCardHandler({ agentCardProvider: async () => wire }),
  );
  app.listen(port, "127.0.0.1");
}
// endregion
//@ norun
