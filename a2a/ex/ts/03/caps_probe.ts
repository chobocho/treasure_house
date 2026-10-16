// 카드에 없는 기능 셋을 SDK 클라이언트로 불러 본다. 클라이언트가
// 카드를 먼저 보고 막는지, 서버까지 가서 오류를 받는지 보려는 것.
//   node 03/caps_probe.ts 카드주소
import { Role } from "@a2a-js/sdk";
import { ClientFactory, type Client } from "@a2a-js/sdk/client";
import { textPart } from "../agents/common.ts";

const fail = (e: unknown) =>
  e instanceof Error ? `${e.name}: ${e.message}` : String(e);

// region: probe
async function probe(client: Client) {
  const message = {
    ...{ messageId: "probe-1", taskId: "", contextId: "" },
    ...{ role: Role.ROLE_USER, parts: [textPart("안녕하세요")] },
    ...{ metadata: undefined, extensions: [], referenceTaskIds: [] },
  };
  const req = { tenant: "", message, configuration: undefined };
  // sendMessageStream 은 카드가 허락하면 스트림, 아니면 막는 호출
  for await (const ev of client.sendMessageStream({
    ...req,
    metadata: undefined,
  })) {
    console.log("① 메시지 →", ev.payload?.$case);
  }
  const hook = { tenant: "", id: "", taskId: "t-1", token: "" };
  try {
    await client.createTaskPushNotificationConfig({
      ...hook,
      url: "http://127.0.0.1:10399/hook",
      authentication: undefined,
    });
  } catch (e) {
    console.log("② 푸시 설정 →", fail(e));
  }
  // 확장 카드를 따로 부르는 메서드는 없다 — getAgentCard 가 판단한다
  const card = await client.getAgentCard();
  console.log("③ 확장 카드 →", card.name);
}
// endregion

const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
await probe(client);
//@ norun
