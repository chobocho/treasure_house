// 기획 에이전트(agents/planner.ts)를 탭 뒤에 띄운다 — 15/planner_at.ts
// 에 카드에 적을 바깥 주소(탭의 포트)를 하나 더 받는다.
//   node 15/planner_via.ts 포트 탭포트 동료포트…
const [port, tap, ...peers] = process.argv.slice(2);
const agents = peers.map((p) => `http://127.0.0.1:${p}/`).join(",");
const url = `http://127.0.0.1:${tap}/`;
process.argv.splice(2, Infinity, "--port", port!, "--url", url);
process.argv.push("--agents", agents);
await import("../agents/planner.ts");
//@ norun
