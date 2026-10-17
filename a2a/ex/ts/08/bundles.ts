// 번들마다 오류 클래스의 사본이 따로 있다 — 그래도 instanceof 가 되나.
//   node 08/bundles.ts
import { AgentCard, GetTaskRequest } from "@a2a-js/sdk";
import { A2AError, TaskNotFoundError } from "@a2a-js/sdk/errors";
import {
  DefaultRequestHandler,
  InMemoryTaskStore,
  JsonRpcTransportHandler,
  ServerCallContext,
} from "@a2a-js/sdk/server";

const handler = new DefaultRequestHandler(
  AgentCard.fromJSON({ name: "시험" }),
  new InMemoryTaskStore(),
  { execute: async () => {}, cancelTask: async () => {} },
);

// region: catch
// 처리기(./server 번들)가 던진 오류를 ./errors 의 클래스로 잡는다
try {
  const req = GetTaskRequest.fromJSON({ id: "t-없음" });
  await handler.getTask(req, new ServerCallContext());
} catch (e) {
  const err = e as Error;
  console.log("던진 것:", err.name, "—", err.message);
  console.log(
    "  같은 클래스인가:",
    err.constructor === TaskNotFoundError,
  );
  const exact = e instanceof TaskNotFoundError;
  console.log("  instanceof TaskNotFoundError:", exact);
  console.log("  instanceof A2AError:", e instanceof A2AError);
}
// endregion

// region: brand
// 이름만 같은 우리 클래스 — SDK 의 표식(Symbol.for)이 없다
class LookAlike extends Error {
  override name = "TaskNotFoundError";
}
const toRpc = JsonRpcTransportHandler.mapToJSONRPCError;
for (const e of [new TaskNotFoundError("t-1"), new LookAlike("t-1")]) {
  const { code, message } = toRpc(e);
  console.log(`${e.constructor.name.padEnd(18)} → ${code} ${message}`);
}
// endregion
