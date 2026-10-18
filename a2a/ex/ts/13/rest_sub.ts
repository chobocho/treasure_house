// SDK 클라이언트의 SubscribeToTask 는 HTTP+JSON 에서 어떤 동사로 가나.
// 없는 작업에 잇기만 한 번 — 동사는 탭이 본다(5장).
//   node 13/rest_sub.ts URL
import { ClientFactory } from "@a2a-js/sdk/client";

// region: sub
const client = await new ClientFactory().createFromUrl(process.argv[2]);
try {
  const req = { tenant: "", id: "t-nope" };
  for await (const _ of client.resubscribeTask(req)) {
  }
} catch (e) {
  console.log("잇기:", (e as Error).constructor.name);
}
// endregion
//@ norun
