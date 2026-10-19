// 정수 자리 손질(asInts) 시험 — 수로 읽을 수 없는 값은 0 이 되어
// 업무 규칙이 거절해야 한다. Go 의 common.Int 와 같은 약속이다.
// 고친 판(test_ints.ts)과 고치기 전 판(test_ints_old.ts)이 함께 쓴다.
import assert from "node:assert/strict";
import { test } from "node:test";
import {
  chooseLodging,
  type LodgingRequest,
} from "../workshop/domain.ts";

type AsInts = (
  d: Record<string, unknown>,
  ...keys: string[]
) => Record<string, unknown>;
const BAD = { date: "2026-10-30", nights: 1, headcount: "서른" };
const BAD_SIZE = "인원과 박 수는 1 이상이어야 합니다"; // SCENARIO §2.7

// region: tests
export function cases(asInts: AsInts) {
  test("numbers come back as ints", () => {
    const got = asInts(
      { nights: 1.0, headcount: "30" },
      "nights",
      "headcount",
    );
    assert.deepEqual(got, { nights: 1, headcount: 30 });
  });
  test("not a number is zero", () => {
    assert.equal(asInts(BAD, "nights", "headcount").headcount, 0);
  });
  test("lodging rejects it", () => {
    const req = asInts(BAD, "nights", "headcount") as LodgingRequest;
    const got = chooseLodging(req); // 견적이 나오면 총액을 적는다
    assert.equal(got.ok ? `${got.total}원 견적` : got.reason, BAD_SIZE);
  });
}
// endregion
//@ norun
