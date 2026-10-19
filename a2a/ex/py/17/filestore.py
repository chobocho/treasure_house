"""Task 를 파일 하나씩(JSON)으로 두는 저장소 — SDK 의 TaskStore.

교재용이라 작게: 소유자 구분·페이지 토큰은 뺐고, 목록은 파일을
다 읽는다.
"""

import os
import re
from pathlib import Path

from a2a.helpers.proto_helpers import new_text_part
from a2a.server.tasks import TaskStore
from a2a.types import (
    ListTasksResponse,
    Message,
    Role,
    Task,
    TaskState,
)
from google.protobuf import json_format

LIVE = (TaskState.TASK_STATE_SUBMITTED, TaskState.TASK_STATE_WORKING)


class FileTaskStore(TaskStore):
    def __init__(self, folder):
        self.dir = Path(folder)
        self.dir.mkdir(parents=True, exist_ok=True)

    # region: path
    def _path(self, task_id):
        # taskId 는 클라이언트가 보낸 글자다 — 파일 이름이 되기 전에
        # 거른다
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", task_id):
            return None
        return self.dir / f"{task_id}.json"

    # endregion

    # region: save
    async def save(self, task, context):
        path = self._path(task.id)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json_format.MessageToJson(task), encoding="utf-8"
        )
        os.replace(
            tmp, path
        )  # 바꿔 끼우기는 원자적 — 반쯤 쓴 파일이 없다

    async def get(self, task_id, context):
        path = self._path(task_id)
        if path is None or not path.exists():
            return None  # 처리기가 TaskNotFoundError(-32001)로 바꾼다
        return json_format.Parse(
            path.read_text(encoding="utf-8"), Task()
        )

    # endregion

    # region: list
    async def list(self, params, context):
        tasks = [
            await self.get(p.stem, context)
            for p in self.dir.glob("*.json")
        ]
        if params.context_id:
            tasks = [
                t for t in tasks if t.context_id == params.context_id
            ]
        if params.status:
            tasks = [
                t for t in tasks if t.status.state == params.status
            ]
        # 새것부터(상태 시각), 같으면 id — InMemoryTaskStore 와 같다
        tasks.sort(
            key=lambda t: (t.status.timestamp.ToNanoseconds(), t.id),
            reverse=True,
        )
        size = params.page_size or 50
        return ListTasksResponse(
            tasks=tasks[:size], total_size=len(tasks), page_size=size
        )

    async def delete(self, task_id, context):
        path = self._path(task_id)
        if path is not None:
            path.unlink(missing_ok=True)

    # endregion

    # region: recover
    async def recover(self):
        """띄울 때 한 번: 실행기 없는 SUBMITTED·WORKING 을 닫는다."""
        for p in sorted(self.dir.glob("*.json")):
            task = await self.get(p.stem, None)
            if task.status.state not in LIVE:
                continue
            was = TaskState.Name(task.status.state).removeprefix(
                "TASK_STATE_"
            )
            task.status.state = TaskState.TASK_STATE_FAILED
            task.status.message.CopyFrom(
                Message(
                    message_id=f"recover-{task.id}",
                    task_id=task.id,
                    context_id=task.context_id,
                    role=Role.ROLE_AGENT,
                    parts=[
                        new_text_part("서버가 다시 시작되어 끊겼습니다")
                    ],
                )
            )
            task.status.timestamp.GetCurrentTime()
            await self.save(task, None)
            print(f"[복구] {task.id} {was} → FAILED", flush=True)

    # endregion


# @ norun
