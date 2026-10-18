// 기획 에이전트(agents/planner.ts)를 동료의 포트만 받아 띄운다 — 주소를
// 쉼표로 이은 --agents 가 명세 한 줄(72칸)에 들어가지 않아서.
//   node 15/planner_at.ts 포트 동료포트…
const [port, ...peers] = process.argv.slice(2);
const agents = peers.map((p) => `http://127.0.0.1:${p}/`).join(",");
process.argv.splice(2, Infinity, "--port", port!, "--agents", agents);
await import("../agents/planner.ts");
//@ norun
