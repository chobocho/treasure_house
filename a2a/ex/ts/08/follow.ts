// 이어 말하기 — 두 번째 execute 의 ctx.task 에는 무엇이 들어 있나.
//   node 08/follow.ts
import {
  AgentCard,
  GetTaskRequest,
  Role,
  SendMessageRequest,
  TaskState,
  type Task,
} from "@a2a-js/sdk";
import {
  AgentEvent,
  DefaultRequestHandler,
  InMemoryTaskStore,
  ServerCallContext,
  type AgentExecutor,
  type ExecutionEventBus,
  type RequestContext,
} from "@a2a-js/sdk/server";

const who = (t?: Task) =>
  (t?.history ?? []).map((m) => `${Role[m.role]} ${m.messageId}`);

class AskOnce implements AgentExecutor {
  // region: executor
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    const turn = ctx.task ? "2차" : "1차";
    console.log(`${turn}: ctx.task ${ctx.task ? "있음" : "없음"}`);
    if (ctx.task) {
      console.log("   이력:", who(ctx.task).join(" · "));
      const last = ctx.task.history.at(-1)?.messageId;
      console.log("   이번 메시지가 이미 있나:", last === "m-2");
    }
    const task: Task = ctx.task ?? {
      ...{ id: ctx.taskId, contextId: ctx.contextId },
      status: undefined,
      ...{ artifacts: [], history: [ctx.userMessage] },
      metadata: undefined,
    };
    bus.publish(AgentEvent.task(task)); // 이어 말하기에도 Task 먼저
    const state = ctx.task
      ? TaskState.TASK_STATE_COMPLETED
      : TaskState.TASK_STATE_INPUT_REQUIRED;
    const message = ctx.task ? undefined : question(ctx);
    const status = { state, message, timestamp: undefined };
    const ids = { taskId: ctx.taskId, contextId: ctx.contextId };
    bus.publish(
      AgentEvent.statusUpdate({ ...ids, status, metadata: undefined }),
    );
  }
  // endregion
  async cancelTask() {}
}

function question(ctx: RequestContext) {
  const text = { $case: "text" as const, value: "인원은?" };
  return {
    ...{ messageId: "q-1", role: Role.ROLE_AGENT, metadata: undefined },
    ...{ taskId: ctx.taskId, contextId: ctx.contextId },
    parts: [
      { content: text, mediaType: "", filename: "", metadata: {} },
    ],
    ...{ extensions: [], referenceTaskIds: [] },
  };
}

const handler = new DefaultRequestHandler(
  AgentCard.fromJSON({ name: "되묻기" }),
  new InMemoryTaskStore(),
  new AskOnce(),
);
const call = new ServerCallContext();
const say = (messageId: string, taskId = "") =>
  SendMessageRequest.fromJSON({
    message: {
      messageId,
      taskId,
      role: "ROLE_USER",
      parts: [{ text: "30명" }],
    },
  });

const first = (await handler.sendMessage(say("m-1"), call)) as Task;
console.log("   →", TaskState[first.status!.state]);
await handler.sendMessage(say("m-2", first.id), call);
const saved = await handler.getTask(
  GetTaskRequest.fromJSON({ id: first.id }),
  call,
);
console.log("저장된 이력:", who(saved).join(" · "));
