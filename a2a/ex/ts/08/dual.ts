// 한 패키지, 두 모듈 체계 — import(ESM) 와 require(CommonJS).
//   node 08/dual.ts
import { createRequire } from "node:module";
import { relative } from "node:path";
import * as esm from "@a2a-js/sdk/errors";
import { TaskState as EsmState } from "@a2a-js/sdk";

// region: dual
const require = createRequire(import.meta.url);
const cjs = require("@a2a-js/sdk/errors") as typeof esm; // index.cjs
const { TaskState: CjsState } = require("@a2a-js/sdk");
const file = relative(".", require.resolve("@a2a-js/sdk"));
console.log("require 가 읽은 파일:", file);
const same = cjs.TaskNotFoundError === esm.TaskNotFoundError;
console.log("두 TaskNotFoundError 는 같은 클래스인가:", same);
const thrown = new cjs.TaskNotFoundError("CommonJS 쪽에서 던짐");
const isEsm = thrown instanceof esm.TaskNotFoundError;
console.log("ESM 클래스로 instanceof:", isEsm);
console.log(
  "ESM A2AError 로 instanceof:",
  thrown instanceof esm.A2AError,
);
const enums = CjsState === EsmState;
console.log("TaskState 객체는 같은가:", enums);
const value =
  CjsState.TASK_STATE_COMPLETED === EsmState.TASK_STATE_COMPLETED;
console.log("TASK_STATE_COMPLETED 값은 같은가:", value);
// endregion
