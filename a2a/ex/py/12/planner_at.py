# 기획 에이전트(agents/planner.py)를 동료 넷의 포트만 받아 띄운다 —
# 주소 넷을 쉼표로 이은 --agents 가 명세 한 줄(72칸)에 들어가지 않아서.
#   python 12/planner_at.py 포트 동료포트…
import runpy
import sys

port, *peers = sys.argv[1:]
agents = ",".join(f"http://127.0.0.1:{p}/" for p in peers)
sys.argv = ["planner.py", "--port", port, "--agents", agents]
runpy.run_module("agents.planner", run_name="__main__")
# @ norun
