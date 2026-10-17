// 완성 에이전트(agents/*.ts)가 SDK 에서 가져다 쓰는 이름을 센다.
//   node 08/used_names.ts
import { readdirSync, readFileSync } from "node:fs";

// region: scan
// import { A, type B } from "@a2a-js/sdk/…"; 꼴을 모두 찾는다
const IMPORT =
  /import\s+(type\s+)?\{([^}]*)\}\s+from\s+"(@a2a-js[^"]*)"/g;
const uses = new Map<string, Map<string, Set<string>>>();
for (const file of readdirSync("agents").sort()) {
  const src = readFileSync(`agents/${file}`, "utf8");
  for (const m of src.matchAll(IMPORT)) {
    const mod = m[3]!;
    if (!uses.has(mod)) uses.set(mod, new Map());
    for (const raw of m[2]!.split(",")) {
      const name = raw.replace(/^\s*type\s+/, "").trim();
      if (!name) continue;
      const files = uses.get(mod)!.get(name) ?? new Set<string>();
      uses.get(mod)!.set(name, files.add(file));
    }
  }
}
// endregion

let names = 0;
for (const mod of [...uses.keys()].sort()) {
  console.log(`${mod}:`);
  const row = [...uses.get(mod)!].sort((a, b) =>
    a[0] < b[0] ? -1 : 1,
  );
  const words = row.map(([n, f]) => `${n}(${f.size})`);
  names += words.length;
  // 한 줄이 72칸을 넘지 않게 접는다
  let line = "   ";
  for (const w of words) {
    if (line.length + w.length > 72) {
      console.log(line);
      line = "   ";
    }
    line += " " + w;
  }
  console.log(line);
}
console.log(`이름 ${names} 개, 모듈 ${uses.size} 개`);
