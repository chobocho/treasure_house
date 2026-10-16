// 맨손 Task 저장소 — Map 하나와 상태 전이 표.
//
// bare_lodging.ts(맨손 숙소 에이전트)가 쓰고, store_rules.ts 가 전이
// 규칙을 시험한다. node:crypto 의 randomUUID 말고는 언어 기본만 쓴다.
import { randomUUID } from "node:crypto";

// region: types
// 와이어의 JSON 모양 그대로 — 파트는 받은 객체를 손대지 않고 둔다.
export type Part = Record<string, unknown>;
export type Message = {
  messageId: string;
  contextId?: string;
  taskId?: string;
  role: string;
  parts: Part[];
  [more: string]: unknown; // metadata·extensions… 받은 그대로
};
export type Status = {
  state: string;
  message?: Message;
  timestamp: string;
};
export type Artifact = {
  artifactId: string;
  name: string;
  parts: Part[];
};
export type Task = {
  id: string;
  contextId: string;
  status: Status;
  artifacts: Artifact[];
  history: Message[];
};
type Ids = { taskId: string; contextId: string };
export type StreamResponse =
  | { task: Partial<Task> }
  | { statusUpdate: Ids & { status: Status } }
  | { artifactUpdate: Ids & { artifact: Artifact } };
// endregion

// region: states
export const SUBMITTED = "TASK_STATE_SUBMITTED";
export const WORKING = "TASK_STATE_WORKING";
export const INPUT_REQUIRED = "TASK_STATE_INPUT_REQUIRED";
export const AUTH_REQUIRED = "TASK_STATE_AUTH_REQUIRED";
export const COMPLETED = "TASK_STATE_COMPLETED";
export const FAILED = "TASK_STATE_FAILED";
export const CANCELED = "TASK_STATE_CANCELED";
export const REJECTED = "TASK_STATE_REJECTED";
const TERMINAL = [COMPLETED, FAILED, CANCELED, REJECTED];

// 지금 상태 → 옮겨 갈 수 있는 상태. 스펙에는 이런 표가 없다(5부).
// 뒤로(SUBMITTED) 가지 않고, 종료 넷에서는 나갈 곳이 없다.
const ALLOWED: Record<string, string[]> = {
  [SUBMITTED]: [WORKING, INPUT_REQUIRED, AUTH_REQUIRED, ...TERMINAL],
  [WORKING]: [WORKING, INPUT_REQUIRED, AUTH_REQUIRED, ...TERMINAL],
  [INPUT_REQUIRED]: [WORKING, CANCELED],
  [AUTH_REQUIRED]: [WORKING, CANCELED],
};

// 표에 없는 전이 — 실행기의 버그다(요청 쪽 잘못이 아니다).
export class IllegalMove extends Error {}

export const canMove = (src: string, dst: string) =>
  ALLOWED[src]?.includes(dst) ?? false; // 종료 상태는 표에 없다
// endregion

// region: ids
// 작업·맥락·메시지·아티팩트 id — UUID 판 4(무작위).
export const newId = () => randomUUID();

// §5.6.1 의 꼴 — UTC, 밀리초, 끝은 Z. toISOString 이 바로 그 꼴이다.
export const now = () => new Date().toISOString();
// endregion

// region: store
// taskId → Task. 이 프로세스의 메모리에만 산다.
export class Store {
  tasks = new Map<string, Task>();

  // 첫 메시지로 새 Task 를 짓는다 — 상태는 SUBMITTED.
  create(msg: Message): Task {
    const task: Task = {
      id: newId(),
      // 클라이언트가 맥락을 정해 왔으면 그대로 쓴다(§3.4.1)
      contextId: msg.contextId || newId(),
      status: { state: SUBMITTED, timestamp: now() },
      artifacts: [],
      history: [],
    };
    this.tasks.set(task.id, task);
    this.append(task, msg);
    return task;
  }

  get(taskId: string): Task | undefined {
    return this.tasks.get(taskId);
  }

  // 받은 메시지를 이력에 넣는다 — 두 id 를 채워서.
  append(task: Task, msg: Message) {
    const { messageId, ...rest } = msg;
    const ids = { contextId: task.contextId, taskId: task.id };
    // 키 차례는 proto 대로: messageId, contextId, taskId, 나머지
    task.history.push({ messageId, ...ids, ...rest, ...ids });
  }
}
// endregion

// region: move
// 상태를 옮기고, 그 일을 알리는 스트림 이벤트를 돌려준다.
// 지난 상태의 메시지(에이전트의 물음)는 이력으로 내린다.
export function move(
  task: Task,
  state: string,
  parts?: Part[],
): StreamResponse {
  const src = task.status.state;
  if (!canMove(src, state)) throw new IllegalMove(`${src} → ${state}`);
  if (task.status.message) task.history.push(task.status.message);
  const message: Message | undefined = parts && {
    messageId: newId(),
    contextId: task.contextId,
    taskId: task.id,
    role: "ROLE_AGENT",
    parts,
  };
  const status: Status = message
    ? { state, message, timestamp: now() }
    : { state, timestamp: now() };
  task.status = status; // 고치지 않고 갈아 끼운다 — 앞 이벤트가 안전
  const ids = { taskId: task.id, contextId: task.contextId };
  return { statusUpdate: { ...ids, status } };
}
// endregion

// region: artifact
// 아티팩트를 붙이고, 그 일을 알리는 스트림 이벤트를 돌려준다.
export function addArtifact(
  task: Task,
  name: string,
  parts: Part[],
): StreamResponse {
  const artifact = { artifactId: newId(), name, parts };
  task.artifacts.push(artifact);
  const ids = { taskId: task.id, contextId: task.contextId };
  return { artifactUpdate: { ...ids, artifact } };
}
// endregion

// region: view
// 와이어로 내보낼 Task — 빈 목록은 빼고, 이력은 최근 N 개만.
// 목록은 새로 만들어 담는다: 작업이 더 바뀌어도 내보낼 모습은 그대로.
export function view(
  task: Task,
  historyLength?: number,
): Partial<Task> {
  const { id, contextId, status } = task;
  const out: Partial<Task> = { id, contextId, status };
  if (task.artifacts.length > 0) out.artifacts = [...task.artifacts];
  let hist = task.history;
  if (historyLength !== undefined) {
    // 0 이면 이력 없이(§3.2.4)
    hist = historyLength > 0 ? hist.slice(-historyLength) : [];
  }
  if (hist.length > 0) out.history = [...hist];
  return out;
}
// endregion
//@ norun
