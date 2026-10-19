// 다시 해도 되는 실패만, 간격을 두 배씩 늘려 다시 한다.
//   node 17/retry.ts 카드주소 죽은주소
import { setTimeout as sleep } from "node:timers/promises";
import { Role, type Message } from "@a2a-js/sdk";
import { ClientFactory } from "@a2a-js/sdk/client";

const BUS = { headcount: 30, nights: 1, depart: "강남역" };

// region: retry
// safe — 두 번 해도 결과가 같은 호출(Get·List·Cancel)인가
async function retry(call: () => Promise<unknown>, safe: boolean) {
  let wait = 100;
  for (let n = 1; ; n++) {
    try {
      return await call();
    } catch (e) {
      const err = e as Error & { cause?: { code?: string } };
      // 요청이 떠나지도 못한 실패는 늘 다시 해도 된다.
      // 그 밖의 전송 실패(시간 초과 등)는 safe 일 때만.
      const refused = err.cause?.code === "ECONNREFUSED";
      const again = refused || (safe && err.name === "TimeoutError");
      const kind = refused ? "ECONNREFUSED" : err.name;
      if (!again || n === 4) {
        console.log(`  시도 ${n}: ${kind} → 그만`);
        throw e;
      }
      console.log(`  시도 ${n}: ${kind} → ${wait / 1000}초 뒤 다시`);
      await sleep(wait);
      wait *= 2; // 지수 백오프(실제로는 지터를 더한다)
    }
  }
}
// endregion

async function attempt(
  title: string,
  call: () => Promise<unknown>,
  safe: boolean,
) {
  console.log(title);
  await retry(call, safe).catch(() => {});
}

// region: main
const factory = new ClientFactory();
const live = await factory.createFromUrl(process.argv[2]!);
const get = {
  tenant: "",
  id: "no-such-task",
  historyLength: undefined,
};
await attempt("① 없는 작업", () => live.getTask(get), true);
const part = {
  ...{ filename: "", mediaType: "", metadata: undefined },
  content: { $case: "data" as const, value: BUS },
};
const message: Message = {
  ...{ messageId: "m-retry", taskId: "", contextId: "" },
  ...{ role: Role.ROLE_USER, parts: [part], metadata: undefined },
  ...{ extensions: [], referenceTaskIds: [] },
};
const send = { tenant: "", message, configuration: undefined };
const first = () =>
  live.sendMessage(
    { ...send, metadata: undefined },
    { signal: AbortSignal.timeout(1500) }, // 시도마다 새 제한
  );
await attempt("② 1.5초에 끊긴 SendMessage", first, false);
// 실험용 — 카드의 주소만 아무도 듣지 않는 포트로 바꿔 끼운다
const card = structuredClone(await live.getAgentCard());
card.supportedInterfaces[0]!.url = process.argv[3]!;
const gone = await factory.createFromAgentCard(card);
await attempt("③ 죽은 주소에 GetTask", () => gone.getTask(get), true);
// endregion
//@ norun
