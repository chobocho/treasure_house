// 이 책의 캡처를 찍은 TypeScript 쪽 판 — 설치본에게 직접 묻는다.
import { readFileSync } from "node:fs";
import { A2A_PROTOCOL_VERSION } from "@a2a-js/sdk";

// node_modules 안 패키지의 package.json 을 읽는다
function pkg(name: string): { name: string; version: string } {
  const url = new URL(
    `../node_modules/${name}/package.json`,
    import.meta.url,
  );
  return JSON.parse(readFileSync(url, "utf8"));
}

// region: show
console.log("node      ", process.version);
console.log("@a2a-js/sdk", pkg("@a2a-js/sdk").version);
console.log("프로토콜  ", A2A_PROTOCOL_VERSION);
console.log("express   ", pkg("express").version);
console.log("typescript", pkg("typescript").version);
// tsc 7 은 이 이름의 패키지에서
// 제 실행 파일(네이티브)을 찾는다
const plat = `${process.platform}-${process.arch}`;
const want = `@typescript/typescript-${plat}`;
const got = pkg(want);
console.log(`찾는 이름 ${want}`);
console.log(`실제 내용 ${got.name} ${got.version}`);
// endregion
