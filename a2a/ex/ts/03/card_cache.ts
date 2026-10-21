// 카드를 한 번 받고, 받은 ETag 으로 조건부 GET 을 한 번 더 한다.
// fetch 만 — 서버가 캐시 머리글을 어떻게 다는지 보려는 것.
//   node 03/card_cache.ts 카드주소...
const WELL_KNOWN = "/.well-known/agent-card.json";

// region: get
async function get(url: string, etag?: string) {
  const headers: Record<string, string> = {};
  if (etag) headers["If-None-Match"] = etag;
  const res = await fetch(url, { headers });
  await res.arrayBuffer(); // 본문을 다 읽어 연결을 돌려준다
  return res;
}
// endregion

// region: main
for (const base of process.argv.slice(2)) {
  const url = base.replace(/\/$/, "") + WELL_KNOWN;
  const first = await get(url);
  const etag = first.headers.get("ETag");
  console.log(base);
  console.log(`  GET → ${first.status} · ETag ${etag ?? "-"}`);
  const cc = first.headers.get("Cache-Control");
  console.log(`    Cache-Control ${cc ?? "-"}`);
  if (etag === null) {
    console.log("  ETag 이 없다 — 조건부로 물을 수 없다");
    continue;
  }
  const again = await get(url, etag);
  console.log(`  GET If-None-Match → ${again.status}`);
}
// endregion
//@ norun
