# OUTLINE — chapter contract per part

Each part's author may refine slide-level content but must keep the chapter list, the
"owns" list (concepts first taught here — later parts link back instead of re-teaching),
and the budget (`deck/budget.txt`). Examples live under `ex/<lang>/NN/` and
`ex/run/NN/`; ports 10000 + NN·100 + k. "×3" means the example exists in py, ts and go and
the slides show each (usually one slide per language + one comparison slide).

Spec references are to `docs/spec/docs/specification.md` (§) and `a2a.proto`.

---

## 0부 읽는 법·시나리오·환경 (00_start, 40)
1. 이 책의 약속 — 돌아가는 코드만, 캡처가 증거, 스펙 v1.0.1·SDK 판(표), 2026-10 기준
2. 시나리오 한눈에 — 보물상사 워크숍, 다섯 에이전트, 기능 지도(SCENARIO §3 표를 슬라이드로)
3. 환경 준비 ×3 — venv·pip 고정판, npm(tsc 7 안드로이드 별칭 사연), go mod; 버전 확인 캡처
4. 캡처 읽는 법 — `[터미널 N]`, 와이어 탭(wiretap.py)과 `--url`, 정규화 표(`<id1>`, `<시각>`)
5. 길잡이 — 부별 지도, 읽는 순서(언어 하나만 따라가도 되는 길)
Owns: capture conventions, wiretap, normalisation.

## 1부 왜 A2A인가 — MCP와의 관계·역사 (01_why, 60)
1. 문제 — 에이전트끼리 말하는 표준이 없을 때(통합 N×M, 불투명 실행)
2. A2A의 설계 원칙 — §1.1–1.2 (불투명성, 기존 표준 재사용, 장기 작업, 모달리티 무관)
3. MCP와 A2A — 도구 호출 vs 동료 위임, 함께 쓰는 그림(사실은 출처로)
4. 역사 — 2025-04 발표, 2025-06 리눅스 재단 이관, 0.2·0.3, 1.0(2026-03), 1.0.1 — 모두 SRC/FACT
5. v0.3 → v1.0 무엇이 바뀌었나 — whats-new-v1.md 요약(메서드 이름, enum, kind 제거, supportedInterfaces)
6. 스펙 문서 구조 — 계층(데이터 모델/추상 연산/바인딩), proto 가 규범
Owns: design principles, history, v0.3→v1.0 diff overview (details later where used).

## 2부 바탕 지식 — HTTP·JSON-RPC 2.0·SSE (02_basics, 70)
1. HTTP 한 장 요약과 curl — 요청/응답, 헤더, 상태 코드 (wiretap 첫 등장)
2. JSON 다루기 ×3 — 직렬화·역직렬화, camelCase, 정수와 큰 수, `null`과 빠진 필드
3. JSON-RPC 2.0 ×3 — request/response/error/notification, id, 배치(A2A 는 안 씀 — 확인)
4. SSE ×3 — `text/event-stream`, `data:` 줄, 빈 줄, 스트림 끝, 서버/클라이언트 맨손 구현
5. 비동기 모델 비교 — asyncio / Promise·async iterator / goroutine·channel (이후 SDK 이해용)
Owns: JSON-RPC 2.0, SSE wire format, per-language async primer.

## 3부 Agent Card와 발견 (03_card, 100)
1. 카드는 이력서 — 필수 필드(proto REQUIRED), 숙소 에이전트 카드 해부
2. well-known 경로 — `/.well-known/agent-card.json`, 카드 서빙 ×3 (맨손)
3. supportedInterfaces — url·protocolBinding·protocolVersion·tenant, 클라이언트의 선택(§8.3)
4. `--url` 과 프록시 — 카드의 url 은 바깥 주소 (wiretap 실연)
5. skills — id·tags·examples·inputModes/outputModes, 스킬로 에이전트 고르기 ×3
6. capabilities — streaming·pushNotifications·extensions·extendedAgentCard, 없는 기능을 부르면(§3.3.4)
7. 카드 캐싱 — §8.6, Cache-Control/ETag ×3
8. 카드 검증기 만들기 ×3 — 필수 필드 검사(우리 도구), 흔한 실수 모음
Owns: AgentCard fields, discovery, capability validation rule. (Security fields → 12부.)

