// 골든 벡터 시험 — ex/fixtures/golden/domain.json 의 기대값과 한 글자도
// 다르면 안 된다. 같은 파일을 Python·Go 시험도 읽는다.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as domain from "./domain.ts";

type Case = { name: string; input: unknown; expected: unknown };
const golden = JSON.parse(
  readFileSync(
    new URL("../../fixtures/golden/domain.json", import.meta.url),
    "utf-8",
  ),
) as Record<string, Case[]>;

// 골든 키(camelCase)가 곧 TypeScript 함수 이름이다.
const funcs: Record<string, (input: never) => unknown> = {
  chooseLodging: domain.chooseLodging,
  planMeals: domain.planMeals,
  chooseBuses: domain.chooseBuses,
  settle: domain.settle,
  parseRequest: domain.parseRequest,
};

for (const [name, fn] of Object.entries(funcs)) {
  for (const c of golden[name] ?? []) {
    test(`${name}/${c.name}`, () => {
      assert.deepStrictEqual(fn(c.input as never), c.expected);
    });
  }
}
