# 고치기 전의 as_ints — agents/common.py 의 2026-10-18 판을 그대로
# 옮겼다. 16/test_ints.py 를 old 로 부르면 이것을 시험한다(RED).
def as_ints(d: dict, *keys) -> dict:
    return {k: int(v) if k in keys else v for k, v in d.items()}


# @ norun