## 4부 Message·Part·Role·contextId (04_message, 100)
1. Message 해부 — messageId·role·parts·contextId·taskId·referenceTaskIds·extensions·metadata
2. Part 네 가지 — text / raw(base64) / url / data, filename·mediaType, `kind` 가 사라진 이유
3. 메시지만 돌려주는 에이전트 — 즉답형(Message 응답) vs Task 응답 (§3.7)
4. DataPart 로 구조화 입력 — 숙소 요청 `{date,nights,headcount}` ×3
5. FilePart — raw 와 url, 큰 파일은 url 로, mediaType 협상(acceptedOutputModes)
6. contextId 규칙 — 서버 생성·보존·불일치 거절(§3.4.1)
7. messageId 와 멱등성 — 중복 메시지 감지(§3.3.1)
8. ProtoJSON 규칙 — camelCase, enum 문자열, 빠진 필드(§5.5–5.7)
Owns: Message/Part model, ProtoJSON rules, contextId semantics.

## 5부 Task 생애주기 (05_task, 120)
1. 왜 Task 인가 — 상태가 있는 일 단위, Message 와의 차이
2. TaskState 9가지 — 상태 기계 그림, 종료/중단 상태 구분
3. blocking 과 returnImmediately — §3.2.2 실측
4. 숙소 에이전트: COMPLETED + artifact — 3~5부는 완성 에이전트(`ex/*/agents/`, 15부가
   해설)를 **블랙박스로** 띄우고 curl·wiretap 으로 와이어를 읽는다. 만드는 법은 6부(맨손)와
   7~9부(SDK)가 소유한다.
5. INPUT_REQUIRED 다중 턴 — 같은 taskId·contextId 로 이어 말하기
6. REJECTED·FAILED·CANCELED — 차이와 실제 응답
7. GetTask 와 historyLength — §3.2.4 세 경우 실측
8. Artifact — artifactId·name·parts, 메시지가 아니라 아티팩트로 결과를(§3.7)
9. 오류 — TaskNotFound(-32001), 종료된 task 에 메시지 보내기
Owns: TaskState machine, blocking vs immediate, multi-turn, artifacts basics.

## 6부 맨손 구현 (06_bare, 130)
1. 목표 — SDK 없이 v1.0 JSON-RPC 서버·클라이언트 (숙소 에이전트 축소판) ×3
2. 라우팅·JSON-RPC 디스패치·오류 코드 ×3
3. Task 저장소·상태 전이 ×3
4. SendMessage·GetTask·CancelTask ×3
5. SendStreamingMessage (SSE) 맨손 ×3
6. 맨손 클라이언트 ×3 — 카드 읽기 → 인터페이스 고르기 → 호출
7. 맨손 구현을 SDK 클라이언트로 두드려 보기 — 호환 확인(교차 3×3 축소판)
8. 맨손이 놓친 것 — 버전 헤더 검사, 동시성, 스트림 재구독 → SDK 가 해 주는 일
Owns: what an A2A server must do mechanically.

## 7부 공식 SDK — Python (07_py, 120)  ·  8부 TypeScript (08_ts, 120)  ·  9부 Go (09_go, 120)
Same chapter shape in each (parallel structure on purpose):
1. 패키지 구조 지도 — 모듈/패키지와 역할 (설치된 소스에서)
2. 타입 — proto 생성 타입 다루기 (py protobuf 메시지 / ts-proto `$case` / Go 구조체·Part 접근자)
3. AgentExecutor — 실행기 인터페이스, 이벤트 큐/버스/iter.Seq2
4. 요청 처리기와 Task 저장소 — DefaultRequestHandler / NewHandler, InMemory 저장소
5. 서버 띄우기 — Starlette+uvicorn / Express / net/http, 카드 핸들러
6. 클라이언트 — create_client / ClientFactory / a2aclient.NewFromCard, 응답 형태
7. 숙소 에이전트 완성판 — INPUT_REQUIRED·REJECTED 포함, 골든 대조
8. 시험 — SDK 서버를 프로세스 안에서 시험하기
9. 이 SDK 만의 것 — (py) compat v0.3·db 저장소 / (ts) 다중 전송·express 미들웨어 / (go) 미들웨어·interceptor·a2aext
Owns: each SDK's API. Domain module `workshop` introduced in 7부 (py), mirrored in 8·9.

## 10부 스트리밍·아티팩트 조각·재구독 (10_stream, 120)
1. SendStreamingMessage 의 와이어 — SSE 이벤트 = StreamResponse(task/message/statusUpdate/artifactUpdate)
2. 식사 에이전트 ×3 — 끼니마다 상태 갱신, 식단표 조각(append·lastChunk)
3. 스트림 종료 규칙 — `final` 이 사라진 v1.0, 종료 상태에서 닫힘
4. 클라이언트에서 조각 다시 붙이기 ×3
5. SubscribeToTask — 끊긴 뒤 다시 붙기, 여러 구독자(§3.5.2)
6. FilePart(menu.md) + DataPart 견적
7. 스트리밍 미지원 카드에 스트림 요청 → UnsupportedOperation
Owns: streaming semantics, chunk reassembly, resubscribe.

