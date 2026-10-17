// 이 부에서 쓸 이름이 설치본의 어느 파일·몇째 줄에 있나.
//   node 08/where.ts
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const entry = fileURLToPath(import.meta.resolve("@a2a-js/sdk"));
const DIST = dirname(entry);

// region: where
// 번들(.js)에서 정의 줄을 찾고, 그 위의 "// src/…" 로 원본을 안다.
// 타입만 있는 이름(interface)은 .js 에 없어 .d.ts 에서 찾는다.
function where(name: string, file: string) {
  for (const ext of [".js", ".d.ts"]) {
    const path = join(DIST, file + ext);
    const lines = readFileSync(path, "utf8").split("\n");
    const def = new RegExp(
      `^(var ${name} = |function ${name}\\(|interface ${name} )`,
    );
    const at = lines.findIndex((l) => def.test(l));
    if (at < 0) continue;
    const src = lines
      .slice(0, at)
      .findLast((l) => l.startsWith("// src/"));
    const from = src ? `  ← ${src.slice(3)}` : "  (타입만)";
    const place = `dist/${file}${ext}:${at + 1}`;
    console.log(`${name.padEnd(25)} ${place}${from}`);
    return;
  }
  console.log(`${name.padEnd(25)} 못 찾음`);
}
// endregion

where("Part", "index");
where("TaskState", "index");
where("AgentExecutor", "server/index");
where("RequestContext", "server/index");
where("AgentEvent", "server/index");
where("DefaultExecutionEventBus", "server/index");
where("DefaultRequestHandler", "server/index");
where("InMemoryTaskStore", "server/index");
where("jsonRpcHandler", "server/express/index");
where("agentCardHandler", "server/express/index");
