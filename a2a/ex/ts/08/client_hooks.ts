// 클라이언트의 갈고리 둘 — 우리 fetch 와 가로채기.
// 상대는 머리글을 되돌려 주는 실험 서버(08/headers.ts)다. 그 서버엔
// 카드 경로가 없어 카드를 손에 쥔 채로 클라이언트를 만든다.
//   node 08/client_hooks.ts URL
import { Message, type Part } from "@a2a-js/sdk";
import {
  ClientFactory,
  ClientFactoryOptions,
  JsonRpcTransportFactory,
  type AfterArgs,
  type BeforeArgs,
  type CallInterceptor,
} from "@a2a-js/sdk/client";
import { card } from "./step1_echo.ts";

// region: fetch
// 전송이 부르는 fetch — 나가는 요청의 판 머리글과 팀 머리글을 찍는다
const logged: typeof fetch = (input, init) => {
  const h = new Headers(init?.headers);
  const ver = h.get("A2A-Version");
  const team = h.get("X-Workshop-Team");
  console.log(`  fetch A2A-Version=${ver} X-Workshop-Team=${team}`);
  return fetch(input, init);
};
// endregion

// region: interceptor
// 보내기 전에 머리글을 하나 달고, 받은 뒤 답의 모양을 찍는다
class TeamHeader implements CallInterceptor {
  async before(args: BeforeArgs) {
    console.log(`  before ${args.input?.method}`);
    const opts = args.options ?? {};
    const team = { "X-Workshop-Team": "general-affairs" };
    // serviceParameters 가 HTTP 머리글이 된다
    opts.serviceParameters = { ...opts.serviceParameters, ...team };
    args.options = opts;
  }
  async after(args: AfterArgs) {
    const v = args.result?.value as object;
    const kind = "messageId" in v ? "Message" : "그 밖";
    console.log(`  after  ${args.result?.method} → ${kind}`);
  }
}
// endregion

// region: main
const options = ClientFactoryOptions.createFrom(
  ClientFactoryOptions.default,
  {
    transports: [new JsonRpcTransportFactory({ fetchImpl: logged })],
    clientConfig: { interceptors: [new TeamHeader()] },
  },
);
const client = await new ClientFactory(options).createFromAgentCard(
  card(process.argv[2]!),
);
const message = Message.fromJSON({
  ...{ messageId: "h-1", role: "ROLE_USER" },
  parts: [{ text: "누구세요" }],
});
const req = { tenant: "", message, configuration: undefined };
// 판 머리글을 손으로 0.3 이라고 적어 본다
const r = await client.sendMessage(
  { ...req, metadata: undefined },
  { serviceParameters: { "A2A-Version": "0.3" } },
);
const texts = "messageId" in r ? r.parts.map(text) : [];
console.log(" ", texts.join(" | "));
// endregion

function text(p: Part) {
  return p.content?.$case === "text" ? p.content.value : "";
}
//@ norun
