// 클라이언트 메서드마다 무엇을 보내나 — 서버 없이, 가짜 fetch 로.
//   node 08/client_api.ts
import { AgentCard } from "@a2a-js/sdk";
import {
  Client,
  ClientFactory,
  ClientFactoryOptions,
  JsonRpcTransportFactory,
} from "@a2a-js/sdk/client";

// region: api
// 요청 본문의 method 만 적어 두고, 늘 같은 JSON-RPC 오류로 답한다.
let sent = "";
const fake: typeof fetch = async (_url, init) => {
  const body = JSON.parse(String(init?.body));
  sent = body.method;
  const error = { code: -32601, message: "가짜" };
  return Response.json({ jsonrpc: "2.0", id: body.id, error });
};
const card = AgentCard.fromJSON({
  name: "가짜",
  supportedInterfaces: [
    { url: "http://fake.test/", protocolBinding: "JSONRPC" },
  ],
  // 클라이언트가 미리 막지 않게 기능을 다 켠다(3부)
  capabilities: {
    ...{ streaming: true, pushNotifications: true },
    extendedAgentCard: true,
  },
});
const transports = [new JsonRpcTransportFactory({ fetchImpl: fake })];
const client = await new ClientFactory({
  transports,
}).createFromAgentCard(card);
const names = Object.getOwnPropertyNames(Client.prototype);
for (const name of names.filter((n) => n !== "constructor")) {
  const fn = (client as unknown as Record<string, Function>)[name];
  if (typeof fn !== "function") continue; // protocolVersion 게터
  sent = "";
  try {
    const r = fn.call(client, { message: undefined });
    if (Symbol.asyncIterator in r) for await (const _ of r);
    else await r;
  } catch {} // 가짜 오류 — 보낸 것만 본다
  console.log(`  ${name.padEnd(33)} ${sent || "(보내지 않음)"}`);
}
// endregion
const kinds = ClientFactoryOptions.default.transports;
console.log(
  "기본 팩토리의 전송:",
  kinds.map((t) => t.protocolName),
);
console.log("client.protocolVersion:", client.protocolVersion);
