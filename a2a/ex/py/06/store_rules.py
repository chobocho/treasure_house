# 맨손 저장소의 전이 표 시험 — 작업 하나를 만들어 이리저리 옮겨 본다.
from bare_store import (
    CANCELED,
    COMPLETED,
    INPUT_REQUIRED,
    SUBMITTED,
    WORKING,
    IllegalMove,
    Store,
    move,
)

store = Store()
first = {"messageId": "m1", "role": "ROLE_USER"}
first["parts"] = [{"text": "2026-10-30 1박 숙소"}]
task = store.create(first)


def short(state):
    return state.removeprefix("TASK_STATE_")


def show():
    roles = [m["role"].removeprefix("ROLE_") for m in task["history"]]
    state = short(task["status"]["state"])
    print(f"   지금 {state}, 이력 {' '.join(roles)}")


# region: try
def attempt(state, parts=None):
    try:
        move(task, state, parts)
    except IllegalMove as e:
        print(f"{short(state):>14} 거부 — {e}")
        return
    print(f"{short(state):>14} 옮김")
    show()


show()
attempt(INPUT_REQUIRED, [{"text": "인원은 몇 명입니까?"}])
attempt(COMPLETED)  # 답을 듣기 전에 끝낼 수는 없다
attempt(WORKING)  # 답이 왔다 — 물음은 이력으로
store.append(task, {"messageId": "m2", "role": "ROLE_USER"})
show()
attempt(SUBMITTED)  # 뒤로 가지 않는다
attempt(COMPLETED)
attempt(WORKING)  # 종료 뒤에는 나갈 곳이 없다
attempt(CANCELED)
# endregion
