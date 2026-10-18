// 완성 에이전트가 부르는 agents/common.ts 대신 끼우는 모듈.
// 나머지는 진짜 common.ts 를 그대로 내보내고, serve 만 바꾼다 —
// JSON-RPC Router 자리에 REST Router 를 단다(13/rest_agent.ts).
import express from "express";
import { AgentCard, TaskState } from "@a2a-js/sdk";
import {
  DefaultRequestHandler,
  InMemoryTaskStore,
  type AgentExecutor,
} from "@a2a-js/sdk/server";
import {
  UserBuilder,
  agentCardHandler,
  restHandler,
} from "@a2a-js/sdk/server/express";

export * from "../agents/common.ts";

// region: mount
export function serve(
  card: object,
  executor: AgentExecutor,
  port: number,
) {
  const typed = AgentCard.fromJSON(card);
  // 카드의 문 하나를 HTTP+JSON 으로 바꿔 적는다(주소는 그대로).
  typed.supportedInterfaces[0].protocolBinding = "HTTP+JSON";
  const handler = new DefaultRequestHandler(
    typed,
    new InMemoryTaskStore(),
    executor,
    undefined, // 이벤트 버스 관리자
    undefined, // 푸시 저장소(두 에이전트는 푸시가 없다)
    undefined, // 푸시 발송기
    undefined, // 확장 카드
    undefined, // 카드 서명기
    // 진짜 serve 와 같은 값(agents/common.ts)
    { keepBusAliveStates: [TaskState.TASK_STATE_INPUT_REQUIRED] },
  );
  const wire = AgentCard.toJSON(typed) as AgentCard;
  const app = express();
  app.use(
    "/.well-known/agent-card.json",
    agentCardHandler({ agentCardProvider: async () => wire }),
  );
  // JSON-RPC 의 jsonRpcHandler 자리에 restHandler
  const userBuilder = UserBuilder.noAuthentication;
  app.use("/", restHandler({ requestHandler: handler, userBuilder }));
  app.listen(port, "127.0.0.1");
}
// endregion
//@ norun
