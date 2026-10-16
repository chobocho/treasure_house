// JSON-RPC 2.0 클라이언트 — fetch 만으로. 요청마다 새 id 를 붙이고,
// 응답의 id 가 맞는지, result 인지 error 인지 가른다.
import { parseArgs } from "node:util";

const { values } = parseArgs({ options: { url: { type: "string" } } });
const url = values.url!;

// region: client
class RpcError extends Error {}

let lastId = 0;

async function call(url: string, method: string, params: unknown) {
  const id = ++lastId;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jsonrpc: "2.0", id, method, params }),
  });
  const reply = await res.json();
  if (reply.id !== id) {
    // 다른 요청의 답이면 받지 않는다
    throw new RpcError(`id 가 다르다: ${reply.id}`);
  }
  if ("error" in reply) {
    throw new RpcError(`${reply.error.code} ${reply.error.message}`);
  }
  return reply.result;
}
// endregion

// region: main
const Q = { date: "2026-10-30", nights: 1, headcount: 30 };
const q = await call(url, "ChooseLodging", Q);
console.log(`ChooseLodging → ${q.venueName} ${q.rooms}실 ${q.total}원`);
try {
  await call(url, "BookLodging", Q);
} catch (e) {
  if (!(e instanceof RpcError)) throw e;
  console.log(`BookLodging → 오류 ${e.message}`);
}
// endregion
//@ norun
