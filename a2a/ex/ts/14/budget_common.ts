// 완성 숙소 에이전트가 부르는 agents/common.ts 대신 끼우는 모듈.
// 나머지는 진짜 common.ts 를 그대로 내보내고 serve 만 바꾼다 — 카드에
// 예산 확장을 적고 실행기를 감싼 뒤 진짜 serve 에 넘긴다.
import type { Artifact } from "@a2a-js/sdk";
import { RequestMalformedError } from "@a2a-js/sdk/errors";
import type {
  AgentExecutor,
  ExecutionEventBus,
  RequestContext,
} from "@a2a-js/sdk/server";
import { serve as plain } from "../agents/common.ts";

export * from "../agents/common.ts";

export const URI = "https://treasure-house.example/a2a/ext/budget/v1";
// 14/budget_agent.ts 가 정한다
export const options = { required: false };

// region: declare
type Card = { capabilities: Record<string, unknown> };
function declare(card: Card) {
  card.capabilities.extensions = [
    {
      uri: URI,
      description: "예산 상한(원)을 받아 견적과 견줍니다.",
      required: options.required,
      params: { currency: "KRW" },
    },
  ];
}
// endregion

// region: mark
// 지나가는 아티팩트에 예산 판정을 덧붙인다.
function mark(art: Artifact, limit: number) {
  const c = art.parts[0]?.content;
  const total = c?.$case === "data" ? Number(c.value.total) : NaN;
  art.extensions = [...art.extensions, URI];
  const within = total <= limit;
  art.metadata = { ...art.metadata, [URI]: { limit, within } };
}
// endregion

// region: executor
class Budget implements AgentExecutor {
  inner: AgentExecutor;
  constructor(inner: AgentExecutor) {
    this.inner = inner;
  }
  async execute(ctx: RequestContext, bus: ExecutionEventBus) {
    // 카드에 없는 확장은 SDK 가 이미 걸러 냈고, required 인데 머리글이
    // 없으면 SDK 가 여기 오기 전에 -32008 로 돌려보냈다.
    if (!ctx.context.requestedExtensions?.includes(URI)) {
      return this.inner.execute(ctx, bus);
    }
    const meta = ctx.userMessage.metadata?.[URI];
    if (typeof meta?.limit !== "number") {
      throw new RequestMalformedError("예산 확장: limit 이 없습니다");
    }
    ctx.context.addActivatedExtension(URI); // 응답 머리글이 된다
    const marked = new Proxy(bus, {
      get(t, k) {
        if (k !== "publish") return Reflect.get(t, k).bind(t);
        return (ev: Parameters<ExecutionEventBus["publish"]>[0]) => {
          if (ev.kind === "artifactUpdate" && ev.data.artifact) {
            mark(ev.data.artifact, meta.limit);
          }
          t.publish(ev);
        };
      },
    });
    return this.inner.execute(ctx, marked);
  }
  cancelTask(taskId: string, bus: ExecutionEventBus) {
    return this.inner.cancelTask(taskId, bus);
  }
}
// endregion

export function serve(
  card: Card,
  executor: AgentExecutor,
  port: number,
) {
  declare(card);
  plain(card, new Budget(executor), port);
}
//@ norun
