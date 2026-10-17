// 완성 숙소 에이전트(agents/lodging.ts)를 서버 없이 불러온다.
// 그 파일은 아무것도 내보내지 않고, 모듈 맨 위에서 parseCli() 와
// serve(…) 를 부른다. 그래서 그 둘이 든 common.ts 를 가짜로 바꿔
// 끼우고 import 해, serve 에 넘어오는 카드와 실행기를 가로챈다.
// node:test 의 mock.module — Node 24 에서는 실험 기능이라
// --experimental-test-module-mocks 로 돌려야 한다(08/run_tests.ts).
import { mock } from "node:test";
import type { AgentExecutor } from "@a2a-js/sdk/server";
import * as real from "../agents/common.ts";

export type Loaded = { card: object; executor: AgentExecutor };

// region: load
export async function loadLodging(url: string): Promise<Loaded> {
  let got: Loaded | undefined;
  mock.module("../agents/common.ts", {
    exports: {
      ...real, // begin·dataPart … 은 진짜 그대로
      parseCli: () => ({ port: 0, url, opts: {} }),
      serve: (card: object, executor: AgentExecutor) => {
        got = { card, executor }; // 띄우지 않고 받아만 둔다
      },
    },
  });
  await import("../agents/lodging.ts"); // 여기서 serve 가 불린다
  if (!got) throw new Error("serve 가 불리지 않았다");
  return got;
}
// endregion
//@ norun
