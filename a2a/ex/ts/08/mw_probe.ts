// 앞에 둔 파서가 바꾸는 것 — 본문 한도와 깨진 JSON 의 답.
//   node 08/mw_probe.ts BASE
const base = process.argv[2]!;

// region: probe
// 150 KB 쯤 되는 정상 요청 하나와, 끝이 잘린 JSON 하나
const message = {
  ...{ messageId: "big-1", role: "ROLE_USER" },
  parts: [{ text: "가".repeat(50_000) }], // UTF-8 로 150,000 바이트
};
const big = JSON.stringify({
  ...{ jsonrpc: "2.0", id: 1, method: "SendMessage" },
  params: { message },
});
const broken = '{"jsonrpc": "2.0", "id": 2, "method": "Send';
for (const path of ["rpc", "big"]) {
  for (const [label, body] of [
    ["150KB", big],
    ["깨진 JSON", broken],
  ]) {
    const res = await fetch(base + path, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "A2A-Version": "1.0",
      },
      body,
    });
    const type = res.headers.get("Content-Type")?.split(";")[0];
    const head = (await res.text()).replace(/\s+/g, " ").slice(0, 48);
    console.log(`/${path} ${label}: ${res.status} ${type} ${head}`);
  }
}
// endregion
//@ norun
