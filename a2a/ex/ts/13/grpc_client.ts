// SDK 클라이언트로 gRPC 문을 쓴다 — 서버 셋에 같은 세 가지를.
//   node 13/grpc_client.ts 이름=URL …
// 1) 막는 SendMessage  2) 없는 작업 GetTask  3) 없는 작업에 잇는 스트림
import {
  Message,
  TaskState,
  type SendMessageRequest,
} from "@a2a-js/sdk";
import {
  ClientFactory,
  ClientFactoryOptions,
} from "@a2a-js/sdk/client";
import { GrpcTransportFactory } from "@a2a-js/sdk/client/grpc";

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
  // 기본 팩토리는 JSON-RPC·HTTP+JSON 뿐 — gRPC 전송 팩토리를 더한다
  const options = ClientFactoryOptions.createFrom(
    ClientFactoryOptions.default,
    { transports: [new GrpcTransportFactory()] },
  );
  const client = await new ClientFactory(options).createFromUrl(url);
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
  const label = arg.slice(0, at);
  // 실패도 한 줄로 찍는다
  await one(label, arg.slice(at + 1)).catch((e: Error) =>
    console.log(`${label}: ${e.constructor.name}: ${e.message}`),
  );
}
//@ norun
