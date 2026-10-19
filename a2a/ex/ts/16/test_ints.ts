// 고친 agents/common.ts 의 asInts 를 시험한다.
//   node 16/run_tests.ts
import { asInts } from "../agents/common.ts";
import { cases } from "./ints_cases.ts";

cases(asInts);
//@ norun
