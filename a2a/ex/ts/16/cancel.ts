// 교통 칸의 셋째 대본 — returnImmediately 로 맡기고, GetTask 로
// WORKING 을 본 뒤 CancelTask, 한 단계 넘게 기다렸다 다시 GetTask.
//   node 16/cancel.ts 카드주소
import { setTimeout as sleep } from "node:timers/promises";
import { Role, taskStateToJSON, type Task } from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";

const BUS = { headcount: 30, nights: 1, depart: "강남역" };

const name = (t: Task) =>
  taskStateToJSON(t.status!.state).replace("TASK_STATE_", "");

const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
const part = {
  ...{ filename: "", mediaType: "", metadata: undefined },
  content: { $case: "data" as const, value: BUS },
};
const message = {
  ...{ messageId: "bus-cancel", taskId: "", contextId: "" },
  ...{ role: Role.ROLE_USER, parts: [part], metadata: undefined },
  ...{ extensions: [], referenceTaskIds: [] },
};
const configuration = {
  ...{ acceptedOutputModes: [], taskPushNotificationConfig: undefined },
  ...{ historyLength: undefined, returnImmediately: true },
};
let task = (await client.sendMessage({
  ...{ tenant: "", message, configuration, metadata: undefined },
})) as Task;
console.log("SendMessage →", name(task));
// region: cancel
const ask = { tenant: "", id: task.id, metadata: undefined };
while (name(task) !== "WORKING") {
  // 첫 단계가 시작될 때까지
  await sleep(50);
  task = await client.getTask({ ...ask, historyLength: undefined });
}
console.log("GetTask     →", name(task));
task = await client.cancelTask(ask);
console.log("CancelTask  →", name(task));
await sleep(2500); // 한 단계(2초)보다 길게 기다린다
task = await client.getTask({ ...ask, historyLength: undefined });
console.log(
  "GetTask     →",
  name(task),
  `아티팩트 ${task.artifacts.length}`,
);
// endregion
//@ norun
