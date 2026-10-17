// 설치된 @a2a-js/sdk 의 package.json 을 읽어 진입점과 의존을 센다.
//   node 08/sdk_exports.ts
import { existsSync, readFileSync } from "node:fs";
import { isBuiltin } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// dist/index.js 에서 두 칸 올라가면 패키지 뿌리다
const entry = fileURLToPath(import.meta.resolve("@a2a-js/sdk"));
const ROOT = dirname(dirname(entry));
const pkg = JSON.parse(
  readFileSync(join(ROOT, "package.json"), "utf8"),
);
const MODULES = join(ROOT, "..", "..");
const has = (name: string) =>
  existsSync(join(MODULES, name)) ? "O" : ".";
// "@bufbuild/protobuf/wire" → "@bufbuild/protobuf", crypto → node 내장
function pkgOf(spec: string) {
  if (isBuiltin(spec)) return `${spec}(node 내장)`;
  const n = spec.startsWith("@") ? 2 : 1;
  const name = spec.split("/").slice(0, n).join("/");
  return `${name}(${has(name)})`;
}

console.log(`${pkg.name} ${pkg.version}`);
console.log(
  "늘 따라오는 의존:",
  Object.keys(pkg.dependencies).join(" "),
);

// region: exports
// 진입점마다 번들(dist/…/index.js)이 import 하는 바깥 패키지
const bare = /^import .* from "([^".][^"]*)";$/gm;
const exportsMap = pkg.exports as Record<string, { import: string }>;
const keys = Object.keys(exportsMap);
console.log(`진입점 ${keys.length}개 (package.json "exports")`);
for (const key of keys) {
  const js = readFileSync(join(ROOT, exportsMap[key]!.import), "utf8");
  const uses = [...js.matchAll(bare)].map((m) => pkgOf(m[1]!));
  const shown = [...new Set(uses)].sort().join(" ");
  console.log(`  ${key.padEnd(28)} ${shown || "-"}`);
}
// endregion

const peers = Object.keys(pkg.peerDependencies);
const optional = pkg.peerDependenciesMeta as object;
const all = peers.every((p) => p in optional);
console.log(`peer ${peers.length}개, 모두 선택(optional): ${all}`);
console.log("  " + peers.map((p) => `${p}(${has(p)})`).join(" "));
