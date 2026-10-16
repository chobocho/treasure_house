// contextId·taskId 규칙(§3.4)을 접수 에이전트에 차례로 두드려 본다.
// 여섯 번 보내고, 답의 상태·작업 id·맥락 id 나 오류를 한 줄씩 찍는다.
//   node 04/ctx_rules.ts 카드주소
import { Role, taskStateToJSON, type Task } from "@a2a-js/sdk";
import { ClientFactory, type Client } from "@a2a-js/sdk/client";
import { textPart } from "../agents/common.ts";

let n = 0; // messageId 가 겹치지 않게

// region: send
async function send(
  c: Client,
  label: string,
  text: string,
  taskId = "", // "" 이면 와이어에 나가지 않는다
  contextId = "",
): Promise<Task | undefined> {
  const message = {
    ...{ messageId: `ctx-ts-${++n}`, taskId, contextId },
    ...{ role: Role.ROLE_USER, parts: [textPart(text)] },
    ...{ metadata: undefined, extensions: [], referenceTaskIds: [] },
  };
  try {
    const t = (await c.sendMessage({
      ...{ tenant: "", message, configuration: undefined },
      metadata: undefined,
    })) as Task;
    const st = taskStateToJSON(t.status!.state).replace(
      "TASK_STATE_",
      "",
    );
    console.log(`${label} ${st} task=${t.id} ctx=${t.contextId}`);
    return t;
  } catch (e) {
    const err = e as Error;
    console.log(`${label} ${err.constructor.name}: ${err.message}`);
  }
}
// endregion

const c = await new ClientFactory().createFromUrl(process.argv[2]!);
// region: rules
const t1 = (await send(c, "①", "워크숍 접수"))!;
await send(c, "②", "20명", "", t1.contextId);
await send(c, "③", "30명", t1.id, "ctx-다른-맥락");
await send(c, "④", "30명", t1.id);
await send(c, "⑤", "30명", "t-없는-작업");
await send(c, "⑥", "25명", "", "ctx-워크숍");
// endregion
//@ norun
