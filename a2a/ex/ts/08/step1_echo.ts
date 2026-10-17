// 1단계 — 메아리 에이전트: 받은 글을 Message 하나로 돌려준다.
//   node 08/step1_echo.ts --port P [--url U]
// 실행기(3장) → 요청 처리기(4장) → 서버(5장)를 한 파일에 담았다.
import { randomUUID } from "node:crypto";
import { parseArgs } from "node:util";
import express from "express";
import { AgentCard, Role, type Message } from "@a2a-js/sdk";
import {
  AgentEvent,
  DefaultRequestHandler,
  InMemoryTaskStore,
  type AgentExecutor,
  type ExecutionEventBus,
  type RequestContext,
} from "@a2a-js/sdk/server";
import {
  agentCardHandler,
  jsonRpcHandler,
  UserBuilder,
} from "@a2a-js/sdk/server/express";
import { UnsupportedOperationError } from "@a2a-js/sdk/errors";

// region: executor
export class EchoExecutor implements AgentExecutor {
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    // 글 파트만 골라 잇는다 — 파이썬 get_user_input() 의 몫
    const text = ctx.userMessage.parts
      .map((p) => (p.content?.$case === "text" ? p.content.value : ""))
      .join("\n");
    const reply: Message = {
      messageId: randomUUID(),
      contextId: ctx.contextId, // 서버 메시지에는 contextId 를
      taskId: "", // Task 를 만들지 않으니 비운다
      role: Role.ROLE_AGENT,
      parts: [
        {
          content: { $case: "text", value: `받은 말: ${text}` },
          ...{ mediaType: "", filename: "", metadata: undefined },
        },
      ],
      ...{ metadata: undefined, extensions: [], referenceTaskIds: [] },
    };
    bus.publish(AgentEvent.message(reply)); // 이벤트는 이것 하나뿐
  }

  async cancelTask() {
    // Message 만 내는 에이전트에는 취소할 작업이 없다
    throw new UnsupportedOperationError();
  }
}
// endregion

// region: card
export function card(url: string): AgentCard {
  return AgentCard.fromJSON({
    name: "보물상사 메아리 에이전트",
    description: "받은 글을 그대로 돌려줍니다.",
    version: "0.1.0",
    supportedInterfaces: [
      { url, protocolBinding: "JSONRPC", protocolVersion: "1.0" },
    ],
    capabilities: {},
    defaultInputModes: ["text/plain"],
    defaultOutputModes: ["text/plain"],
    skills: [
      {
        ...{ id: "echo", name: "메아리", tags: ["debug"] },
        description: "받은 글을 돌려줍니다.",
      },
    ],
  });
}
// endregion

// region: serve
function main() {
  const { values } = parseArgs({
    options: { port: { type: "string" }, url: { type: "string" } },
  });
  const port = Number(values.port);
  const url = values.url ?? `http://127.0.0.1:${port}/`;
  const agentCard = card(url);
  const handler = new DefaultRequestHandler(
    agentCard,
    new InMemoryTaskStore(),
    new EchoExecutor(),
  );
  const app = express();
  // SDK 설명서의 예 그대로 — 처리기를 카드 공급자로 준다
  app.use(
    "/.well-known/agent-card.json",
    agentCardHandler({ agentCardProvider: handler }),
  );
  const userBuilder = UserBuilder.noAuthentication;
  app.use(
    "/",
    jsonRpcHandler({ requestHandler: handler, userBuilder }),
  );
  app.listen(port, "127.0.0.1");
}
// endregion

if (import.meta.main) main();
//@ norun
