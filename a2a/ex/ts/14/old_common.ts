// 완성 숙소 에이전트가 부르는 agents/common.ts 대신 끼우는 모듈.
// serve 만 바꾼다 — 카드에 판 0.3 문 하나만 적고(옛 에이전트 흉내),
// 카드와 JSON-RPC 경로에 v0.3 호환을 켠다(14/old_agent.ts).
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
  jsonRpcHandler,
} from "@a2a-js/sdk/server/express";
import * as compat from "@a2a-js/sdk/compat/v0_3/server/express";

export * from "../agents/common.ts";

// region: serve
export function serve(
  card: { supportedInterfaces: object[] },
  executor: AgentExecutor,
  port: number,
) {
  const [v1] = card.supportedInterfaces; // 주소는 그대로 두고
  card.supportedInterfaces = [{ ...v1, protocolVersion: "0.3" }];
  const typed = AgentCard.fromJSON(card);
  const handler = new DefaultRequestHandler(
    typed,
    new InMemoryTaskStore(),
    executor,
    undefined, // 이벤트 버스 관리자
    undefined, // 푸시 저장소(숙소 에이전트는 푸시가 없다)
    undefined, // 푸시 발송기
    undefined, // 확장 카드
    undefined, // 카드 서명기
    // 진짜 serve 와 같은 값(agents/common.ts)
    { keepBusAliveStates: [TaskState.TASK_STATE_INPUT_REQUIRED] },
  );
  const wire = AgentCard.toJSON(typed) as AgentCard;
  const app = express();
  const path = "/.well-known/agent-card.json";
  // 판 머리글이 없거나 0.3 이면 v0.3 모양의 카드, 아니면 다음 처리기
  app.use(
    path,
    compat.legacyAgentCardRouter({ agentCardProvider: handler }),
  );
  app.use(
    path,
    agentCardHandler({ agentCardProvider: async () => wire }),
  );
  const userBuilder = UserBuilder.noAuthentication;
  const legacyCompat = { enabled: true }; // 판 머리글로 가른다
  app.use(
    "/",
    jsonRpcHandler({
      requestHandler: handler,
      userBuilder,
      legacyCompat,
    }),
  );
  app.listen(port, "127.0.0.1");
}
// endregion
//@ norun