## 11부 푸시 알림·장기 작업·취소·목록 (11_push, 120)
1. 교통 에이전트 ×3 — returnImmediately, 3단계 배차
2. 폴링 — GetTask 반복과 그 비용
3. 푸시 설정 — SendMessageConfiguration.taskPushNotificationConfig / Create…Config, token
4. 웹훅 수신기 ×3 — 페이로드(StreamResponse 형식), 토큰 검증, AuthenticationInfo
5. 푸시 설정 CRUD — Get/List/Delete
6. CancelTask — 진행 중 취소, 종료 후 취소(TaskNotCancelable -32002)
7. ListTasks — 필터·페이지 토큰
8. 웹훅 보안 — SSRF(파이썬 SDK push_url_validator), 서명/토큰
Owns: push notifications, cancel, list.

## 12부 보안 (12_security, 120)
1. 전송 보안 — HTTPS 요구(§7.1), 이 책이 로컬 http 를 쓰는 이유
2. securitySchemes·securityRequirements — 다섯 스킴 해부
3. 로컬 OAuth2 토큰 발급기 ×3 — client_credentials
4. 정산 에이전트 Bearer 검사 ×3, 401 과 WWW-Authenticate
5. 스코프 — intern 은 조회만, planner 는 승인까지
6. 확장 카드 — GetExtendedAgentCard, capabilities.extendedAgentCard
7. AUTH_REQUIRED — 작업 중 권한(§7.6), 승인 토큰으로 이어가기
8. 서명된 카드 — JCS(RFC 8785) + JWS(ES256), 서명·검증 ×3, 위조 카드 탐지
Owns: everything security.

## 13부 전송 바인딩 (13_binding, 90)
1. 세 바인딩의 동등성(§5.1)과 메서드 대응표(§5.3)
2. HTTP+JSON(REST) ×3 — 경로·동사, 오류 → HTTP 상태
3. gRPC ×3 — proto, 서버·클라이언트, 스트리밍, 오류 → gRPC status
4. 한 서버 세 바인딩 — supportedInterfaces 여러 개, 클라이언트 선택
5. 스펙의 어긋남 — SubscribeToTask REST 동사(proto GET vs §5.3 POST)와 SDK 실제 동작
Owns: REST and gRPC bindings, error mapping table.

## 14부 확장과 버전 협상 (14_ext, 60)
1. 확장 선언·활성화 — AgentExtension, `A2A-Extensions` 헤더, required
2. 예산 확장 ×3 — 메타데이터 계약, ExtensionSupportRequired(-32008)
3. 버전 — A2A-Version 헤더, 빈 값 = 0.3, VersionNotSupported(-32009)
4. v0.3 피어와 공존 — SDK 호환 계층(설치본에서 확인되는 것만)
Owns: extensions, versioning.

## 15부 시나리오 완성 (15_scenario, 140)
1. 기획 에이전트 설계 — 발견→팬아웃→정산→계획서
2. 에이전트 레지스트리와 스킬 매칭 ×3
3. 동시 위임 — 같은 contextId, asyncio.gather / Promise.all / errgroup
4. referenceTaskIds 로 정산 요청
5. 진행 상황 스트리밍 — 기획 에이전트 자신의 SSE
6. 전 과정 실행 — 언어별 단일 메시 ×3, 그다음 섞인 메시(예: 기획 py → 숙소 go·식사 ts·교통 py·정산 go)
7. 실패 경로 — 숙소 거절, 예산 초과, 교통 취소
Owns: orchestration patterns.

## 16부 상호운용·적합성·오류 처리 (16_interop, 90)
1. 3×3 매트릭스 — 다섯 에이전트 × 세 클라이언트 언어, 표로 결과
2. 와이어 차이 — 빈 필드 직렬화 등 언어별 차이, 그래도 호환되는 이유
3. 오류 표 전수 — -32001…-32009 를 실제로 일으키기
4. 적합성 시험 — (설치·실행 가능하면) 공식 TCK, 아니면 우리 체크리스트
Owns: interop evidence.

## 17부 운영 (17_ops, 70)
1. 타임아웃·재시도·멱등성 ×3
2. 영속 Task 저장소 — SDK TaskStore 인터페이스로 파일 저장소 ×3, 재시작 후 GetTask
3. 로깅·추적 — 요청 id, contextId 로 흐름 잇기
4. 배포 체크리스트 — HTTPS, 카드 url, 캐시, 키 교체
Owns: operations.

## 18부 부록 (18_appendix, 60)
오류 코드표, 메서드 대응표, 필드 사전(proto 에서 생성), 용어집(glossary.tsv), 찾아보기,
출처 목록, 퀴즈 모음 링크.
