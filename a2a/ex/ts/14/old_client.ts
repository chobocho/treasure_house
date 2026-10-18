// 카드가 판 0.3 문 하나만 적은 에이전트에 TS SDK 클라이언트로 묻는다.
// 옛 판은 켜야 쓴다 — 카드 해석기와 JSON-RPC 전송 둘 다.
//   node 14/old_client.ts URL
import { Message, TaskState } from "@a2a-js/sdk";
import {
  ClientFactory,
  DefaultAgentCardResolver,
  JsonRpcTransportFactory,
} from "@a2a-js/sdk/client";

// region: send
const legacyCompat = { enabled: true };
const factory = new ClientFactory({
  transports: [new JsonRpcTransportFactory({ legacyCompat })],
  cardResolver: new DefaultAgentCardResolver({ legacyCompat }),
});
const client = await factory.createFromUrl(process.argv[2]!);
const message = Message.fromJSON({
  ...{ messageId: "o-1", role: "ROLE_USER" },
  parts: [{ data: { date: "2026-10-30", nights: 1, headcount: 30 } }],
});
const r = await client.sendMessage({
  ...{ tenant: "", message },
  ...{ configuration: undefined, metadata: undefined },
});
if (!("messageId" in r)) {
  const c = r.artifacts[0]!.parts[0]!.content;
  const venue = c?.$case === "data" ? c.value.venueName : "";
  console.log(TaskState[r.status!.state], venue);
}
// endregion
//@ norun
