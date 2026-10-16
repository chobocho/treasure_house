// SSE 서버 — node:http 만으로. 식단을 짜며 끼니마다 이벤트 하나를
// 흘려 보내고, 마지막에 합계를 보낸 뒤 연결을 닫는다.
import { createServer } from "node:http";
import { setTimeout as sleep } from "node:timers/promises";
import { parseArgs } from "node:util";
import { planMeals, type MealsRequest } from "../workshop/domain.ts";

const { values } = parseArgs({ options: { port: { type: "string" } } });
const port = Number(values.port);

// 이벤트로 보낼 객체들 — 끼니마다 하나, 끝에 합계.
function* events(req: MealsRequest): Generator<object> {
  const plan = planMeals(req);
  if (!plan.ok) {
    yield plan;
    return;
  }
  for (const s of plan.slots) {
    yield {
      slot: s.slot,
      regular: s.regular?.name,
      vegetarian: s.vegetarian?.name,
    };
  }
  yield { total: plan.total };
}

// region: stream
const server = createServer(async (req, res) => {
  let body = "";
  for await (const chunk of req) body += chunk;
  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
  });
  let count = 0;
  for (const ev of events(JSON.parse(body))) {
    // 이벤트 하나 = "data: …" 줄 + 빈 줄. write 는 바로 내보낸다
    res.write(`data: ${JSON.stringify(ev)}\n\n`);
    count++;
    await sleep(50); // 식단 짜는 시간인 셈
  }
  res.end(); // 응답을 끝내는 것이 곧 스트림의 끝
  console.log(`이벤트 ${count}개를 보내고 닫음`);
});
// endregion

server.listen(port, "127.0.0.1", () => {
  console.log(`SSE 서버(ts): 127.0.0.1:${port}`);
});
//@ norun
