// 규칙을 어기는 실행기 일곱 — 처리기는 무엇을 잡고, 무엇을 저장하나.
//   node 08/rules.ts
import {
  AgentCard,
  ListTasksRequest,
  Message,
  SendMessageRequest,
  TaskState,
  type Task,
} from "@a2a-js/sdk";
import {
  AgentEvent,
  DefaultRequestHandler,
  InMemoryTaskStore,
  JsonRpcTransportHandler,
  ServerCallContext,
  type ExecutionEventBus as Bus,
  type RequestContext as Ctx,
} from "@a2a-js/sdk/server";
import { RequestMalformedError } from "@a2a-js/sdk/errors";

const say = (ctx: Ctx, text: string) =>
  AgentEvent.message(
    Message.fromJSON({
      ...{
        messageId: text,
        role: "ROLE_AGENT",
        contextId: ctx.contextId,
      },
      parts: [{ text }],
    }),
  );
const task = (ctx: Ctx, id = ctx.taskId): Task => ({
  ...{ id, contextId: ctx.contextId, artifacts: [], metadata: {} },
  status: { state: 1, message: undefined, timestamp: undefined },
  history: [ctx.userMessage],
});
const working = (ctx: Ctx) =>
  AgentEvent.statusUpdate({
    ...{ taskId: ctx.taskId, contextId: ctx.contextId, metadata: {} },
    status: { state: 2, message: undefined, timestamp: undefined },
  });

// region: bad
const BAD: Record<string, (ctx: Ctx, bus: Bus) => Promise<void>> = {
  async TwoMessages(ctx, bus) {
    bus.publish(say(ctx, "하나")); // Message 는 하나만
    bus.publish(say(ctx, "둘"));
  },
  async StatusFirst(ctx, bus) {
    bus.publish(working(ctx)); // Task 보다 상태가 먼저
  },
  async MessageAfterTask(ctx, bus) {
    bus.publish(AgentEvent.task(task(ctx))); // Task 다음에 Message
    bus.publish(say(ctx, "끝났습니다"));
  },
  async OtherId(ctx, bus) {
    bus.publish(AgentEvent.task(task(ctx, "my-own-id"))); // 다른 id
  },
  async Silent() {}, // 아무것도 싣지 않고 돌아간다
  async Refuses() {
    throw new RequestMalformedError("인원이 없습니다"); // A2A 오류
  },
  async Crashes() {
    throw new Error("견적표를 못 읽었습니다"); // 아무 예외
  },
};
// endregion

// region: try
const CARD = AgentCard.fromJSON({ capabilities: { streaming: true } });
const CALL = new ServerCallContext();
const REQ = SendMessageRequest.fromJSON({
  message: {
    messageId: "m-1",
    role: "ROLE_USER",
    parts: [{ text: "30" }],
  },
});
const fresh = (name: string) => {
  const store = new InMemoryTaskStore();
  const exec = { execute: BAD[name]!, cancelTask: async () => {} };
  return {
    store,
    handler: new DefaultRequestHandler(CARD, store, exec),
  };
};

async function blocking(name: string) {
  const { store, handler } = fresh(name);
  const got = await within2s(handler.sendMessage(REQ, CALL)).then(
    describe,
    failed,
  );
  const page = await store.list(ListTasksRequest.fromJSON({}), CALL);
  const saved = page.tasks.map((t) => TaskState[t.status!.state]);
  return [got, `[${saved.join(", ")}]`];
}

async function streaming(name: string) {
  const seen: string[] = [];
  const run = async () => {
    for await (const ev of fresh(name).handler.sendMessageStream(
      ...[REQ, CALL],
    )) {
      const p = ev.payload!;
      const state = p.$case === "statusUpdate" && p.value.status!.state;
      seen.push(state ? TaskState[state]! : p.$case);
    }
    return seen.join(" ") || "(이벤트 없음)";
  };
  return within2s(run()).catch(
    (e) => `${seen.join(" ")} ✗ ${failed(e)}`,
  );
}
// endregion

function describe(r: Message | Task) {
  if (!("status" in r))
    return `Message "${r.parts[0]?.content?.value}"`;
  const id = r.id === "my-own-id" ? ` ${r.id}` : "";
  return `Task${id} ${TaskState[r.status!.state]}`;
}
// 오류면 이름·글과, 와이어에 나갈 JSON-RPC 코드
function failed(e: unknown) {
  if (!(e instanceof Error)) return String(e);
  const { code } = JsonRpcTransportHandler.mapToJSONRPCError(e);
  return `${e.name}(${code}): ${e.message}`;
}
function within2s<T>(p: Promise<T>) {
  const late = (_: unknown, no: (why: string) => void) =>
    setTimeout(() => no("2초 동안 답이 없다"), 2000);
  return Promise.race([p, new Promise<never>(late)]);
}

// SDK 의 오류 기록(추적 정보)은 끈다
console.error = console.warn = () => {};
for (const name of Object.keys(BAD)) {
  const [got, saved] = await blocking(name);
  console.log(name);
  console.log(`  막는 호출  ${got}\n  저장       ${saved}`);
  console.log(`  스트림     ${(await streaming(name)).trim()}`);
}
