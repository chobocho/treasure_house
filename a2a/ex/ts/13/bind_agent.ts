// 완성 에이전트(agents/*.ts)를 고치지 않고 다른 문으로 띄운다.
//   node 13/bind_agent.ts grpc 에이전트 --port P --grpc-port G …
//   node 13/bind_agent.ts doors 에이전트 --port P --grpc-port G …
// 13/rest_agent.ts 와 같은 해석 훅이다. 에이전트가 가져가는
// ./common.ts 를 13/<문>_common.ts 로 바꿔 끼운다.
import { registerHooks } from "node:module";

const [doors, agent] = process.argv.splice(2, 2);

// region: hook
registerHooks({
  resolve(spec, ctx, next) {
    if (spec === "./common.ts" && ctx.parentURL?.includes("/agents/")) {
      const swap = new URL(`./${doors}_common.ts`, import.meta.url);
      return next(swap.href, ctx);
    }
    return next(spec, ctx);
  },
});
await import(`../agents/${agent}.ts`);
// endregion
//@ norun
