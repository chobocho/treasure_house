// 고치기 전의 기획 에이전트(15/planner_old.ts)를 동료의 포트만 받아
// 띄운다 — 15/planner_at.ts 와 같은 겉층.
//   node 15/old_at.ts 포트 동료포트…
const [port, ...peers] = process.argv.slice(2);
const agents = peers.map((p) => `http://127.0.0.1:${p}/`).join(",");
process.argv.splice(2, Infinity, "--port", port!, "--agents", agents);
await import("./planner_old.ts");
//@ norun
