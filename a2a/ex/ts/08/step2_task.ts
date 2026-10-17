// 2단계 — 견적 에이전트: DataPart 를 받아 Task 로 견적을 낸다.
//   node 08/step2_task.ts --port P [--url U] [--path /a2a]
import { randomUUID } from "node:crypto";
import { parseArgs } from "node:util";
import express from "express";
import {
  AgentCard,
  Role,
  TaskState,
  type Message,
  type Part,
  type Task,
} from "@a2a-js/sdk";
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
  chooseLodging,
  type LodgingRequest,
} from "../workshop/domain.ts";

const part = (content: Part["content"]): Part => ({
  ...{ content, mediaType: "", filename: "", metadata: undefined },
});

// DataPart 들을 앞에서부터 합친다. JSON 의 30 은 TS 에서도 30 이다.
export function requestOf(m: Message) {
  const req: Record<string, unknown> = {};
  for (const p of m.parts) {
    if (p.content?.$case === "data")
      Object.assign(req, p.content.value);
  }
  return req as LodgingRequest;
}

// region: events
// 갱신기(TaskUpdater)가 없어 이벤트 객체를 직접 짓는다
function newTask(ctx: RequestContext): Task {
  return {
    ...{ id: ctx.taskId, contextId: ctx.contextId },
    status: { state: TaskState.TASK_STATE_SUBMITTED, ...EMPTY },
    ...{ artifacts: [], history: [ctx.userMessage] },
    metadata: undefined,
  };
}
const EMPTY = { message: undefined, timestamp: undefined };

function update(
  bus: ExecutionEventBus,
  ctx: RequestContext,
  state: TaskState,
  message?: Message,
) {
  const timestamp = new Date().toISOString();
  bus.publish(
    AgentEvent.statusUpdate({
      ...{ taskId: ctx.taskId, contextId: ctx.contextId },
      status: { state, message, timestamp },
      metadata: undefined,
    }),
  );
}

// 이 작업에 딸린 에이전트 말 — 파이썬 up.new_agent_message 몫
function agentSays(ctx: RequestContext, parts: Part[]): Message {
  return {
    ...{ messageId: randomUUID(), role: Role.ROLE_AGENT, parts },
    ...{ taskId: ctx.taskId, contextId: ctx.contextId },
    ...{ metadata: undefined, extensions: [], referenceTaskIds: [] },
  };
}
// endregion

export class QuoteExecutor implements AgentExecutor {
  // region: executor
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    bus.publish(AgentEvent.task(newTask(ctx))); // ① Task 를 먼저
    update(bus, ctx, TaskState.TASK_STATE_WORKING); // ② WORKING
    const quote = chooseLodging(requestOf(ctx.userMessage));
    if (!quote.ok) {
      // ③ 거절 — 까닭을 상태 메시지로
      const why = [part({ $case: "text", value: quote.reason })];
      const msg = agentSays(ctx, why);
      update(bus, ctx, TaskState.TASK_STATE_REJECTED, msg);
      return;
    }
    // ③ 견적은 아티팩트로, 그다음 끝
    bus.publish(
      AgentEvent.artifactUpdate({
        ...{ taskId: ctx.taskId, contextId: ctx.contextId },
        artifact: {
          ...{ artifactId: randomUUID(), name: "숙소 견적" },
          ...{ description: "", metadata: undefined, extensions: [] },
          parts: [part({ $case: "data", value: quote })],
        },
        ...{ append: false, lastChunk: false, metadata: undefined },
      }),
    );
    update(bus, ctx, TaskState.TASK_STATE_COMPLETED);
  }
  // endregion

  async cancelTask(taskId: string, bus: ExecutionEventBus) {
    // 멈출 일이 없다(execute 는 곧바로 끝난다) — CANCELED 만 싣는다
    bus.publish(
      AgentEvent.statusUpdate({
        ...{ taskId, contextId: "", metadata: undefined },
        status: { state: TaskState.TASK_STATE_CANCELED, ...EMPTY },
      }),
    );
  }
}

export function card(url: string): AgentCard {
  return AgentCard.fromJSON({
    name: "보물상사 견적 에이전트",
    description: "날짜·박 수·인원으로 숙소 견적을 냅니다.",
    version: "0.2.0",
    supportedInterfaces: [
      { url, protocolBinding: "JSONRPC", protocolVersion: "1.0" },
    ],
    capabilities: {},
    defaultInputModes: ["application/json"],
    defaultOutputModes: ["application/json"],
    skills: [
      {
        ...{
          id: "quote-lodging",
          name: "숙소 견적",
          tags: ["lodging"],
        },
        description: "DataPart 로 받은 조건에 맞는 숙소를 고릅니다.",
      },
    ],
  });
}

// region: serve
function main() {
  const { values } = parseArgs({
    options: {
      ...{ port: { type: "string" }, url: { type: "string" } },
      path: { type: "string", default: "/" }, // JSON-RPC 를 달 경로
    },
  });
  const port = Number(values.port);
  const url = values.url ?? `http://127.0.0.1:${port}${values.path}`;
  const agentCard = card(url);
  const handler = new DefaultRequestHandler(
    agentCard,
    new InMemoryTaskStore(),
    new QuoteExecutor(),
  );
  const app = express();
  // 카드는 와이어 모양(toJSON)으로 바꿔서 준다 — 5장
  const wire = AgentCard.toJSON(agentCard) as AgentCard;
  app.use(
    "/.well-known/agent-card.json",
    agentCardHandler({ agentCardProvider: async () => wire }),
  );
  const userBuilder = UserBuilder.noAuthentication;
  const rpc = jsonRpcHandler({ requestHandler: handler, userBuilder });
  app.use(values.path, rpc);
  app.listen(port, "127.0.0.1");
}
// endregion

if (import.meta.main) main();
//@ norun
