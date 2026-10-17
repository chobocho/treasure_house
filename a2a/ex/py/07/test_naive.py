# 같은 시험을 3단계(이력 전부를 듣는 판)에 돌린다 — 빨간불 확인.
#   python 07/test_naive.py
import test_lodging as base
from step3_ask import AskExecutor


# region: naive
class NaiveTests(base.Tests):
    executor = AskExecutor  # 시험은 그대로, 실행기만 3단계로


# endregion

if __name__ == "__main__":
    base.main()
# @ exit: 1
# @ timeout: 60
