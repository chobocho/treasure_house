// 완성 숙소·식사 에이전트(agents/*.ts)를 고치지 않고 HTTP+JSON(REST)
// 문 하나로 띄운다.
//   node 13/rest_agent.ts lodging --port P [--url U]
// 그 파일들은 모듈 맨 위에서 common.ts 의 serve(…) 를 부른다. 그래서
// import 하기 전에 해석 훅을 걸어, 에이전트가 가져가는 ./common.ts 를
// 13/rest_common.ts 로 바꿔 끼운다(실행기·카드는 진짜 그대로).
import { registerHooks } from "node:module";

const agent = process.argv[2];
process.argv.splice(2, 1); // 에이전트의 parseCli 는 --port 만 안다

// region: hook
registerHooks({
  resolve(spec, ctx, next) {
    if (spec === "./common.ts" && ctx.parentURL?.includes("/agents/")) {
      const swap = new URL("./rest_common.ts", import.meta.url);
      return next(swap.href, ctx);
    }
    return next(spec, ctx);
  },
});
await import(`../agents/${agent}.ts`);
// endregion
//@ norun
