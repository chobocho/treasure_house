// node --test 를 프로그램으로 — 걸린 시간을 찍지 않는 보고기를 단다.
//   node 08/run_tests.ts 08/test_lodging.ts
// 하는 일은 아래 명령과 같다(보고 모양만 우리 것):
//   node --test --experimental-test-module-mocks 08/test_lodging.ts
// 내장 보고기는 시험마다 "(3.7ms)" 를 찍어 실행마다 글자가 달라진다.
import { run } from "node:test";

type Row = { depth: number; name: string; ok?: boolean; why?: string };

// region: runner
const rows: Row[] = []; // 시험이 시작한 차례(나무를 위에서 아래로)
const stream = run({
  files: process.argv.slice(2),
  execArgv: ["--experimental-test-module-mocks"], // mock.module 용
});
stream.on("test:start", (d) => {
  rows.push({ depth: d.nesting, name: d.name });
});
stream.on("test:pass", (d) => settle(d.nesting, d.name, true));
stream.on("test:fail", (d) => {
  const err = d.details.error as Error & { cause?: unknown };
  settle(d.nesting, d.name, false, reason(err.cause ?? err));
  process.exitCode = 1;
});
stream.on("test:stderr", (d) => {
  const line = d.message.trimEnd(); // 프로세스 번호는 실행마다 다르다
  console.log("stderr:", line.replace(/\(node:\d+\)/, "(node:<pid>)"));
});
// 에이전트의 서버 로그(test:stdout)는 시험의 관심사가 아니라 버린다
stream.on("end", () => {
  for (const r of rows) {
    const mark = r.ok ? "✔" : "✖";
    console.log(`${"  ".repeat(r.depth)}${mark} ${r.name}`);
    if (r.why) console.log(`${"  ".repeat(r.depth + 1)}${r.why}`);
  }
  const leaves = rows.filter(
    (r, i) => rows[i + 1]?.depth !== r.depth + 1,
  );
  const failed = leaves.filter((r) => !r.ok).length;
  console.log(`시험 ${leaves.length}, 통과 ${leaves.length - failed}`);
});
// endregion

// 실패한 까닭 한 줄 — assert 의 오류면 실제 값과 기대 값까지
function reason(e: unknown) {
  if (!(e instanceof Error)) return String(e);
  const first = e.message.split("\n")[0];
  if (!("expected" in e)) return first;
  const { actual, expected } = e as Record<string, unknown>;
  const [a, b] = [actual, expected].map((v) => JSON.stringify(v));
  return `${first} 실제 ${a}, 기대 ${b}`;
}

// 끝난 시험을 아직 결과가 없는 같은 이름·깊이의 줄에 붙인다
function settle(depth: number, name: string, ok: boolean, why = "") {
  const r = rows.findLast(
    (x) => x.depth === depth && x.name === name && x.ok === undefined,
  );
  if (r) Object.assign(r, { ok, why });
}
stream.resume();
//@ norun
