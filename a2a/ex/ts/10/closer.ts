// 종료 실험 에이전트 — 첫 글 파트로 고른 차례대로 상태를 싣고
// 돌아간다. SDK 가 스트림을 언제 닫는지 보려는 실험용이다(3장).
// 서버는 SDK 기본값 그대로다 — agents/common.ts 의 serve 는
// keepBusAliveStates 를 바꾸므로 여기서는 쓰지 않는다.
import { randomUUID } from "node:crypto";
import { setTimeout as sleep } from "node:timers/promises";
import express from "express";
import { AgentCard, Role, TaskState } from "@a2a-js/sdk";
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
import {
  begin,
  jsonrpcInterface,
  parseCli,
  textOf,
  textPart,
} from "../agents/common.ts";

// region: plans
// 고른 말 → 실행기가 싣는 상태들. "쉼" 은 0.3초 쉬기,
// "BOOM" 은 예외 던지기. MESSAGE 는 Task 없이 Message 하나.
const PLANS: Record<string, string[]> = {
  COMPLETED: ["WORKING", "COMPLETED"],
  INPUT_REQUIRED: ["INPUT_REQUIRED"],
  AUTH_REQUIRED: ["AUTH_REQUIRED"],
  WORKING: ["WORKING"], // 끝 상태 없이 돌아간다
  LATE: ["INPUT_REQUIRED", "쉼", "WORKING", "COMPLETED"],
  BOOM: ["WORKING", "쉼", "BOOM"],
  MESSAGE: [],
};
// endregion

// region: execute
class Closer implements AgentExecutor {
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    const word = textOf(ctx.userMessage);
    if (word === "MESSAGE") {
      const parts = [textPart("메시지로 답함")];
      const ids = { messageId: randomUUID(), contextId: ctx.contextId };
      const rest = { taskId: "", extensions: [], referenceTaskIds: [] };
      const msg = { ...ids, role: Role.ROLE_AGENT, parts, ...rest };
      bus.publish(AgentEvent.message({ ...msg, metadata: undefined }));
      return;
    }
    const { up } = begin(ctx, bus); // Task(SUBMITTED) 가 먼저
    for (const step of PLANS[word] ?? []) {
      if (step === "쉼") {
        await sleep(300);
      } else if (step === "BOOM") {
        console.log(`[종료] ${word}: 예외를 던진다`);
        throw new Error("실행기가 죽었다");
      } else {
        const name = `TASK_STATE_${step}` as keyof typeof TaskState;
        up.status(TaskState[name]);
      }
    }
    console.log(`[종료] ${word}: 실행기가 돌아갔다`);
  }
  async cancelTask() {} // 실험에서는 취소하지 않는다
}
// endregion

// region: serve
// SDK 의 기본 옵션 그대로 — 아홉째 인자(options)를 주지 않는다.
const { port, url } = parseCli();
const card = AgentCard.fromJSON({
  name: "보물상사 종료 실험 에이전트",
  description: "고른 상태에서 실행을 끝냅니다.",
  version: "1.0.0",
  supportedInterfaces: [jsonrpcInterface(url)],
  capabilities: { streaming: true },
  defaultInputModes: ["text/plain"],
  defaultOutputModes: ["text/plain"],
  skills: [{ id: "close", name: "종료 실험", tags: ["debug"] }],
});
const store = new InMemoryTaskStore();
const handler = new DefaultRequestHandler(card, store, new Closer());
const app = express();
const wire = AgentCard.toJSON(card) as AgentCard;
app.use(
  "/.well-known/agent-card.json",
  agentCardHandler({ agentCardProvider: async () => wire }),
);
const userBuilder = UserBuilder.noAuthentication;
app.use("/", jsonRpcHandler({ requestHandler: handler, userBuilder }));
app.listen(port, "127.0.0.1");
// endregion
//@ norun
