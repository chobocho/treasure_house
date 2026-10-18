// SDK 클라이언트로 HTTP+JSON 문을 쓴다 — 서버 셋에 같은 세 가지를.
//   node 13/rest_client.ts 이름=URL …
// 1) 막는 SendMessage  2) 없는 작업 GetTask  3) 없는 작업에 잇는 스트림
import {
  Message,
  TaskState,
  type SendMessageRequest,
} from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";

function msg(taskId = ""): SendMessageRequest {
  const message = Message.fromJSON({
    ...{ messageId: "c-1", role: "ROLE_USER", taskId },
    parts: [{ text: "2026-10-30 1박 30명" }],
  });
  return {
    tenant: "",
    message,
    configuration: undefined,
    metadata: undefined,
  };
}

async function kindOf(call: () => Promise<unknown>) {
  try {
    await call();
  } catch (e) {
    return (e as Error).constructor.name; // 어떤 오류인지가 답이다
  }
  return "성공";
}

// region: client
async function one(label: string, url: string) {
  // TS 공장은 기본으로 JSON-RPC 와 HTTP+JSON 을 둘 다 안다
  const client = await new ClientFactory().createFromUrl(url);
  const r = await client.sendMessage(msg());
  const state =
    "messageId" in r ? "Message" : TaskState[r.status!.state];
  const got = await kindOf(() =>
    client.getTask({ tenant: "", id: "t-nope" }),
  );
  const sub = await kindOf(async () => {
    for await (const _ of client.sendMessageStream(msg("t-nope"))) {
    }
  });
  const s = state.slice(11);
  console.log(`${label}: 보내기 ${s} | 없는 작업 ${got} | 잇기 ${sub}`);
}
// endregion

for (const arg of process.argv.slice(2)) {
  const at = arg.indexOf("=");
  await one(arg.slice(0, at), arg.slice(at + 1));
}
//@ norun
