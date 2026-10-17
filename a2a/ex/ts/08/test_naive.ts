// 같은 시험을 3단계(이력 전부를 듣는 판)에 돌린다 — 빨간불 확인.
//   node 08/run_tests.ts 08/test_naive.ts
import { AskExecutor, card } from "./step3_ask.ts";
import { lodgingSuite } from "./lodging_suite.ts";

// region: naive
// 시험은 그대로, 실행기만 3단계로
lodgingSuite("3단계", new AskExecutor(), card("http://naive.test/"));
// endregion
//@ norun
