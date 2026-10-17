// 모르는 필드가 든 답을 TS SDK 클라이언트는 어떻게 읽나.
//   node 08/strict.ts URL
import { Message, TaskState, type Task } from "@a2a-js/sdk";
import { ClientFactory, type Client } from "@a2a-js/sdk/client";
import { A2AError, TaskNotFoundError } from "@a2a-js/sdk/errors";

const NAMES = ["plain", "task", "status", "result", "envelope"];
NAMES.push("enum", "error");

function seen(t: Task) {
  const state = TaskState[t.status?.state ?? 0];
  const extra = "createdAt" in t ? " (createdAt 남음)" : "";
  return `받음 ${state}${extra}`;
}

function caught(e: unknown) {
  const err = e as Error;
  const cause = err.cause as Error | undefined;
  const a = e instanceof A2AError;
  const nf = e instanceof TaskNotFoundError;
  const c = cause ? ` cause=${cause.name}` : "";
  return `${err.name} A2AError=${a} TaskNotFound=${nf}${c}`;
}

// region: probe
async function probe(client: Client, stream: boolean) {
  console.log(stream ? "스트림" : "막는 호출");
  for (const name of NAMES) {
    const message = Message.fromJSON({
      ...{ messageId: `s-${name}`, role: "ROLE_USER" },
      parts: [{ text: name }],
    });
    const req = { tenant: "", message, configuration: undefined };
    const params = { ...req, metadata: undefined };
    try {
      if (!stream) {
        const r = await client.sendMessage(params);
        console.log(`  ${name.padEnd(9)}`, seen(r as Task));
        continue;
      }
      for await (const ev of client.sendMessageStream(params)) {
        const t = ev.payload?.$case === "task" && ev.payload.value;
        if (t) console.log(`  ${name.padEnd(9)}`, seen(t));
      }
    } catch (e) {
      console.log(`  ${name.padEnd(9)}`, caught(e));
    }
  }
}
// endregion

const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
const card = await client.getAgentCard();
console.log("카드에 createdAt 이 남았나:", "createdAt" in card);
await probe(client, false);
await probe(client, true);
//@ norun
