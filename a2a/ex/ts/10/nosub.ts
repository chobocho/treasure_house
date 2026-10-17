// 스트리밍을 켜지 않은 카드(3부의 안내 에이전트)에 SDK 클라이언트로
// 스트림 보내기와 SubscribeToTask 를 부른다 — 무엇이 서버까지 가나.
//   node 10/nosub.ts URL
import { Message } from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";

// region: probe
const client = await new ClientFactory().createFromUrl(
  process.argv[2]!,
);
const message = Message.fromJSON({
  ...{ messageId: "n-1", role: "ROLE_USER" },
  parts: [{ text: "안녕하세요" }],
});
const req = {
  ...{ tenant: "", message, configuration: undefined },
  metadata: undefined,
};
for await (const ev of client.sendMessageStream(req))
  console.log("① 스트림 보내기 →", ev.payload?.$case);
try {
  for await (const ev of client.resubscribeTask({
    tenant: "",
    id: "t-1",
  }))
    console.log("② 구독 →", ev.payload?.$case);
} catch (e) {
  const err = e as Error & { cause?: Error };
  const real = err.cause ?? err; // 스트림 오류는 cause 에(8부)
  console.log(`② 구독 → ${real.constructor.name}: ${real.message}`);
}
// endregion
//@ norun
