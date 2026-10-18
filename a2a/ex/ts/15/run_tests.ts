// 15/test_planner.ts 를 08/run_tests.ts 로 돌린다 — 명세가 15부의
// 예제를 부르게 해서 시험 파일이 캡처의 입력(ex/ts/15)에 들게 한다.
//   node 15/run_tests.ts
process.argv.splice(2, Infinity, "15/test_planner.ts");
await import("../08/run_tests.ts");
//@ norun
