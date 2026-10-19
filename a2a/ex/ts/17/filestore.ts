// Task 를 파일 하나씩(JSON)으로 두는 저장소 — SDK 의 TaskStore.
// 교재용이라 작게: 소유자 구분·페이지 토큰은 뺐고, 목록은 파일을
// 다 읽는다.
import fs from "node:fs";
import path from "node:path";
import {
  Role,
  Task,
  TaskState,
  taskStateToJSON,
  type ListTasksRequest,
  type ListTasksResponse,
} from "@a2a-js/sdk";
import type { TaskStore } from "@a2a-js/sdk/server";
import { textPart } from "../agents/common.ts";

const LIVE = [
  TaskState.TASK_STATE_SUBMITTED,
  TaskState.TASK_STATE_WORKING,
];

export class FileTaskStore implements TaskStore {
  readonly dir: string;
  constructor(dir: string) {
    this.dir = dir;
    fs.mkdirSync(dir, { recursive: true });
  }

  // region: path
  // taskId 는 클라이언트가 보낸 글자다 — 파일 이름이 되기 전에 거른다
  private file(id: string) {
    if (!/^[A-Za-z0-9_-]{1,64}$/.test(id)) return undefined;
    return path.join(this.dir, `${id}.json`);
  }
  // endregion

  // region: save
  async save(task: Task) {
    const file = this.file(task.id)!;
    const tmp = `${file}.tmp`;
    fs.writeFileSync(tmp, JSON.stringify(Task.toJSON(task)));
    fs.renameSync(tmp, file); // 바꿔 끼우기는 원자적
  }

  async load(id: string) {
    const file = this.file(id);
    if (!file || !fs.existsSync(file)) return undefined; // → -32001
    return Task.fromJSON(JSON.parse(fs.readFileSync(file, "utf8")));
  }
  // endregion

  // region: list
  async list(p: ListTasksRequest): Promise<ListTasksResponse> {
    const ids = fs
      .readdirSync(this.dir)
      .filter((f) => f.endsWith(".json"))
      .map((f) => f.slice(0, -5));
    let tasks = (await Promise.all(ids.map((id) => this.load(id))))
      .filter((t) => t !== undefined)
      .filter((t) => !p.contextId || t.contextId === p.contextId)
      .filter((t) => !p.status || t.status?.state === p.status);
    // 새것부터(상태 시각), 같으면 id — InMemoryTaskStore 와 같은 차례
    const key = (t: Task) => `${t.status?.timestamp ?? ""} ${t.id}`;
    tasks.sort((a, b) => key(b).localeCompare(key(a)));
    const totalSize = tasks.length;
    const pageSize = p.pageSize ?? 50;
    tasks = tasks.slice(0, pageSize);
    // 아티팩트를 뺄지는 TS 에서는 저장소의 몫이다
    if (!p.includeArtifacts) for (const t of tasks) t.artifacts = [];
    return { tasks, nextPageToken: "", pageSize, totalSize };
  }
  // endregion

  // region: recover
  // 띄울 때 한 번: 실행기 없이 남은 SUBMITTED·WORKING 을 FAILED 로
  async recover() {
    for (const f of fs.readdirSync(this.dir).sort()) {
      if (!f.endsWith(".json")) continue;
      const t = (await this.load(f.slice(0, -5)))!;
      if (!LIVE.includes(t.status!.state)) continue;
      const was = taskStateToJSON(t.status!.state).slice(11);
      const text = "서버가 다시 시작되어 끊겼습니다";
      const message = {
        ...{ messageId: `recover-${t.id}`, taskId: t.id },
        ...{ contextId: t.contextId, role: Role.ROLE_AGENT },
        ...{ parts: [textPart(text)], metadata: undefined },
        ...{ extensions: [], referenceTaskIds: [] },
      };
      const timestamp = new Date().toISOString();
      const state = TaskState.TASK_STATE_FAILED;
      t.status = { state, message, timestamp };
      await this.save(t);
      console.log(`[복구] ${t.id} ${was} → FAILED`);
    }
  }
  // endregion
}
//@ norun
