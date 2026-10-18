# 고치기 전의 기획 에이전트(15/planner_old.py)를 동료의 포트만 받아
# 띄운다 — 12/planner_at.py 와 같은 겉층.
#   python 15/old_at.py 포트 동료포트…
import runpy
import sys
from pathlib import Path

port, *peers = sys.argv[1:]
agents = ",".join(f"http://127.0.0.1:{p}/" for p in peers)
sys.argv = ["planner_old.py", "--port", port, "--agents", agents]
old = Path(__file__).with_name("planner_old.py")
runpy.run_path(str(old), run_name="__main__")
# @ norun
