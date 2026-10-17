# 3단계 — 모자란 것을 되묻는 숙소 에이전트. 아직 결함이 하나 있다.
#   python 07/step3_ask.py --port P [--url U]
# 질문 목록·글 읽기·카드는 완성판(agents/lodging.py)의 것을 빌린다.
# 완성판과 다른 곳은 실행기의 "무엇을 들었나" 한 줄과 로그뿐이다.
import json

from a2a.helpers import get_message_text, new_data_part, new_text_part
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater

from agents.common import as_ints, begin, data_of, parse_args, serve
from agents.lodging import QUESTIONS, card, from_text
from workshop import domain


# region: executor
class AskExecutor(AgentExecutor):
    async def execute(self, ctx: RequestContext, queue: EventQueue):
        task, up = await begin(ctx, queue)  # 이번 메시지까지 이력에
        heard = list(task.history)  # 이력 전부 — 이것이 결함이다
        req = data_of(*heard)
        for m in heard:
            req.update(from_text(get_message_text(m)))
        print("[3단계] 들은 것:", json.dumps(req, sort_keys=True))
        missing = [k for k in QUESTIONS if k not in req]
        if missing:  # 첫째 빠진 것을 묻고, 빠진 목록은 데이터로
            ask = up.new_agent_message(
                [
                    new_text_part(QUESTIONS[missing[0]]),
                    new_data_part({"missing": missing}),
                ]
            )
            await up.requires_input(ask)  # 중단 상태 — 다음 말을 기다림
            return
        quote = domain.choose_lodging(
            as_ints(req, "nights", "headcount")
        )
        if not quote["ok"]:
            reason = new_text_part(quote["reason"])
            await up.reject(up.new_agent_message([reason]))
            return
        await up.add_artifact([new_data_part(quote)], name="숙소 견적")
        await up.complete()

    async def cancel(self, ctx: RequestContext, queue: EventQueue):
        task = ctx.current_task
        await TaskUpdater(queue, task.id, task.context_id).cancel()


# endregion

if __name__ == "__main__":
    args = parse_args("3단계 숙소 에이전트")
    serve(card(args.url), AskExecutor(), args.port)
# @ norun
