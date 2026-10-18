// 예산 확장을 켜고 숙소 견적을 묻는 TypeScript SDK 클라이언트.
//   node 14/budget_client.ts URL
import { Message, type Artifact } from "@a2a-js/sdk";
import {
  ClientFactory,
  ServiceParameters,
  withA2AExtensions,
} from "@a2a-js/sdk/client";

const URI = "https://treasure-house.example/a2a/ext/budget/v1";
const won = (n: number) => n.toLocaleString("en-US") + "원";

// region: send
async function main(url: string) {
  const client = await new ClientFactory().createFromUrl(url);
  const card = await client.getAgentCard();
  const ext = card.capabilities?.extensions?.find((e) => e.uri === URI);
  console.log("카드:", ext?.required ? "필수" : "선택");
  const message = Message.fromJSON({
    ...{ messageId: "b-1", role: "ROLE_USER" },
    parts: [{ data: { date: "2026-10-30", nights: 1, headcount: 30 } }],
    extensions: [URI], // 이 메시지에 확장의 데이터가 있다
    metadata: { [URI]: { limit: 2000000 } },
  });
  // 켜 달라는 요청은 메시지가 아니라 서비스 매개변수(머리글)로
  const serviceParameters = ServiceParameters.create(
    withA2AExtensions(URI),
  );
  const r = await client.sendMessage(
    {
      tenant: "",
      message,
      configuration: undefined,
      metadata: undefined,
    },
    { serviceParameters },
  );
  if (!("messageId" in r)) show(r.artifacts[0]!);
}
// endregion

// region: show
function show(art: Artifact) {
  const c = art.parts[0]?.content;
  const total = c?.$case === "data" ? Number(c.value.total) : NaN;
  const got = art.metadata?.[URI];
  if (got === undefined) {
    console.log(`견적 ${won(total)} · 판정 없음`);
    return;
  }
  const verdict = got.within ? "안" : "넘음";
  console.log(`견적 ${won(total)} · 상한 ${won(got.limit)} ${verdict}`);
}
// endregion

await main(process.argv[2]!);
//@ norun
