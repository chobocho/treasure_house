// 요청 처리기를 HTTP 없이 직접 부른다 — 처리기가 하는 일만 떼어 보기.
//   node 08/direct.ts
import { setTimeout as sleep } from "node:timers/promises";
import {
  GetTaskRequest,
  ListTasksRequest,
  SendMessageRequest,
  TaskState,
  type Task,
} from "@a2a-js/sdk";
import {
  DefaultRequestHandler,
  InMemoryTaskStore,
  ServerCallContext,
} from "@a2a-js/sdk/server";
import { QuoteExecutor, card } from "./step2_task.ts";

function request(n: number, now = false) {
  const data = { date: "2026-10-30", nights: 1, headcount: n };
  return SendMessageRequest.fromJSON({
    message: {
      ...{ messageId: `m-${n}`, role: "ROLE_USER" },
      parts: [{ data }],
    },
    configuration: { returnImmediately: now },
  });
}

function show(label: string, task: Task) {
  const state = TaskState[task.status!.state];
  const { history, artifacts } = task;
  const sizes = `이력 ${history.length} 아티팩트 ${artifacts.length}`;
  console.log(`${label}: ${state} ${sizes}`);
}

// region: handler
const store = new InMemoryTaskStore();
const handler = new DefaultRequestHandler(
  card("http://127.0.0.1:10800/"),
  store,
  new QuoteExecutor(),
);
const call = new ServerCallContext(); // 누가 불렀나 — 여기서는 익명
// endregion

// region: calls
const task = (await handler.sendMessage(request(30), call)) as Task;
show("SendMessage (막는 호출)", task);
const get = GetTaskRequest.fromJSON({ id: task.id });
show("GetTask", await handler.getTask(get, call));
const quick = await handler.sendMessage(request(20, true), call);
show("SendMessage (곧바로)", quick as Task);
await sleep(100); // 실행기는 뒤에서 마저 돈다
show("0.1초 뒤 GetTask", (await store.load((quick as Task).id, call))!);
const page = await handler.listTasks(
  ListTasksRequest.fromJSON({}),
  call,
);
console.log("ListTasks:", page.tasks.length, "개");
try {
  for await (const _ of handler.sendMessageStream(request(30), call)) {
  }
} catch (e) {
  console.log("스트림:", (e as Error).name, "—", (e as Error).message);
}
// endregion
