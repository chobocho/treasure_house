// 시간 초과 뒤 같은 messageId 로 다시 보내면 — 작업이 둘 생긴다.
//   node 17/resend.ts 카드주소
import {
  Role,
  TaskState,
  taskStateToJSON,
  type Message,
  type Task,
} from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";

const BUS = { headcount: 30, nights: 1, depart: "강남역" };
// 나중에 ListTasks 로 거르려고 맥락을 정해 둔다
const CTX = "ctx-resend";

const name = (t: Task) =>
  taskStateToJSON(t.status!.state).replace("TASK_STATE_", "");

const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);

// region: send
async function send(ms: number) {
  const part = {
    ...{ filename: "", mediaType: "", metadata: undefined },
    content: { $case: "data" as const, value: BUS },
  };
  const message: Message = {
    ...{ messageId: "m-resend", taskId: "", contextId: CTX },
    ...{ role: Role.ROLE_USER, parts: [part], metadata: undefined },
    ...{ extensions: [], referenceTaskIds: [] },
  };
  const signal = AbortSignal.timeout(ms); // 이 호출만의 제한
  const req = { tenant: "", message, configuration: undefined };
  return (await client.sendMessage(
    { ...req, metadata: undefined },
    { signal },
  )) as Task;
}
// endregion

try {
  await send(1500);
} catch (e) {
  const err = e as Error;
  console.log("① 1.5초 제한 →", err.name, err.message);
}
const task = await send(10_000);
console.log("② 같은 messageId 로 다시 →", name(task));
const page = await client.listTasks({
  ...{ tenant: "", contextId: CTX, pageToken: "" },
  ...{ status: TaskState.TASK_STATE_UNSPECIFIED },
  statusTimestampAfter: undefined,
});
console.log(`③ ListTasks(contextId) → ${page.tasks.length}건`);
for (const t of page.tasks) {
  console.log("  ", name(t), "첫 메시지", t.history[0]!.messageId);
}
//@ norun
