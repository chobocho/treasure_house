# 교통 에이전트에 SSRF 검사를 켠 판 — 실행기와 카드는 agents/bus.py 의
# 것을 그대로 쓰고, 요청 처리기와 보내는 것에 push_url_validator 를
# 단다(파이썬 SDK 의 기본값은 None — 검사하지 않는다).
#   python 11/guarded.py --port P
import httpx
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
)
from a2a.utils.push_url_validator import validate_push_notification_url

from agents.bus import BusExecutor, card
from agents.common import parse_args, serve

args = parse_args(
    "SSRF 검사를 켠 교통 에이전트", step_ms=("단계(ms)", 300)
)
# region: guard
store = InMemoryPushNotificationConfigStore()
sender = BasePushNotificationSender(
    httpx.AsyncClient(),
    store,
    push_url_validator=validate_push_notification_url,  # 보낼 때 또
)
serve(
    card(args.url),
    BusExecutor(args.step_ms),
    args.port,
    push_config_store=store,
    push_sender=sender,
    push_url_validator=validate_push_notification_url,  # 받을 때
)
# endregion
# @ norun
