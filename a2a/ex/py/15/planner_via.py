# 기획 에이전트(agents/planner.py)를 탭 뒤에 띄운다 — 12/planner_at.py
# 에 카드에 적을 바깥 주소(탭의 포트)를 하나 더 받는다.
#   python 15/planner_via.py 포트 탭포트 동료포트…
import runpy
import sys

port, tap, *peers = sys.argv[1:]
agents = ",".join(f"http://127.0.0.1:{p}/" for p in peers)
url = f"http://127.0.0.1:{tap}/"
sys.argv = ["planner.py", "--port", port, "--url", url]
sys.argv += ["--agents", agents]
runpy.run_module("agents.planner", run_name="__main__")
# @ norun
