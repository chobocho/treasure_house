// 진입점마다 dist 번들이 몇 줄이고, 원본(src/) 모듈 몇 개를 품었나.
//   node 08/sdk_map.ts
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const entry = fileURLToPath(import.meta.resolve("@a2a-js/sdk"));
const ROOT = dirname(dirname(entry));
const pkg = JSON.parse(
  readFileSync(join(ROOT, "package.json"), "utf8"),
);
const exportsMap = pkg.exports as Record<string, { import: string }>;
const comma = (n: number) => n.toLocaleString("en-US");

// region: map
// tsup 은 번들 안에 원본 파일마다 "// src/…" 머리 줄을 남긴다
const where = new Map<string, Set<string>>(); // 원본 → 진입점들
let total = 0;
console.log("진입점                         줄 수  원본 모듈");
for (const [key, files] of Object.entries(exportsMap)) {
  const js = readFileSync(join(ROOT, files.import), "utf8");
  const lines = js.split("\n").length - 1;
  const srcs = new Set(js.match(/^\/\/ src\/\S+/gm) ?? []);
  for (const s of srcs) {
    if (!where.has(s)) where.set(s, new Set());
    where.get(s)!.add(key);
  }
  total += lines;
  const n = String(srcs.size).padStart(3);
  console.log(`  ${key.padEnd(28)} ${comma(lines).padStart(6)}  ${n}`);
}
// endregion
console.log(`  합계 ${comma(total)}줄, 서로 다른 원본 ${where.size}개`);

// region: shared
console.log("여러 번들에 사본이 든 원본 (많은 차례로 다섯)");
const shared = [...where].sort(
  (a, b) => b[1].size - a[1].size || a[0].localeCompare(b[0]),
);
for (const [src, keys] of shared.slice(0, 5)) {
  const name = src.slice(3);
  console.log(`  ${name.padEnd(40)} 번들 ${keys.size}개`);
}
// endregion
