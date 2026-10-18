// HTTPS 로 카드를 두 번 읽는다 — 기본 신뢰 목록으로 한 번, 시험 CA 를
// 믿게 하고 한 번. 서버 인증서 검사는 SDK 가 아니라 Node 의 일이다.
//   node 12/tls_card.ts https://127.0.0.1:P/ CA파일
import { readFileSync } from "node:fs";
import tls from "node:tls";
import { DefaultAgentCardResolver } from "@a2a-js/sdk/client";

const [url, ca] = process.argv.slice(2) as [string, string];

// region: main
// 보안 스킴이 있는 카드는 리졸버가 ts-proto 객체로 바꿔 돌려준다
// (없으면 JSON 그대로 — 8부). 그래서 oneof 는 $case 로 읽는다.
async function card() {
  return new DefaultAgentCardResolver().resolve(url);
}

try {
  await card(); // Node 에 든 공인 CA 목록
} catch (e) {
  const err = e as Error & { cause?: { code?: string } };
  console.log(`① 기본 신뢰 목록 → ${err.constructor.name}`);
  console.log(`   원인: ${err.message} / ${err.cause?.code}`);
}
// 이 프로세스의 TLS 기본 CA 를 시험 CA 하나로 바꾼다(Node 24)
tls.setDefaultCACertificates([readFileSync(ca, "utf-8")]);
const c = await card();
const scheme = c.securitySchemes["oauth"]?.scheme;
if (scheme?.$case !== "oauth2SecurityScheme") throw Error(url);
const flow = scheme.value.flows?.flow;
if (flow?.$case !== "clientCredentials") throw Error(url);
console.log(`② 시험 CA 를 믿으면 → ${c.name}`);
console.log(`   인터페이스 ${c.supportedInterfaces[0]?.url}`);
console.log(`   토큰 주소 ${flow.value.tokenUrl}`);
// endregion
//@ norun
