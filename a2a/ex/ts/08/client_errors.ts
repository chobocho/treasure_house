// 클라이언트 쪽에서 오류는 어떤 값으로 오나.
//   node 08/client_errors.ts URL DEAD_URL
// URL 은 숙소 에이전트, DEAD_URL 은 아무도 듣지 않는 주소다.
import { AgentCard, Message } from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";
import { A2AError } from "@a2a-js/sdk/errors";

function report(label: string, e: unknown) {
  const err = e as Error;
  const a2a = e instanceof A2AError ? "A2AError 갈래" : "SDK 오류 아님";
  console.log(`${label}: ${err.name} (${a2a})`);
  const line = err.message.split("\n")[0]!;
  console.log("   ", line.length > 90 ? line.slice(0, 90) + "…" : line);
  const cause = err.cause as (Error & { code?: string }) | undefined;
  const code = cause?.code ? ` ${cause.code}` : "";
  if (cause) console.log(`    cause: ${cause.name}${code}`);
}

// region: errors
const [url, dead] = process.argv.slice(2) as [string, string];
const factory = new ClientFactory();
try {
  await factory.createFromUrl(dead); // ① 카드를 받을 수 없다
} catch (e) {
  report("① 닿지 않는 카드", e);
}
try {
  await factory.createFromUrl(url + "nothing/"); // ② 카드 경로가 404
} catch (e) {
  report("② 없는 카드", e);
}
const client = await factory.createFromUrl(url);
try {
  await client.getTask({ tenant: "", id: "t-없음" }); // ③ JSON-RPC 오류
} catch (e) {
  report("③ 없는 작업", e);
}
const card = (await client.getAgentCard()) as AgentCard;
const bad = structuredClone(card); // 인터페이스 url 만 틀리게 고친 사본
bad.supportedInterfaces[0]!.url = url + "rpc";
const wrong = await factory.createFromAgentCard(bad);
const message = Message.fromJSON({
  ...{ messageId: "e-1", role: "ROLE_USER", parts: [{ text: "숙소" }] },
});
const req = { tenant: "", message, configuration: undefined };
try {
  await wrong.sendMessage({ ...req, metadata: undefined }); // ④ 404
} catch (e) {
  report("④ 틀린 url", e);
}
// endregion
//@ norun
