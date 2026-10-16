// 교통 에이전트에 같은 배차 요청을 두 번 — 막는 호출로 한 번,
// returnImmediately 로 한 번 — 보내고, 둘째는 GetTask 로 지켜본다.
//   node 05/modes.ts 카드주소
import { setTimeout as sleep } from "node:timers/promises";
import {
  Role,
  taskStateToJSON,
  type Message,
  type Task,
} from "@a2a-js/sdk";
import { ClientFactory, type Client } from "@a2a-js/sdk/client";

const BUS = { headcount: 30, nights: 1, depart: "강남역" };
const DONE = ["COMPLETED", "FAILED", "CANCELED", "REJECTED"];

const name = (t: Task) =>
  taskStateToJSON(t.status!.state).replace("TASK_STATE_", "");

// region: send
async function send(client: Client, messageId: string, now: boolean) {
  const part = {
    ...{ filename: "", mediaType: "", metadata: undefined },
    content: { $case: "data" as const, value: BUS },
  };
  const message: Message = {
    ...{ messageId, taskId: "", contextId: "", role: Role.ROLE_USER },
    ...{ parts: [part], metadata: undefined, extensions: [] },
    referenceTaskIds: [],
  };
  // returnImmediately 는 요청의 configuration 에 싣는다
  const configuration = {
    ...{
      acceptedOutputModes: [],
      taskPushNotificationConfig: undefined,
    },
    ...{ historyLength: undefined, returnImmediately: now },
  };
  const res = await client.sendMessage({
    ...{ tenant: "", message, configuration, metadata: undefined },
  });
  return res as Task; // 교통 에이전트는 늘 Task 로 답한다
}
// endregion

// region: poll
async function poll(client: Client, id: string) {
  let seen = "";
  for (;;) {
    // 상태가 바뀔 때만 찍는다(몇 번 물었는지는 그때그때 다르다)
    const task = await client.getTask({ tenant: "", id });
    if (name(task) !== seen) {
      seen = name(task);
      console.log("  GetTask →", seen);
    }
    if (DONE.includes(seen)) return task;
    await sleep(100);
  }
}
// endregion

const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
let task = await send(client, "bus-wait", false);
console.log("막는 호출         →", name(task), task.artifacts.length);
task = await send(client, "bus-now", true);
console.log("returnImmediately →", name(task), task.artifacts.length);
task = await poll(client, task.id);
console.log("  아티팩트:", task.artifacts[0]!.name);
//@ norun
