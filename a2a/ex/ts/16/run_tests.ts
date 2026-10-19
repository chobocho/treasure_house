// 16/test_ints*.ts 를 08/run_tests.ts 로 돌린다 — 명세가 16부의
// 예제를 부르게 해서 시험 파일이 캡처의 입력(ex/ts/16)에 들게 한다.
//   node 16/run_tests.ts        고친 판
//   node 16/run_tests.ts old    고치기 전 판
const old = process.argv[2] === "old";
const file = old ? "16/test_ints_old.ts" : "16/test_ints.ts";
process.argv.splice(2, Infinity, file);
await import("../08/run_tests.ts");
//@ norun
