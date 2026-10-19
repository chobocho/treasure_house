"""완성 에이전트를 한 줄도 고치지 않고 띄우며 요청 로그를 단다.

    python 17/logged.py 이름 [그 에이전트의 인자…]

이름은 agents/ 의 모듈(lodging, catering, bus, settlement, planner).
--sdk 를 맨 앞에 주면 SDK 자신의 logging 기록도 표준 출력으로 켠다
(INFO, 그리고 JSON-RPC 를 받는 모듈 하나만 DEBUG).
"""

import logging
import runpy
import sys

import uvicorn
from jsonlog import JsonLog

args = sys.argv[1:]
if args[0] == "--sdk":
    args = args[1:]
    # region: sdk
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,  # SDK 전체는 INFO
        # 메시지는 170자에서 자른다(화면 폭)
        format="%(levelname)s %(module)s: %(message).170s",
    )
    # 요청을 받는 곳 하나만 DEBUG — 받은 본문을 통째로 적는다
    rpc = logging.getLogger("a2a.server.routes.jsonrpc_dispatcher")
    rpc.setLevel(logging.DEBUG)
    # endregion

# region: wrap
name, *rest = args
serve = uvicorn.run  # agents/common.py 의 serve() 가 끝에 부르는 함수


def logged(app, **kw):  # 앱 바깥을 미들웨어로 한 겹 감싼다
    serve(JsonLog(app, name), **kw)


uvicorn.run = logged
sys.argv = [f"{name}.py", *rest]
runpy.run_module(f"agents.{name}", run_name="__main__")
# endregion
# @ norun
