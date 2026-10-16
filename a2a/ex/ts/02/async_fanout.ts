// 비동기 두 가지 — (1) 차례로 생기는 이벤트를 하나씩 받기,
// (2) 세 견적을 한꺼번에 기다리기. Promise 와 async 이터레이터.
import { setTimeout as sleep } from "node:timers/promises";
import {
  chooseBuses,
  chooseLodging,
  planMeals,
} from "../workshop/domain.ts";

const LODGING = { date: "2026-10-30", nights: 1, headcount: 30 };
const MEALS = { nights: 1, headcount: 30, vegetarians: 2 };
const BUS = { headcount: 30, nights: 1 };
type Ruled = { ok: true; total: number } | { ok: false };

// region: steps
async function* steps() {
  // 비동기 제너레이터: 기다렸다가 하나씩 내놓는다
  for (const s of ["배차 요청 접수", "기사 배정", "차량 확정"]) {
    await sleep(50);
    yield s;
  }
}
// endregion

// region: fanout
async function quote(name: string, ms: number, rule: () => Ruled) {
  await sleep(ms); // 다른 에이전트에 묻는 시간인 셈
  console.log("끝남:", name);
  const r = rule();
  return [name, r.ok ? r.total : 0] as const;
}

for await (const s of steps()) console.log("상태:", s); // 생기는 대로

// 셋을 동시에 띄우고 모두 기다린다 — 결과는 넘긴 순서대로
const results = await Promise.all([
  quote("숙소", 300, () => chooseLodging(LODGING)),
  quote("식사", 100, () => planMeals(MEALS)),
  quote("교통", 200, () => chooseBuses(BUS)),
]);
console.log(
  "모은 순서:",
  results.map(([n, t]) => `${n} ${t}`).join(" · "),
);
console.log(
  "합계:",
  results.reduce((sum, [, t]) => sum + t, 0),
);
// endregion
