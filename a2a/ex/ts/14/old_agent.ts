// 완성 숙소 에이전트(agents/lodging.ts)를 판 0.3 문 하나만 적은 카드로
// 띄운다 — v0.3 만 아는 옛 에이전트의 흉내.
//   node 14/old_agent.ts --port P [--url U]
// 13부의 해석 훅과 같다 — ./common.ts 를 14/old_common.ts 로
// 바꿔 끼운다.
import { registerHooks } from "node:module";

// region: hook
registerHooks({
  resolve(spec, ctx, next) {
    if (spec === "./common.ts" && ctx.parentURL?.includes("/agents/")) {
      const swap = new URL("./old_common.ts", import.meta.url);
      return next(swap.href, ctx);
    }
    return next(spec, ctx);
  },
});
await import("../agents/lodging.ts");
// endregion
//@ norun
