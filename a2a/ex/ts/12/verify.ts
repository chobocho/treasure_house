// 정산 카드의 서명을 SDK 로 검증한다 — 진짜 카드, 고친 카드 둘,
// 가짜 카드를 미리 받아 둔 키로, 마지막엔 가짜 카드의 jku 를 따라가서.
//   node 12/verify.ts 진짜주소 가짜주소
import {
  createPublicKey,
  type JsonWebKey,
  type KeyObject,
} from "node:crypto";
import { readFileSync } from "node:fs";
import { verifyAgentCardSignature, type AgentCard } from "@a2a-js/sdk";

const [REAL, FAKE] = process.argv.slice(2) as [string, string];
type Jwk = JsonWebKey & { kid: string };
// SDK 는 틀린 서명마다 console.debug 로 그 서명과 오류를 통째로
// 찍는다(dist/index.js 의 verifyAgentCardSignature). 화면이 넘쳐 끈다.
console.debug = () => {};

async function cardJson(url: string) {
  const r = await fetch(url + ".well-known/agent-card.json");
  return (await r.json()) as Record<string, any>;
}

// region: verifiers
// 미리 받아 둔 공개 키(ex/fixtures/keys/jwks.json)만 믿는다
const path = new URL("../../fixtures/keys/jwks.json", import.meta.url);
const jwks = JSON.parse(readFileSync(path, "utf-8")) as { keys: Jwk[] };
const keys = new Map<string, KeyObject>(
  jwks.keys.map((k) => [
    k.kid,
    createPublicKey({ key: k, format: "jwk" }),
  ]),
);
const pinned = verifyAgentCardSignature(async (kid) => {
  const key = keys.get(kid);
  if (key === undefined) throw Error(`모르는 키 ${kid}`);
  return key;
});

// 카드가 가리키는 JWKS 를 그대로 믿는다
const trusting = verifyAgentCardSignature(async (kid, jku) => {
  const got = (await (await fetch(jku!)).json()) as { keys: Jwk[] };
  const jwk = got.keys.find((k) => k.kid === kid)!;
  return createPublicKey({ key: jwk, format: "jwk" });
});
// endregion

// region: main
async function check(
  label: string,
  raw: object,
  verify: typeof pinned,
) {
  try {
    await verify(raw as AgentCard);
    console.log(`${label} → 맞음`);
  } catch (e) {
    console.log(`${label} → 틀림: ${(e as Error).message}`);
  }
}

const real = await cardJson(REAL);
const fake = await cardJson(FAKE);
const moved = structuredClone(real);
const flows = moved.securitySchemes.oauth.oauth2SecurityScheme.flows;
flows.clientCredentials.tokenUrl = FAKE + "oauth/token";
await check("① 진짜 카드", real, pinned);
await check("② tokenUrl 을 바꾼 진짜 카드", moved, pinned);
await check(
  "③ 모르는 필드를 더한 진짜 카드",
  { ...real, note: "덧붙임" },
  pinned,
);
await check("④ 가짜 카드", fake, pinned);
await check("⑤ 가짜 카드, jku 를 따라가면", fake, trusting);
// endregion
//@ norun
