// 완성 숙소 에이전트(agents/lodging.ts)에 예산 확장을 씌워 띄운다.
//   node 14/budget_agent.ts --port P [--url U] [--required]
// 13부의 해석 훅과 같다 — 에이전트가 가져가는 ./common.ts 를
// 14/budget_common.ts 로 바꿔 끼운다(실행기·카드는 진짜 그대로).
import { registerHooks } from "node:module";
import { options } from "./budget_common.ts";

// 에이전트의 parseCli 는 --port·--url 만 안다
const at = process.argv.indexOf("--required");
if (at >= 0) process.argv.splice(at, 1);
options.required = at >= 0;

// region: hook
registerHooks({
  resolve(spec, ctx, next) {
    if (spec === "./common.ts" && ctx.parentURL?.includes("/agents/")) {
      const swap = new URL("./budget_common.ts", import.meta.url);
      return next(swap.href, ctx);
    }
    return next(spec, ctx);
  },
});
await import("../agents/lodging.ts");
// endregion
//@ norun
