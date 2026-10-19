// SDK 기본값 그대로 — 6초 걸리는 배차를 막는 호출로 맡긴다.
//   node 17/defaults.ts 카드주소
import {
  Role,
  taskStateToJSON,
  type Message,
  type Task,
} from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";

const BUS = { headcount: 30, nights: 1, depart: "강남역" };

// region: main
// region: make
// signal 을 주지 않으면 SDK 는 fetch 에 아무 제한도 걸지 않는다
const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
// endregion
const part = {
  ...{ filename: "", mediaType: "", metadata: undefined },
  content: { $case: "data" as const, value: BUS },
};
const message: Message = {
  ...{ messageId: "m-default", taskId: "", contextId: "" },
  ...{ role: Role.ROLE_USER, parts: [part], metadata: undefined },
  ...{ extensions: [], referenceTaskIds: [] },
};
const task = (await client.sendMessage({
  ...{ tenant: "", message, configuration: undefined },
  metadata: undefined,
})) as Task;
console.log("SendMessage →", taskStateToJSON(task.status!.state));
// endregion
//@ norun
