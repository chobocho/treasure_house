// referenceTaskIds 를 SDK 가 작업으로 풀어 주나 — 처리기를 HTTP 없이
// 직접 부른다. 다른 서버의 작업 하나와 이 서버의 작업 하나를 가리킨다.
//   node 15/refs.ts
import {
  AgentCard,
  SendMessageRequest,
  TaskState,
  type Task,
} from "@a2a-js/sdk";
import {
  DefaultRequestHandler,
  InMemoryTaskStore,
  ServerCallContext,
  type ExecutionEventBus,
  type RequestContext,
} from "@a2a-js/sdk/server";
import { begin, textOf, textPart } from "../agents/common.ts";

// region: seen
// 실행기가 받은 referenceTasks 의 id 를 끝 상태 메시지로 알린다.
const seen = {
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    const { up } = begin(ctx, bus);
    const refs = ctx.referenceTasks ?? [];
    const ids = refs.map((t) => t.id).join(", ") || "없음";
    const text = `referenceTasks ${refs.length}개: ${ids}`;
    up.status(TaskState.TASK_STATE_COMPLETED, [textPart(text)]);
  },
  async cancelTask() {},
};

// 처리기의 설정은 기본 그대로 — 끄고 켜는 스위치가 없다.
const card = AgentCard.fromJSON({ name: "refs", version: "1" });
const handler = () =>
  new DefaultRequestHandler(card, new InMemoryTaskStore(), seen);
// endregion

async function send(
  h: DefaultRequestHandler,
  text: string,
  refs: string[] = [],
) {
  const message = {
    messageId: text,
    role: "ROLE_USER",
    parts: [{ text }],
  };
  const req = SendMessageRequest.fromJSON({
    message: { ...message, referenceTaskIds: refs },
  });
  return (await h.sendMessage(req, new ServerCallContext())) as Task;
}

// region: main
const other = await send(handler(), "숙소 견적"); // 다른 서버
console.log(`다른 서버의 작업 ${other.id}`);
const h = handler();
const mine = await send(h, "앞 작업");
console.log(`이 서버의 작업 ${mine.id}`);
const t = await send(h, "정산", [other.id, mine.id]);
console.log(`  기본 → ${textOf(t.status?.message)}`);
// endregion
