// 무엇으로 시험하나 — 깔려 있는 것부터 묻는다.
//   node 08/test_tools.ts
import { readFileSync } from "node:fs";
import * as nodeTest from "node:test";

const pkg = JSON.parse(readFileSync("package.json", "utf8"));
console.log("Node", process.version);
const dev = Object.keys(pkg.devDependencies);
console.log("devDependencies:", dev.join(" "));
// 흔한 시험 도구들 — 이 node_modules 에서 찾아지나(express 는 견줌)
const tools = ["express", "jest", "vitest", "mocha", "supertest"];
for (const name of tools) {
  let found = "없음";
  try {
    found = import.meta.resolve(name) ? "있음" : "없음";
  } catch {}
  console.log(`  ${name.padEnd(10)} ${found}`);
}
// 내장 node:test 가 내보내는 것
const names = Object.keys(nodeTest).filter((n) => n !== "default");
console.log("node:test:", names.sort().join(" "));
console.log("mock.module:", typeof nodeTest.mock.module);
