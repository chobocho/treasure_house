// 숙소 에이전트 시험 — 완성판을 서버 없이 불러와 처리기로 부른다.
//   node 08/run_tests.ts 08/test_lodging.ts
import { loadLodging } from "./load_lodging.ts";
import { lodgingSuite } from "./lodging_suite.ts";

const { card, executor } = await loadLodging("http://lodging.test/");
lodgingSuite("완성판", executor, card);
//@ norun
