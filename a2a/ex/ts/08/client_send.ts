// SDK 클라이언트로 숙소 견적을 묻는다 — 막는 호출과 스트림.
//   node 08/client_send.ts URL [--no-stream]
import { parseArgs } from "node:util";
import {
  Message,
  TaskState,
  type SendMessageRequest,
  type StreamResponse,
} from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";

const name = (s: TaskState | undefined) =>
  TaskState[s ?? 0].replace(/^TASK_STATE_/, "");

// region: show
// StreamResponse 하나 — 넷 중 무엇이 들었는지는 payload.$case 로
function show(ev: StreamResponse) {
  const p = ev.payload;
  if (p?.$case === "task") {
    const t = p.value;
    const n = t.artifacts.length;
    console.log(`  task ${name(t.status?.state)} 아티팩트 ${n}`);
  } else if (p?.$case === "statusUpdate") {
    console.log(`  statusUpdate ${name(p.value.status?.state)}`);
  } else if (p?.$case === "artifactUpdate") {
    console.log(`  artifactUpdate ${p.value.artifact?.name}`);
  } else console.log(`  ${p?.$case}`);
}
// endregion

// region: send
async function main(url: string, stream: boolean) {
  const client = await new ClientFactory().createFromUrl(url);
  const message = Message.fromJSON({
    ...{ messageId: "c-1", role: "ROLE_USER" },
    parts: [{ data: { date: "2026-10-30", nights: 1, headcount: 30 } }],
  });
  const req: SendMessageRequest = {
    ...{ tenant: "", message, configuration: undefined },
    metadata: undefined,
  };
  let taskId = "";
  if (stream) {
    console.log("스트림");
    for await (const ev of client.sendMessageStream(req)) {
      show(ev);
      taskId ||=
        ev.payload?.$case === "task" ? ev.payload.value.id : "";
    }
  } else {
    console.log("막는 호출");
    const r = await client.sendMessage(req); // Task 또는 Message
    if ("messageId" in r) console.log("  Message");
    else console.log(`  Task ${name(r.status?.state)}`);
    taskId = "messageId" in r ? "" : r.id;
  }
  const t = await client.getTask({ tenant: "", id: taskId });
  const [a, h] = [t.artifacts.length, t.history.length];
  console.log(
    `GetTask: ${name(t.status?.state)} 아티팩트 ${a} 이력 ${h}`,
  );
}
// endregion

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: { "no-stream": { type: "boolean" } },
});
await main(positionals[0]!, !values["no-stream"]);
//@ norun
