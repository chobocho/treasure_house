// 실행기가 채울 것과 쓸 것 — 설치본의 타입 파일에서 직접 읽는다.
//   node 08/executor_api.ts
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { AgentEvent } from "@a2a-js/sdk/server";

const entry = fileURLToPath(import.meta.resolve("@a2a-js/sdk/server"));
const DTS = join(dirname(entry), "index.d.ts");
const lines = readFileSync(DTS, "utf8").split("\n");

// region: api
// 선언 하나를 머리 줄부터 짝 맞는 } 까지, 문서 주석은 빼고 찍는다
function show(head: string) {
  const start = lines.findIndex((l) => l.startsWith(head));
  console.log(`── dist/server/index.d.ts:${start + 1}`);
  for (let i = start, depth = 0; i < lines.length; i++) {
    const l = lines[i]!;
    const t = l.trim();
    if (!t.startsWith("*") && !t.startsWith("/**")) console.log(l);
    depth += (l.match(/\{/g) ?? []).length;
    depth -= (l.match(/\}/g) ?? []).length;
    if (depth === 0 && i > start) break;
  }
}
show("interface AgentExecutor ");
show("interface ExecutionEventBus ");
console.log("AgentEvent:", Object.keys(AgentEvent).join(" "));
// endregion
