// 한 카드에 바인딩 둘 — 클라이언트는 어느 문으로 들어가나.
//   node 08/mt_client.ts BASE
import { Message, type Part } from "@a2a-js/sdk";
import {
  ClientFactory,
  ClientFactoryOptions,
  RestTransportFactory,
} from "@a2a-js/sdk/client";

const text = (p: Part) =>
  p.content?.$case === "text" ? p.content.value : "";

// region: pick
const base = process.argv[2]!;
const { default: dflt, createFrom } = ClientFactoryOptions;
const ways: [string, ClientFactoryOptions][] = [
  ["기본(카드 차례)", dflt],
  [
    "HTTP+JSON 을 앞세움",
    createFrom(dflt, {
      preferredTransports: ["HTTP+JSON"],
    }),
  ],
  ["REST 만 앎", { transports: [new RestTransportFactory()] }],
];
for (const [label, options] of ways) {
  const client = await new ClientFactory(options).createFromUrl(base);
  const message = Message.fromJSON({
    ...{ messageId: `mt-${label.length}`, role: "ROLE_USER" },
    parts: [{ text: label }],
  });
  const req = { tenant: "", message, configuration: undefined };
  const r = await client.sendMessage({ ...req, metadata: undefined });
  const said = "messageId" in r ? r.parts.map(text).join("") : "Task";
  const proto = client.transport.protocolName;
  console.log(`${proto.padEnd(9)} ← ${label} — ${said}`);
}
// endregion
//@ norun
