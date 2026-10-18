"""카드만 있고 문지기는 없는 정산 에이전트.

완성 정산 에이전트(agents/settlement.py)의 카드와 실행기를 그대로
가져다 쓰고, 토큰을 검사하는 미들웨어만 뺐다. 카드가 OAuth2 를 요구해도
서버가 검사하지 않으면 아무 일도 일어나지 않는다는 것을 보려는 것.
    python 12/card_only.py --port P
"""

from agents.common import parse_args, serve
from agents.settlement import SettlementExecutor, card

# region: main
if __name__ == "__main__":
    args = parse_args("카드만 있는 정산 에이전트")
    # 같은 카드, 같은 실행기 — routes·middleware 를 넘기지 않았다
    serve(card(args.url), SettlementExecutor(), args.port)
# endregion
# @ norun
