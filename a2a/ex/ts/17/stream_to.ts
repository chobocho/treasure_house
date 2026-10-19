// 스트림에 시간 제한 1.5초 — AbortSignal 은 "호출 전체" 의 제한이다.
//   node 17/stream_to.ts 카드주소
import { setTimeout as sleep } from "node:timers/promises";
import {
  Role,
  taskStateToJSON,
  type Message,
  type StreamResponse,
  type TaskState,
} from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";

const BUS = { headcount: 30, nights: 1, depart: "강남역" };

const name = (s: TaskState) =>
  taskStateToJSON(s).replace("TASK_STATE_", "");

function show(ev: StreamResponse) {
  const p = ev.payload;
  if (p?.$case === "task") return `Task ${name(p.value.status!.state)}`;
  if (p?.$case === "statusUpdate") {
    const st = p.value.status!;
    // 끝 상태엔 말이 없다
    const said = (st.message?.parts ?? []).map((x) =>
      x.content?.$case === "text" ? x.content.value : "",
    );
    return ["상태", name(st.state), ...said].join(" ");
  }
  if (p?.$case === "artifactUpdate")
    return `아티팩트 ${p.value.artifact!.name}`;
  return "?";
}

const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
const part = {
  ...{ filename: "", mediaType: "", metadata: undefined },
  content: { $case: "data" as const, value: BUS },
};
const message: Message = {
  ...{ messageId: "m-stream", taskId: "", contextId: "" },
  ...{ role: Role.ROLE_USER, parts: [part], metadata: undefined },
  ...{ extensions: [], referenceTaskIds: [] },
};
// region: main
const req = { tenant: "", message, configuration: undefined };
// region: limit
const signal = AbortSignal.timeout(1500); // 이 호출 전체의 제한
const evs = client.sendMessageStream(
  { ...req, metadata: undefined },
  { signal },
);
// endregion
let taskId = "";
try {
  for await (const ev of evs) {
    console.log("  ", show(ev));
    if (ev.payload?.$case === "task") taskId = ev.payload.value.id;
  }
  console.log("스트림 끝");
} catch (e) {
  console.log("시간 초과 →", (e as Error).name);
}
await sleep(3000); // 서버의 세 단계가 다 지나도록
const task = await client.getTask({
  ...{ tenant: "", id: taskId, historyLength: undefined },
});
console.log("3초 뒤 GetTask →", name(task.status!.state));
// endregion
//@ norun
